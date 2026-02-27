# Valet Studio

## Overview
Deterministic text-to-structured-audit + TikTok-ready video pipeline. Built with Python 3.11 and FastAPI.

## Architecture
- **Backend**: FastAPI + Uvicorn on port 5000
- **Entry point**: `app/api/server.py`
- **API routes**: `app/api/routes.py` (pipeline endpoint), `app/api/senate_dossier.py` (senate vote lookup)

## Project Structure
```
app/
  api/         - FastAPI server and routes
  audit/       - Audit rules and runner
  core/        - Pipeline service, LLM client, state store
  datasources/ - Senate data sources
  doctrine/    - Doctrine contract and guard
  entity_resolver/ - Entity matching and normalization
  epistemic/   - Epistemic enforcer
  escrow/      - Signing, hashing, IPFS upload
  incentive_graph/ - Graph module
  ingest/      - Article and video extraction
  internal_audit/ - Coverage and cluster analysis
  ledger/      - Article, editorial, but-if ledger
fixtures/      - Sample story .txt files for testing
tests/         - Pytest test suite
tools/         - CLI entry points (run_pipeline.py)
```

## Running the App
```bash
uvicorn app.api.server:app --host 0.0.0.0 --port 5000 --reload
```

## Key Endpoints
- `GET /health` - Health check
- `POST /pipeline` - Main pipeline (modes: scalpel, scalpel-ledger)
- `POST /dossier/senate-vote` - Senate vote lookup

## Dependencies
Managed via pip (pyproject.toml). Key packages:
- fastapi, uvicorn, pydantic
- openai, anthropic (LLM clients)
- trafilatura (web scraping), yt-dlp (video), openai-whisper (transcription)
- pillow, moviepy, numpy (media processing)
- networkx (graph)
- gunicorn (production server)

## Deployment
- Target: autoscale
- Run: `gunicorn --bind=0.0.0.0:5000 --reuse-port --worker-class=uvicorn.workers.UvicornWorker app.api.server:app`
