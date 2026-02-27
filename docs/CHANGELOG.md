# Changelog

## v0.6.6

- fixed packaged no-model bootstrap reliability on GitHub macOS runner:
  - removed hard `pyaudio` pin from `requirements.lite.txt`
  - keep `pyaudio` as best-effort optional install in backend bootstrap
- unified project version to `0.6.6`

## v0.6.5

- aligned release smoke test with runtime policy:
  - `httpx` and `imageio-ffmpeg` remain required
  - `pyaudio` is treated as optional (warn-only) for environments without wheel/toolchain support
- unified project version to `0.6.5`

## v0.6.4

- unified visual-memory enrichment path for both:
  - async analysis after recording
  - manual reanalyze from Videos
- upgraded content tagging and keyword extraction for precision retrieval
- improved chat/video ranking with query-aware relevance scoring
- added graceful no-model fallback for async memory enrichment:
  - recording remains fully usable
  - enrichment state is persisted as `model_unavailable` instead of staying pending
- added minimal `analysis_status` propagation and UI badges in Videos:
  - `Analyzing`
  - `No Model`
- unified project version to `0.6.4` across Python, Flutter, and README

## v0.6.3

- unified project version to `0.6.3` across Python package, API, Flutter, and README
- refreshed README positioning and product comparison section
- added single-package macOS release packaging (no bundled models):
  - one installer package for end users
  - embedded backend bootstrap
  - on-demand model bootstrap script
- added GitHub Actions release packaging workflow
- added optional macOS signing/notarization support for frontend packaging
- fixed packaged backend import path resolution to always use bundled source
- added CI installer smoke test for no-model recording runtime availability
- cleaned legacy scripts and historical/obsolete docs

## v0.6.2

- Flutter frontend became primary runtime UI
- recording and floating workflows were further stabilized

## v0.6.0

- major runtime and UX optimization phase
