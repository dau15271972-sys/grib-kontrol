# Offline Knowledge Pack install flow v1

## SAF selection

Android selects one `.gribpack` through `ACTION_OPEN_DOCUMENT`, requests a
persisted read grant and streams the content URI. The app does not request
`MANAGE_EXTERNAL_STORAGE`, legacy read/write storage permissions or `INTERNET`.
Cancellation and a removed SD card are normal fail-closed outcomes.

## Transaction

```text
select document
→ persist read permission
→ preflight free space and declared limits
→ bounded stream copy to app-owned staging
→ strict ZIP64 central-directory/path inspection
→ manifest and file-manifest schema validation
→ streaming SHA-256 for every declared file
→ signature/trust-store verification
→ ArtifactCompatibilityGate
→ read-only runtime/index open probe
→ atomic active-directory switch
→ remove obsolete app-owned staging/rollback
```

The source document is never modified or deleted. Neither the ZIP nor an index
is loaded fully into RAM. Copy/hash/extraction buffers are bounded. Extraction
rejects duplicate paths, case/Unicode-normalized collisions, absolute/UNC/drive
paths, `..`, backslashes, encoded traversal, symlinks/special entries, nested
archives, excessive file count/size and suspicious compression ratios.

The detached signature envelope binds the exact manifest, file manifest and
checksums digests. No approved production verifier exists in Stage B0, so the
only installed signature implementation is rejecting and activation remains
blocked. Staging integrity is checked both before trust/compatibility and again
after runtime smoke-open to detect changes before activation.

## Storage invariants

- Staging, active and rollback are siblings on one app-specific filesystem.
- Active content is read-only to inference and search components.
- Activation requires an atomic filesystem operation; unsupported atomic moves
  fail and restore the previous pointer.
- The pointer and pending-activation journal are atomically replaced outside
  active content; restart restores rollback after a mid-switch crash.
- Startup removes only incomplete app-owned staging directories.
- Uninstall may remove app-owned installed packs; it cannot remove the original
  SAF document.
- Reinstall loses app-private packs and persisted grants according to Android
  platform behavior, so runtime returns `RECOGNITION_UNAVAILABLE` until a pack
  is imported again.
- Low-memory closes search/native handles and fails closed; it does not retry by
  loading the whole index.

## Rollback

The prior active pack remains usable until the new pack passes every gate and
runtime-open probe. A failed copy, verification, signature, compatibility,
index-open or atomic-switch step discards only the new staging directory. No
mixed-version files can be exposed to `InferenceEngine`.

## Recovery matrix

| Event | Recovery |
|---|---|
| Process death during copy | remove incomplete staging on next startup |
| User cancellation | close streams, discard staging, preserve active |
| Source/SD disappears | treat as read failure, preserve active |
| Disk full | stop bounded copy, discard staging, preserve active |
| Hash/signature mismatch | quarantine/discard new staging |
| Atomic move unavailable | abort activation and restore previous active |
| Process death during active switch | pending journal restores previous pointer/directory |
| File changes after verification | second integrity check rejects candidate |
| Active pack missing | mark `MISSING`, close runtime, return unavailable |
| Active pack corrupt | mark `CORRUPTED`, never use partial data |
