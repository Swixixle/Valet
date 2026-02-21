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