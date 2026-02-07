# MemScreen 用户使用指南

欢迎使用 MemScreen - 您的个人 AI 屏幕记忆系统！

## 🚀 快速开始

### 启动应用

在 macOS 上启动 MemScreen 后，你会看到：

1. **悬浮球** - 显示在屏幕右上角的圆形图标（猫头鹰 logo）
2. **主窗口** - 启动时自动最小化到后台

### 基本操作

#### 悬浮球控制

- **右键点击悬浮球** - 打开完整功能菜单
- **左键点击悬浮球** - 显示/隐藏主窗口
- **拖拽悬浮球** - 移动到屏幕任意位置

## 📱 功能菜单详解

### 🎯 Select Region（选择录制区域）
- 自定义选择屏幕上的任意区域进行录制
- 显示十字准星辅助线，精确定位
- 支持全屏模式和自定义区域切换

### ⏺ Start Recording（开始录制）
- **录制内容**：屏幕画面 + 可选音频
- **默认设置**：60秒时长，2秒间隔
- **状态指示**：
  - 录制中：悬浮球显示白色圆点 (●)
  - 暂停：悬浮球显示暂停符号 (II)
  - 待机：仅显示 logo

### ⏹ Stop Recording（停止录制）
- 停止当前录制
- 自动保存视频到 `~/.memscreen/videos/`
- 可在 Videos 界面查看所有录制

### ⏸ Pause/Resume（暂停/恢复）
- 暂停录制：保留当前会话，停止捕获
- 恢复录制：继续暂停的录制会话

### 🏠 Recording（录制界面）
显示主窗口的录制界面：
- 实时预览当前录制区域
- 选择录制模式（全屏/自定义区域）
- 选择音频源（系统音频/麦克风/无音频）
- 开始/停止录制控制

### 🎬 Videos（视频库）
查看和管理所有录制的视频：
- 时间轴视图显示所有录制
- 点击视频查看详情
- 播放录制的屏幕内容

### 💬 AI Chat（AI 聊天）
基于屏幕内容的智能对话：
- 自然语言搜索你的屏幕历史
- AI 理解并回答关于屏幕内容的问题
- 完全本地运行，保护隐私

### ⚡ Process（进程挖掘）
查看键盘和鼠标使用统计：
- 按键频率统计
- 鼠标点击热图
- 应用使用时间分析

### ℹ️ About（关于）
- 版本信息
- 项目链接
- 许可证信息

### 🚪 Quit MemScreen（退出）
安全退出应用

## 💡 使用技巧

### 快速录制工作流

1. **启动应用** - 悬浮球自动出现
2. **右键悬浮球** - 打开菜单
3. **选择区域**（可选）- 点击 "Select Region" 精确选择
4. **开始录制** - 点击 "Start Recording"
5. **录制中** - 继续正常工作，悬浮球显示录制状态
6. **停止录制** - 点击 "Stop Recording" 或右键选择停止
7. **查看视频** - 右键菜单 → "Videos"

### 切换界面

悬浮球可以快速切换到任何界面：
- Recording - 录制控制和预览
- Videos - 视频库
- AI Chat - 智能助手
- Process - 使用统计

### 悬浮球位置

- 拖拽到任意位置，避免遮挡重要内容
- 位置会自动保存
- 跨所有桌面空间可见

## 🔒 隐私说明

MemScreen 的核心设计原则是 **100% 本地，100% 私密**：

- ✅ 所有 AI 处理在本地完成
- ✅ 无需云服务或 API 密钥
- ✅ 录制视频存储在本地
- ✅ 完全离线工作（模型下载后）
- ✅ 开源代码，可自行审查

## 📂 数据存储位置

所有用户数据存储在 `~/.memscreen/` 目录：

```
~/.memscreen/
├── db/                    # 数据库
│   ├── screen_capture.db # 屏幕录制
│   ├── audio/            # 音频文件
│   └── input_events.db   # 输入事件
├── videos/               # 录制视频
├── logs/                 # 日志文件
└── switch_screen.txt     # 屏幕切换触发器
```

## ⚙️ 配置

MemScreen 通过以下方式配置：

1. **环境变量** - 设置 AI 后端、模型等
2. **config.yaml** - 主配置文件（首次运行自动生成）

### 环境变量示例

```bash
# 使用 Ollama（默认）
export MEMSCREEN_LLM_BACKEND=ollama

# 使用 vLLM（高性能）
export MEMSCREEN_LLM_BACKEND=vllm
export MEMSCREEN_VLLM_URL=http://localhost:8000
```

## 🆘 常见问题

### Q: 悬浮球不见了？
A: 检查应用是否还在运行。如果已退出，重新运行 `python start.py`

### Q: 录制没有开始？
A:
1. 确保已授予屏幕录制权限（系统偏好设置 → 隐私与安全性 → 屏幕录制）
2. 检查主窗口是否显示错误信息
3. 查看日志：`~/.memscreen/logs/`

### Q: AI 功能不工作？
A:
1. 确保 Ollama 正在运行：`ollama serve`
2. 检查模型是否已下载：`ollama list`
3. 查看完整指南：[docs/INSTALLATION.md](INSTALLATION.md)

### Q: 如何更改录制时长？
A: 在录制界面调整设置，或编辑配置文件

### Q: 录制文件太大？
A:
- 减少录制时长
- 增加捕获间隔（降低帧率）
- 选择特定区域而非全屏

## 📚 更多文档

- [安装指南](INSTALLATION.md) - 详细安装说明
- [Docker 部署](DOCKER.md) - 使用 Docker 运行
- [录制指南](RECORDING_GUIDE.md) - 高级录制功能
- [架构说明](ARCHITECTURE.md) - 系统设计
- [API 文档](CORE_API.md) - 开发者接口

## 💬 获取帮助

- **GitHub Issues**: [报告问题](https://github.com/smileformylove/MemScreen/issues)
- **讨论区**: [提问和建议](https://github.com/smileformylove/MemScreen/discussions)
- **邮件**: jixiangluo85@gmail.com

---

享受你的 AI 屏幕记忆之旅！🦉
