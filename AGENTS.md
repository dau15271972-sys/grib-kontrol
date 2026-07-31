# AGENTS.md

## Scope

These rules apply to the entire repository. The master assignment for the
“Гриб Контроль” project is the source of truth. When convenience, accuracy,
performance, size, or delivery speed conflicts with safety, safety wins.

## Product boundary

The application is an offline, conservative aid for preliminary mushroom
risk assessment from several photographs. It must never decide or imply that
a mushroom may be eaten, collected, cooked, or is safe.

Allowed final statuses:

- `RECOGNITION_UNAVAILABLE`
- `TECHNICAL_FAILURE`
- `HIGH_RISK`
- `NEED_MORE_PHOTOS`
- `UNKNOWN`
- `POSSIBLE_TAXON`

There is no `SAFE` status or equivalent. `POSSIBLE_TAXON` is only a tentative
taxonomic match and is never an edibility or safety conclusion.

## Non-negotiable safety invariants

- Fail closed whenever a model, taxonomy, calibration, risk rules, manifest,
  or compatibility contract is missing, untrusted, or incompatible.
- A trusted dangerous signal must not be replaced by `TECHNICAL_FAILURE` or
  averaged away.
- Never show logits, raw softmax, cosine similarity, distance scores, or an
  uncalibrated percentage as user confidence.
- Never use horizontal mirroring or rotation as an independent test.
- Never infer `unknown` by adding a normal softmax class.
- Never weaken rejection, dangerous-confusion handling, thresholds, or
  artifact version locking without a separately marked `SAFETY` review.
- Do not add network access to the inference path.
- Do not store photos or GPS without explicit consent and a declared retention
  period. Temporary captures must remain app-private and be disposable.
- Do not add an unregistered model asset. Every production model must be
  declared centrally, checked by `ArtifactCompatibilityGate`, and covered by
  CI.
- Medical and emergency wording must be treated as human-reviewed content.
  Do not silently expand it.

## Current implementation stage

SAFETY: Stage A is closed. The current stage is:

`Stage B0 — Mandatory Offline Knowledge Pack Architecture`.

Stage B0 permits contracts, manifest and import/storage architecture,
compatibility gates, synthetic fixtures, fail-closed runtime, vector-search
abstractions, tests and documentation.

Stage B0 forbids production inference, real models or photographs, a real ANN
index, BioCLIP, training, weakened open-set or RiskEngine behavior, raw
similarity in UI/API, and any result based on one nearest reference image.

SAFETY: a fully validated, compatible, trusted and active `.gribpack` is
mandatory for recognition. Without it, every inference surface must return
`RECOGNITION_UNAVAILABLE`; no fallback recognizer is allowed.

## Architecture expectations

- Android capture, quality, inference, artifact, safety, emergency, history,
  and UI responsibilities stay separated.
- `InferenceEngine` is the only inference contract.
- `NoModelInferenceEngine` remains the default implementation during Stage B0.
- `ArtifactCompatibilityGate` must run before any future production inference.
- Pack import must finish checksum, signature, compatibility and runtime-open
  verification before atomic activation; failed updates preserve the previous
  active pack.
- ANN may retrieve internal candidates only. Exact reranking, multi-view
  evidence and the future RiskEngine remain separate safety-reviewed stages.
- Observation sessions identify explicit view types; transformed copies are
  not independent observations.
- Bounding boxes, crops, and nullable masks are distinct types.
- UI, API, ViewModel, Room, history, and tests must not expose second/third
  confidence fields from the removed recognizer.
- The emergency screen remains reachable when recognition is unavailable and
  after technical failure.

## Approved visual baseline

`Гриб контроль.png` and `android_preview.html` define the approved visual
composition. The following elements are protected unless the user separately
approves a redesign:

- `assets/karelia-bg-2.jpg` as the forest page background;
- `assets/karelia-bg.webp` as the hero mushroom photograph;
- the `ГРИБ КОНТРОЛЬ` hero heading;
- the natural green/cream palette, rounded light cards, and vertically
  scrollable page.

SAFETY: preserve that visual structure while removing or replacing unsafe demo
content. The reference and production UI must not contain edible labels,
confidence percentages, second/third tests, low-risk claims, mushroom names as
an inference result, or permission to collect, cook, or consume.

## Required verification for Stage B0

Run and report all of the following:

- Python tests
- Python lint
- Android unit tests
- Android lint
- Android debug APK build
- Desktop EXE build
- Gradle Wrapper validation
- forbidden UI phrase tests
- unbound model asset test
- `ArtifactCompatibilityGate` tests
- emergency-access tests
- taxonomy and reference-pack validators
- mandatory-pack and vector-search contract tests

Do not hide failures, unavailable dependencies, build problems, or data
limitations. Do not move to the next major stage until tests and the Stage A
report are complete.

## Repository hygiene

- Inspect existing changes before editing and preserve unrelated user work.
- Mark safety-affecting code and review notes with `SAFETY`.
- Do not commit, push, open a pull request, merge, or modify `main` without a
  separate explicit user command.
- If GitHub Issues cannot be created, prepare complete Markdown issue bodies in
  `docs/issues/` and report the exact access failure.
