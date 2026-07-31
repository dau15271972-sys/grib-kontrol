from __future__ import annotations

from app.inference import InferenceResult
from scripts.benchmark_vector_search import (
    BENCHMARK_VECTOR_COUNTS,
    ExactBaselineEngine,
    ExactReranker,
    ProductionVectorSearchEngineFactory,
    SearchCancellation,
    SearchCandidate,
    SearchIndexDescriptor,
    SearchIndexFormat,
    SearchQuery,
    SyntheticExactVectorSearchEngineFactory,
    SyntheticVector,
    UnavailableVectorSearchEngine,
    benchmark_plan,
    recall_at,
    retain_dangerous_evidence,
    run_small_synthetic_benchmark,
)

DESCRIPTOR = SearchIndexDescriptor(
    "region_a",
    "CAP_TOP",
    "embedding-a",
    2,
    "exact-json-v1",
    SearchIndexFormat.EXACT_BASELINE,
    "1.0.0",
    "SYNTHETIC_IN_MEMORY_ONLY",
)
VECTORS = [
    SyntheticVector("obs_1", "thumb_1", "tx_a", "region_a", "CAP_TOP", (1.0, 0.0)),
    SyntheticVector("obs_1", "thumb_2", "tx_a", "region_a", "CAP_TOP", (0.9, 0.1)),
    SyntheticVector("obs_2", "thumb_3", "tx_b", "region_a", "CAP_TOP", (0.0, 1.0)),
    SyntheticVector("obs_3", "thumb_4", "tx_c", "region_b", "CAP_TOP", (1.0, 0.0)),
    SyntheticVector("obs_4", "thumb_5", "tx_d", "region_a", "UNDERSIDE", (1.0, 0.0)),
]


def _query(**changes: object) -> SearchQuery:
    values: dict[str, object] = {
        "vector": (1.0, 0.0),
        "region_id": "region_a",
        "view_type": "CAP_TOP",
        "embedding_model_id": "embedding-a",
        "embedding_dimension": 2,
        "allowed_taxon_ids": frozenset(),
        "excluded_observation_ids": frozenset(),
        "top_k": 10,
        "search_budget": 100,
    }
    values.update(changes)
    return SearchQuery(**values)  # type: ignore[arg-type]


def test_exact_baseline_is_deterministic() -> None:
    engine = ExactBaselineEngine(DESCRIPTOR, VECTORS)

    first = engine.search(_query(), SearchCancellation())
    second = engine.search(_query(), SearchCancellation())

    assert first.candidates == second.candidates


def test_search_returns_only_allowed_taxon_ids() -> None:
    engine = ExactBaselineEngine(DESCRIPTOR, VECTORS)
    result = engine.search(
        _query(allowed_taxon_ids=frozenset({"tx_b"})),
        SearchCancellation(),
    )

    assert {candidate.taxon_id for candidate in result.candidates} == {"tx_b"}


def test_region_filter_is_enforced() -> None:
    engine = ExactBaselineEngine(DESCRIPTOR, VECTORS)

    result = engine.search(_query(), SearchCancellation())

    assert "obs_3" not in {candidate.observation_id for candidate in result.candidates}


def test_view_type_filter_is_enforced() -> None:
    engine = ExactBaselineEngine(DESCRIPTOR, VECTORS)

    result = engine.search(_query(), SearchCancellation())

    assert "obs_4" not in {candidate.observation_id for candidate in result.candidates}


def test_one_observation_is_not_duplicated_by_thumbnails() -> None:
    engine = ExactBaselineEngine(DESCRIPTOR, VECTORS)

    result = engine.search(_query(), SearchCancellation())

    assert [item.observation_id for item in result.candidates].count("obs_1") == 1


def test_search_cancellation_and_close_release_resources() -> None:
    engine = ExactBaselineEngine(DESCRIPTOR, VECTORS)
    cancellation = SearchCancellation()
    cancellation.cancel()

    result = engine.search(_query(), cancellation)
    engine.close()
    after_close = engine.search(_query(), SearchCancellation())

    assert result.diagnostics.cancelled
    assert engine.closed
    assert after_close.available is False


def test_reopen_shares_synthetic_store_instead_of_copying_full_index() -> None:
    factory = SyntheticExactVectorSearchEngineFactory(VECTORS)

    first = factory.open(DESCRIPTOR)
    second = factory.open(DESCRIPTOR)

    assert first.storage_identity == second.storage_identity
    assert factory.open_count == 2


def test_unavailable_index_returns_unavailable() -> None:
    result = UnavailableVectorSearchEngine().search(_query(), SearchCancellation())

    assert result.available is False
    assert result.candidates == ()


def test_exact_reranking_changes_only_internal_order() -> None:
    original = (
        SearchCandidate("obs_b", "ref_b", "tx_b", 0.8),
        SearchCandidate("obs_a", "ref_a", "tx_a", 0.1),
    )

    reranked = ExactReranker.rerank(original)

    assert [item.observation_id for item in reranked] == ["obs_a", "obs_b"]
    assert set(reranked) == set(original)


def test_raw_distance_is_not_part_of_user_facing_result_contract() -> None:
    public_fields = set(InferenceResult.__dataclass_fields__)

    assert "distance" not in public_fields
    assert "internal_distance" not in public_fields
    assert "search_candidates" not in public_fields


def test_dangerous_evidence_is_not_dropped_by_ann_ranking() -> None:
    ranked = (SearchCandidate("obs_a", "ref_a", "tx_a", 0.1),)
    dangerous = (
        SearchCandidate("obs_danger", "ref_danger", "tx_danger", 0.9, True),
    )

    retained = retain_dangerous_evidence(ranked, dangerous)

    assert "obs_danger" in {item.observation_id for item in retained}


def test_reference_candidates_do_not_form_user_result() -> None:
    result = ExactBaselineEngine(DESCRIPTOR, VECTORS).search(
        _query(),
        SearchCancellation(),
    )

    assert not isinstance(result, InferenceResult)
    assert result.diagnostics.internal_only


def test_benchmark_plan_covers_required_scales_and_metrics() -> None:
    plan = benchmark_plan()

    assert plan["vector_counts"] == BENCHMARK_VECTOR_COUNTS
    assert plan["minimum_production_recall"] == "OPEN_SAFETY_PARAMETER"
    assert {"recall@10", "recall@50", "recall@100", "peak_rss"} <= set(
        plan["metrics"]
    )


def test_peak_memory_benchmark_is_recorded() -> None:
    report = run_small_synthetic_benchmark(50, dimension=4, query_count=3)

    assert report["peak_rss_bytes"] > 0
    assert report["peak_tracemalloc_bytes"] > 0
    assert report["index_size_bytes"] > 0
    assert report["multi_view_latency_ms"] >= 0


def test_recall_benchmark_compares_against_exact_baseline() -> None:
    exact = (
        SearchCandidate("obs_a", "ref_a", "tx_a", 0.1),
        SearchCandidate("obs_b", "ref_b", "tx_b", 0.2),
    )

    assert recall_at(exact, exact, 10) == 1.0
    report = run_small_synthetic_benchmark(50, dimension=4, query_count=3)
    assert report["recall@10"] == 1.0
    assert report["recall@50"] == 1.0
    assert report["recall@100"] == 1.0
    assert report["recall_interpretation"] == (
        "exact-vs-exact sanity check; not ANN performance"
    )


def test_production_factory_cannot_open_synthetic_exact_engine() -> None:
    engine = ProductionVectorSearchEngineFactory().open(DESCRIPTOR)

    assert isinstance(engine, UnavailableVectorSearchEngine)
    assert engine.search(_query(), SearchCancellation()).available is False


def test_descriptor_region_and_view_mismatch_is_unavailable() -> None:
    engine = ExactBaselineEngine(DESCRIPTOR, VECTORS)

    assert engine.search(_query(region_id="region_b"), SearchCancellation()).available is False
    assert engine.search(_query(view_type="UNDERSIDE"), SearchCancellation()).available is False


def test_no_candidates_never_becomes_a_user_safety_result() -> None:
    result = ExactBaselineEngine(DESCRIPTOR, VECTORS).search(
        _query(allowed_taxon_ids=frozenset({"missing"})),
        SearchCancellation(),
    )

    assert result.candidates == ()
    assert not isinstance(result, InferenceResult)
