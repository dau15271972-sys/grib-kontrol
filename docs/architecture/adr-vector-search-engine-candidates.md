# ADR: vector search engine candidates

- Status: **PROVISIONAL / PRODUCTION NOT APPROVED**
- Stage: B0 architecture and synthetic benchmark contracts

## Decision

```text
Primary prototype candidate: USearch
Fallback candidate: hnswlib
Research candidate: SQLite Vec1
Exact oracle: EXACT_BASELINE
Production decision: NOT YET APPROVED
```

USearch is the first prototype candidate because its published design supports
file persistence, memory-mapped index views, local ANN use and an Apache 2.0
license. These are candidate-selection reasons, not a production approval.

hnswlib remains the fallback for comparative HNSW behavior. SQLite Vec1 remains
a research candidate for page-oriented integration with metadata. Exact search
is limited to small synthetic inputs and recall ground truth.

## Constraints

- Do not bundle several heavy native engines in the production APK.
- A native proof-of-concept must remain isolated from production inference.
- Compare size, open/query latency, peak memory, lifecycle/cancellation and
  recall at required cutoffs on target devices.
- Evaluate dangerous-confusion recall before any production choice.
- Confirm licenses, ABI coverage, reproducible builds and resource cleanup.

## Consequence

No native dependency is added in Stage B0. `UnavailableVectorSearchEngine`
remains the fail-closed default; the synthetic exact engine only proves contract
behavior. A later ADR must replace this status after benchmark and safety review.
