# API HTTP

Base URL:
- `http://127.0.0.1:8765`

Health:
- `GET /health`

## Chat

- `POST /chat`
- `POST /chat/stream` (SSE)
- `GET /chat/models`
- `GET /chat/model`
- `PUT /chat/model`
- `GET /chat/history`

## Recording

- `POST /recording/start`
- `POST /recording/stop`
- `GET /recording/status`
- `GET /recording/screens`
- `GET /recording/windows`
- `POST /recording/select-region`
- `POST /recording/select-window`
- `POST /recording/audio/diagnose`

## Videos

- `GET /video/list`
- `GET /video/{filename}`
- `DELETE /video/{filename}`
- `POST /video/reanalyze`

## Process / Input tracking

- `GET /process/sessions`
- `POST /process/sessions`
- `GET /process/sessions/{id}`
- `GET /process/sessions/{id}/analysis`
- `POST /process/tracking/start`
- `POST /process/tracking/stop`
- `GET /process/tracking/status`
- `POST /process/sessions/from-tracking`

Notes:
- API models are loaded from local configuration.
- Model capability is optional; non-model recording flows can still run.
