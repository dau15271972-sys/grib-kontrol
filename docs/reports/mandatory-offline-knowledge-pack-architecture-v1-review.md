# Mandatory Offline Knowledge Pack Architecture v1 — independent review

## Verdict

**MANDATORY OFFLINE KNOWLEDGE PACK ARCHITECTURE V1 REVIEW: PASSED**

This verdict applies to Stage B0 architecture and synthetic contracts only.
There is still no approved production pack, signing key, importer, model or ANN
runtime. Every current production entrypoint remains fail-closed.

## Review baseline

- Repository: `dau15271972-sys/grib-kontrol`.
- Branch: `arch/offline-reference-pack-v1`.
- Base and current HEAD:
  `59797d3e4397e402c4267572a82eba5704599a12`.
- Initial verdict: `MANDATORY OFFLINE KNOWLEDGE PACK ARCHITECTURE V1: READY FOR REVIEW`.
- Initial staged files: none.
- Initial Python tests: 125 passed.
- Initial Android tests: 34 passed, 0 failed/errors/skipped.
- Commit, push, PR, merge, rebase and `main` changes were prohibited and were
  not performed.

The initial commands confirmed the exact branch/SHA, an unstaged Stage B0-only
worktree and no Compose layout, design asset, Android manifest, taxonomy matrix,
real model, real photograph or `.gribpack` change. `git diff --check` reported
only informational Git line-ending conversion warnings.

## Files reviewed

All modified and untracked paths were read or validated. The exact Stage B0
inventory was:

```text
.github/workflows/ci.yml
AGENTS.md
README.md
android-app/app/src/main/java/com/mushroom/detector/artifacts/ArtifactBundleManifest.kt
android-app/app/src/main/java/com/mushroom/detector/artifacts/ArtifactCompatibilityGate.kt
android-app/app/src/main/java/com/mushroom/detector/artifacts/CompatibilityMatrix.kt
android-app/app/src/main/java/com/mushroom/detector/artifacts/KnowledgePackContracts.kt
android-app/app/src/main/java/com/mushroom/detector/artifacts/KnowledgePackStorage.kt
android-app/app/src/main/java/com/mushroom/detector/artifacts/VectorSearch.kt
android-app/app/src/main/java/com/mushroom/detector/inference/NoModelInferenceEngine.kt
android-app/app/src/main/java/com/mushroom/detector/inference/SafeInferenceRunner.kt
android-app/app/src/test/java/com/mushroom/detector/artifacts/ArtifactCompatibilityGateTest.kt
android-app/app/src/test/java/com/mushroom/detector/artifacts/KnowledgePackArchitectureTest.kt
android-app/app/src/test/java/com/mushroom/detector/artifacts/VectorSearchContractTest.kt
android-app/app/src/test/java/com/mushroom/detector/inference/SafeInferenceRunnerTest.kt
app/artifacts.py
app/inference.py
app/main.py
data/reference-pack/README.md
data/reference-pack/fixtures/invalid-synthetic/missing-manifest/README.md
data/reference-pack/fixtures/invalid-synthetic/path-traversal/README.md
data/reference-pack/fixtures/invalid-synthetic/path-traversal/file-manifest.json
data/reference-pack/fixtures/valid-synthetic/calibration/calibration.json
data/reference-pack/fixtures/valid-synthetic/checksums.sha256
data/reference-pack/fixtures/valid-synthetic/embeddings/cap-top/synthetic-vectors.json
data/reference-pack/fixtures/valid-synthetic/embeddings/embedding-contract.json
data/reference-pack/fixtures/valid-synthetic/embeddings/underside/synthetic-vectors.json
data/reference-pack/fixtures/valid-synthetic/file-manifest.json
data/reference-pack/fixtures/valid-synthetic/licenses/attribution.json
data/reference-pack/fixtures/valid-synthetic/licenses/source-registry.json
data/reference-pack/fixtures/valid-synthetic/manifest.json
data/reference-pack/fixtures/valid-synthetic/metadata/reference.json
data/reference-pack/fixtures/valid-synthetic/model/synthetic-model-contract.json
data/reference-pack/fixtures/valid-synthetic/open-set/rejection-contract.json
data/reference-pack/fixtures/valid-synthetic/risk-rules/risk-rules.json
data/reference-pack/fixtures/valid-synthetic/search-index/benchmark-report.json
data/reference-pack/fixtures/valid-synthetic/search-index/build-config.json
data/reference-pack/fixtures/valid-synthetic/search-index/exact-baseline-index.json
data/reference-pack/fixtures/valid-synthetic/taxonomy/confusion-groups.json
data/reference-pack/fixtures/valid-synthetic/taxonomy/taxonomy.json
data/reference-pack/schema/file-manifest.schema.json
data/reference-pack/schema/manifest.schema.json
data/reference-pack/schema/search-index-descriptor.schema.json
data/reference-pack/schema/signature.schema.json
data/reference-pack/templates/benchmark-config.json
data/reference-pack/templates/file-manifest.json
data/reference-pack/templates/manifest.json
data/reference-pack/templates/search-index-descriptor.json
data/reference-pack/templates/signature.json
docs/architecture/adr-vector-search-engine-candidates.md
docs/architecture/mandatory-offline-knowledge-pack-v1.md
docs/architecture/offline-knowledge-pack-install-flow-v1.md
docs/architecture/vector-search-engine-v1.md
docs/issues/08-mandatory-offline-knowledge-pack-v1.md
docs/issues/README.md
docs/reports/mandatory-offline-knowledge-pack-architecture-v1.md
docs/reports/mandatory-offline-knowledge-pack-architecture-v1-review.md
scripts/benchmark_vector_search.py
scripts/validate_reference_pack.py
tests/test_app.py
tests/test_artifacts.py
tests/test_reference_pack_contract.py
tests/test_vector_search_benchmark.py
```

Supporting review covered `AndroidManifest.xml`, `MushroomViewModel`, all
`InferenceEngine` definitions/usages, `MushroomApiResponse`, capture temporary
storage, Stage A final report/architecture, taxonomy schemas/policies/validator,
Gradle configuration/wrapper, safety/medical gates, desktop build script and the
complete CI workflow.

## Recognition call trace and main invariant

Production Python/desktop:

```text
desktop/run_desktop.py
→ create_app()                    # no engine/gate/manifest parameters
→ SafeInferenceRunner(NoModelInferenceEngine())
→ RECOGNITION_UNAVAILABLE
```

Production Android:

```text
MushroomViewModel
→ SafeInferenceRunner(NoModelInferenceEngine())
→ RECOGNITION_UNAVAILABLE
```

Future pack runtime contract:

```text
KnowledgePackRepository.activePack
→ ACTIVE + signatureTrusted + readOnly
→ manifest/model/index providers
→ KnowledgePackCompatibilityGate
→ ArtifactCompatibilityGate
→ trusted runtime open + available
→ otherwise UnavailableKnowledgePackRuntime
→ NoModelInferenceEngine
```

No legacy recognizer, embedded model runtime or alternate compatibility gate was
found. Python `create_app` previously exposed an engine injection path; the review
removed it from the production factory. Synthetic exact search is now rejected
by both Python and Kotlin production compatibility gates. Therefore, without a
trusted ACTIVE `.gribpack`, recognition is impossible in all shipping paths.
The emergency route remains independent and available.

## Confirmed defects and fixes

| ID | Severity | Confirmed defect | Correction |
|---|---|---|---|
| R1 | Critical | Python `create_app` accepted caller-supplied engine/gate/manifest booleans | production factory now has no injection parameters and always installs `NoModelInferenceEngine` |
| R2 | High | `EXACT_BASELINE` could satisfy the old production compatibility matrix | rejected in Python/Kotlin production gates; production search factory always unavailable |
| R3 | High | ZIP validation missed case-fold, Unicode NFC and encoded traversal collisions, special entries and nested archives | canonical collision checks, encoded-path rejection, special/link/nested-archive rejection and tests added |
| R4 | High | signature metadata was not bound to control manifests and could be mistaken for proof | strict detached-envelope schema binds manifest/file-manifest/checksums hashes; cryptographic verification remains explicitly unavailable/fail-closed |
| R5 | High | active state existed only in memory and a crash between directory moves could lose the previous pointer | atomic pointer, pending journal, startup rollback recovery and persisted descriptor tests added |
| R6 | High | Kotlin manifest omitted schema fields and compatibility ignored required relationships | complete schema field registry, raw unknown/missing rejection, field/path/hash/count/dtype/metric/descriptor checks and parity tests added |
| R7 | High | staging could change after verification/runtime probe | required integrity verifier is executed before trust and again immediately before activation |
| R8 | Medium | free-space arithmetic covered only unpacked size and was not overflow-safe | checked `Long` sum now includes archive, unpacked content and rollback margin |
| R9 | Medium | search accepted query region/view different from the opened descriptor and raw distance was serialization-visible | mismatch returns unavailable; distance is JVM-transient; production/synthetic factories separated |
| R10 | Medium | benchmark labelled Python allocation proxy as peak RSS | OS peak RSS and `tracemalloc` are reported separately with scope limitation |
| R11 | Medium | CI validated the synthetic fixture but did not prove production activation stayed blocked | explicit expected-failure production validator step added without replacing pytest/safety gates |
| R12 | Documentation | README implied a shipping importer already existed | clarified that copier/extractor/signature verifier are Stage B0 contracts and production activation is unavailable |

No unconfirmed or cosmetic change was made.

## Schema–Python–Kotlin parity

| Area | JSON Schema | Python validator | Kotlin contract/gate | Result |
|---|---|---|---|---|
| Unknown properties | `additionalProperties=false` | deterministic unknown-field error | exact field registries reject unknown/missing | PASS |
| Required/nullability | explicit required list; only signing key nullable | strict type/required validation | non-null constructor fields; nullable signing key only | PASS |
| Semver/app range | patterns/const | strict parser and inclusive range | strict parser and inclusive range | PASS |
| SHA-256 | lowercase 64-hex | streaming file/control digest checks | shape checks; verified file set is prerequisite | PASS |
| Sizes/counts | signed Long/Int maxima | bounded sums and operational limits | checked Long preflight, positive count checks | PASS |
| Model/embedding | ID/paths/hash/dimension/dtype | policy + file-manifest binding | matrix + descriptor + path/hash/dtype | PASS |
| Taxonomy/confusions/open-set/calibration/risk | independent version/path/hash | policy + digest binding | matrix + path/hash checks | PASS |
| Search | engine/version/format/metric/shards/counts/loading | policy and schemas | manifest/index descriptor relational checks | PASS |
| Trust | approval/signature fields | signed-envelope contract; crypto unavailable | rejecting verifier; trusted/active/read-only required | FAIL-CLOSED |

The Python validator remains the package structure/checksum boundary;
`ArtifactCompatibilityGate` remains the sole version-lock decision. The Kotlin
adapter delegates to it and does not form a second permissive policy.

## Package threat model

| Threat | Control | Result |
|---|---|---|
| `../`, absolute, drive, UNC, mixed separators | strict relative POSIX paths; backslash forbidden | rejected |
| percent-encoded traversal | repeated decode safety check | rejected |
| exact/case-insensitive/Unicode collisions | duplicate + NFC/casefold canonical key | rejected |
| symlink/special/link entry | Unix mode inspection; control links rejected before open | rejected |
| nested archive | ZIP/JAR/APK/GRIBPACK suffix ban | rejected |
| zip bomb/high ratio | file/count/total/ratio limits | rejected |
| integer overflow | signed-Long maxima and checked cumulative addition | rejected |
| manifest/archive/file size mismatch | exact entry sizes, total payload and exact archive size | rejected |
| undeclared/missing file | exact file-manifest set comparison | rejected |
| file mutation/TOCTOU | streaming digest plus second staging integrity check | rejected |
| signature substitution | detached envelope binds all three control manifests | rejected; no crypto verifier approved |
| unknown key/algorithm | empty trust store and ED25519 contract | rejected |

ZIP has no portable hard-link record. Unix entries that identify a link or
non-regular special type are rejected; a production extractor must preserve
this rule and create every file exclusively inside canonical app-owned staging.

## Import and activation failure matrix

| Stage/failure | Candidate | Previous active | Recovery/result |
|---|---|---|---|
| selected/cancelled/revoked SAF | not read | unchanged | preflight failed |
| source disappears during copy | incomplete staging | unchanged | close/discard app staging; contract only until copier exists |
| preflight low space/overflow/FAT32 limit | not imported | unchanged | fail closed; FAT32 source/container limits documented for production importer |
| copying/extracting process death | orphan staging | unchanged | startup cleanup |
| unsafe/corrupt archive | rejected | unchanged | no extraction outside staging |
| checksum or signed-envelope mismatch | untrusted/corrupt | unchanged | staging discarded |
| compatibility mismatch | incompatible | unchanged | staging discarded |
| SQLite/index/model smoke-open failure | corrupt | unchanged | activation never called |
| file changes after smoke-open | corrupt | unchanged | second integrity check blocks activation |
| crash after old active move | pending journal | rollback retained | startup restores rollback |
| crash after new active move, before pointer | uncommitted new active | rollback retained | new candidate removed; rollback restored |
| atomic move unsupported | not active | restored | false result; no pointer change |
| cleanup failure | no runtime promotion from staging | active pointer remains authoritative | fail closed/report in future importer |

The active tree is marked owner-readable and owner-non-writable; replacement
temporarily restores owner write permission only inside the app-owned root.
The original SAF document URI/content is never written, deleted or stored in the
active pointer.

## Storage and memory audit

- Python reads manifest JSON with a 2 MiB bound and hashes payloads with a 1 MiB
  streaming buffer; no archive payload uses unbounded `read()`.
- Size fields use Python bounded arithmetic compatible with Kotlin signed Long;
  Kotlin uses `Math.addExact` for archive + unpacked + rollback margin.
- No real model, index or SQLite runtime exists, so there is no hidden whole-file
  load or per-query shard reopen in production.
- Future production descriptors permit `MEMORY_MAPPED` or `PAGE_BASED`; the only
  in-memory mode is synthetic-only and rejected by production factories.
- Search buffers, executor count and threads are bounded; cancellation and close
  are explicit.
- No 5 GB fixture was created. Files larger than 2/4 GB remain a future device
  import test, but the current arithmetic/path contracts do not narrow to Int.

## Vector search audit

The implemented pipeline stops at safe contracts:

```text
metadata filtering
→ candidate retrieval
→ exact reranking
→ future multi-view evidence
→ future InferenceEngine/RiskEngine integration
```

Region/view/model/dimension mismatches return unavailable. Thumbnails and
transformed copies sharing an observation ID contribute one observation. Exact
reranking only reorders internal candidates. Empty candidates do not create a
safety result. Raw distance is internal/transient and absent from API/UI.
Trusted dangerous evidence is retained outside ANN truncation. Reference matches
never create `MushroomApiResponse`, `SAFE`, confidence or a taxonomic top-1 result.

`ProductionVectorSearchEngineFactory` always returns unavailable. The synthetic
exact classes remain test/benchmark-only. No native dependency, index or final
aggregation was added.

## Benchmark and native isolation audit

Profiles 10k/100k/1m, fixed seed, required latency percentiles, index size,
multi-view latency and recall cutoffs are defined. Only the allowed 10k exact
smoke was run; no generated index was tracked. Its final result was:

| Metric | Result |
|---|---:|
| open | 186.2989 ms |
| cold | 180.5918 ms |
| warm mean | 176.0014 ms |
| p50/p95/p99 | 175.7167 / 183.9370 / 183.9370 ms |
| process peak RSS | 58,089,472 bytes |
| peak traced Python allocation | 10,858,867 bytes |
| estimated vector storage | 1,280,000 bytes |
| multi-view | 727.9806 ms |
| exact-vs-exact recall@10/50/100 | 1.0 / 1.0 / 1.0 |

Recall=1.0 is explicitly an exact-oracle sanity check, not ANN evidence.
Production minimum recall remains `OPEN_SAFETY_PARAMETER` pending dangerous-
confusion evaluation.

Future isolation options are documented: in-process native runtime has minimal
IPC but no crash isolation; isolated Android service adds sandbox/IPC overhead;
a separate-process service adds strongest crash separation and lifecycle/memory
cost. Production choice remains **NOT YET APPROVED**.

## Privacy and permissions

- Android manifest contains CAMERA only; no INTERNET, broad storage or location
  permission is present.
- Knowledge-pack runtime contains no URL/HTTP/OkHttp/Retrofit code.
- SAF contract accepts only persisted readable `content://` selection and does
  not scan sibling files.
- Active pointer contains pack ID/version/trust/read-only state only: no URI,
  path, GPS or personal data.
- Pack storage does not import or reference `CaptureFileStore`; temporary Stage A
  capture deletion policy was unchanged.
- Synthetic fixture has zero images and invented IDs only.

## CI audit

The reference validator runs after Ruff/pytest/taxonomy and before existing
safety/medical gates. A separate expected-failure step proves the synthetic pack
cannot activate. The validator is offline, uses no secrets/downloads and creates
no pack. Android unit/lint/APK and desktop jobs are unchanged and not replaced.

## Regression tests added during review

Coverage was added for case/Unicode collisions, backslash/encoded/drive paths,
nested archives, signed-Long overflow, archive/file size mismatch, mutation
after validation, strict unknown fields, signed-envelope binding, schema parity,
SAF revocation/source loss, staging restart cleanup, persisted pointer, activation
crash recovery, read-only state, double integrity check, production exact-engine
isolation, descriptor region/view, transformed observations, empty evidence,
raw-distance transient serialization, forbidden permissions/network/capture
coupling, real peak RSS semantics and CI negative activation.

## Verification results

| Check | Result |
|---|---|
| Python Ruff | PASS |
| Full pytest | PASS, 139 passed; baseline 125 (+14) |
| Taxonomy validator | PASS, 3 taxa / 1 group / 4 reviews |
| Reference-pack validator | PASS, 18 container files, synthetic/non-production |
| Production reference activation | EXPECTED FAIL: exact synthetic, signature not required, not approved |
| Safety source gates | PASS |
| Medical development gate | PASS |
| Medical production gate | EXPECTED FAIL, placeholder remains blocked |
| Gradle Wrapper validator | PASS |
| Android unit tests | PASS, 46; baseline 34 (+12), 0 failed/errors/skipped |
| Android lint | PASS, 0 errors; 15 pre-existing GradleDependency warnings |
| Android debug APK | PASS, 13,894,498 bytes |
| Desktop EXE | PASS, 5,101,640 bytes; bundled model/pack count 0 |
| JSON validation | PASS, 34 JSON files |
| UTF-8/final newline | PASS, 146 text files before this report |
| `git diff --check` | PASS; informational line-ending warnings only |

Final artifact hashes:

```text
APK SHA-256  96274C366CAC1FF9F2A4217E92E526443E46BA6AE8D4A87F00F16C26ED8FB7F3
EXE SHA-256  4EC34BE5290059C214BF0FDB1A8E4C39EC8F7BC30752CDF6BC23207751EE674F
```

## Files changed by the review

The review corrected or extended:

```text
.github/workflows/ci.yml
README.md
app/artifacts.py
app/main.py
android-app/app/src/main/java/com/mushroom/detector/artifacts/ArtifactCompatibilityGate.kt
android-app/app/src/main/java/com/mushroom/detector/artifacts/CompatibilityMatrix.kt
android-app/app/src/main/java/com/mushroom/detector/artifacts/KnowledgePackContracts.kt
android-app/app/src/main/java/com/mushroom/detector/artifacts/KnowledgePackStorage.kt
android-app/app/src/main/java/com/mushroom/detector/artifacts/VectorSearch.kt
android-app/app/src/test/java/com/mushroom/detector/artifacts/ArtifactCompatibilityGateTest.kt
android-app/app/src/test/java/com/mushroom/detector/artifacts/KnowledgePackArchitectureTest.kt
android-app/app/src/test/java/com/mushroom/detector/artifacts/VectorSearchContractTest.kt
android-app/app/src/test/java/com/mushroom/detector/inference/SafeInferenceRunnerTest.kt
data/reference-pack/schema/file-manifest.schema.json
data/reference-pack/schema/manifest.schema.json
data/reference-pack/schema/search-index-descriptor.schema.json
data/reference-pack/schema/signature.schema.json
data/reference-pack/templates/search-index-descriptor.json
data/reference-pack/templates/signature.json
docs/architecture/mandatory-offline-knowledge-pack-v1.md
docs/architecture/offline-knowledge-pack-install-flow-v1.md
docs/architecture/vector-search-engine-v1.md
scripts/benchmark_vector_search.py
scripts/validate_reference_pack.py
tests/test_app.py
tests/test_artifacts.py
tests/test_reference_pack_contract.py
tests/test_vector_search_benchmark.py
docs/reports/mandatory-offline-knowledge-pack-architecture-v1-review.md
```

## Git diff and status

Tracked `git diff --stat` before this untracked report:

```text
16 files changed, 573 insertions(+), 97 deletions(-)
```

Untracked files are intentionally not represented by ordinary `git diff`; after
this report there are 47 untracked files. Staged files remain absent.

Final short status is recorded as:

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
 M app/main.py
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
?? docs/reports/mandatory-offline-knowledge-pack-architecture-v1-review.md
?? docs/reports/mandatory-offline-knowledge-pack-architecture-v1.md
?? scripts/benchmark_vector_search.py
?? scripts/validate_reference_pack.py
?? tests/test_reference_pack_contract.py
?? tests/test_vector_search_benchmark.py
```

## Open production questions

1. Approved production pack builder and bounded Android SAF copier/extractor.
2. ED25519 trust store, key custody, rotation, revocation and audit process.
3. Real SQLite/model/index smoke-open implementations and low-memory device tests.
4. FAT32/removable-media and >2/>4 GB physical-device import tests.
5. Comparative USearch/hnswlib/SQLite Vec1 benchmark, ABI/license review and
   decision between in-process/service/separate-process isolation.
6. Dangerous-confusion recall floors, aggregation/RiskEngine and production
   medical-copy approvals.

None is silently defaulted or reachable in current production code. Each needs
a separate safety review before activation can be enabled.

## Scope confirmation

- Real photographs/reference media: absent.
- Model weights/BioCLIP: absent/not run.
- Native ANN libraries: absent.
- Production `.gribpack`: absent.
- Real taxa: not added.
- UI/Compose/design/assets/CameraX: unchanged.
- Production medical gate: still blocked.
- Commit/push/PR/merge/rebase/`main`: not performed.

**MANDATORY OFFLINE KNOWLEDGE PACK ARCHITECTURE V1 REVIEW: PASSED**
