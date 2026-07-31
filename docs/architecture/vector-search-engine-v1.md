# Vector Search Engine Architecture v1

## Boundary

`VectorSearchEngine` is a replaceable internal candidate-retrieval mechanism.
It does not classify a mushroom and cannot create a user-visible status.
`SearchCandidate.internalDistance` is deliberately absent from UI/API models.
It is also JVM-transient so generic serialization cannot expose it accidentally.

Contracts:

```text
VectorSearchEngine
VectorSearchEngineFactory
SearchIndexDescriptor
SearchIndexFormat
SearchQuery
SearchCandidate
SearchDiagnostics
ExactReranker
UnavailableVectorSearchEngine
```

## Two-stage search

```text
metadata filtering
→ ANN candidate retrieval
→ exact reranking
→ future multi-view evidence aggregation
→ InferenceEngine
→ future RiskEngine
```

Stage B0 implements only filters, a small synthetic exact oracle and internal
reranking contracts. It does not implement multi-view aggregation or RiskEngine.

Queries lock `region_id`, independent `view_type`, `embedding_model_id`,
dimension, allowed taxa, excluded observations, `top_k` and bounded search
budget. One observation is deduplicated across thumbnails. CAP_TOP is never
queried against an UNDERSIDE shard.
The query region and view must equal the opened descriptor; using matching
vectors with a mismatched descriptor returns unavailable rather than searching.

Indexes are independently addressable by region, view, embedding contract and
index format version. A descriptor mismatch returns unavailable before search.

## Memory and resources

Production candidates must support memory-mapped or page-based read-only access,
lazy shard opening, bounded candidate/vector buffers, cancellation, deterministic
close, low-memory shutdown and one managed executor with a small thread limit.
The full multi-gigabyte pack/index must not be copied or loaded on each launch.
The in-memory implementation is permitted only for the tiny synthetic exact
baseline.

`ProductionVectorSearchEngineFactory` is deliberately unavailable in Stage B0
and can never return the synthetic exact engine. `EXACT_BASELINE` is rejected
by production compatibility even when a caller forges approval booleans.

## Benchmark harness

`scripts/benchmark_vector_search.py` defines research profiles for 10,000,
100,000 and 1,000,000 synthetic vectors without committing generated indexes.
Every ANN run must compare candidates with `EXACT_BASELINE` and record:

- open, cold, warm and multi-view latency;
- p50, p95 and p99;
- peak RSS and index size;
- recall@10, recall@50 and recall@100.

The executable default prints the plan only. `--run-small N` runs a bounded
local exact smoke benchmark. Large profiles require a separate research run and
report, not repository artifacts.

Peak RSS is obtained from the operating-system process counter; Python
`tracemalloc` is reported separately. It remains a whole-process measurement,
not an isolated native-engine value. Exact-vs-exact recall=1.0 is labelled only
as a harness sanity check and is not ANN performance evidence.

## Future native failure isolation

| Option | Crash isolation | Memory/IPC | Lifecycle/cancellation | Status |
|---|---|---|---|---|
| In-process native runtime | lowest | least IPC, shared RSS | simplest, crash affects app | research only |
| Isolated Android service | stronger sandbox | binder/copy overhead | explicit bind/death/cancel handling | research option |
| Separate process service | native crash separated | extra process RSS and IPC | most complex cleanup/restart | research option |

Production choice is **NOT YET APPROVED**. Benchmark, low-memory behavior,
native handle closure and crash-injection results are required first.

SAFETY: minimum production recall remains `OPEN_SAFETY_PARAMETER`. It can be
approved only after dangerous-confusion evaluation. Speed, top-1 distance or
absence of a dangerous match cannot lower safety thresholds. Trusted dangerous
evidence is retained outside ANN truncation.
