# Valet Studio

> Deterministic text → structured audit + TikTok-ready video.  
> Input a story. Get back `audit.yaml`, `receipt.png`, `receipt.json`, and a 9:16 `video.mp4`.

---

## What It Does

Valet Studio is a deterministic content pipeline. You feed it a text file — a financial story, a script, a structured narrative — and it outputs:

- **`audit.yaml`** — structured semantic audit of the input
- **`receipt.png` / `receipt.json`** — a visual and machine-readable receipt of the transformation
- **`video.mp4`** — a vertical 9:16 video formatted for TikTok and short-form platforms
- **`integrity_ledger.json`** — integrity scores and risk-level assessment

The pipeline runs in two modes: `scalpel` (surgical, high-fidelity) and `scalpel-ledger` (adds a But-If damage estimate). Additional modes are configurable via the CLI.

Voice and tone are governed externally by the <a href="https://github.com/Swixixle/voice-library">`voice-library`</a> repo. If there is ever a conflict between application output and the voice-library, **the voice-library wins.**

---

## Project Structure

```
Valet/
  app/
    api/             ← FastAPI server (uvicorn entry point)
  fixtures/
    stories/         ← sample input .txt files for testing
  tests/             ← test suite
  tools/
    run_pipeline.py  ← CLI entry point
  .github/workflows/ ← CI/CD
  pyproject.toml     ← dependencies and project metadata
```

## Copilot Policy

Repository-level Copilot behavior and safety requirements are defined in [.github/copilot-instructions.md](.github/copilot-instructions.md).
Security-critical areas include `app/escrow/` (signing, hashing, chain-linking); treat related changes as forensic-integrity sensitive.

---

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/Swixixle/Valet.git
cd Valet
pip install -e ".[dev]"
```

---

## Usage

### Run the API server

```bash
uvicorn app.api.server:app --reload
```

The API will be available at `http://localhost:8000`.

### Run the CLI pipeline

```bash
python tools/run_pipeline.py --mode scalpel --file fixtures/stories/01-designed.txt
```

### Generate a signed audit from a prompt

```bash
RECEIPT_SIGNING_KEY="your-signing-key" \
python -m tools.generate_signed_audit \
  --prompt "Explain why a signed receipt is better than a standard log."
```

This command writes the same artifacts to `dist/<slug>/` and prints `signature_valid: true` when the generated `receipt.json` verifies.

**Options:**

| Flag | Short | Description |
|------|-------|-------------|
| `--mode` | `-m` | Pipeline mode (`scalpel` default; `scalpel-ledger` adds But-If damage estimate) |
| `--file` | `-f` | Path to input `.txt` story file (mutually exclusive with `--text`) |
| `--text` | `-t` | Inline story text string (mutually exclusive with `--file`) |
| `--target` | | Character target for voice governance (default: `valet`) |

### API

Start the server with `uvicorn app.api.server:app --reload`, then `POST /pipeline`:

```json
{ "mode": "scalpel", "story_text": "Your story here...", "target": "valet" }
```

Or ingest from a video URL:

```json
{ "mode": "scalpel", "url": "https://youtube.com/watch?v=...", "target": "valet" }
```

`story_text` and `url` are mutually exclusive — provide one. `target` is optional.

### Output

Running the pipeline writes all files to `dist/<slug>/` and produces:

| File | Description |
|------|-------------|
| `audit.yaml` | Structured semantic audit |
| `receipt.png` | Visual receipt image |
| `receipt.json` | Machine-readable receipt |
| `video.mp4` | 9:16 vertical video |
| `integrity_ledger.json` | Full integrity ledger with risk scores |

`voice_governance.txt` is written when the voice-library is wired. `but_if_video.mp4` is written in `scalpel-ledger` mode only. See the [Operator Runbook](#operator-runbook) for the full output contract.

---

## Operator Runbook

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | LLM backend to use: `openai` or `anthropic` |
| `OPENAI_API_KEY` | If `LLM_PROVIDER=openai` | OpenAI API key |
| `ANTHROPIC_API_KEY` | If `LLM_PROVIDER=anthropic` | Anthropic API key |
| `RECEIPT_SIGNING_KEY` | Yes | HMAC key used to sign `receipt.json` payloads |
| `WHISPER_MODEL` | No | Whisper model size for video transcription (default: `base`) |

### Output Contract

All pipeline artifacts are written to `dist/<slug>/`:

```
dist/<slug>/
  audit.yaml              ← structured semantic audit
  receipt.json            ← machine-readable receipt
  receipt.png             ← visual receipt image
  video.mp4               ← 9:16 vertical video
  integrity_ledger.json   ← integrity scores and risk level
  voice_governance.txt    ← voice payload (if voice-library is wired)
  but_if_video.mp4        ← alternate video (scalpel-ledger mode only)
```

`receipt.json` includes a `signature` block (`algorithm`, `payload_hash`, `value`) that verifies receipt integrity.

### Schema Compatibility Notes

To support mixed consumers during migration, output payloads include both newer and legacy field names:

- `audit.epistemic.transparency_tier` (current) and `audit.epistemic.transparency_level` (legacy)
- `audit.internal_audit.*_status` fields (current) and boolean summary fields (`passed`, `cluster_balance_ok`, `data_completeness_ok`, `language_bias_ok`, `flagged_for_review`, `violations`) for legacy readers

When building new integrations, prefer the current status-based fields and treat legacy fields as backward-compatibility aliases.

---

## Development

Run tests:

```bash
pytest tests/
```

Add a new fixture story to `fixtures/stories/` and run the pipeline against it to validate changes.

---

## Voice & Tone

All character voice, tone, and personality governance lives in the <a href="https://github.com/Swixixle/voice-library">`voice-library`</a> repo. That repo is the authoritative source — application output always defers to it.

Valet currently uses two characters:

- **The Valet** — trickster-sage in scrubs. Calm, precise, faintly disappointed.
- **The Perimeter Walker** — sensory metaphors, morally intact, controlled danger.

---

## Roadmap

- [ ] Phase 1: LLM integration with voice-library conditioning
- [ ] Additional pipeline modes beyond `scalpel`
- [ ] Extended output formats

---

## License

Private. All rights reserved.