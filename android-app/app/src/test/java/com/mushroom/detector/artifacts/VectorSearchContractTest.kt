package com.mushroom.detector.artifacts

import com.mushroom.detector.MushroomApiResponse
import com.mushroom.detector.capture.CaptureViewType
import java.lang.reflect.Modifier
import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class VectorSearchContractTest {
    private val descriptor = SearchIndexDescriptor(
        regionId = "region_a",
        viewType = CaptureViewType.CAP_TOP,
        embeddingModelId = "embedding-a",
        embeddingDimension = 2,
        indexFormatVersion = "exact-json-v1",
        engine = SearchIndexFormat.EXACT_BASELINE,
        engineVersion = "1.0.0",
        metric = "COSINE_DISTANCE_INTERNAL_ONLY",
        shardCount = 1,
        vectorCount = 5,
        loadingMode = SearchIndexLoadingMode.SYNTHETIC_IN_MEMORY_ONLY
    )
    private val vectors = listOf(
        SyntheticReferenceVector(
            "obs_1", "thumb_1", "tx_a", "region_a",
            CaptureViewType.CAP_TOP, floatArrayOf(1f, 0f)
        ),
        SyntheticReferenceVector(
            "obs_1", "thumb_2", "tx_a", "region_a",
            CaptureViewType.CAP_TOP, floatArrayOf(0.9f, 0.1f)
        ),
        SyntheticReferenceVector(
            "obs_2", "thumb_3", "tx_b", "region_a",
            CaptureViewType.CAP_TOP, floatArrayOf(0f, 1f)
        ),
        SyntheticReferenceVector(
            "obs_3", "thumb_4", "tx_c", "region_b",
            CaptureViewType.CAP_TOP, floatArrayOf(1f, 0f)
        ),
        SyntheticReferenceVector(
            "obs_4", "thumb_5", "tx_d", "region_a",
            CaptureViewType.UNDERSIDE, floatArrayOf(1f, 0f)
        )
    )

    private fun query(
        regionId: String = "region_a",
        viewType: CaptureViewType = CaptureViewType.CAP_TOP,
        allowedTaxonIds: Set<String> = emptySet()
    ) = SearchQuery(
        embedding = floatArrayOf(1f, 0f),
        regionId = regionId,
        viewType = viewType,
        embeddingModelId = "embedding-a",
        embeddingDimension = 2,
        allowedTaxonIds = allowedTaxonIds,
        excludedObservationIds = emptySet(),
        topK = 10,
        searchBudget = 100
    )

    @Test
    fun exactBaselineIsDeterministicAndReturnsOnlyAllowedIds() {
        val engine = SyntheticExactVectorSearchEngine(descriptor, vectors)
        val first = engine.search(query(allowedTaxonIds = setOf("tx_b"))) { false }
        val second = engine.search(query(allowedTaxonIds = setOf("tx_b"))) { false }

        val candidates = (first as VectorSearchResult.Candidates).values
        assertEquals(candidates, (second as VectorSearchResult.Candidates).values)
        assertEquals(setOf("tx_b"), candidates.map { it.taxonId }.toSet())
    }

    @Test
    fun regionAndViewFiltersAreEnforced() {
        val result = SyntheticExactVectorSearchEngine(descriptor, vectors)
            .search(query(), SearchCancellation { false }) as VectorSearchResult.Candidates

        assertFalse(result.values.any { it.observationId == "obs_3" })
        assertFalse(result.values.any { it.observationId == "obs_4" })
    }

    @Test
    fun thumbnailsDoNotDuplicateOneObservation() {
        val result = SyntheticExactVectorSearchEngine(descriptor, vectors)
            .search(query(), SearchCancellation { false }) as VectorSearchResult.Candidates

        assertEquals(1, result.values.count { it.observationId == "obs_1" })
    }

    @Test
    fun cancellationAndCloseReleaseResources() {
        val engine = SyntheticExactVectorSearchEngine(descriptor, vectors)
        val cancellation = MutableSearchCancellation().also { it.cancel() }

        val cancelled = engine.search(query(), cancellation) as VectorSearchResult.Candidates
        engine.close()
        val afterClose = engine.search(query(), SearchCancellation { false })

        assertTrue(cancelled.diagnostics.cancelled)
        assertTrue(engine.closed)
        assertTrue(afterClose is VectorSearchResult.Unavailable)
    }

    @Test
    fun repeatedOpenSharesSyntheticStoreAndDoesNotCopyFullIndex() {
        val factory = SyntheticVectorSearchEngineFactory(
            vectors,
            "embedding-a",
            2,
            "1.0.0",
            "exact-json-v1"
        )

        val first = factory.open(descriptor) as SyntheticExactVectorSearchEngine
        val second = factory.open(descriptor) as SyntheticExactVectorSearchEngine

        assertEquals(first.backingStoreIdentity, second.backingStoreIdentity)
    }

    @Test
    fun incompatibleOrCorruptedDescriptorReturnsUnavailable() {
        val factory = SyntheticVectorSearchEngineFactory(
            vectors,
            "embedding-a",
            2,
            "1.0.0",
            "exact-json-v1"
        )

        assertTrue(
            factory.open(descriptor.copy(engineVersion = "99"))
                is UnavailableVectorSearchEngine
        )
        assertTrue(
            factory.open(descriptor.copy(embeddingModelId = "other"))
                is UnavailableVectorSearchEngine
        )
        assertTrue(
            factory.open(descriptor.copy(embeddingDimension = 3))
                is UnavailableVectorSearchEngine
        )
        assertTrue(
            factory.open(descriptor.copy(indexFormatVersion = "corrupted"))
                is UnavailableVectorSearchEngine
        )
    }

    @Test
    fun exactRerankingChangesOnlyInternalOrder() {
        val original = listOf(
            SearchCandidate("obs_b", "ref_b", "tx_b", 0.8f),
            SearchCandidate("obs_a", "ref_a", "tx_a", 0.1f)
        )
        val reranked = ExactReranker().rerank(
            original,
            mapOf("obs_a" to 0.9f, "obs_b" to 0.2f)
        )

        assertEquals(listOf("obs_b", "obs_a"), reranked.map { it.observationId })
        assertEquals(original.map { it.observationId }.toSet(), reranked.map { it.observationId }.toSet())
    }

    @Test
    fun rawDistanceIsAbsentFromUiApiContract() {
        val fields = MushroomApiResponse::class.java.declaredFields.map { it.name }.toSet()

        assertFalse("distance" in fields)
        assertFalse("internalDistance" in fields)
        assertFalse("searchCandidates" in fields)
        val internalDistance = SearchCandidate::class.java.getDeclaredField("internalDistance")
        assertTrue(Modifier.isTransient(internalDistance.modifiers))
    }

    @Test
    fun dangerousEvidenceIsNotDroppedByAnnRanking() {
        val ranked = listOf(SearchCandidate("obs_a", "ref_a", "tx_a", 0.1f))
        val dangerous = listOf(
            SearchCandidate("obs_danger", "ref_danger", "tx_danger", 0.9f, true)
        )

        val retained = retainTrustedDangerousEvidence(ranked, dangerous)

        assertTrue(retained.any { it.observationId == "obs_danger" })
    }

    @Test
    fun referenceMatchesCannotBecomeUserResult() {
        val searchResult = SyntheticExactVectorSearchEngine(descriptor, vectors)
            .search(query(), SearchCancellation { false })

        assertNotEquals(MushroomApiResponse::class.java, searchResult::class.java)
    }

    @Test
    fun descriptorRegionAndViewMismatchReturnUnavailable() {
        val engine = SyntheticExactVectorSearchEngine(descriptor, vectors)

        assertTrue(engine.search(query(regionId = "region_b")) { false } is VectorSearchResult.Unavailable)
        assertTrue(
            engine.search(query(viewType = CaptureViewType.UNDERSIDE)) { false }
                is VectorSearchResult.Unavailable
        )
    }

    @Test
    fun transformedCopiesRemainOneObservation() {
        val transformed = vectors + SyntheticReferenceVector(
            "obs_1", "thumb_1_rotated", "tx_a", "region_a",
            CaptureViewType.CAP_TOP, floatArrayOf(1f, 0f)
        )
        val result = SyntheticExactVectorSearchEngine(descriptor, transformed)
            .search(query(), SearchCancellation { false }) as VectorSearchResult.Candidates

        assertEquals(1, result.values.count { it.observationId == "obs_1" })
    }

    @Test
    fun noCandidatesIsInternalEmptyEvidenceNotSafety() {
        val result = SyntheticExactVectorSearchEngine(descriptor, vectors).search(
            query(allowedTaxonIds = setOf("missing")),
            SearchCancellation { false }
        ) as VectorSearchResult.Candidates

        assertTrue(result.values.isEmpty())
        assertNotEquals(MushroomApiResponse::class.java, result::class.java)
    }

    @Test
    fun productionFactoryNeverExposesSyntheticExactBaseline() {
        val engine = ProductionVectorSearchEngineFactory().open(descriptor)

        assertTrue(engine is UnavailableVectorSearchEngine)
        assertTrue(engine.search(query(), SearchCancellation { false }) is VectorSearchResult.Unavailable)
    }

    @Test
    fun searchDescriptorSchemaMatchesKotlinContract() {
        val schema = sequenceOf(
            File("../../data/reference-pack/schema/search-index-descriptor.schema.json"),
            File("../data/reference-pack/schema/search-index-descriptor.schema.json"),
            File("data/reference-pack/schema/search-index-descriptor.schema.json")
        ).first { it.isFile }.readLines()
        val fields = schema.mapNotNull { line ->
            Regex("""^    "([a-z0-9_]+)":""").find(line)?.groupValues?.get(1)
        }.toSet()

        assertEquals(fields, SearchIndexDescriptorContract.jsonFields)
        assertEquals(
            listOf("unknown field: bypass"),
            SearchIndexDescriptorContract.validateRawFields(fields + "bypass")
        )
    }
}
