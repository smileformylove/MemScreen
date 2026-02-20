# UI 

2026-02**Screen App **

---

## 

|  |  |  |
|------|------------------|------|
| ** ScreenChat / Process / Recording / Video** | LLMDB | ✅ **** |
| **MemScreenApp.build()** |  Memory get_config  MemoryConfig Presenter  | ⚠ **** |

---

## 

### 2.1 Chat

- **UIChatScreen**  
  -  typing `presenter.send_message_sync(text, on_done=...)` `_on_chat_done`  `Clock.schedule_once`  UI typing AI   
  - ****`memory_system.search``memory_system.add``OllamaLLM`system prompt 
- ****  
  -  `ChatPresenter` messagesLLM 

**Chat  UI **

### 2.2 Process

- **UIProcessScreen**  
  -  Core `core_save_session``core_load_sessions``core_get_session_analysis``core_delete_session``core_delete_all_sessions`  
  - ****`sqlite3``_categorize_activities``_analyze_patterns`  
  - `current_session_events` InputTracker  UI  `result['categories']` / `result['patterns']`  `analysis_text` ****
- ****  
  -  `memscreen.services.session_analysis`CRUD`categorize_activities``analyze_patterns`

**Process  UI  Service API  Presenter**

### 2.3 Recording / Video

-  `RecordingPresenter` / `VideoPresenter` UI 

****

### 2.4  Screen  memory_system 

- `memory_system`  `BaseScreen.__init__`  Screen **** `memory_system.search``memory_system.add` 
- Chat  `presenter.send_message_sync`  Core Process  `session_analysis`  Core 

---

## App 

****`MemScreenApp.build()` L2237–L2276

- ****  
  -  `get_config()`  `MemoryConfig` / `EmbedderConfig` / `LlmConfig` / `VectorStoreConfig`  `Memory(config=...)`  
  -  `RecordingPresenter``VideoPresenter``ChatPresenter`  Screen
- **** Core  UI Screen 
- ****  
  - **Screen ** Core   
  - **kivy_app ** `memscreen``memory.models``config`  UI  `start.py`  `main_kivy.py` Kivy  `memory`  presenters App  config/MemoryConfig

****  
- Screen  Presenter/Service → ****  
- kivy_app  Core / →  App 

---

## UI_CORE_SEPARATION_EVALUATION

- ** 1Chat  ChatPresenter**`kivy_app.py`  LLM/Chat  `presenter.send_message_sync`  
- ** 2Process  Core**`kivy_app.py`  sqlite3 / `_categorize_activities` / `_analyze_patterns` `session_analysis`  
- ** 3**`CORE_API.md` / UI  TODO

---

## 

- **UI **  
  - ****LLM CorePresenter  session_analysis Screen   
- ****  
  -  Memory/Presenter  `MemScreenApp.build()`  `start.py`  kivy_app  config/MemoryConfig   
  - Process  Recording/Video  `ProcessMiningPresenter`  `session_analysis` Service UI 
