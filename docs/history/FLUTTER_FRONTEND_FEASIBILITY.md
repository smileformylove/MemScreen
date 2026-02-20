# Flutter  Todolist

**** Flutter ** Kivy UI ** KivyFlutter 

**** Kivy  API  Flutter  `start.py` → Kivy 

---

## 

|  |  |  |
|------|------|------|
| **§  API ** | ✅  | `memscreen/api/` FastAPI + depsconfig  api.*`docs/API_HTTP.md`  |
| **§ API ** | ✅  | Chat / Process / Recording / Video / config / health 2.13 2.15  |
| **§  Kivy** | ✅  |  `kivy_app.py` `setup/start.py`  |
| **§ Flutter ** | ✅  | `frontend/flutter/` API  |
| **§ Flutter ** | ✅  | Chat / Process / Recording / Video /   API |
| **§ ** | ✅  | README “”docs/FLUTTER.md  CI  |
| **§ ** | ⏳  | Kivy  API API  |

****2.13/2.154.9/4.126.3§ProcessUI 4.9

---

##  Review

### 

---

### 1. 

|  |  |  |
|------|------|------|
| **API ** | ✅  |  CorePresenter/Service CRUD Kivy/ Kivy  Flutter  Core |
| **Core ** | ✅  | Kivy  API  Memory/Presenter 1.2  factory  start API  Presenter Kivy  |
| **** | ✅  |  `kivy_app.py` `start.py` API  |

---

### 2.  Core 

- **Chat**`ChatPresenter.send_message_sync(on_done=...)`  + API  `on_done`  HTTP  View `on_response_chunk`  SSE/WebSocket `CORE_API.md` 
- **Process**`get_session_analysis(session_id, event_count, keystrokes, clicks, start_time, end_time)`  `session_id`  **API  `GET /process/sessions/{id}/analysis`** `session_id`  `sessions`  `event_count/keystrokes/clicks/start_time/end_time`  `get_session_analysis`
- **Recording**`start_recording(duration, interval)` `mode/region/screen_index`  **`set_recording_mode(mode, bbox=..., screen_index=...)`**  API  `POST /recording/start`  `duration/interval`  `mode``region``screen_index`** `set_recording_mode`  `start_recording`** Presenter 
- **Video**`VideoPresenter.get_video_list()`  `List[VideoInfo]``VideoInfo.to_dict()` API  `filename` ** Flutter ** path **Flutter ** `GET /video/file?path=...`  id todolist 2.15 / GET /video/file  /video/stream
- **Presenter  View**API  Presenter  `view=None``RecordingPresenter`  `start_recording`  `if self.view: self.view.on_recording_started()` view  no-op Presenter  `show_error`  API  HTTP 4xx/5xx 

---

### 3. 

- ******Kivy  API ** Kivy  `start.py` Flutter  API  + Flutter  DB/Chroma
- ** 7.2**Kivy  API Memory/PresenterFlutter  API  Kivy  DB/ Kivy  FastAPI /Presenter  Kivy 
- ****Chat /Recording  API / session  user 

---

### 4. 

- API  Kivy ****`get_config()` `config_path`  env `db_path``videos_dir``ollama_base_url`  Flutter  Kivy 1.2  Kivy  Core  `~/.memscreen`

---

### 5. 

- **Process 4.9** Kivy  InputTracker /Flutter  (a) Flutter  POST  `POST /process/sessions` (b)  API  API `API_HTTP.md`  **events  JSON ** `CORE_API.md`  `type/text/time` 
- **Video ** Flutter todolist **GET /video/file  /video/stream path  id ** Flutter  URL 
- ****`GET /health` Ollama DB  Flutter /

---

### 6. 

|  |  |
|------|------|
|  | API Kivy Core  |
|  Core  |  Process  id Recording  set_recording_mode  start |
|  |  Kivy/API  API  |
|  |  API  Kivy  |
|  | Process events  JSON Video /health  |

 todolist 

---

##  API  UI 

- [x] **1.1**  `memscreen/api/`  `memscreen/server/` `memscreen/ui/`  `ui/kivy_app.py`
- [x] **1.2**  FastAPI  API  `memscreen/api/app.py` `get_config()`  Presenter/Service ** Kivy  Core **`memscreen/api/deps.py`  create_memory/create_*_presenter API 
- [x] **1.3**  `python -m memscreen.api`  `setup/start_api.py` API ****  `setup/start.py`  Kivy
- [x] **1.4**  `config` `api.enabled``api.host``api.port` API `MEMSCREEN_API_PORT` / `MEMSCREEN_API_HOST` / `MEMSCREEN_API_ENABLED`
- [x] **1.5**  `docs/API_HTTP.md`/ JSON `CORE_API.md`  Process  events JSON 

---

## API  Core 

### Chat

- [x] **2.1** `POST /chat` —  `{ "message": "..." }` `{ "reply": "...", "error": null }`  `ChatPresenter.send_message_sync`
- [x] **2.2** `POST /chat/stream` — SSE `ChatPresenter`  `on_response_chunk` / `on_response_completed` 
- [x] **2.3** `GET /chat/models` — `GET /chat/model` — `PUT /chat/model` —  `get_available_models` / `get_current_model` / `set_model`
- [x] **2.4** `GET /chat/history` —  `get_conversation_history` JSON 

### Process

- [x] **2.5** `GET /process/sessions` —  `load_sessions` query `limit` 20
- [x] **2.6** `POST /process/sessions` —  `events``start_time``end_time` `save_session`
- [x] **2.7** `GET /process/sessions/{id}` —  events `get_session_events`
- [x] **2.8** `GET /process/sessions/{id}/analysis` —  `session_id`  `get_session_analysis`
- [x] **2.9** `DELETE /process/sessions/{id}` — `DELETE /process/sessions` — 

### Recording

- [x] **2.10** `POST /recording/start` —  `duration``interval``mode``region``screen_index` `set_recording_mode`  `start_recording`
- [x] **2.11** `POST /recording/stop` — 
- [x] **2.12** `GET /recording/status` — 
- [ ] **2.13** WebSocket  SSE Flutter “”

### Video

- [x] **2.14** `GET /video/list` —  VideoPresenter
- [ ] **2.15** `GET /video/{id}/thumbnail`  URL Flutter  `GET /video/file` path  id 

### 

- [x] **2.16** `GET /config` — ollama_base_urldb_dirvideos_dir Flutter 
- [x] **2.17** `GET /health` — Ollama DB  Flutter “”

---

## Flutter 

- [x] **3.1**  Flutter  `flutter_app/`  `frontend/flutter/` `memscreen/``setup/` 
- [x] **3.2**  Flutter  API base URL `http://127.0.0.1:8765` `docs/API_HTTP.md` ** API**  Conda  `MemScreen``conda activate MemScreen`  `python -m memscreen.api`  `python setup/start_api.py`
- [x] **3.3**  API Dart HTTP  SSE/WebSocket 
- [x] **3.4**  URL

---

## Flutter  Core 

### Chat

- [x] **4.1** /AI 
- [x] **4.2**  `POST /chat`  `POST /chat/stream`
- [x] **4.3** / `GET /chat/models``PUT /chat/model`
- [x] **4.4** `GET /chat/history`

### Process

- [x] **4.5**  `GET /process/sessions` start/endevent_countkeystrokesclicks
- [x] **4.6**  start_timeend_timetype: keypress/click/infotexttime `POST /process/sessions`4.9 
- [x] **4.7**  `GET /process/sessions/{id}/analysis` categoriespatterns  Kivy 
- [x] **4.8** `DELETE`
- [ ] **4.9** “”//InputTracker  Flutter  API  events  `CORE_API.md` 

### Recording

- [x] **4.10** //
- [x] **4.11**  `POST /recording/start``POST /recording/stop` `GET /recording/status`  UI /
- [ ] **4.12**  WebSocket/SSE “”

### Video

- [x] **4.13**  `GET /video/list`
- [x] **4.14**  path  URL  Flutter  VideoPresenter 

### 

- [x] **4.15** `GET /config`API base URL 
- [x] **4.16**  About 

---

##  Kivy UI

- [x] **5.1**  `memscreen/ui/kivy_app.py`  Screen  Presenter  Kivy 
- [x] **5.2**  `setup/start.py`  `MemScreenApp().run()`
- [x] **5.3** Core MemoryPresenterconfig Kivy API  `deps.py`  Kivy 
- [x] **5.4** READMEAPI_HTTP todolist KivyFlutter  API `conda activate MemScreen`  `python -m memscreen.api` Flutter 

---

## 

- [x] **6.1**  `README.md`  `docs/` “”Kivy Flutter API + Flutter
- [x] **6.2**  Flutter /`flutter run`/
- [ ] **6.3**  CI  API  API  Core 

---

## 

- [ ] **7.1** “” API  Flutter  API Flutter
- [ ] **7.2**  Kivy  API “ API ” Kivy  API Flutter 
- [ ] **7.3** / Flutter “” API todolist 

---

##  Review

###  vs 

|  |  |
|------|----------|
| ** Flutter** | ✅ Chat / Process / Recording / Video /   API§ Flutter § `CORE_API.md`  Presenter/Service  |
| ** Kivy UI ** | ✅ §  `kivy_app.py` `start.py` §  API  |

### 

1. **** §API API_HTTP.md  §  Chat → Process → Recording → Video → config/health  
2. **Flutter**§  § Chat → Process → Recording → Video → /   
3. ****§§  Kivy

### 

- **** Kivy  `DELETE /video` `DELETE /video/{id}` Flutter Core  `VideoPresenter.delete_video(filename)`
- **1.2  Kivy **“ Kivy  Core ” `kivy_app.build()`  Memory/Presenter  `memscreen.core_bootstrap.create_core()` Kivy  API  Kivy 

### 

**Todolist **  Core 

---

**** API  Flutter  Kivy UI 
