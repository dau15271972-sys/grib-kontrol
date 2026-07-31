package com.mushroom.detector.artifacts

import com.mushroom.detector.capture.CaptureViewType
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.math.sqrt

enum class SearchIndexFormat {
    USEARCH_HNSW,
    HNSWLIB,
    SQLITE_VEC1,
    EXACT_BASELINE
}

enum class SearchIndexLoadingMode {
    MEMORY_MAPPED,
    PAGE_BASED,
    SYNTHETIC_IN_MEMORY_ONLY
}

data class SearchIndexDescriptor(
    val regionId: String,
    val viewType: CaptureViewType,
    val embeddingModelId: String,
    val embeddingDimension: Int,
    val indexFormatVersion: String,
    val engine: SearchIndexFormat,
    val engineVersion: String,
    val metric: String,
    val shardCount: Int,
    val vectorCount: Long,
    val loadingMode: SearchIndexLoadingMode
)

object SearchIndexDescriptorContract {
    val jsonFields: Set<String> = setOf(
        "region_id", "view_type", "embedding_model_id", "embedding_dimension",
        "index_format_version", "engine", "engine_version", "metric", "vector_count",
        "shard_count", "loading_mode"
    )

    fun validateRawFields(fields: Set<String>): List<String> = buildList {
        (jsonFields - fields).sorted().forEach { add("missing field: $it") }
        (fields - jsonFields).sorted().forEach { add("unknown field: $it") }
    }
}

data class SearchQuery(
    val embedding: FloatArray,
    val regionId: String,
    val viewType: CaptureViewType,
    val embeddingModelId: String,
    val embeddingDimension: Int,
    val allowedTaxonIds: Set<String> = emptySet(),
    val excludedObservationIds: Set<String> = emptySet(),
    val topK: Int,
    val searchBudget: Int
)

data class SearchCandidate(
    val observationId: String,
    val referenceId: String,
    val taxonId: String,
    @Transient internal val internalDistance: Float,
    internal val dangerousEvidence: Boolean = false
)

data class SearchDiagnostics(
    val engine: SearchIndexFormat?,
    val visitedVectors: Int,
    val elapsedNanos: Long,
    val cancelled: Boolean,
    val unavailableReason: String? = null
)

sealed interface VectorSearchResult {
    data class Candidates(
        val values: List<SearchCandidate>,
        val diagnostics: SearchDiagnostics
    ) : VectorSearchResult

    data class Unavailable(
        val diagnostics: SearchDiagnostics
    ) : VectorSearchResult
}

fun interface SearchCancellation {
    fun isCancelled(): Boolean
}

class MutableSearchCancellation : SearchCancellation {
    private val cancelled = AtomicBoolean(false)

    fun cancel() {
        cancelled.set(true)
    }

    override fun isCancelled(): Boolean = cancelled.get()
}

interface VectorSearchEngine : AutoCloseable {
    fun search(query: SearchQuery, cancellation: SearchCancellation): VectorSearchResult
}

interface VectorSearchEngineFactory {
    fun open(descriptor: SearchIndexDescriptor): VectorSearchEngine
}

data class SearchExecutionPolicy(
    val executorCount: Int = 1,
    val maxThreads: Int = 1,
    val maxCandidateBuffer: Int = 512,
    val maxBufferBytes: Long = 8L * 1024L * 1024L
) {
    init {
        require(executorCount == 1) { "Exactly one managed search executor is allowed." }
        require(maxThreads in 1..2) { "Search thread count must remain bounded." }
        require(maxCandidateBuffer > 0)
        require(maxBufferBytes > 0)
    }
}

class ExactReranker {
    fun rerank(
        candidates: List<SearchCandidate>,
        exactDistances: Map<String, Float>
    ): List<SearchCandidate> = candidates
        .map { candidate ->
            val exactDistance = exactDistances[candidate.observationId]
                ?: candidate.internalDistance
            candidate.copy(internalDistance = exactDistance)
        }
        .sortedWith(
            compareBy<SearchCandidate> { it.internalDistance }
                .thenBy { it.observationId }
                .thenBy { it.referenceId }
        )
}

class UnavailableVectorSearchEngine(
    private val reason: String = "Search index is unavailable."
) : VectorSearchEngine {
    override fun search(
        query: SearchQuery,
        cancellation: SearchCancellation
    ): VectorSearchResult {
        @Suppress("UNUSED_VARIABLE")
        val ignored = query
        return VectorSearchResult.Unavailable(
            SearchDiagnostics(
                engine = null,
                visitedVectors = 0,
                elapsedNanos = 0,
                cancelled = cancellation.isCancelled(),
                unavailableReason = reason
            )
        )
    }

    override fun close() = Unit
}

data class SyntheticReferenceVector(
    val observationId: String,
    val referenceId: String,
    val taxonId: String,
    val regionId: String,
    val viewType: CaptureViewType,
    val embedding: FloatArray,
    val dangerousEvidence: Boolean = false
)

internal class SyntheticExactVectorSearchEngine(
    private val descriptor: SearchIndexDescriptor,
    vectors: List<SyntheticReferenceVector>,
    private val executionPolicy: SearchExecutionPolicy = SearchExecutionPolicy()
) : VectorSearchEngine {
    private var vectors: List<SyntheticReferenceVector>? = vectors
    val backingStoreIdentity: Int = System.identityHashCode(vectors)
    var closed: Boolean = false
        private set

    override fun search(
        query: SearchQuery,
        cancellation: SearchCancellation
    ): VectorSearchResult {
        val activeVectors = vectors
            ?: return UnavailableVectorSearchEngine("Search engine is closed.")
                .search(query, cancellation)
        if (
            descriptor.engine != SearchIndexFormat.EXACT_BASELINE ||
            descriptor.loadingMode != SearchIndexLoadingMode.SYNTHETIC_IN_MEMORY_ONLY ||
            query.regionId != descriptor.regionId ||
            query.viewType != descriptor.viewType ||
            query.embeddingModelId != descriptor.embeddingModelId ||
            query.embeddingDimension != descriptor.embeddingDimension ||
            query.embedding.size != descriptor.embeddingDimension ||
            query.topK <= 0 ||
            query.searchBudget <= 0
        ) {
            return UnavailableVectorSearchEngine("Search contract mismatch.")
                .search(query, cancellation)
        }

        val started = System.nanoTime()
        var visited = 0
        val bestByObservation = linkedMapOf<String, SearchCandidate>()
        for (reference in activeVectors) {
            if (cancellation.isCancelled() || visited >= query.searchBudget) break
            if (reference.regionId != query.regionId || reference.viewType != query.viewType) {
                continue
            }
            if (
                query.allowedTaxonIds.isNotEmpty() &&
                reference.taxonId !in query.allowedTaxonIds
            ) {
                continue
            }
            if (reference.observationId in query.excludedObservationIds) continue
            visited += 1
            val candidate = SearchCandidate(
                reference.observationId,
                reference.referenceId,
                reference.taxonId,
                cosineDistance(query.embedding, reference.embedding),
                reference.dangerousEvidence
            )
            val previous = bestByObservation[reference.observationId]
            if (
                previous == null ||
                compareValuesBy(
                    candidate,
                    previous,
                    SearchCandidate::internalDistance,
                    SearchCandidate::referenceId
                ) < 0
            ) {
                bestByObservation[reference.observationId] = candidate
            }
        }
        val values = bestByObservation.values
            .sortedWith(
                compareBy<SearchCandidate> { it.internalDistance }
                    .thenBy { it.observationId }
                    .thenBy { it.referenceId }
            )
            .take(minOf(query.topK, executionPolicy.maxCandidateBuffer))
        return VectorSearchResult.Candidates(
            values,
            SearchDiagnostics(
                descriptor.engine,
                visited,
                System.nanoTime() - started,
                cancellation.isCancelled()
            )
        )
    }

    override fun close() {
        vectors = null
        closed = true
    }

    private fun cosineDistance(left: FloatArray, right: FloatArray): Float {
        if (left.size != right.size) return 1f
        var dot = 0f
        var leftNorm = 0f
        var rightNorm = 0f
        for (index in left.indices) {
            dot += left[index] * right[index]
            leftNorm += left[index] * left[index]
            rightNorm += right[index] * right[index]
        }
        if (leftNorm == 0f || rightNorm == 0f) return 1f
        return 1f - dot / (sqrt(leftNorm) * sqrt(rightNorm))
    }
}

internal class SyntheticVectorSearchEngineFactory(
    vectors: List<SyntheticReferenceVector>,
    private val expectedEmbeddingModelId: String,
    private val expectedEmbeddingDimension: Int,
    private val expectedEngineVersion: String,
    private val expectedIndexFormatVersion: String
) : VectorSearchEngineFactory {
    private val sharedVectors = vectors.toList()

    override fun open(descriptor: SearchIndexDescriptor): VectorSearchEngine {
        if (
            descriptor.engine != SearchIndexFormat.EXACT_BASELINE ||
            descriptor.engineVersion != expectedEngineVersion ||
            descriptor.indexFormatVersion != expectedIndexFormatVersion ||
            descriptor.embeddingModelId != expectedEmbeddingModelId ||
            descriptor.embeddingDimension != expectedEmbeddingDimension ||
            sharedVectors.any { it.embedding.size != descriptor.embeddingDimension }
        ) {
            return UnavailableVectorSearchEngine("Incompatible search index descriptor.")
        }
        return SyntheticExactVectorSearchEngine(descriptor, sharedVectors)
    }
}

class ProductionVectorSearchEngineFactory : VectorSearchEngineFactory {
    override fun open(descriptor: SearchIndexDescriptor): VectorSearchEngine {
        @Suppress("UNUSED_VARIABLE")
        val requestedDescriptor = descriptor
        // SAFETY: no native engine is approved in Stage B0; exact baseline is synthetic-only.
        return UnavailableVectorSearchEngine("Production vector search is not approved.")
    }
}

internal fun retainTrustedDangerousEvidence(
    ranked: List<SearchCandidate>,
    trustedDangerous: List<SearchCandidate>
): List<SearchCandidate> {
    // SAFETY: ANN truncation cannot erase an independently trusted dangerous signal.
    val retained = ranked.associateByTo(linkedMapOf()) { it.observationId }
    trustedDangerous.filter { it.dangerousEvidence }.forEach { candidate ->
        retained.putIfAbsent(candidate.observationId, candidate)
    }
    return retained.values.sortedWith(
        compareBy<SearchCandidate> { it.internalDistance }
            .thenBy { it.observationId }
    )
}
