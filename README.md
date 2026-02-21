# Valet Studio (v0)

Deterministic text → audit.yaml + receipt.png/json + TikTok-ready 9:16 video.mp4.

## Install
```shell
pip install -e ".[dev]"
```

## Run API
```shell
uvicorn app.api.server:app --reload
```

## Run CLI
```shell
python tools/run_pipeline.py --mode scalpel --file fixtures/stories/01-designed.txt
```

## Voice Governance (voice-library)

Valet supports a **voice governance layer** that injects character-level conditioning text (bible, anchors, calibration, drift) into every pipeline run for audit traceability.

### Setup

Clone [voice-library](https://github.com/Swixixle/voice-library) adjacent to this repo:

```shell
git clone https://github.com/Swixixle/voice-library ../voice-library
```

Or point to an existing checkout via the environment variable:

```shell
export VOICE_LIBRARY_PATH=/path/to/voice-library
```

### Usage

Pass `--target` (CLI) or `target` (API) to select a character:

```shell
python tools/run_pipeline.py --mode scalpel --target valet --file fixtures/stories/01-designed.txt
python tools/run_pipeline.py --mode scalpel --target perimeter_walker --file fixtures/stories/01-designed.txt
```

If `--target` is omitted, the character defaults to `"valet"`.

### Output

Each run writes `dist/<slug>/voice_governance.txt` containing the assembled governance payload, and records provenance in `audit.yaml` under the `voice` key:

```yaml
voice:
  character: valet
  source: voice-library
  payload_file: voice_governance.txt
```

If the voice-library path is not found, the pipeline continues without governance (no `voice_governance.txt` is written).