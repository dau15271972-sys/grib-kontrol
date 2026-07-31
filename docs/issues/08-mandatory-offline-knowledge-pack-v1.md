# [SAFETY][B0] Mandatory Offline Knowledge Pack Architecture v1

## Goal

Make a fully validated, compatible, trusted and active `.gribpack` mandatory
for every recognition attempt.

## Scope

Manifest/file schemas, offline validator, SAF/app-storage contracts, atomic
activation/rollback, expanded `ArtifactCompatibilityGate`, synthetic fixture,
replaceable vector search boundary, exact recall oracle, benchmark design, CI
and architecture reports.

## Prohibited

No production inference, model, real photograph/taxon/embedding/index, BioCLIP,
training, production RiskEngine, raw similarity in UI/API, network inference,
broad storage permission or result from one nearest reference.

## Acceptance

- Missing/corrupt/incompatible/untrusted pack returns
  `RECOGNITION_UNAVAILABLE`.
- Verification precedes atomic activation and failed updates preserve active.
- Synthetic pack has `production_approved=false` and cannot activate.
- ANN candidates remain internal and exact baseline measures recall.
- Python, Android, safety, taxonomy/reference validators, lint and debug build
  pass without changing the approved visual composition.

## Open dependencies

Signing/key policy, licensed regional inventory, real model research,
dangerous-confusion recall floors, device benchmark and human safety approvals.
