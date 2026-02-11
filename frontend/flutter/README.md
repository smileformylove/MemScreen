# MemScreen Flutter 前端

MemScreen 的可选 Flutter 客户端，通过 HTTP API 连接后端。默认 API 地址：`http://127.0.0.1:8765`。

## 快速运行

1. **启动后端 API**（在仓库根目录，Conda 环境 `MemScreen`）：
   ```bash
   conda activate MemScreen
   python -m memscreen.api
   ```

2. **运行 Flutter 应用**：
   ```bash
   flutter pub get
   flutter run
   ```

若未生成平台工程，可先执行：`flutter create . --project-name memscreen_flutter`。

## 配置

- API 地址：默认 `http://127.0.0.1:8765`。连接失败时可在应用内点击「配置 API 地址」修改。
- 更多说明见仓库 [docs/FLUTTER.md](../../docs/FLUTTER.md)。
