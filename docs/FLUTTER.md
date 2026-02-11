# MemScreen Flutter 前端

MemScreen 的可选 Flutter 前端，与默认 Kivy UI 并存。通过 HTTP API 与后端通信。

## 依赖

- [Flutter SDK](https://flutter.dev/docs/get-started/install)（3.0+）
- 后端 API 运行在 Conda 环境 `MemScreen` 下

## 配置

- **API Base URL**：默认 `http://127.0.0.1:8765`，与 [API_HTTP.md](API_HTTP.md) 一致。
- 若后端使用其他地址，可在应用内「无法连接后端」时点击 **配置 API 地址** 修改。
- 环境变量：可通过 `--dart-define=API_BASE_URL=http://...` 在构建时传入（需在代码中读取，当前版本以默认 + 应用内配置为主）。

## 开发与运行

```bash
# 1. 进入 Flutter 项目目录
cd frontend/flutter

# 2. 若尚未生成平台工程，可先创建（可选）
flutter create . --project-name memscreen_flutter

# 3. 安装依赖
flutter pub get

# 4. 运行（需先启动后端 API）
flutter run
```

**先启动后端**（在项目根目录或任意目录，使用 Conda 环境 MemScreen）：

```bash
conda activate MemScreen
python -m memscreen.api
# 或
python setup/start_api.py
```

后端默认监听 `http://127.0.0.1:8765`。Flutter 应用启动后会请求 `GET /health` 检查连接；若不可达会显示「无法连接 MemScreen 后端」及重试、配置 API 地址入口。

## 项目结构（简要）

```
frontend/flutter/
├── lib/
│   ├── main.dart           # 入口、连接门控
│   ├── app_state.dart      # 全局状态、API 门面
│   ├── config/
│   │   └── api_config.dart # API base URL
│   ├── api/                # 通用客户端与各模块 API
│   │   ├── api_client.dart # HTTP、错误处理、SSE
│   │   ├── chat_api.dart
│   │   ├── process_api.dart
│   │   ├── recording_api.dart
│   │   ├── video_api.dart
│   │   ├── config_api.dart
│   │   └── health_api.dart
│   ├── connection/         # 连接状态与错误提示
│   │   ├── connection_state.dart
│   │   ├── connection_service.dart
│   │   └── connection_gate.dart
│   └── screens/            # Chat / Process / Recording / Video / 设置·关于
├── pubspec.yaml
└── README.md
```

## 功能对应

| 功能     | 页面     | API 对接说明 |
|----------|----------|----------------|
| 对话     | Chat     | POST /chat、POST /chat/stream、模型与历史 |
| 流程分析 | Process  | 会话列表、分析、删除 |
| 录制     | Recording| 开始/停止、状态轮询 |
| 视频     | Video    | 视频列表（同机 path；跨机需后端文件流接口） |
| 设置/关于| Settings | GET /config、关于信息 |

接口详情见 [API_HTTP.md](API_HTTP.md)。

## 可选：CI 中的 API 健康检查

若需在 CI 中验证 API 与 Core 行为，可：

- 在 workflow 中启动 API 服务后调用 `GET /health`，检查返回 `status: ok`。
- 或对少数关键接口（如 `GET /chat/models`、`GET /video/list`）做简单自动化测试。

示例（GitHub Actions）思路：`conda activate MemScreen` → `python -m memscreen.api` 后台启动 → `curl -s http://127.0.0.1:8765/health` 检查。
