# UI + Python Core 彻底分离方案评估

## 一、现状概览

### 1.1 当前架构

```
memscreen/
├── ui/                    # 当前唯一 UI 实现（Kivy）
│   └── kivy_app.py        # ~2900 行，单文件巨型 UI
├── presenters/            # MVP 的 P 层，部分被 UI 使用
│   ├── base_presenter.py
│   ├── recording_presenter.py   ✅ 被 RecordingScreen 使用
│   ├── video_presenter.py       ✅ 被 VideoScreen 使用
│   ├── chat_presenter.py        ❌ 存在但 Kivy 未使用
│   └── process_mining_presenter.py  ❌ 存在但 Kivy 未使用
├── memory/                # 记忆系统（Core）
├── llm/                   # 大模型（Core）
├── embeddings/            # 向量/嵌入（Core）
├── vector_store/          # 向量库（Core）
├── storage/               # 存储（Core）
├── config/                # 配置（Core）
├── agent/                 # 智能体（Core）
├── process_mining.py      # 流程分析（Core，但与 UI 中 Process 逻辑不统一）
└── ...
```

### 1.2 耦合情况

| 模块 | UI 中的使用方式 | 业务逻辑是否在 UI 内 |
|------|------------------|----------------------|
| **RecordingScreen** | 通过 `RecordingPresenter` 调用 | 否，逻辑在 Presenter |
| **VideoScreen** | 通过 `VideoPresenter` 调用 | 否，逻辑在 Presenter |
| **ChatScreen** | 直接 `Memory` + 内联 LLM/记忆搜索/模型选择 | **是**，~200 行逻辑在 `kivy_app.py` |
| **ProcessScreen** | 直接 `sqlite3` + 内联分类/统计/CRUD | **是**，~400+ 行逻辑在 `kivy_app.py` |
| **AboutScreen** | 纯展示 | 否 |

**结论**：录制、视频已做到「UI 只做展示 + 委托 Presenter」；聊天和流程分析是「UI 里写满业务逻辑」，且未使用已有的 `ChatPresenter` / `ProcessMiningPresenter`。

---

## 二、方案目标：UI + Python Core 彻底分离

### 2.1 目标定义

- **UI 层**：只负责
  - 布局、控件、样式、事件绑定
  - 把用户操作转成对「Core / Presenter」的调用
  - 把 Core 返回的数据/状态渲染出来（不解释业务规则）
- **Python Core**：承担
  - 所有业务逻辑（记忆、搜索、LLM、流程分析、会话存储等）
  - 通过 **稳定接口** 对 UI 暴露能力（Presenter 或 Service API）
  - 可被 CLI、其他 UI（如 Web）、自动化测试直接复用

### 2.2 预期效果

- 换 UI（例如从 Kivy 换到 Qt/Web）时，只需重写视图层，Core 不变。
- Core 可单独做单元测试/集成测试，不依赖 Kivy。
- 职责清晰：改 UI 不动业务，改业务不动 UI 结构。

---

## 三、方案评估

### 3.1 优点

| 维度 | 说明 |
|------|------|
| **可维护性** | 业务集中到 Core，UI 变薄，改一处不会牵动另一层 |
| **可测试性** | Core 无 GUI 依赖，便于 mock 与自动化测试 |
| **可复用性** | 同一套 Core 可服务 Kivy、CLI、未来 Web/桌面 |
| **与现有 MVP 一致** | 已有 Recording/Video 的 Presenter 用法可推广到 Chat/Process |
| **技术栈自由** | 将来若用 Electron/Web 做 UI，只需实现同一套 Core 接口 |

### 3.2 难点与成本

| 项目 | 说明 | 建议 |
|------|------|------|
| **ChatScreen 迁到 ChatPresenter** | 当前聊天逻辑（记忆搜索、模型选择、LLM 调用、写回记忆）全在 `kivy_app.py` 内联 | 把这段逻辑迁入 `ChatPresenter`（或 Core 的 ChatService），UI 只发「发消息」、收「流式/最终回复」 |
| **ProcessScreen 与 Core 统一** | ProcessScreen 自建 `process_mining.db` 与 `sessions` 表，自写 `_classify_activity` / `_analyze_patterns`；Core 的 `ProcessMiningAnalyzer` 用的是另一套 DB（`keyboard_mouse_logs`） | 二选一：要么把 UI 的「会话+分类+统计」收拢到 Core（新/统一 ProcessMining 服务），要么让 ProcessMiningPresenter 接上现有 UI 的数据源并迁逻辑到 Presenter |
| **接口约定** | UI 与 Core 之间需要稳定 API（方法名、参数、回调/异步方式） | 用 Presenter 的现有模式：View 调用 Presenter，Presenter 回调 View 的 `update_*` / `show_error` 等；必要时为流式/异步定义小接口（如 `on_chunk`、`on_done`） |
| **Kivy 主线程** | Core 若在后台线程跑，结果要回到 Kivy 主线程更新 UI | 保持现有做法：Core 在 thread 里跑，用 `Clock.schedule_once` 或 Presenter 内封装「回调到主线程」 |
| **工作量** | 需重构 ChatScreen 与 ProcessScreen，并可能统一/扩展 process_mining | 建议分两期：先 Chat（收益大、逻辑集中），再 Process（顺带统一 DB/分析逻辑） |

### 3.3 风险

- **接口设计不当**：若 Core 暴露的 API 过于「为当前 Kivy 定制」，以后换 UI 会再改 Core。应对：Presenter 或 Service 层面向「用例」设计（如 `send_message(query, on_response)`），不暴露 Kivy 专有类型。
- **Process 双轨**：若保留 UI 内自建 DB 与 Core 的 `ProcessMiningAnalyzer` 两套逻辑，会长期双轨维护。应对：明确「流程分析」只由 Core 一处实现，UI 只调 Core。
- **过度抽象**：为「将来可能换 UI」引入过多层/接口会增加理解成本。应对：先做到「UI 不写业务、只调 Presenter/Core」，接口保持当前 Presenter 风格即可，不必立刻做成通用 RPC。

---

## 四、推荐实施路径

### 阶段 1：Chat 彻底分离（优先）

1. **在 Core 侧**（或沿用 `ChatPresenter`）：
   - 提供「发送一条用户消息」的入口：内部完成记忆搜索、模型选择、LLM 调用、写回记忆。
   - 通过回调或队列把「流式片段 / 最终回复 / 错误」回传给调用方。
2. **在 Kivy 侧**：
   - `ChatScreen` 只保留：输入框、发送按钮、历史区、loading/错误展示。
   - 发送时调用上述 Core/Presenter 接口；在回调里用 `Clock.schedule_once` 更新 UI（添加气泡、隐藏 typing、显示错误）。
3. **验收**：Chat 相关逻辑从 `kivy_app.py` 移除，全部由 `ChatPresenter`（或 Core 的 chat 模块）承担；UI 文件行数明显下降。

### 阶段 2：Process 统一到 Core

1. **统一数据与逻辑**：
   - 决定流程分析的数据源：要么沿用 UI 当前的 `process_mining.db` + `sessions`，要么迁移到与 `ProcessMiningAnalyzer` 一致的 schema；二者只保留一套。
   - 将 `_classify_activity`、`_analyze_patterns` 以及会话的 CRUD 迁入 Core（例如 `process_mining` 模块或 `ProcessMiningPresenter`）。
2. **UI 只做调用与展示**：
   - ProcessScreen 只：调「开始/停止追踪」「保存会话」「加载历史」「按会话分析」等 Core 接口，并把返回的结构化数据渲染成列表/统计/图表。
3. **验收**：`kivy_app.py` 中不再出现 `sqlite3`、`_classify_activity`、`_analyze_patterns` 等业务实现；Process 相关 DB 与算法全部在 Core。

### 阶段 3：接口固化与文档（可选）

- 为 Presenter 或 Core 的「对 UI 暴露面」写简短说明：方法、参数、回调含义。
- 若有计划支持其他 UI，可增加一层薄薄的 Application Service（门面），让 Kivy 与未来 UI 都通过同一门面调 Core。

---

## 五、结论与建议

- **方案可行性**：高。现有 Recording/Video 已证明「UI + Presenter + Core」的分离在项目内可行；Chat 与 Process 的耦合是局部问题，可逐步迁出 UI。
- **建议**：采用「UI + Python Core 彻底分离」方向，并按上述三阶段推进：先 Chat，再 Process，最后视需要固化接口与文档。
- **预期收益**：`kivy_app.py` 从 ~2900 行缩减到以「布局 + 事件转发 + 渲染」为主；业务逻辑集中到 Core/Presenter，便于测试和未来多端复用。

---

## 五.1 能否保持原逻辑完全不变？

**可以。** 分离采用「纯搬迁」方式即可：

- **Chat**：将 `kivy_app.py` 内当前那段逻辑（记忆搜索、模型选择、构造 messages、LLM 调用、写回记忆）**原样**迁入 Core（如 ChatPresenter 或独立函数），不修改任何算法、参数、prompt 或 DB 用法；UI 只负责取输入、调用 Core、用返回值更新气泡和 typing。
- **Process**：将 `_categorize_activities`、`_analyze_patterns` 及当前 sqlite3 的建表/增删查**原样**迁入 Core（同一 `process_mining.db`、同一 `sessions` 表结构）；UI 只负责调 Core 的「保存会话 / 拉列表 / 按 session 取分析」，再用返回的 dict/列表按现有格式拼文案和列表。

**结果**：用户可见的界面、文案、交互、数据完全一致；逻辑 1:1 搬迁，零重写，仅增加一层「UI 调 Core」的薄接口。

---

## 六、具体改动清单

以下按「阶段 1：Chat」「阶段 2：Process」列出可执行的改动项（文件路径、方法/行号、操作类型）。

---

### 阶段 1：Chat 迁到 ChatPresenter

#### 1.1 Core 侧：`memscreen/presenters/chat_presenter.py`

| 序号 | 状态 | 操作 | 位置 | 说明 |
|------|------|------|------|------|
| C1.1 | DONE | **确认/扩展** | `ChatPresenter.__init__` | 构造时接收 `memory_system`，Kivy 传入 `MemScreenApp.memory`。 |
| C1.2 | DONE | **确认** | `send_message(user_message, use_agent=None)` (约 L327) | 已有：内部会 `_search_memory`、`_build_messages`、`_start_streaming`，无需在 UI 再写一遍。 |
| C1.3 | DONE | **确认 View 回调** | View 需实现 | Kivy 采用 `send_message_sync` + `on_done`，在 `_on_chat_done` 中更新 UI。 |
| C1.4 | DONE | **可选** | 新增 `send_message_sync(user_message, on_done)` | 已实现：非流式入口，后台线程跑原逻辑，回调 `on_done(ai_text, error_text)`。 |

#### 1.2 Kivy 侧：`memscreen/ui/kivy_app.py`

| 序号 | 状态 | 操作 | 位置（行号约） | 说明 |
|------|------|------|----------------|------|
| K1.1 | DONE | **删除** | L553–L722（`send_message` 内 `get_ai_response` 整段） | 已删内联逻辑，改为 `presenter.send_message_sync(text, on_done=...)`。 |
| K1.2 | DONE | **保留并瘦身** | L513–L551 | 已保留取 text、清空、用户气泡、typing；改为调 `self.presenter.send_message_sync(text, on_done)`。 |
| K1.3 | DONE | **替换** | L624–L718（`update_ui` 闭包） | 已由 `_on_chat_done(typing_label, ai_text, error_text)` 实现，在 `on_done` 里 `Clock.schedule_once` 调用。 |
| K1.4 | DONE | **新增** | `ChatScreen` 内 | 使用 `send_message_sync` + `_on_chat_done` 更新 UI，未实现流式 View 回调。 |
| K1.5 | DONE | **新增** | `ChatScreen` / App | Presenter 由 App 创建并注入，ChatScreen 不创建 Presenter。 |
| K1.6 | DONE | **修改** | `MemScreenApp.build()` | 已创建 `ChatPresenter(memory_system, ollama_base_url)`、`set_view`/`set_presenter`、`initialize()`；`on_stop` 中 `chat_presenter.cleanup()`。 |
| K1.7 | DONE | **删除** | `_fix_filesystem_encoding`、`_show_error_message` | 已删除，错误展示在 `_on_chat_done` 中。 |

#### 1.3 验收（阶段 1）

- [x] DONE `kivy_app.py` 中不再包含：`memory_system.search`、`OllamaLLM`、`memory_system.add`、模型选择与 system prompt 拼接。
- [x] DONE Chat 发送一条消息后，仍能正常显示用户消息与 AI 回复（含错误提示）。
- [ ] TODO 可选：流式回复时打字机效果由 `on_response_chunk` 驱动。

---

### 阶段 2：Process 迁到 Core

#### 2.1 Core 侧：会话存储与分析

| 序号 | 状态 | 操作 | 文件/位置 | 说明 |
|------|------|------|------------|------|
| P1.1 | DONE | **新增** | `memscreen/services/session_analysis.py` | 已实现 `categorize_activities(events)`、`analyze_patterns(events)`，返回与 UI 一致的 dict。 |
| P1.2 | DONE | **新增** | 同上 | 已实现 `save_session`、`load_sessions`、`get_session_events`、`get_session_analysis`、`delete_session`、`delete_all_sessions`；DB 为 `process_mining.db` + `sessions` 表，schema 与原 UI 一致。 |
| P1.3 | TODO | **可选** | `ProcessMiningPresenter` | 未做：ProcessScreen 仍用「内存列表 + 结束时保存」+ Core 会话接口，未接 InputTracker。 |

#### 2.2 Kivy 侧：`memscreen/ui/kivy_app.py`

| 序号 | 状态 | 操作 | 位置（行号约） | 说明 |
|------|------|------|----------------|------|
| K2.1 | DONE | **删除** | `_save_session` 内联 sqlite3 | 已改为调用 `core_save_session(...)`。 |
| K2.2 | DONE | **删除** | `_load_history` 内联 sqlite3 | 已改为调用 `core_load_sessions(limit=20)`，仍用 `_create_session_item` 组装。 |
| K2.3 | DONE | **删除** | `_show_session_analysis` 内联逻辑 | 已改为调用 `core_get_session_analysis(...)`，再拼 `analysis_text`。 |
| K2.4 | DONE | **删除** | `_categorize_activities` | 已整段迁到 Core（`session_analysis.categorize_activities`）。 |
| K2.5 | DONE | **删除** | `_analyze_patterns` | 已整段迁到 Core（`session_analysis.analyze_patterns`）。 |
| K2.6 | DONE | **保留** | `_create_session_item` 及删除/清空 | 已保留；点击时调 `_show_session_analysis`（内部已调 Core）。 |
| K2.7 | DONE | **保持** | `start`/`stop`/`_add_session_event` | 保持当前「内存列表 + 结束时保存」逻辑，保存/加载已改为调 Core。 |
| K2.8 | DONE | **修改** | `_delete_session`/`_delete_all_sessions` | 已改为调用 `core_delete_session`/`core_delete_all_sessions`，再 `_load_history()`。 |

#### 2.3 验收（阶段 2）

- [x] DONE `kivy_app.py` 中不再出现 `sqlite3`、`_categorize_activities`、`_analyze_patterns`。
- [x] DONE 开始/停止追踪、保存会话、加载历史、按会话查看分析、删除单条/清空，行为与改动前一致（逻辑 1:1 搬迁）。
- [x] DONE 会话数据仍存于 `process_mining.db`，无数据丢失。

---

### 阶段 3（可选）：接口文档与入口统一

| 序号 | 状态 | 操作 | 说明 |
|------|------|------|------|
| D1 | DONE | **文档** | 已实现：`docs/CORE_API.md` 列出 ChatPresenter 的 `send_message`/`send_message_sync` 与 View 回调约定；Process 的会话 CRUD + 分析接口签名及使用示例。 |
| D2 | TODO | **入口** | 若有多 UI 计划：在 `memscreen/` 下提供薄门面（如 `get_chat_service()`、`get_process_service()`），内部返回 Presenter 或 Service 实例。 |

---

### 改动清单小结

| 阶段 | 状态 | 主要改动 |
|------|------|----------|
| **阶段 1 Chat** | DONE | Core：新增 `ChatPresenter.send_message_sync`（原 Kivy 逻辑 1:1）；Kivy：删内联逻辑，改为 `presenter.send_message_sync` + `_on_chat_done`，App 创建并注入 ChatPresenter。 |
| **阶段 2 Process** | DONE | Core：新增 `memscreen/services/session_analysis.py`（会话 CRUD + `categorize_activities`/`analyze_patterns`）；Kivy：删内联 sqlite 与算法，改为调 Core 接口。 |
| **阶段 3 可选** | D1 DONE / D2 TODO | D1 已补充 `docs/CORE_API.md`；D2 门面待多 UI 时再做。 |
