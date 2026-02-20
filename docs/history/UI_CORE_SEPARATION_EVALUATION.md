# UI + Python Core 

## 

### 1.1 

```
memscreen/
├── ui/                    #  UI Kivy
│   └── kivy_app.py        # ~2900  UI
├── presenters/            # MVP  P  UI 
│   ├── base_presenter.py
│   ├── recording_presenter.py   ✅  RecordingScreen 
│   ├── video_presenter.py       ✅  VideoScreen 
│   ├── chat_presenter.py        ❌  Kivy 
│   └── process_mining_presenter.py  ❌  Kivy 
├── memory/                # Core
├── llm/                   # Core
├── embeddings/            # /Core
├── vector_store/          # Core
├── storage/               # Core
├── config/                # Core
├── agent/                 # Core
├── process_mining.py      # Core UI  Process 
└── ...
```

### 1.2 

|  | UI  |  UI  |
|------|------------------|----------------------|
| **RecordingScreen** |  `RecordingPresenter`  |  Presenter |
| **VideoScreen** |  `VideoPresenter`  |  Presenter |
| **ChatScreen** |  `Memory` +  LLM// | ****~200  `kivy_app.py` |
| **ProcessScreen** |  `sqlite3` + //CRUD | ****~400+  `kivy_app.py` |
| **AboutScreen** |  |  |

****UI  +  PresenterUI  `ChatPresenter` / `ProcessMiningPresenter`

---

## UI + Python Core 

### 2.1 

- **UI **
  - 
  - Core / Presenter
  -  Core /
- **Python Core**
  - LLM
  -  ****  UI Presenter  Service API
  -  CLI UI Web

### 2.2 

-  UI Kivy  Qt/WebCore 
- Core / Kivy
-  UI  UI 

---

## 

### 3.1 

|  |  |
|------|------|
| **** |  CoreUI  |
| **** | Core  GUI  mock  |
| **** |  Core  KivyCLI Web/ |
| ** MVP ** |  Recording/Video  Presenter  Chat/Process |
| **** |  Electron/Web  UI Core  |

### 3.2 

|  |  |  |
|------|------|------|
| **ChatScreen  ChatPresenter** | LLM  `kivy_app.py`  |  `ChatPresenter` Core  ChatServiceUI / |
| **ProcessScreen  Core ** | ProcessScreen  `process_mining.db`  `sessions`  `_classify_activity` / `_analyze_patterns`Core  `ProcessMiningAnalyzer`  DB`keyboard_mouse_logs` |  UI ++ Core/ ProcessMining  ProcessMiningPresenter  UI  Presenter |
| **** | UI  Core  API/ |  Presenter View  PresenterPresenter  View  `update_*` / `show_error` / `on_chunk``on_done` |
| **Kivy ** | Core  Kivy  UI | Core  thread  `Clock.schedule_once`  Presenter  |
| **** |  ChatScreen  ProcessScreen/ process_mining |  Chat Process DB/ |

### 3.3 

- **** Core  API  Kivy  UI  CorePresenter  Service  `send_message(query, on_response)` Kivy 
- **Process ** UI  DB  Core  `ProcessMiningAnalyzer`  Core UI  Core
- **** UI/UI  Presenter/Core Presenter  RPC

---

## 

###  1Chat 

1. ** Core ** `ChatPresenter`
   - LLM 
   -  /  / 
2. ** Kivy **
   - `ChatScreen` loading/
   -  Core/Presenter  `Clock.schedule_once`  UI typing
3. ****Chat  `kivy_app.py`  `ChatPresenter` Core  chat UI 

###  2Process  Core

1. ****
   -  UI  `process_mining.db` + `sessions` `ProcessMiningAnalyzer`  schema
   -  `_classify_activity``_analyze_patterns`  CRUD  Core `process_mining`  `ProcessMiningPresenter`
2. **UI **
   - ProcessScreen / Core //
3. ****`kivy_app.py`  `sqlite3``_classify_activity``_analyze_patterns` Process  DB  Core

###  3

-  Presenter  Core  UI 
-  UI Application Service Kivy  UI  Core

---

## 

- **** Recording/Video UI + Presenter + CoreChat  Process  UI
- ****UI + Python Core  Chat Process
- ****`kivy_app.py`  ~2900  +  +  Core/Presenter

---

## .1 

**** 

- **Chat** `kivy_app.py`  messagesLLM **** Core ChatPresenter prompt  DB UI  Core typing
- **Process** `_categorize_activities``_analyze_patterns`  sqlite3 /**** Core `process_mining.db` `sessions` UI  Core  /  /  session  dict/

**** 1:1 UI  Core

---

## 

 1Chat 2Process/

---

###  1Chat  ChatPresenter

#### 1.1 Core `memscreen/presenters/chat_presenter.py`

|  |  |  |  |  |
|------|------|------|------|------|
| C1.1 | DONE | **/** | `ChatPresenter.__init__` |  `memory_system`Kivy  `MemScreenApp.memory` |
| C1.2 | DONE | **** | `send_message(user_message, use_agent=None)` ( L327) |  `_search_memory``_build_messages``_start_streaming` UI  |
| C1.3 | DONE | ** View ** | View  | Kivy  `send_message_sync` + `on_done` `_on_chat_done`  UI |
| C1.4 | DONE | **** |  `send_message_sync(user_message, on_done)` |  `on_done(ai_text, error_text)` |

#### 1.2 Kivy `memscreen/ui/kivy_app.py`

|  |  |  |  |  |
|------|------|------|----------------|------|
| K1.1 | DONE | **** | L553–L722`send_message`  `get_ai_response`  |  `presenter.send_message_sync(text, on_done=...)` |
| K1.2 | DONE | **** | L513–L551 |  texttyping `self.presenter.send_message_sync(text, on_done)` |
| K1.3 | DONE | **** | L624–L718`update_ui`  |  `_on_chat_done(typing_label, ai_text, error_text)`  `on_done`  `Clock.schedule_once`  |
| K1.4 | DONE | **** | `ChatScreen`  |  `send_message_sync` + `_on_chat_done`  UI View  |
| K1.5 | DONE | **** | `ChatScreen` / App | Presenter  App ChatScreen  Presenter |
| K1.6 | DONE | **** | `MemScreenApp.build()` |  `ChatPresenter(memory_system, ollama_base_url)``set_view`/`set_presenter``initialize()``on_stop`  `chat_presenter.cleanup()` |
| K1.7 | DONE | **** | `_fix_filesystem_encoding``_show_error_message` |  `_on_chat_done`  |

#### 1.3  1

- [x] DONE `kivy_app.py` `memory_system.search``OllamaLLM``memory_system.add` system prompt 
- [x] DONE Chat  AI 
- [ ] TODO  `on_response_chunk` 

---

###  2Process  Core

#### 2.1 Core 

|  |  |  | / |  |
|------|------|------|------------|------|
| P1.1 | DONE | **** | `memscreen/services/session_analysis.py` |  `categorize_activities(events)``analyze_patterns(events)` UI  dict |
| P1.2 | DONE | **** |  |  `save_session``load_sessions``get_session_events``get_session_analysis``delete_session``delete_all_sessions`DB  `process_mining.db` + `sessions` schema  UI  |
| P1.3 | TODO | **** | `ProcessMiningPresenter` | ProcessScreen  + + Core  InputTracker |

#### 2.2 Kivy `memscreen/ui/kivy_app.py`

|  |  |  |  |  |
|------|------|------|----------------|------|
| K2.1 | DONE | **** | `_save_session`  sqlite3 |  `core_save_session(...)` |
| K2.2 | DONE | **** | `_load_history`  sqlite3 |  `core_load_sessions(limit=20)` `_create_session_item`  |
| K2.3 | DONE | **** | `_show_session_analysis`  |  `core_get_session_analysis(...)` `analysis_text` |
| K2.4 | DONE | **** | `_categorize_activities` |  Core`session_analysis.categorize_activities` |
| K2.5 | DONE | **** | `_analyze_patterns` |  Core`session_analysis.analyze_patterns` |
| K2.6 | DONE | **** | `_create_session_item` / |  `_show_session_analysis` Core |
| K2.7 | DONE | **** | `start`/`stop`/`_add_session_event` |  + / Core |
| K2.8 | DONE | **** | `_delete_session`/`_delete_all_sessions` |  `core_delete_session`/`core_delete_all_sessions` `_load_history()` |

#### 2.3  2

- [x] DONE `kivy_app.py`  `sqlite3``_categorize_activities``_analyze_patterns`
- [x] DONE // 1:1 
- [x] DONE  `process_mining.db`

---

###  3

|  |  |  |  |
|------|------|------|------|
| D1 | DONE | **** | `docs/CORE_API.md`  ChatPresenter  `send_message`/`send_message_sync`  View Process  CRUD +  |
| D2 | TODO | **** |  UI  `memscreen/`  `get_chat_service()``get_process_service()` Presenter  Service  |

---

### 

|  |  |  |
|------|------|----------|
| ** 1 Chat** | DONE | Core `ChatPresenter.send_message_sync` Kivy  1:1Kivy `presenter.send_message_sync` + `_on_chat_done`App  ChatPresenter |
| ** 2 Process** | DONE | Core `memscreen/services/session_analysis.py` CRUD + `categorize_activities`/`analyze_patterns`Kivy sqlite  Core  |
| ** 3 ** | D1 DONE / D2 TODO | D1  `docs/CORE_API.md`D2  UI  |
