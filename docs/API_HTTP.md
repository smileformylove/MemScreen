# MemScreen HTTP API 约定

供 Flutter 等前端调用的 REST/SSE 接口说明。与 `CORE_API.md` 语义对齐。

**启动 API**（在项目 Conda 环境 `MemScreen` 下）：`conda activate MemScreen` 后执行 `python -m memscreen.api` 或 `python setup/start_api.py`。

**Base URL**：默认 `http://127.0.0.1:8765`（可由配置 `api.host` / `api.port` 或环境变量 `MEMSCREEN_API_HOST` / `MEMSCREEN_API_PORT` 修改）。

---

## 一、Chat

### POST /chat

非流式发送一条消息，返回完整回复。

- **Request**：`application/json`  
  `{ "message": "用户输入文本" }`
- **Response**：`200`  
  `{ "reply": "AI 回复正文", "error": null }` 或 `{ "reply": null, "error": "错误信息" }`

### POST /chat/stream

流式发送，通过 **Server-Sent Events (SSE)** 推送片段。

- **Request**：同 `POST /chat`
- **Response**：`200`，`Content-Type: text/event-stream`  
  每行一条事件，`data:` 后为 JSON：
  - `{ "chunk": "一段文本" }` — 流式片段
  - `{ "error": "错误信息" }` — 出错
  - `{ "done": true, "full": "完整回复" }` — 结束

### GET /chat/models

- **Response**：`{ "models": ["model1", "model2", ...] }`

### GET /chat/model

- **Response**：`{ "model": "当前模型名" }`

### PUT /chat/model

- **Request**：`{ "model": "模型名" }`
- **Response**：`200` 时 `{ "model": "当前模型名" }`；模型不可用时 `400`

### GET /chat/history

- **Response**：`{ "messages": [ { "role": "user"|"assistant", "content": "..." }, ... ] }`

---

## 二、Process（流程分析）

会话与分析的 DB 与 Core 的 `session_analysis` 一致（默认 `~/.memscreen/db/process_mining.db`）。

### GET /process/sessions

- **Query**：`limit`（可选，默认 20，1–100）
- **Response**：  
  `{ "sessions": [ { "id", "start_time", "end_time", "event_count", "keystrokes", "clicks" }, ... ] }`

### POST /process/sessions

保存一条会话。

- **Request**：`{ "events": [ ... ], "start_time": "HH:MM:SS 或 ISO", "end_time": "..." }`
- **events 单条约定**（与 `CORE_API.md` 一致）：建议包含 `type`（如 `"keypress"`、`"click"`、`"info"`）、`text`、`time`。事件由**客户端或独立采集服务**提供，后端仅存储与分析。

### GET /process/sessions/{id}

- **Response**：`{ "events": [ ... ] }`；不存在则 `404`

### GET /process/sessions/{id}/analysis

- **Response**：`{ "categories": { ... }, "patterns": { ... }, "event_count", "keystrokes", "clicks", "start_time", "end_time" }`；不存在则 `404`

### DELETE /process/sessions/{id}

- **Response**：`{ "deleted": 1 }`

### DELETE /process/sessions

- **Response**：`{ "deleted": N }`

### 键盘/鼠标采集（与 Kivy「开始采集」一致）

采集在**运行 API 的后端机器**上进行（需辅助功能/无障碍权限）。

- **POST /process/tracking/start** — 开始采集键盘/鼠标事件。
- **Response**：`{ "ok": true, "is_tracking": true }`；已开启或失败时 400/403。
- **POST /process/tracking/stop** — 停止采集。
- **Response**：`{ "ok": true, "is_tracking": false }`
- **GET /process/tracking/status** — 当前是否在采集及事件数。
- **Response**：`{ "is_tracking", "event_count", ... }`
- **POST /process/sessions/from-tracking** — 将当前采集到的事件保存为一条会话（等价 Kivy「保存当前会话」）。
- **Response**：`{ "ok": true, "events_saved", "start_time", "end_time" }`；无事件或事件过少时 400。

---

## 三、Recording（录制）

### POST /recording/start

- **Request**：`application/json`，可选字段：  
  `duration`（默认 60）、`interval`（默认 2.0）、`mode`（`fullscreen` | `fullscreen-single` | `region`）、`region`（`[left, top, right, bottom]`）、`screen_index`（整数）。  
  若传 `mode`，先设置再启动；`region` 用于 `mode=region`，`screen_index` 用于 `mode=fullscreen-single`。
- **Response**：`200` 时 `{ "ok": true }`；失败 `500`

### POST /recording/stop

- **Response**：`{ "ok": true }`

### GET /recording/status

- **Response**：`{ "is_recording", "duration", "interval", "output_dir", "frame_count", "elapsed_time", "mode", "region", "screen_index" }`  
  `mode` 为当前录制模式（fullscreen / fullscreen-single / region）；`region` 为 `[left, top, right, bottom]` 或 null；`screen_index` 为单屏时的屏幕索引或 null。

### GET /recording/screens

- **Response**：`{ "screens": [ { "index", "name", "width", "height", "is_primary" }, ... ] }`  
  用于「单屏」模式下选择要录制的屏幕。

---

## 四、Video（视频列表）

### GET /video/list

- **Response**：`{ "videos": [ { "filename", "timestamp", "frame_count", "fps", "duration", "file_size" }, ... ] }`  
  `filename` 为本地绝对路径；同机 Flutter 可直接用 path 播放，跨机/移动端需另行提供文件流接口（如 `GET /video/file`）。

---

## 五、配置与健康

### GET /config

只读配置，供前端展示或连接提示。

- **Response**：`{ "ollama_base_url", "db_dir", "videos_dir" }`（仅必要字段）

### GET /health

- **Response**：`{ "status": "ok", "ollama": "ok"|"error: ...", "db": "ok"|"error: ..." }`

---

## 六、错误码

- `400` — 参数错误（如模型不可用、mode/region 无效）
- `404` — 资源不存在（如 session id）
- `500` — 内部错误（如录制启动失败）
- `503` — 服务不可用（如 Chat/Recording/Video 未初始化）

错误响应体为 FastAPI 默认格式（`detail` 等）。
