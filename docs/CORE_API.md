# MemScreen Core API（UI 对接约定）

本文档列出 **UI 与 Python Core** 的对接接口：ChatPresenter 的发送/回调约定，以及 Process 会话的 CRUD 与分析接口。供 Kivy、CLI 或未来 Web 等前端统一调用。

---

## 一、Chat：ChatPresenter

**模块**：`memscreen.presenters.chat_presenter`

**构造**：
```python
ChatPresenter(
    view=None,                    # 可选，View 实例
    memory_system=None,           # Memory 实例，用于记忆搜索与写回
    ollama_base_url="http://127.0.0.1:11434"
)
```

### 1.1 发送消息（两种方式）

**方式 A：非流式（Kivy 当前使用）**

```python
def send_message_sync(
    self,
    user_message: str,
    on_done: Callable[[str, Optional[str]], None],
) -> None
```

- **说明**：在后台线程执行「记忆搜索 → 模型选择 → LLM 调用 → 写回记忆」，完成后调用 `on_done(ai_text, error_text)`。
- **`on_done`**：`(ai_text: str, error_text: Optional[str])`。成功时 `error_text is None`；失败时 `error_text` 为错误字符串。
- **注意**：`on_done` 在**工作线程**执行，若在 UI 中更新控件，需在主线程调度（如 Kivy 的 `Clock.schedule_once`）。

**方式 B：流式**

```python
def send_message(self, user_message: str, use_agent: bool = None) -> bool
```

- **说明**：内部会 `_search_memory`、`_build_messages`、`_start_streaming`；可能走 Intelligent Agent / Agent / 标准聊天。返回 `True` 表示已发起请求。
- **View 需实现以下回调**（Presenter 会调用）：
  - `view.on_message_added(role: str, content: str)` — 用户消息已加入历史时
  - `view.on_response_started()` — 开始收流时（可显示 typing）
  - `view.on_response_chunk(chunk: str)` — 每收到一段内容时（可选，用于打字机效果）
  - `view.on_response_completed(full_response: str)` — 流式结束，完整回复

### 1.2 其他对 View 有用的接口

| 方法 | 签名 | 说明 |
|------|------|------|
| `initialize()` | `() -> None` | 初始化（如加载模型列表），View 就绪后调用。 |
| `cleanup()` | `() -> None` | 释放资源，App 退出时调用。 |
| `set_view(view)` | `(view) -> None` | 设置/更换 View。 |
| `get_conversation_history()` | `() -> List[ChatMessage]` | 当前对话历史。 |
| `get_available_models()` | `() -> List[str]` | 可用模型列表。 |
| `get_current_model()` | `() -> str` | 当前选中模型。 |
| `set_model(model_name: str)` | `(str) -> bool` | 设置当前模型。 |
| `show_error(message, title="Error")` | `(str, str) -> None` | 通过 View 显示错误（若 View 实现 `show_error`）。 |

---

## 二、Process：会话存储与分析

**模块**：`memscreen.services.session_analysis`  
**DB**：默认 `./db/process_mining.db`，表 `sessions`（与原有 UI 一致）。

### 2.1 常量

| 名称 | 类型 | 说明 |
|------|------|------|
| `DEFAULT_DB_PATH` | `str` | 默认 DB 路径：`"./db/process_mining.db"`。 |

### 2.2 会话 CRUD

| 函数 | 签名 | 说明 |
|------|------|------|
| `save_session` | `(events: List[Dict], start_time: str, end_time: str, db_path: str = DEFAULT_DB_PATH) -> None` | 保存一条会话；建表不存在时会自动建表。 |
| `load_sessions` | `(limit: int = 20, db_path: str = DEFAULT_DB_PATH) -> List[Tuple[int, str, str, int, int, int]]` | 加载会话列表。返回 `(id, start_time, end_time, event_count, keystrokes, clicks)`。 |
| `get_session_events` | `(session_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[List[Dict]]` | 按 session_id 取该条会话的 events（JSON 解析后的 list）。未找到返回 `None`。 |
| `delete_session` | `(session_id: int, db_path: str = DEFAULT_DB_PATH) -> int` | 删除一条会话；返回删除行数。 |
| `delete_all_sessions` | `(db_path: str = DEFAULT_DB_PATH) -> int` | 删除所有会话；返回删除行数。 |

### 2.3 会话分析（供 UI 展示）

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_session_analysis` | `(session_id, event_count, keystrokes, clicks, start_time, end_time, db_path=DEFAULT_DB_PATH) -> Optional[Dict]` | 加载该会话的 events，并计算分类与统计。返回 `None` 表示会话不存在；否则返回 dict：`categories`、`patterns`、以及传入的 `event_count`、`keystrokes`、`clicks`、`start_time`、`end_time`。 |
| `categorize_activities` | `(events: List[Dict]) -> Dict[str, Any]` | 对 events 做活动分类。返回结构含 `typing`/`browsing`/`design`/`programming`/`communication`/`document`/`gaming`/`other`（各含 `score`、`percentage`）及 `primary`。 |
| `analyze_patterns` | `(events: List[Dict]) -> Dict[str, Any]` | 对 events 做模式统计。返回 `top_keys`、`avg_events_per_minute`、`click_ratio`、`duration_minutes`。 |

### 2.4 单条 event 的约定

- **List[Dict]** 中每个元素建议包含：`type`（如 `"keypress"`、`"click"`、`"info"`）、`text`、`time`（如 `"HH:MM:SS"`）。与原有 ProcessScreen 内存列表格式一致。

---

## 三、使用示例（Kivy 侧）

**Chat（非流式）**：
```python
def on_send():
    text = self.chat_input.text
    if not text or not self.presenter:
        return
    self.chat_input.text = ""
    # 显示用户气泡、typing 占位...
    def on_done(ai_text, error_text):
        Clock.schedule_once(lambda dt: self._on_chat_done(typing_label, ai_text, error_text), 0)
    self.presenter.send_message_sync(text, on_done=on_done)
```

**Process（加载历史并展示分析）**：
```python
from memscreen.services.session_analysis import (
    load_sessions,
    get_session_analysis,
    delete_session,
    DEFAULT_DB_PATH,
)
sessions = load_sessions(limit=20, db_path=DEFAULT_DB_PATH)
# 每条: (session_id, start_time, end_time, event_count, keystrokes, clicks)
result = get_session_analysis(session_id, event_count, keystrokes, clicks, start_time, end_time, db_path=DEFAULT_DB_PATH)
if result:
    categories, patterns = result["categories"], result["patterns"]
    # 拼 analysis_text 更新 UI
```
