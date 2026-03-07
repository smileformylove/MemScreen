# API HTTP

Base URL:
- `http://127.0.0.1:8765`

Health:
- `GET /health`

System:
- `GET /config`

## Chat

- `POST /chat`
- `POST /chat/stream` (SSE)
- `GET /chat/models`
- `GET /chat/model`
- `PUT /chat/model`
- `GET /chat/threads`
- `POST /chat/threads`
- `PUT /chat/threads/active`
- `GET /chat/history`

## Models

- `GET /models/catalog`
- `POST /models/download`

## Recording

- `POST /recording/start`
- `POST /recording/stop`
- `GET /recording/status`
- `GET /recording/audio/diagnose`
- `GET /recording/screens`

Notes:
- region and window selection are currently handled by frontend/macOS integration, not dedicated HTTP endpoints

## Videos

- `GET /video/list`
- `POST /video/reanalyze`
- `POST /video/playable`

## Process / Input tracking

- `GET /process/sessions`
- `POST /process/sessions`
- `GET /process/sessions/{id}`
- `GET /process/sessions/{id}/analysis`
- `DELETE /process/sessions/{id}`
- `DELETE /process/sessions`
- `POST /process/tracking/start`
- `POST /process/tracking/stop`
- `GET /process/tracking/status`
- `POST /process/tracking/mark-start`
- `POST /process/sessions/from-tracking`

Notes:
- API models are loaded from local configuration.
- Model capability is optional; non-model recording flows can still run.
- `docs/API_HTTP.md` is intended to match the live FastAPI surface in `memscreen/api/app.py`.
