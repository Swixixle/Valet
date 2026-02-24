# Senate Integration for Valet

## What is SENATE_DATA_DIR?

`SENATE_DATA_DIR` is an environment variable that tells Valet where to find the verified Senate data artifacts on disk. It must point to the root of the Senate `data/` directory (not the repo root).

## Expected Directory Layout

```
SENATE_DATA_DIR/
  events/      # vote event artifacts (JSON)
  senators/    # senator identity artifacts (JSON)
  manifest.json  # (optional) schema_version
```

## Local Setup

1. Clone or place the Senate `data/` directory adjacent to your Valet repo, or anywhere on disk.
2. Set the environment variable:
   ```sh
   export SENATE_DATA_DIR=/full/path/to/Senate/data
   ```
3. Run Valet as usual. The adapter will validate the directory and index data on first use.

## Replit Setup

1. Upload the Senate `data/` directory to your Replit project.
2. Go to Secrets and add:
   - Key: `SENATE_DATA_DIR`
   - Value: `/home/runner/<repl>/Senate/data`

## Fail-Closed Behavior

- If `SENATE_DATA_DIR` is missing, or required folders/files are missing or invalid, all queries will fail closed (no guesses, no partial results).
- The dossier layer will respond: “No verified Senate record available.”

## API

The adapter exposes:
- `getSenatorById(id)`
- `searchSenators(query)`
- `getVotesBySenator(senator_id, opts)`
- `getVoteByBillAndSenator(bill_id, senator_id)`

All queries are fast and in-memory after first use.

## Automatic Routing in Dossier Pipeline

- Natural-language voting questions (e.g. "How did Senator X vote on Bill Y?") are automatically routed to the Senate datasource.
- If a verified record is found, the response includes:
  - answer
  - senator id/name
  - bill id
  - grounding: event_id, source_file, timestamp
- If no record is found or data is unavailable, the response is:
  - {"ok": false, "message": "No verified Senate record available."}
- Non-voting questions use the normal dossier pipeline.
- Fail-closed behavior is guaranteed for all voting queries.

## Grounded Response Example

A successful query returns:

```
{
  "ok": true,
  "vote": "YEA",
  "senator": {"id": "S1", "name": "Jane Doe"},
  "bill_id": "B1",
  "grounding": {
    "event_id": "E1",
    "source_file": "events/vote1.json",
    "timestamp": "2025-01-01T12:00:00Z"
  }
}
```

If no record is found or the data is unavailable, you get:

```
{"ok": false, "message": "No verified Senate record available."}
```

## Fail-Closed Guarantee

- If `SENATE_DATA_DIR` is missing, or required folders/files are missing or invalid, all queries fail closed (no guesses, no partial results).
- The dossier layer will respond: “No verified Senate record available.”
