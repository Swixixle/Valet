# Valet Recording Subsystem — Invariant Spec

## canonical_json Definition
- Uses `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`
- Always UTF-8 encoded bytes
- No whitespace, no ASCII escaping

## Event Hash Chain Formula
- Each event includes:
  - `event_hash`: SHA-256 of canonical_json(event)
  - `seq`: sequential integer
  - `ts`: ISO-8601 UTC timestamp
  - `payload_hash`: SHA-256 of canonical_json(payload)
- Chain: Each event references previous event_hash (except genesis)

## transcript_hash Definition
- SHA-256 of canonical_json(list of all event dicts in session, in order)
- Used for session integrity

## bundle_manifest Schema (halo.bundle_manifest.v1)
- Fields:
  - `schema_version`: "halo.bundle_manifest.v1"
  - `mode`: "record" or "snapshot"
  - `meta_sha256`: SHA-256 of canonical_json(meta_dict)
  - `receipt_sha256`: SHA-256 of canonical_json(receipt_for_manifest(receipt_dict))
  - `events_sha256` or `payload_sha256`: SHA-256 of canonical_json(events or payload)
  - `raw_content_sha256`: SHA-256 of raw_content.txt (if present)
  - `attachments`: list of attachment dicts (sorted)
- `bundle_hash`: SHA-256 of canonical_json(bundle_manifest)

## receipt_for_manifest Transform
- Removes only:
  - `bundle_hash`
  - `signatures`
- All other fields preserved
- Used for receipt_sha256 calculation

## Deterministic Zip Writer Requirements
- Use `ZipInfo` for every entry
- Fixed metadata:
  - `date_time`: (1980, 1, 1, 0, 0, 0)
  - `create_system`: 0
  - `external_attr`: 0o644 << 16
  - `compress_type`: ZIP_DEFLATED
  - `compresslevel`: 6
- Write files in exact order:
  1. meta.json
  2. bundle_manifest.json
  3. session_receipt.json or snapshot_receipt.json
  4. events.json or payload.json
  5. raw_content.txt (if exists)
  6. verification_log.json
  7. attachments/* (sorted by path)

---
This spec is the contract. Any deviation risks drift and breaks forensic guarantees.