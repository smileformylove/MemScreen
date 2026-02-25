# Testing Guide

## Smoke test (recommended)

1. Start app stack:

```bash
./scripts/launch.sh
```

2. Verify backend health:

```bash
curl http://127.0.0.1:8765/health
```

3. Validate recording flow:
- start a short screen recording
- stop recording
- confirm new video appears in `Videos`

4. Validate audio toggles:
- enable/disable `System audio` and `Microphone` in Settings
- record short clips and verify playback

5. Validate input tracking:
- enable `Key-Mouse tracking`
- produce a short input session
- verify Process page metrics update

## Backend-only checks

```bash
./scripts/launch.sh --mode api
curl http://127.0.0.1:8765/recording/status
curl http://127.0.0.1:8765/video/list
```

## Packaging checks

```bash
./scripts/release/build_all_release_artifacts.sh
```

Verify artifacts exist in:
- `dist/release/frontend/macos/`
- `dist/release/backend/`
