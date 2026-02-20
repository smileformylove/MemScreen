# MemScreen Core APIUI 

 **UI  Python Core** ChatPresenter / Process  CRUD  KivyCLI  Web 

---

## ChatChatPresenter

****`memscreen.presenters.chat_presenter`

****
```python
ChatPresenter(
    view=None,                    # View 
    memory_system=None,           # Memory 
    ollama_base_url="http://127.0.0.1:11434"
)
```

### 1.1 

** AKivy **

```python
def send_message_sync(
    self,
    user_message: str,
    on_done: Callable[[str, Optional[str]], None],
) -> None
```

- **** →  → LLM  →  `on_done(ai_text, error_text)`
- **`on_done`**`(ai_text: str, error_text: Optional[str])` `error_text is None` `error_text` 
- ****`on_done` **** UI  Kivy  `Clock.schedule_once`

** B**

```python
def send_message(self, user_message: str, use_agent: bool = None) -> bool
```

- **** `_search_memory``_build_messages``_start_streaming` Intelligent Agent / Agent /  `True` 
- **View **Presenter 
  - `view.on_message_added(role: str, content: str)` — 
  - `view.on_response_started()` —  typing
  - `view.on_response_chunk(chunk: str)` — 
  - `view.on_response_completed(full_response: str)` — 

### 1.2  View 

|  |  |  |
|------|------|------|
| `initialize()` | `() -> None` | View  |
| `cleanup()` | `() -> None` | App  |
| `set_view(view)` | `(view) -> None` | / View |
| `get_conversation_history()` | `() -> List[ChatMessage]` |  |
| `get_available_models()` | `() -> List[str]` |  |
| `get_current_model()` | `() -> str` |  |
| `set_model(model_name: str)` | `(str) -> bool` |  |
| `show_error(message, title="Error")` | `(str, str) -> None` |  View  View  `show_error` |

---

## Process

****`memscreen.services.session_analysis`  
**DB** `./db/process_mining.db` `sessions` UI 

### 2.1 

|  |  |  |
|------|------|------|
| `DEFAULT_DB_PATH` | `str` |  DB `"./db/process_mining.db"` |

### 2.2  CRUD

|  |  |  |
|------|------|------|
| `save_session` | `(events: List[Dict], start_time: str, end_time: str, db_path: str = DEFAULT_DB_PATH) -> None` |  |
| `load_sessions` | `(limit: int = 20, db_path: str = DEFAULT_DB_PATH) -> List[Tuple[int, str, str, int, int, int]]` |  `(id, start_time, end_time, event_count, keystrokes, clicks)` |
| `get_session_events` | `(session_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[List[Dict]]` |  session_id  eventsJSON  list `None` |
| `delete_session` | `(session_id: int, db_path: str = DEFAULT_DB_PATH) -> int` |  |
| `delete_all_sessions` | `(db_path: str = DEFAULT_DB_PATH) -> int` |  |

### 2.3  UI 

|  |  |  |
|------|------|------|
| `get_session_analysis` | `(session_id, event_count, keystrokes, clicks, start_time, end_time, db_path=DEFAULT_DB_PATH) -> Optional[Dict]` |  events `None`  dict`categories``patterns` `event_count``keystrokes``clicks``start_time``end_time` |
| `categorize_activities` | `(events: List[Dict]) -> Dict[str, Any]` |  events  `typing`/`browsing`/`design`/`programming`/`communication`/`document`/`gaming`/`other` `score``percentage` `primary` |
| `analyze_patterns` | `(events: List[Dict]) -> Dict[str, Any]` |  events  `top_keys``avg_events_per_minute``click_ratio``duration_minutes` |

### 2.4  event 

- **List[Dict]** `type` `"keypress"``"click"``"info"``text``time` `"HH:MM:SS"` ProcessScreen 

---

## Kivy 

**Chat**
```python
def on_send():
    text = self.chat_input.text
    if not text or not self.presenter:
        return
    self.chat_input.text = ""
    # typing ...
    def on_done(ai_text, error_text):
        Clock.schedule_once(lambda dt: self._on_chat_done(typing_label, ai_text, error_text), 0)
    self.presenter.send_message_sync(text, on_done=on_done)
```

**Process**
```python
from memscreen.services.session_analysis import (
    load_sessions,
    get_session_analysis,
    delete_session,
    DEFAULT_DB_PATH,
)
sessions = load_sessions(limit=20, db_path=DEFAULT_DB_PATH)
# : (session_id, start_time, end_time, event_count, keystrokes, clicks)
result = get_session_analysis(session_id, event_count, keystrokes, clicks, start_time, end_time, db_path=DEFAULT_DB_PATH)
if result:
    categories, patterns = result["categories"], result["patterns"]
    #  analysis_text  UI
```
