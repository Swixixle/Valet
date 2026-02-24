# Senate Audit / Review Mode

## What is Audit Mode?

Audit Mode in Valet provides forensic, fail-closed verification of Senate-backed claims. It checks for data integrity, provenance, and schema compliance, and flags ambiguous or invalid records. Audit Mode never hallucinates or guesses: if the data is missing or inconsistent, it fails closed and reports the anomaly.

## How to Enable Audit Mode

- For the main dossier pipeline, add `?audit=true` to your POST `/pipeline` request.
- For a full dataset scan, POST to `/audit/senate`.

## AuditStatus Values

- **VERIFIED**: The claim is fully supported by a unique, provenance-grounded Senate record.
- **NO_RECORD**: No matching record exists for the claim.
- **AMBIGUOUS**: Multiple conflicting records exist for the claim.
- **INVALID_DATA**: Data is missing required fields, schema is invalid, or the Senate datasource is unavailable.

## Fail-Closed Guarantees

- If the Senate datasource is missing, corrupt, or ambiguous, Valet returns `NO_RECORD` or `INVALID_DATA` and never falls back to LLM guesses.
- All audit results are deterministic and reproducible.

## Example JSON Response

```
{
  "ok": true,
  "answer": "Senator Jane Doe voted YEA on B1.",
  "grounding": {
    "event_id": "E1",
    "source_file": "events/vote1.json",
    "timestamp": "2025-01-01T12:00:00Z"
  },
  "audit": {
    "status": "VERIFIED",
    "checks": [
      {"coverage": true, "count": 1},
      {"uniqueness": true, "vote": "YEA"},
      {"provenance": true},
      {"manifest": true}
    ],
    "anomalies": []
  }
}
```

## Dataset Audit Example

POST `/audit/senate` returns:

```
{
  "ok": true,
  "audit": {
    "status": "INVALID_DATA",
    "checks": [{"total_events": 2}],
    "anomalies": [
      {"conflict": true, "bill_id": "B1", "senator_id": "S1", "votes": ["YEA", "NAY"]}
    ]
  }
}
```

---

Audit Mode is designed for compliance, transparency, and forensic review. For more, see the code in `app/audit/`.
