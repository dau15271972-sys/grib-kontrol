from __future__ import annotations

import argparse
import ctypes
import math
import os
import random
import statistics
import sys
import time
import tracemalloc
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Protocol

BENCHMARK_VECTOR_COUNTS = (10_000, 100_000, 1_000_000)
RECALL_LEVELS = (10, 50, 100)


class SearchIndexFormat(StrEnum):
    USEARCH_HNSW = "USEARCH_HNSW"
    HNSWLIB = "HNSWLIB"
    SQLITE_VEC1 = "SQLITE_VEC1"
    EXACT_BASELINE = "EXACT_BASELINE"


@dataclass(frozen=True)
class SearchIndexDescriptor:
    region_id: str
    view_type: str
    embedding_model_id: str
    embedding_dimension: int
    index_format_version: str
    engine: SearchIndexFormat
    engine_version: str
    loading_mode: str


@dataclass(frozen=True)
class SearchQuery:
    vector: tuple[float, ...]
    region_id: str
    view_type: str
    embedding_model_id: str
    embedding_dimension: int
    allowed_taxon_ids: frozenset[str]
    excluded_observation_ids: frozenset[str]
    top_k: int
    search_budget: int


@dataclass(frozen=True)
class SearchCandidate:
    observation_id: str
    reference_id: str
    taxon_id: str
    internal_distance: float
    dangerous_evidence: bool = False


@dataclass(frozen=True)
class SearchDiagnostics:
    engine: SearchIndexFormat
    visited_vectors: int
    elapsed_ms: float
    cancelled: bool
    internal_only: bool = True


@dataclass(frozen=True)
class SearchResult:
    candidates: tuple[SearchCandidate, ...]
    diagnostics: SearchDiagnostics
    available: bool = True


@dataclass(frozen=True)
class SyntheticVector:
    observation_id: str
    reference_id: str
    taxon_id: str
    region_id: str
    view_type: str
    values: tuple[float, ...]
    dangerous_evidence: bool = False


class SearchCancellation:
    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled


class VectorSearchEngine(Protocol):
    def search(self, query: SearchQuery, cancellation: SearchCancellation) -> SearchResult: ...

    def close(self) -> None: ...


class VectorSearchEngineFactory(Protocol):
    def open(self, descriptor: SearchIndexDescriptor) -> VectorSearchEngine: ...


class ExactReranker:
    """Internal-only exact reranking; never produces a user-facing result."""

    @staticmethod
    def rerank(candidates: tuple[SearchCandidate, ...]) -> tuple[SearchCandidate, ...]:
        return tuple(
            sorted(
                candidates,
                key=lambda item: (
                    item.internal_distance,
                    item.observation_id,
                    item.reference_id,
                ),
            )
        )


class UnavailableVectorSearchEngine:
    def search(self, query: SearchQuery, cancellation: SearchCancellation) -> SearchResult:
        del query, cancellation
        return SearchResult(
            (),
            SearchDiagnostics(SearchIndexFormat.EXACT_BASELINE, 0, 0.0, False),
            available=False,
        )

    def close(self) -> None:
        return None


class ExactBaselineEngine:
    """Small synthetic oracle used only to measure ANN recall."""

    def __init__(
        self,
        descriptor: SearchIndexDescriptor,
        vectors: list[SyntheticVector] | tuple[SyntheticVector, ...],
    ) -> None:
        self.descriptor = descriptor
        self._vectors = vectors if isinstance(vectors, tuple) else tuple(vectors)
        self.storage_identity = id(self._vectors)
        self.closed = False

    def search(self, query: SearchQuery, cancellation: SearchCancellation) -> SearchResult:
        if self.closed:
            return UnavailableVectorSearchEngine().search(query, cancellation)
        if (
            query.region_id != self.descriptor.region_id
            or query.view_type != self.descriptor.view_type
            or query.embedding_model_id != self.descriptor.embedding_model_id
            or query.embedding_dimension != self.descriptor.embedding_dimension
            or len(query.vector) != self.descriptor.embedding_dimension
            or query.top_k <= 0
            or query.search_budget <= 0
        ):
            return UnavailableVectorSearchEngine().search(query, cancellation)

        started = time.perf_counter_ns()
        best_by_observation: dict[str, SearchCandidate] = {}
        visited = 0
        for item in self._vectors:
            if cancellation.cancelled:
                break
            if visited >= query.search_budget:
                break
            if item.region_id != query.region_id or item.view_type != query.view_type:
                continue
            if query.allowed_taxon_ids and item.taxon_id not in query.allowed_taxon_ids:
                continue
            if item.observation_id in query.excluded_observation_ids:
                continue
            visited += 1
            distance = _cosine_distance(query.vector, item.values)
            candidate = SearchCandidate(
                item.observation_id,
                item.reference_id,
                item.taxon_id,
                distance,
                item.dangerous_evidence,
            )
            existing = best_by_observation.get(item.observation_id)
            if existing is None or (
                candidate.internal_distance,
                candidate.reference_id,
            ) < (existing.internal_distance, existing.reference_id):
                best_by_observation[item.observation_id] = candidate

        ordered = ExactReranker.rerank(tuple(best_by_observation.values()))
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
        return SearchResult(
            ordered[: query.top_k],
            SearchDiagnostics(
                SearchIndexFormat.EXACT_BASELINE,
                visited,
                elapsed_ms,
                cancellation.cancelled,
            ),
        )

    def close(self) -> None:
        self.closed = True
        self._vectors = ()


class SyntheticExactVectorSearchEngineFactory:
    """Shares one synthetic vector store across opens; production indexes use mmap/pages."""

    def __init__(self, vectors: list[SyntheticVector]) -> None:
        self._vectors = tuple(vectors)
        self.open_count = 0

    def open(self, descriptor: SearchIndexDescriptor) -> ExactBaselineEngine:
        self.open_count += 1
        return ExactBaselineEngine(descriptor, self._vectors)


class ProductionVectorSearchEngineFactory:
    """SAFETY: Stage B0 has no approved production vector-search engine."""

    def open(self, descriptor: SearchIndexDescriptor) -> UnavailableVectorSearchEngine:
        del descriptor
        return UnavailableVectorSearchEngine()


def retain_dangerous_evidence(
    ranked: tuple[SearchCandidate, ...],
    trusted_dangerous: tuple[SearchCandidate, ...],
) -> tuple[SearchCandidate, ...]:
    """SAFETY: ANN truncation cannot erase independently trusted dangerous evidence."""

    by_observation = {item.observation_id: item for item in ranked}
    for item in trusted_dangerous:
        if item.dangerous_evidence:
            by_observation.setdefault(item.observation_id, item)
    return ExactReranker.rerank(tuple(by_observation.values()))


def _cosine_distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 1.0
    return 1.0 - dot / (left_norm * right_norm)


def recall_at(
    exact: tuple[SearchCandidate, ...],
    approximate: tuple[SearchCandidate, ...],
    k: int,
) -> float:
    exact_ids = {item.observation_id for item in exact[:k]}
    if not exact_ids:
        return 1.0
    approximate_ids = {item.observation_id for item in approximate[:k]}
    return len(exact_ids & approximate_ids) / len(exact_ids)


def benchmark_plan() -> dict[str, object]:
    return {
        "vector_counts": BENCHMARK_VECTOR_COUNTS,
        "metrics": (
            "open_latency",
            "cold_query_latency",
            "warm_query_latency",
            "p50",
            "p95",
            "p99",
            "peak_rss",
            "index_size",
            "recall@10",
            "recall@50",
            "recall@100",
            "multi_view_latency",
        ),
        "baseline": SearchIndexFormat.EXACT_BASELINE,
        "minimum_production_recall": "OPEN_SAFETY_PARAMETER",
    }


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = math.ceil(percentile / 100 * len(ordered)) - 1
    return ordered[max(0, position)]


def _peak_rss_bytes() -> int:
    if os.name == "nt":
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        psapi.GetProcessMemoryInfo.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(ProcessMemoryCounters),
            ctypes.c_ulong,
        )
        psapi.GetProcessMemoryInfo.restype = ctypes.c_int
        if not psapi.GetProcessMemoryInfo(
            kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
        ):
            return 0
        return int(counters.PeakWorkingSetSize)

    import resource

    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak if sys.platform == "darwin" else peak * 1024


def run_small_synthetic_benchmark(
    vector_count: int,
    *,
    dimension: int = 16,
    query_count: int = 10,
    seed: int = 15271972,
) -> dict[str, object]:
    if vector_count <= 0 or dimension <= 0 or query_count <= 0:
        raise ValueError("benchmark dimensions must be positive")
    random_source = random.Random(seed)
    tracemalloc.start()
    opened = time.perf_counter_ns()
    vectors = [
        SyntheticVector(
            observation_id=f"obs_{index}",
            reference_id=f"ref_{index}",
            taxon_id=f"tx_{index % 10}",
            region_id="region_synthetic",
            view_type="CAP_TOP",
            values=tuple(random_source.random() for _ in range(dimension)),
        )
        for index in range(vector_count)
    ]
    descriptor = SearchIndexDescriptor(
        "region_synthetic",
        "CAP_TOP",
        "synthetic-embedding-model",
        dimension,
        "exact-json-v1",
        SearchIndexFormat.EXACT_BASELINE,
        "1.0.0",
        "SYNTHETIC_IN_MEMORY_ONLY",
    )
    engine = ExactBaselineEngine(descriptor, vectors)
    open_latency_ms = (time.perf_counter_ns() - opened) / 1_000_000
    latencies: list[float] = []
    recall: dict[str, float] = {}
    for index in range(query_count):
        query = SearchQuery(
            vectors[index % vector_count].values,
            "region_synthetic",
            "CAP_TOP",
            descriptor.embedding_model_id,
            dimension,
            frozenset(),
            frozenset(),
            min(100, vector_count),
            vector_count,
        )
        exact = engine.search(query, SearchCancellation())
        approximate = exact
        latencies.append(exact.diagnostics.elapsed_ms)
        for k in RECALL_LEVELS:
            recall[f"recall@{k}"] = recall_at(exact.candidates, approximate.candidates, k)
    _, peak_bytes = tracemalloc.get_traced_memory()
    peak_rss_bytes = _peak_rss_bytes()
    tracemalloc.stop()
    engine.close()
    return {
        "vector_count": vector_count,
        "open_latency_ms": open_latency_ms,
        "cold_query_latency_ms": latencies[0],
        "warm_query_latency_ms": statistics.fmean(latencies[1:] or latencies),
        "p50_ms": _percentile(latencies, 50),
        "p95_ms": _percentile(latencies, 95),
        "p99_ms": _percentile(latencies, 99),
        "peak_rss_bytes": peak_rss_bytes,
        "peak_tracemalloc_bytes": peak_bytes,
        "peak_rss_scope": "whole benchmark process; not isolated from interpreter baseline",
        "index_size_bytes": sum(len(item.values) * 8 for item in vectors),
        "multi_view_latency_ms": sum(latencies[: min(4, len(latencies))]),
        "recall_interpretation": "exact-vs-exact sanity check; not ANN performance",
        **recall,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Research-only synthetic vector-search benchmark harness."
    )
    parser.add_argument("--run-small", type=int, metavar="VECTOR_COUNT")
    args = parser.parse_args()
    if args.run_small is None:
        print(asdict(_BenchmarkPlanView.from_plan(benchmark_plan())))
        return 0
    print(run_small_synthetic_benchmark(args.run_small))
    return 0


@dataclass(frozen=True)
class _BenchmarkPlanView:
    vector_counts: tuple[int, ...]
    metrics: tuple[str, ...]
    baseline: str
    minimum_production_recall: str

    @classmethod
    def from_plan(cls, plan: dict[str, object]) -> _BenchmarkPlanView:
        return cls(
            tuple(plan["vector_counts"]),
            tuple(plan["metrics"]),
            str(plan["baseline"]),
            str(plan["minimum_production_recall"]),
        )


if __name__ == "__main__":
    raise SystemExit(main())
