# Flutter 前端迁移 Todolist

**目标**：将核心能力全部迁移到新 Flutter 前端，同时**兼容并保持现有 Kivy UI 不变**（默认仍为 Kivy，Flutter 为可选新前端）。

**原则**：不修改现有 Kivy 调用路径；新增 API 层与 Flutter 项目为增量，现有 `start.py` → Kivy 行为保持不变。

---

## 实现进度小结（当前）

| 区块 | 状态 | 说明 |
|------|------|------|
| **§一 后端 API 层** | ✅ 已完成 | `memscreen/api/` 已建，FastAPI + deps，独立启动，config 增加 api.*，`docs/API_HTTP.md` 已写。 |
| **§二 API 路由** | ✅ 已完成 | Chat / Process / Recording / Video / config / health 全部实现；2.13 录制预览、2.15 视频流为可选未做。 |
| **§五 兼容 Kivy** | ✅ 已满足 | 未改 `kivy_app.py`、未改 `setup/start.py` 默认行为。 |
| **§三 Flutter 项目** | ✅ 已完成 | `frontend/flutter/` 已建，API 客户端、连接状态与错误提示已实现。 |
| **§四 Flutter 功能** | ✅ 已完成 | Chat / Process / Recording / Video / 设置与关于 各页面对接 API。 |
| **§六 文档与交付** | ✅ 已完成 | README 已补“双前端”说明，docs/FLUTTER.md 开发说明，可选 CI 见文档。 |
| **§七 可选增强** | ⏳ 未做 | 一体化启动脚本、Kivy 内嵌 API、记忆搜索 API 等。 |

**下一步建议**：可选项（2.13/2.15、4.9/4.12、6.3、§七）按需补齐；Process「保存会话」UI 依赖事件来源（4.9）后可补入口。

---

## 架构合理性 Review

### 结论：整体合理，可落地；以下为细化建议与风险点。

---

### 1. 分层与职责

| 层级 | 评价 | 说明 |
|------|------|------|
| **API 薄封装** | ✅ 合理 | 与现有 Core（Presenter/Service）一一对应，不重写业务；路由设计面向「用例」（发消息、会话 CRUD、录制控制），不暴露 Kivy/内部类型，便于 Kivy 与 Flutter 长期共用 Core。 |
| **Core 复用** | ✅ 合理 | Kivy 与 API 共用同一套 Memory/Presenter 初始化逻辑（1.2 要求抽到共享 factory 或 start 辅助），避免双份实现；API 进程内使用单例 Presenter，与 Kivy 单进程单实例一致。 |
| **兼容策略** | ✅ 合理 | 不改 `kivy_app.py`、不改 `start.py` 默认行为；API 独立启动、可选配置，现有用户无感。 |

---

### 2. 与现有 Core 的对接一致性

- **Chat**：`ChatPresenter.send_message_sync(on_done=...)` 为回调 + 后台线程，API 层用线程池阻塞等待 `on_done` 再返回 HTTP 响应即可；流式用「适配器 View」把 `on_response_chunk` 推到 SSE/WebSocket。与现有 `CORE_API.md` 一致。
- **Process**：`get_session_analysis(session_id, event_count, keystrokes, clicks, start_time, end_time)` 需要除 `session_id` 外的元数据。建议 **API 只暴露 `GET /process/sessions/{id}/analysis`**，后端根据 `session_id` 查 `sessions` 表取 `event_count/keystrokes/clicks/start_time/end_time` 再调 `get_session_analysis`，避免客户端重复传一遍列表里的字段。
- **Recording**：`start_recording(duration, interval)` 仅两个参数；`mode/region/screen_index` 由 **`set_recording_mode(mode, bbox=..., screen_index=...)`** 在启动前设置。建议 API 的 `POST /recording/start` 请求体在包含 `duration/interval` 外，可选包含 `mode`、`region`、`screen_index`，**实现时先调 `set_recording_mode` 再调 `start_recording`**。与现有 Presenter 能力一致。
- **Video**：`VideoPresenter.get_video_list()` 返回 `List[VideoInfo]`，`VideoInfo.to_dict()` 已存在；API 直接返回该结构即可。注意：列表项中的 `filename` 为本地绝对路径。**同机 Flutter 桌面端**可用 path 直接播放；**Flutter 移动端或远程**需后端提供「文件服务」（如 `GET /video/file?path=...` 或按 id 流式返回），todolist 2.15 可明确补充「若需远程/移动端播放，增加 GET /video/file 或 /video/stream」。
- **Presenter 无 View**：API 侧 Presenter 的 `view=None`。`RecordingPresenter` 在 `start_recording` 成功后会调 `if self.view: self.view.on_recording_started()`，无 view 时仅为 no-op，可接受。其他 Presenter 的 `show_error` 等可在 API 层转为 HTTP 4xx/5xx 或错误体。

---

### 3. 进程模型与状态

- **推荐默认**：**Kivy 与 API 不同时运行**（二选一）。用户用 Kivy 时只起 `start.py`；用 Flutter 时只起 API 服务 + Flutter 客户端。两进程不会同时写同一 DB/Chroma，避免锁与状态分叉。
- **可选 7.2**：若实现「Kivy 进程内嵌 API」，则同一进程内共享 Memory/Presenter，Flutter 连本机 API 即与 Kivy 共享状态；此时仅一套 DB/连接，需注意 Kivy 主线程与 FastAPI 异步/线程的兼容（Presenter 回调若来自后台线程，与当前 Kivy 一致，无额外问题）。
- **会话状态**：Chat 的「当前对话/当前模型」、Recording 的「是否在录」均为单例状态；多端同时连同一 API 会共享该状态（谁后操作谁生效）。若未来要多用户/多会话，再引入 session 或 user 维度即可，当前不必过度设计。

---

### 4. 配置与数据路径

- API 服务应与 Kivy 使用**同一配置来源**（`get_config()`、同一 `config_path` 或 env），保证 `db_path`、`videos_dir`、`ollama_base_url` 等一致，否则 Flutter 与 Kivy 交替使用时数据会「分家」。1.2 的「复用与 Kivy 相同的 Core 初始化逻辑」已覆盖，实现时注意工作目录与配置查找顺序（如 `~/.memscreen`）一致。

---

### 5. 未覆盖点与建议补充

- **Process 事件来源（4.9）**：当前 Kivy 端由 InputTracker 采集键盘/鼠标。Flutter 端要么 (a) Flutter 自己采集并 POST 到 `POST /process/sessions`，要么 (b) 本机跑一个与 API 同进程或独立进程的「采集服务」把事件推给 API。建议在 `API_HTTP.md` 中约定 **events 的 JSON 格式**（与 `CORE_API.md` 的 `type/text/time` 等一致），并注明「事件由客户端或独立采集服务提供」。
- **Video 播放**：若 Flutter 与后端非同机（或移动端），todolist 建议显式增加一项：**「GET /video/file 或 /video/stream：按 path 或 id 返回视频文件流」**，便于 Flutter 统一用 URL 播放。
- **健康检查**：`GET /health` 除「进程存活」外，可包含「Ollama 是否可达」「DB 是否可连」等，便于 Flutter 展示更明确的连接/错误提示。

---

### 6. 小结

| 维度 | 结论 |
|------|------|
| 分层与兼容 | 合理；API 薄封装、Kivy 不变、Core 复用。 |
| 与 Core 对接 | 需注意 Process 分析接口由后端按 id 解析元数据；Recording 先 set_recording_mode 再 start。 |
| 进程与状态 | 默认 Kivy/API 二选一；可选同进程内嵌 API 共享状态。 |
| 配置与路径 | 强调 API 与 Kivy 同源配置、同数据目录。 |
| 待补 | Process events 来源与 JSON 约定；Video 跨机/移动端时的文件服务；health 细化。 |

按当前 todolist 实施即可落地；实现时按上述细节点做即可提升一致性与可维护性。

---

## 一、后端 API 层（与现有 UI 兼容）

- [x] **1.1** 新建 `memscreen/api/` 包（或 `memscreen/server/`），与 `memscreen/ui/` 平级，不侵入 `ui/kivy_app.py`。
- [x] **1.2** 用 FastAPI 实现 API 应用入口（如 `memscreen/api/app.py`），从 `get_config()` 与现有 Presenter/Service 构造依赖，**复用与 Kivy 相同的 Core 初始化逻辑**（`memscreen/api/deps.py` 中 create_memory/create_*_presenter，供 API 使用）。
- [x] **1.3** 提供独立启动方式：例如 `python -m memscreen.api` 或 `setup/start_api.py`，仅启动 API 服务；**未修改** 现有 `setup/start.py` 的默认行为（仍只启动 Kivy）。
- [x] **1.4** 在 `config` 中增加可选配置项：`api.enabled`、`api.host`、`api.port`，默认不启动 API；支持 `MEMSCREEN_API_PORT` / `MEMSCREEN_API_HOST` / `MEMSCREEN_API_ENABLED`。
- [x] **1.5** 编写 `docs/API_HTTP.md`：记录各路由、请求/响应 JSON、错误码，与 `CORE_API.md` 对齐；含 Process 的 events JSON 约定及事件来源说明。

---

## 二、API 路由与 Core 能力映射

### Chat

- [x] **2.1** `POST /chat` — 非流式发送消息，请求体 `{ "message": "..." }`，响应 `{ "reply": "...", "error": null }` 或错误信息；内部调用 `ChatPresenter.send_message_sync`。
- [x] **2.2** `POST /chat/stream` — 流式发送（SSE），内部调用 `ChatPresenter` 流式路径，将 `on_response_chunk` / `on_response_completed` 推送到客户端。
- [x] **2.3** `GET /chat/models` — 可用模型列表；`GET /chat/model` — 当前模型；`PUT /chat/model` — 设置当前模型（对应 `get_available_models` / `get_current_model` / `set_model`）。
- [x] **2.4** `GET /chat/history` — 当前对话历史（对应 `get_conversation_history`），返回 JSON 数组。

### Process（流程分析）

- [x] **2.5** `GET /process/sessions` — 会话列表，对应 `load_sessions`，可选 query `limit`（默认 20）。
- [x] **2.6** `POST /process/sessions` — 保存会话，请求体含 `events`、`start_time`、`end_time`，对应 `save_session`。
- [x] **2.7** `GET /process/sessions/{id}` — 单条会话的 events，对应 `get_session_events`。
- [x] **2.8** `GET /process/sessions/{id}/analysis` — 单条会话分析结果；后端由 `session_id` 查表取元数据再调 `get_session_analysis`。
- [x] **2.9** `DELETE /process/sessions/{id}` — 删除一条会话；`DELETE /process/sessions` — 清空所有会话。

### Recording（录制）

- [x] **2.10** `POST /recording/start` — 开始录制，请求体可选 `duration`、`interval`、`mode`、`region`、`screen_index`；实现时先 `set_recording_mode` 再 `start_recording`。
- [x] **2.11** `POST /recording/stop` — 停止录制。
- [x] **2.12** `GET /recording/status` — 当前是否在录制、当前文件、统计信息等。
- [ ] **2.13** （可选）录制预览：WebSocket 或 SSE 推送帧数据，或仅状态；若不做预览，Flutter 仅显示“录制中”状态。

### Video（视频浏览）

- [x] **2.14** `GET /video/list` — 视频列表（对应 VideoPresenter），返回元数据（路径、时长、时间等）。
- [ ] **2.15** （可选）`GET /video/{id}/thumbnail` 或 URL；若 Flutter 与后端非同机或为移动端，增加 `GET /video/file`（按 path 或 id 返回视频流）供播放。

### 配置与健康

- [x] **2.16** `GET /config` — 只读配置（ollama_base_url、db_dir、videos_dir），用于 Flutter 展示或连接提示。
- [x] **2.17** `GET /health` — 健康检查（进程存活；Ollama 可达性、DB 可连），便于 Flutter 显示“后端已连接”及具体错误提示。

---

## 三、Flutter 项目与基础架构

- [x] **3.1** 在仓库中新建 Flutter 项目目录（如 `flutter_app/` 或 `frontend/flutter/`），与 `memscreen/`、`setup/` 平级。
- [x] **3.2** 配置 Flutter 连接后端：环境变量或配置文件指定 API base URL（如 `http://127.0.0.1:8765`），与 `docs/API_HTTP.md` 一致。**后端 API** 需在项目 Conda 环境下运行（环境名为项目名 `MemScreen`）：`conda activate MemScreen` 后执行 `python -m memscreen.api` 或 `python setup/start_api.py`。
- [x] **3.3** 实现通用 API 客户端（Dart）：封装 HTTP 调用、错误处理、可选 SSE/WebSocket 解析，所有请求走该客户端。
- [x] **3.4** 实现连接状态与错误提示：后端不可达时统一提示，并可重试或配置 URL。

---

## 四、Flutter 功能迁移（对应 Core 能力）

### Chat

- [x] **4.1** 聊天页：输入框、发送按钮、历史消息列表（用户/AI 气泡）。
- [x] **4.2** 调用 `POST /chat` 或 `POST /chat/stream`，展示回复或流式打字机效果。
- [x] **4.3** 模型选择：下拉/列表选择模型，调用 `GET /chat/models`、`PUT /chat/model`。
- [x] **4.4** 加载并展示当前对话历史（`GET /chat/history`），支持清空或新会话（若后端支持）。

### Process（流程分析）

- [x] **4.5** 流程分析页：会话列表（来自 `GET /process/sessions`），展示 start/end、event_count、keystrokes、clicks。
- [x] **4.6** 保存会话：流程分析页「保存会话」入口，弹层内填写 start_time、end_time，可添加多条事件（type: keypress/click/info、text、time），调用 `POST /process/sessions`；事件来源目前为手动录入，4.9 采集为可选。
- [x] **4.7** 查看单条分析：进入某会话后调用 `GET /process/sessions/{id}/analysis`，展示 categories、patterns 等（与现有 Kivy 展示逻辑对齐）。
- [x] **4.8** 删除单条会话、清空所有会话（`DELETE`）。
- [ ] **4.9** 若需“当前会话事件采集”（键盘/鼠标），需约定数据来源：由后端/InputTracker 提供或 Flutter 采集后上传，并在 API 中约定 events 格式（与 `CORE_API.md` 一致）。

### Recording（录制）

- [x] **4.10** 录制页：开始/停止按钮，可选参数（时长、间隔、全屏/区域、屏幕索引）通过表单或简单配置传入。
- [x] **4.11** 调用 `POST /recording/start`、`POST /recording/stop`，根据 `GET /recording/status` 更新 UI 状态（录制中/空闲、当前文件等）。
- [ ] **4.12** （可选）若实现预览：消费 WebSocket/SSE 帧数据并显示；否则仅显示“正在录制”与状态文案。

### Video（视频浏览）

- [x] **4.13** 视频列表页：调用 `GET /video/list`，展示列表（标题、时间、时长等）。
- [x] **4.14** 播放：使用返回的 path 或 URL 在 Flutter 中播放（本地文件或流），与现有 VideoPresenter 行为一致。

### 设置与关于

- [x] **4.15** 设置页：展示只读配置（`GET /config`）、API base URL 配置（若支持多环境）。
- [x] **4.16** 关于页：版本、项目说明，与现有 About 信息一致。

---

## 五、兼容现有 Kivy UI（保持不变）

- [x] **5.1** 不修改 `memscreen/ui/kivy_app.py` 中现有 Screen 与 Presenter 的调用方式；不删除或替换 Kivy 代码。
- [x] **5.2** 不修改 `setup/start.py` 默认入口：默认仍为 `MemScreenApp().run()`，用户无配置时行为与现在完全一致。
- [x] **5.3** Core 初始化（Memory、Presenter、config）保持可被 Kivy 直接使用；API 在独立进程中通过 `deps.py` 自建实例，与 Kivy 互不修改。
- [x] **5.4** 文档（README、API_HTTP、本 todolist）已说明：默认启动为 Kivy；Flutter 需先启动 API 服务（`conda activate MemScreen` 后 `python -m memscreen.api`），再启动 Flutter 应用。

---

## 六、文档与交付

- [x] **6.1** 在 `README.md` 或 `docs/` 中增加“双前端”说明：Kivy（默认）与 Flutter（可选），以及如何启动 API + Flutter。
- [x] **6.2** 提供 Flutter 的简要开发/运行说明（依赖、`flutter run`、环境变量/配置）。
- [ ] **6.3** 若需要，在 CI 中增加 API 健康检查或少量接口的自动化测试，确保 API 与 Core 行为一致。

---

## 七、可选增强

- [ ] **7.1** 提供“一体化”启动脚本：同时启动 API 服务与 Flutter 桌面端（或仅启动 API，由用户手动开 Flutter），方便开发与演示。
- [ ] **7.2** 若 Kivy 与 API 共用进程：在设置中增加“同时启动 API 服务”选项，仅当用户勾选时在 Kivy 进程内启动 API，便于同一台机器用 Flutter 连接。
- [ ] **7.3** 记忆搜索/配置写入：若 Flutter 需要独立“记忆搜索”或修改配置，再增加对应只读或受控 API，并在本 todolist 中补充子项。

---

## 最终 Review（可执行性确认）

### 覆盖度 vs 目标

| 目标 | 覆盖情况 |
|------|----------|
| **核心能力全迁移到 Flutter** | ✅ Chat / Process / Recording / Video / 配置与健康 均有对应 API（§二）与 Flutter 项（§四）；与 `CORE_API.md` 及现有 Presenter/Service 一一对应。 |
| **兼容现有 Kivy UI 且保持不变** | ✅ §五 明确不改 `kivy_app.py`、不改 `start.py` 默认行为；§一 要求 API 独立启动、可选配置，现有用户无感。 |

### 实施顺序建议

1. **后端**：先完成 §一（API 包、启动、配置、API_HTTP.md 骨架），再按 §二 实现 Chat → Process → Recording → Video → config/health。  
2. **Flutter**：§三 搭好项目与客户端后，按 §四 Chat → Process → Recording → Video → 设置/关于 逐项对接。  
3. **兼容与文档**：§五、§六 在实现过程中随时校验（不改 Kivy、文档同步更新）。

### 可选补充（非阻塞）

- **视频删除**：若需与 Kivy 完全一致，可增加 `DELETE /video`（或 `DELETE /video/{id}`）及 Flutter 删除入口；Core 已有 `VideoPresenter.delete_video(filename)`。
- **1.2 与 Kivy 的共享初始化**：为“复用与 Kivy 相同的 Core 初始化逻辑”，可能需将当前 `kivy_app.build()` 中的 Memory/Presenter 创建抽到共享函数（如 `memscreen.core_bootstrap.create_core()`），再由 Kivy 与 API 共同调用；仅移动代码位置、不改变 Kivy 对外行为，仍视为兼容。

### 结论

**Todolist 已可执行。** 结构完整、与 Core 对齐、兼容约束清晰；按上述顺序实施即可。可选补充可按需在实现中追加。

---

**完成标准**：上述 API 全部实现且 Flutter 端完成对应页面与调用；现有 Kivy UI 无需改动即可继续使用，默认启动方式与行为保持不变。
