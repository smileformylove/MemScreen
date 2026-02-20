# MemScreen HTTP API 

 Flutter  REST/SSE  `CORE_API.md` 

** API** Conda  `MemScreen` `conda activate MemScreen`  `python -m memscreen.api`  `python setup/start_api.py`

**Base URL** `http://127.0.0.1:8765` `api.host` / `api.port`  `MEMSCREEN_API_HOST` / `MEMSCREEN_API_PORT` 

---

## Chat

### POST /chat



- **Request**`application/json`  
  `{ "message": "" }`
- **Response**`200`  
  `{ "reply": "AI ", "error": null }`  `{ "reply": null, "error": "" }`

### POST /chat/stream

 **Server-Sent Events (SSE)** 

- **Request** `POST /chat`
- **Response**`200``Content-Type: text/event-stream`  
  `data:`  JSON
  - `{ "chunk": "" }` — 
  - `{ "error": "" }` — 
  - `{ "done": true, "full": "" }` — 

### GET /chat/models

- **Response**`{ "models": ["model1", "model2", ...] }`

### GET /chat/model

- **Response**`{ "model": "" }`

### PUT /chat/model

- **Request**`{ "model": "" }`
- **Response**`200`  `{ "model": "" }` `400`

### GET /chat/history

- **Response**`{ "messages": [ { "role": "user"|"assistant", "content": "..." }, ... ] }`

---

## Process

 DB  Core  `session_analysis`  `~/.memscreen/db/process_mining.db`

### GET /process/sessions

- **Query**`limit` 201–100
- **Response**  
  `{ "sessions": [ { "id", "start_time", "end_time", "event_count", "keystrokes", "clicks" }, ... ] }`

### POST /process/sessions



- **Request**`{ "events": [ ... ], "start_time": "HH:MM:SS  ISO", "end_time": "..." }`
- **events ** `CORE_API.md`  `type` `"keypress"``"click"``"info"``text``time`****

### GET /process/sessions/{id}

- **Response**`{ "events": [ ... ] }` `404`

### GET /process/sessions/{id}/analysis

- **Response**`{ "categories": { ... }, "patterns": { ... }, "event_count", "keystrokes", "clicks", "start_time", "end_time" }` `404`

### DELETE /process/sessions/{id}

- **Response**`{ "deleted": 1 }`

### DELETE /process/sessions

- **Response**`{ "deleted": N }`

### / Kivy

** API **/

- **POST /process/tracking/start** — /
- **Response**`{ "ok": true, "is_tracking": true }` 400/403
- **POST /process/tracking/stop** — 
- **Response**`{ "ok": true, "is_tracking": false }`
- **GET /process/tracking/status** — 
- **Response**`{ "is_tracking", "event_count", ... }`
- **POST /process/sessions/from-tracking** —  Kivy
- **Response**`{ "ok": true, "events_saved", "start_time", "end_time" }` 400

---

## Recording

### POST /recording/start

- **Request**`application/json`  
  `duration` 60`interval` 2.0`mode``fullscreen` | `fullscreen-single` | `region``region``[left, top, right, bottom]``screen_index`  
   `mode``region`  `mode=region``screen_index`  `mode=fullscreen-single`
- **Response**`200`  `{ "ok": true }` `500`

### POST /recording/stop

- **Response**`{ "ok": true }`

### GET /recording/status

- **Response**`{ "is_recording", "duration", "interval", "output_dir", "frame_count", "elapsed_time", "mode", "region", "screen_index" }`  
  `mode` fullscreen / fullscreen-single / region`region`  `[left, top, right, bottom]`  null`screen_index`  null

### GET /recording/screens

- **Response**`{ "screens": [ { "index", "name", "width", "height", "is_primary" }, ... ] }`  
  

---

## Video

### GET /video/list

- **Response**`{ "videos": [ { "filename", "timestamp", "frame_count", "fps", "duration", "file_size" }, ... ] }`  
  `filename`  Flutter  path / `GET /video/file`

---

## 

### GET /config



- **Response**`{ "ollama_base_url", "db_dir", "videos_dir" }`

### GET /health

- **Response**`{ "status": "ok", "ollama": "ok"|"error: ...", "db": "ok"|"error: ..." }`

---

## 

- `400` — mode/region 
- `404` —  session id
- `500` — 
- `503` —  Chat/Recording/Video 

 FastAPI `detail` 
