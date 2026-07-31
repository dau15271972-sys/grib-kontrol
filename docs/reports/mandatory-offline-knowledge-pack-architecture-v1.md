# Mandatory Offline Knowledge Pack Architecture v1 — отчёт

## Итоговый статус

**MANDATORY OFFLINE KNOWLEDGE PACK ARCHITECTURE V1: READY FOR REVIEW**

Архитектурный каркас обеспечивает принцип:

```text
VALID ACTIVE KNOWLEDGE PACK IS MANDATORY
```

Без полностью проверенного, compatible, trusted и active pack распознавание
возвращает `RECOGNITION_UNAVAILABLE`. Production inference, реальные данные и
нативный ANN engine не добавлены.

## Исходное состояние и ветка

- Репозиторий: `dau15271972-sys/grib-kontrol`.
- Базовая ветка: `data/taxonomy-matrix-v1`.
- Проверенный base/local/origin SHA:
  `59797d3e4397e402c4267572a82eba5704599a12`.
- Исходное рабочее дерево: чистое.
- Codex создал локальную ветку `arch/offline-reference-pack-v1` точно от
  указанного SHA.
- Ветка не отправлялась на GitHub; commit, push, PR, merge и rebase отсутствуют.

## Архитектура до изменений

Stage A предоставлял `NoModelInferenceEngine`, единый `InferenceEngine`,
`ArtifactCompatibilityGate` для model/input/taxonomy/calibration/risk,
multi-view CameraX capture, emergency route и fail-closed UI/API. Отдельного
формата устанавливаемого pack, SAF/storage transaction, signature policy,
reference metadata/index contracts и replaceable vector-search boundary не
было. Незарегистрированный engine мог попасть в Python runner без pack gate.

## Архитектура после изменений

```text
SAF ACTION_OPEN_DOCUMENT
→ app-owned bounded staging
→ strict ZIP64/path/size validation
→ manifest + file-manifest schema
→ per-file SHA-256
→ signature policy
→ expanded ArtifactCompatibilityGate
→ runtime/index open probe
→ atomic read-only activation with rollback
→ metadata filtering
→ ANN candidate retrieval
→ exact reranking
→ future multi-view evidence
→ InferenceEngine
→ future RiskEngine
```

Stage B0 заканчивается до multi-view aggregation и RiskEngine. Runtime shell
остаётся `NoModelInferenceEngine`; отсутствующий, повреждённый, неподписанный,
неутверждённый или несовместимый pack не запускает приблизительный fallback.

## Сохранённые Stage A компоненты

- `InferenceEngine` остаётся единственной точкой пользовательского результата.
- `NoModelInferenceEngine` остаётся default implementation.
- `ArtifactCompatibilityGate` расширен; конкурентный permissive gate не создан.
- CameraX, `ObservationSession`, независимые view types и app-private captures
  сохранены.
- Emergency route и `UNAPPROVED_MEDICAL_PLACEHOLDER` сохранены.
- Approved Compose layout, assets, colors, cards and scrolling не менялись.
- Android manifest не изменён; `INTERNET` и broad storage permissions не
  добавлены.
- Existing taxonomy, safety, wrapper and medical gates не ослаблены.

Fail-closed runtime wording теперь явно сообщает об отсутствующем активном
автономном pack. Визуальная композиция и новые экраны не добавлялись.

## Новые компоненты

Android/domain:

- `KnowledgePackManifest`, `KnowledgePackDescriptor`, `KnowledgePackState`;
- `KnowledgePackInstaller`, `KnowledgePackStorage`,
  `KnowledgePackRepository`;
- `KnowledgePackCompatibilityGate`, `KnowledgePackSignatureVerifier`;
- `KnowledgePackRuntime`, `MandatoryKnowledgePackRuntimeFactory`;
- `NoKnowledgePackRepository`, `RejectingKnowledgePackSignatureVerifier`,
  `UnavailableKnowledgePackRuntime`;
- SAF selection contract and app-owned staging/atomic storage;
- complete vector-search interfaces, synthetic exact engine and unavailable
  implementation.

Python/data:

- manifest/file/search-index schemas and templates;
- deterministic offline directory/ZIP64 validator;
- small unpacked synthetic pack fixture;
- exact baseline and synthetic benchmark harness;
- CI step `python scripts/validate_reference_pack.py`.

## `.gribpack` structure

Future production transfer is one ZIP64-compatible
`grib-karelia-northwest-v1.gribpack` with manifests, model, per-view embeddings,
sharded indexes, optimized reference images, metadata SQLite, taxonomy,
confusion groups, open-set/OOD, calibration, risk rules, attribution/source
registry, checksums and signature.

The repository contains no real `.gribpack`. Its unpacked fixture contains only
small JSON contracts, 4-dimensional invented vectors, 3 invented observation
IDs, invented taxon IDs, exact-index metadata and empty attribution/source
records. It contains zero reference images and no model weights.

Fixture flags:

```text
production_approved=false
signature_required=false
vector_search_engine=EXACT_BASELINE
reference_image_count=0
```

Structural validation passes; `--require-production` correctly fails with:

```text
manifest.json: production activation requires signature_required=true
manifest.json: production_approved=false cannot activate
```

## Compatibility matrix

| Contract | Gate behavior |
|---|---|
| Pack format/app range | unknown format or app outside min/max rejected |
| Model | contract, ID and SHA-256 exact match required |
| Embeddings | model ID, SHA-256, dimension and dtype locked |
| Taxonomy | version/hash independently locked |
| Dangerous confusion groups | version/hash independently locked |
| Open-set | version/hash independently locked |
| Calibration | version/hash independently locked |
| Risk rules | version/hash independently locked |
| Search index | engine/version/format/embedding contract locked |
| Trust | production approval, required signature and known key required |
| Runtime | pack must be active, trusted, read-only and openable |

The Android `KnowledgePackCompatibilityGate` delegates to the expanded
`ArtifactCompatibilityGate`. Python `ArtifactBundleManifest` and the same gate
also enforce mandatory pack format, search contract, approval, trust and active
flags.

## Storage and import flow

- System selection contract: `ACTION_OPEN_DOCUMENT`, persisted read grant.
- Preflight uses an injected allocatable-space probe; future Android wiring can
  use `StorageManager#getAllocatableBytes`.
- Copy/hash/extraction must be streaming with bounded buffers.
- ZIP inspection rejects duplicate/absolute/drive/traversal paths, backslashes,
  symlinks, excess count/size and suspicious compression ratios.
- Staging, active and rollback live on one app-owned filesystem.
- Atomic move is mandatory. Unsupported/failing activation restores previous
  active descriptor.
- Interrupted staging is cleaned; user-selected source is never removed.
- Active pack is exposed read-only and is not recopied on each launch.

## Failure matrix

| Failure | New pack | Existing active | Runtime result |
|---|---|---|---|
| no pack | none | none | `RECOGNITION_UNAVAILABLE` |
| selection cancelled/source removed | discarded | preserved | previous if valid, else unavailable |
| insufficient space | preflight failed | preserved | previous if valid |
| malformed ZIP/path/symlink/bomb | rejected | preserved | previous if valid |
| missing file/incorrect SHA | rejected | preserved | previous if valid |
| version/model/dimension mismatch | incompatible | preserved | previous if valid |
| missing/unknown signature | untrusted | preserved | previous if valid |
| runtime/index probe failure | corrupted | preserved | previous if valid |
| active pack later missing/corrupt | no partial use | unavailable | `RECOGNITION_UNAVAILABLE` |

## Vector-search architecture

Implemented contracts:

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

Supported research identifiers: `USEARCH_HNSW`, `HNSWLIB`, `SQLITE_VEC1`,
`EXACT_BASELINE`. Only the small synthetic exact oracle is executable. No native
dependency is present in APK.

Filters lock region, view type, embedding model/dimension, allowed taxa,
excluded observations, top K and search budget. Multiple thumbnails deduplicate
to one observation. Search buffers, thread count and executor count are bounded;
cancellation and `close()` are explicit. Production descriptors require
memory-mapped or page-based access and lazy shards; full-index RAM loads are
allowed only for synthetic exact tests.

SAFETY: candidates and distances are internal. Top-1 is not a taxonomic result,
distance is not confidence, and trusted dangerous evidence is retained outside
ANN truncation. `MushroomApiResponse`/API contain no raw distance or candidates.

## ADR

```text
Primary prototype candidate: USearch
Fallback candidate: hnswlib
Research candidate: SQLite Vec1
Production decision: NOT YET APPROVED
```

USearch is provisional due to persistence, memory-mapped view, Apache 2.0 and
local ANN suitability. No engine is selected for production before comparative
device benchmark and dangerous-confusion recall evaluation.

## Benchmark design and result

Harness profiles: 10,000 / 100,000 / 1,000,000 synthetic vectors. Metrics:
open/cold/warm/multi-view latency, p50/p95/p99, peak RSS, index size and
recall@10/50/100. Every future ANN result must compare with `EXACT_BASELINE`.

Executed exact 10k smoke run:

| Metric | Result |
|---|---:|
| open latency | 210.6986 ms |
| cold query | 194.8990 ms |
| warm mean | 191.8179 ms |
| p50 / p95 / p99 | 190.0448 / 201.4998 / 201.4998 ms |
| peak RSS proxy (`tracemalloc`) | 10,858,867 bytes |
| estimated vector storage | 1,280,000 bytes |
| multi-view latency (4 queries) | 771.8197 ms |
| recall@10 / @50 / @100 | 1.0 / 1.0 / 1.0 |

This is an exact-oracle harness smoke test, not ANN evidence and not an
on-device production benchmark. 100k/1m profiles are defined but were not
materialized in the repository. Minimum production recall remains
`OPEN_SAFETY_PARAMETER`.

## Tests and builds

| Check | Result |
|---|---|
| Python Ruff | PASS, `All checks passed!` |
| Full pytest | PASS, `125 passed in 2.38s` |
| Taxonomy validator | PASS, 3 taxa / 1 group / 4 reviews |
| Reference-pack validator | PASS, 18 container files, synthetic/non-production |
| Synthetic production activation | EXPECTED FAIL, approval/signature absent |
| Safety gate | PASS |
| Medical placeholder development gate | PASS |
| Medical production gate | EXPECTED FAIL / remains blocked |
| Gradle Wrapper validation | PASS |
| Android unit tests | PASS, 34/34; 0 failed/skipped/errors |
| Android lint | PASS, 0 errors / 15 existing `GradleDependency` warnings |
| Android debug APK | PASS |
| Desktop non-production EXE | PASS |
| `git diff --check` | PASS; informational Git line-ending warnings only |
| UTF-8/whitespace/final-newline audit | PASS, 57 files before this report |

Android artifacts:

- APK: `13,894,498` bytes;
- APK SHA-256:
  `9139F89ABD4E4CB11ECE7E95002FBA9C94AD4846F07E2B1C34F954348F9217EA`.

Desktop artifacts:

- EXE: `5,101,798` bytes;
- EXE SHA-256:
  `8851442CE2C7C66635E05C0271618EB27EC8187B743FDB13BDACD22949EE44B5`;
- bundled model/pack files: 0.

The first direct Gradle call in the Cyrillic workspace reproduced the known KSP
`lateinit property cleanFilenames` environment issue. The required ASCII-drive
script then exposed and helped fix two missing imports. A new `UsableSpace` lint
warning was fixed architecturally with an injected capacity probe. Final ASCII
Android verification is successful; only the 15 pre-existing dependency-update
warnings remain.

## Changed files

Modified tracked files:

- `.github/workflows/ci.yml`;
- `AGENTS.md`;
- `README.md`;
- `app/artifacts.py`, `app/inference.py`;
- Android artifact/inference manifests, gates, matrix and corresponding tests;
- `docs/issues/README.md`;
- `tests/test_app.py`, `tests/test_artifacts.py`.

New files/directories:

- `android-app/.../artifacts/KnowledgePackContracts.kt`;
- `android-app/.../artifacts/KnowledgePackStorage.kt`;
- `android-app/.../artifacts/VectorSearch.kt`;
- `android-app/.../artifacts/KnowledgePackArchitectureTest.kt`;
- `android-app/.../artifacts/VectorSearchContractTest.kt`;
- all files under `data/reference-pack/` (schemas, templates and synthetic
  valid/invalid fixtures);
- all four files under `docs/architecture/`;
- `docs/issues/08-mandatory-offline-knowledge-pack-v1.md`;
- `scripts/validate_reference_pack.py`;
- `scripts/benchmark_vector_search.py`;
- `tests/test_reference_pack_contract.py`;
- `tests/test_vector_search_benchmark.py`;
- this report.

No Compose screen/layout, Android manifest, CameraX, emergency copy, visual
asset, taxonomy matrix or real knowledge data file was changed.

## `git diff --stat`

Ordinary `git diff --stat` lists only the 15 modified tracked files; all new
files remain untracked as required:

```text
15 files changed, 440 insertions(+), 57 deletions(-)
```

## Final `git status --short --branch`

```text
## arch/offline-reference-pack-v1
 M .github/workflows/ci.yml
 M AGENTS.md
 M README.md
 M android-app/app/src/main/java/com/mushroom/detector/artifacts/ArtifactBundleManifest.kt
 M android-app/app/src/main/java/com/mushroom/detector/artifacts/ArtifactCompatibilityGate.kt
 M android-app/app/src/main/java/com/mushroom/detector/artifacts/CompatibilityMatrix.kt
 M android-app/app/src/main/java/com/mushroom/detector/inference/NoModelInferenceEngine.kt
 M android-app/app/src/main/java/com/mushroom/detector/inference/SafeInferenceRunner.kt
 M android-app/app/src/test/java/com/mushroom/detector/artifacts/ArtifactCompatibilityGateTest.kt
 M android-app/app/src/test/java/com/mushroom/detector/inference/SafeInferenceRunnerTest.kt
 M app/artifacts.py
 M app/inference.py
 M docs/issues/README.md
 M tests/test_app.py
 M tests/test_artifacts.py
?? android-app/app/src/main/java/com/mushroom/detector/artifacts/KnowledgePackContracts.kt
?? android-app/app/src/main/java/com/mushroom/detector/artifacts/KnowledgePackStorage.kt
?? android-app/app/src/main/java/com/mushroom/detector/artifacts/VectorSearch.kt
?? android-app/app/src/test/java/com/mushroom/detector/artifacts/KnowledgePackArchitectureTest.kt
?? android-app/app/src/test/java/com/mushroom/detector/artifacts/VectorSearchContractTest.kt
?? data/reference-pack/
?? docs/architecture/
?? docs/issues/08-mandatory-offline-knowledge-pack-v1.md
?? docs/reports/mandatory-offline-knowledge-pack-architecture-v1.md
?? scripts/benchmark_vector_search.py
?? scripts/validate_reference_pack.py
?? tests/test_reference_pack_contract.py
?? tests/test_vector_search_benchmark.py
```

Staged changes and commits are absent.

## Open questions

1. Signing algorithm, trust store, key custody/rotation/revocation.
2. Real-data licensing, reviewer identities and photo replacement policy.
3. Device-specific import/free-space margin and installed-pack retention.
4. Comparative USearch/hnswlib/SQLite Vec1 benchmark and ABI/build review.
5. Dangerous-confusion recall floors and multi-view evidence policy.
6. Future RiskEngine/open-set/calibration approvals and production medical copy.

## Scope confirmations

- Real `.gribpack`: not created.
- Photographs: not downloaded or added.
- Model training: not performed.
- BioCLIP: not run.
- Production RiskEngine: not implemented or weakened.
- Native ANN dependency: not added.
- Network/external APIs: not used.
- UI composition/design: unchanged; no import screen added.
- Production medical gate: remains blocked.
- Commit/push/PR/merge/rebase/main changes: not performed.

**MANDATORY OFFLINE KNOWLEDGE PACK ARCHITECTURE V1: READY FOR REVIEW**
