# Mandatory Offline Knowledge Pack Architecture v1

## Decision boundary

**VALID ACTIVE KNOWLEDGE PACK IS MANDATORY.**

Recognition may run only when one installed `.gribpack` is complete, trusted,
compatible, runtime-openable and atomically marked active. Missing, partial,
corrupt, untrusted or incompatible packs result in
`RECOGNITION_UNAVAILABLE`. There is no embedded or legacy fallback recognizer.

Stage B0 adds architecture and synthetic contracts only. It adds no production
model, photograph, embedding, ANN index, RiskEngine, signing key or real taxon.

## APK boundary

The APK retains the approved UI, CameraX multi-view capture, emergency route,
temporary app-private photo storage, SAF import contract, verifier/runtime
contracts, atomic activation/rollback and `NoModelInferenceEngine`. Knowledge,
weights, references, calibration and risk artifacts are not bundled in the APK.

No new screen or broad storage/network permission is introduced. The SAF
selection contract uses `ACTION_OPEN_DOCUMENT` and persisted read permission.

## Transfer and installed layouts

The transfer artifact is a single ZIP64-compatible file, conventionally:

```text
grib-karelia-northwest-v1.gribpack
```

Future production contents:

```text
manifest.json
file-manifest.json
model/mobile-model.tflite
embeddings/{cap-top,underside,side,stem,stem-base}/
search-index/index shards
reference-images/optimized references
metadata/reference.sqlite
taxonomy/taxonomy.json
taxonomy/confusion-groups.json
open-set/rejection-contract.json
open-set/ood-artifacts/
calibration/calibration.json
risk-rules/risk-rules.json
licenses/attribution.json
licenses/source-registry.json
checksums.sha256
signature.json
```

After verification, the pack is expanded into app-specific storage. The active
directory is read-only to runtime code. Staging, active and rollback ownership
never extends beyond the app-owned pack root.

SAF copying and ZIP extraction are architecture contracts in Stage B0, not a
shipping importer. Until a bounded copier/extractor and approved signature
verifier are implemented and reviewed, no pack can reach production activation.

## Training dataset versus mobile pack

A training dataset is a research input with source observations, splits,
labels, augmentation policy and training provenance. It is never copied into
the application as-is. A mobile pack is a separately released, size-bounded,
version-locked runtime artifact containing only approved deployable outputs and
their evidence manifests. Dataset approval does not imply pack approval.

## Manifest and version lock

`manifest.schema.json` locks app range, model contract and digest, embedding
model/dimension/dtype, taxonomy, dangerous confusion groups, open-set,
calibration, risk rules, search engine/index format, license/file manifests,
signature policy, sizes/counts and production approval.

The existing `ArtifactCompatibilityGate` remains the single compatibility
boundary. `KnowledgePackCompatibilityGate` delegates to its expanded pack
method. No parallel permissive gate exists.

Schema parity is explicit: Kotlin field registries reject missing and unknown
manifest/index properties, while the offline Python validator applies the same
closed JSON Schemas. File hashes are verified before compatibility; compatibility
then checks every version, ID, dtype, count, metric and descriptor relationship.

| Component | Required match |
|---|---|
| App | current version within inclusive min/max |
| Pack | supported format and immutable pack ID/version |
| Model | ID, contract version and SHA-256 |
| Embeddings | model ID, SHA-256, dimension and dtype |
| Taxonomy/confusions | exact independent versions and hashes |
| Open-set/calibration/risk | exact versions and hashes |
| Search | engine/version, index format, metric, shards and embedding contract |
| Trust | production approval, required signature and known signing key |

`signature.json` is a detached envelope over the exact SHA-256 values of
`manifest.json`, `file-manifest.json` and `checksums.sha256`; the latter binds
every payload file. Stage B0 has no approved key/trust-store or cryptographic
verifier, so even a structurally correct envelope is rejected for production.
Metadata equality is never treated as signature proof.

## Runtime chain

```text
active read-only pack
→ ArtifactCompatibilityGate
→ KnowledgePackRuntime open probe
→ metadata filtering
→ ANN candidate retrieval
→ exact reranking
→ future multi-view evidence aggregation
→ InferenceEngine
→ future RiskEngine
```

Stage B0 stops before final aggregation and RiskEngine. Search candidates are
internal records and cannot become `MushroomApiResponse` or API output.

## Pack lifecycle

States are `NOT_INSTALLED`, `SELECTED`, `PREFLIGHT_FAILED`, `IMPORTING`,
`VERIFYING`, `INCOMPATIBLE`, `UNTRUSTED`, `READY`, `ACTIVE`, `CORRUPTED`,
`MISSING` and `REMOVING`.

A failed update never changes the current active pointer. Successful activation
uses a same-filesystem atomic move. Interrupted staging is removed at next
startup. Only app-owned staging/rollback data may be deleted; the user-selected
source document is never deleted.

The active pointer is a separate atomically replaced app-private record. An
activation-pending marker permits startup recovery: if a crash occurs between
moving old/new directories and replacing the pointer, rollback is restored and
the uncommitted candidate is discarded. Active files are marked read-only.

## Failure matrix

| Condition | New pack | Previous pack | Recognition |
|---|---|---|---|
| No installed pack | none | none | `RECOGNITION_UNAVAILABLE` |
| Selection cancelled/SD removed | not activated | preserved | previous if still valid; otherwise unavailable |
| Low space | preflight fails | preserved | previous if valid |
| Unsafe ZIP path/symlink/bomb | rejected | preserved | previous if valid |
| Missing file/hash mismatch | rejected | preserved | previous if valid |
| Unknown version/signing key | rejected | preserved | previous if valid |
| Runtime open probe fails | rejected | preserved | previous if valid |
| Active files later disappear/corrupt | quarantined | no partial use | `RECOGNITION_UNAVAILABLE` |

Path validation rejects `/` and drive/UNC absolutes, backslashes, `..`, encoded
traversal, exact duplicates, case-folded collisions, Unicode NFC collisions,
special/link entries and nested ZIP/JAR/APK/GRIBPACK payloads. Counts, individual
sizes, cumulative sizes and compression ratios are bounded using signed-`Long`
compatible limits. Control-file symlinks are rejected before they are opened.

Five-gigabyte packs must be copied and hashed with bounded streaming buffers.
Import free-space arithmetic uses checked `Long` addition for archive, unpacked
content and rollback margin. Future model/index/SQLite open paths are required
to use mmap/page-based access; Stage B0 provides no code that loads a real pack.

The pack contains release references only. Capture URIs, GPS and temporary
photos never enter pack storage or diagnostic identifiers. SAF source URIs are
not persisted in the active pointer and import never enumerates sibling files.

## Knowledge updates and replacement

Every taxonomy, reference-image or metadata replacement produces a new pack
version and file digest. An obsolete photograph is not edited in place: a new
pack removes its reference ID, records provenance/review in the release inputs
and rebuilds affected embeddings/index shards. Rollback keeps the prior complete
pack until activation succeeds. Stale packs require an explicit expiry/revocation
policy before production.

## Open questions

- Approved signing algorithm, key custody, rotation and revocation.
- Maximum installed pack count and user-visible storage policy.
- Device-specific 5 GB import time/free-space margins.
- Human approval process for real references and dangerous confusion evidence.
- Production recall floors, which remain open until dangerous-confusion tests.
