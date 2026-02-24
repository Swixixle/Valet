# Senate DataSource Adapter (Valet)

This module provides a fail-closed, filesystem-based adapter for reading verified Senate artifacts from disk and exposing them to Valet dossiers.

## Usage
- Reads `SENATE_DATA_DIR` from the environment (must point to the Senate `data/` directory).
- Validates the existence of `events/` and `senators/` subdirectories.
- Optionally validates `manifest.json` if present.
- Indexes all data in memory on first use for fast queries.

## API
- `getSenatorById(id)`
- `searchSenators(query)`
- `getVotesBySenator(senator_id, opts)`
- `getVoteByBillAndSenator(bill_id, senator_id)`

## Fail-closed
If any required data is missing or invalid, all queries fail closed (no guesses, no partial results).

## Directory Structure
```
SENATE_DATA_DIR/
  events/
    <event>.json
  senators/
    <senator>.json
  manifest.json (optional)
```
