# Mandatory Offline Knowledge Pack v1

`VALID ACTIVE KNOWLEDGE PACK IS MANDATORY`.

This directory contains only schemas, authoring templates and a small unpacked
synthetic fixture. It contains no production `.gribpack`, real model, image,
taxon, geographic observation, signing key or expert signature.

## Container

The transfer format is one ZIP64-compatible `.gribpack`. Verification must be
streaming and bounded; the container is never loaded fully into RAM. After all
checks pass, files are expanded into app-specific staging and activated
atomically as a read-only pack.

The future production layout is documented in
`docs/architecture/mandatory-offline-knowledge-pack-v1.md`. The synthetic
fixture intentionally replaces model weights, reference images and SQLite/native
indexes with small JSON contracts. Its manifest has
`production_approved=false`, `signature_required=false` and
`vector_search_engine=EXACT_BASELINE`.

## Validation

```powershell
.venv\Scripts\python.exe scripts\validate_reference_pack.py
.venv\Scripts\python.exe scripts\validate_reference_pack.py --require-production
```

The first command validates structure and compatibility of the synthetic
fixture. The second command must fail closed because the fixture is neither
production-approved nor signed.

SAFETY: contract validation is not activation approval. A future production
pack additionally requires a known signing key, human approvals, dangerous
confusion evaluation and a compatible runtime.
