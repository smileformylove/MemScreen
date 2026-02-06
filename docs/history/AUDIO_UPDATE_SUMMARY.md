# 音频录制功能实现总结

## 概述

成功为 MemScreen 添加了统一的音频录制功能，支持麦克风和系统音频录制，并已集成到录制界面中。

## 实现的功能

### 1. 音频录制模块 (`memscreen/audio/`)

#### 核心类：`AudioRecorder`
- **麦克风录制**：跨平台支持，自动检测可用的音频输入设备
- **系统音频录制**：
  - macOS：支持通过 BlackHole 虚拟音频设备录制系统音频
  - Windows：预留 WASAPI loopback 支持（实验性）
  - Linux：预留 PulseAudio/JACK 支持
- **实时音频监控**：提供音频电平监测（0.0-1.0）
- **后台录制**：使用独立线程进行音频录制，不影响主程序性能

#### 音频源枚举：`AudioSource`
```python
class AudioSource(Enum):
    MICROPHONE = "microphone"    # 麦克风录音
    SYSTEM_AUDIO = "system_audio"  # 系统音频
    NONE = "none"                # 无音频
```

### 2. Presenter 层集成 (`memscreen/presenters/recording_presenter.py`)

#### 新增功能
- **音频源选择**：`set_audio_source(source: AudioSource)`
- **可用音频源查询**：`get_audio_sources()`
- **音视频同步录制**：在开始屏幕录制时自动启动音频录制
- **自动合并**：停止录制时自动将音频和视频合并
- **数据库更新**：存储音频源信息和音频文件路径

#### 数据库架构更新
```sql
ALTER TABLE recordings ADD COLUMN audio_file TEXT;
ALTER TABLE recordings ADD COLUMN audio_source TEXT;
```

### 3. UI 界面集成 (`memscreen/ui/kivy_app.py`)

#### RecordingScreen 更新
- **音频源选择下拉菜单**：
  - No Audio（无音频）
  - Microphone（麦克风）
  - System Audio（系统音频）
- **状态显示**：录制状态显示当前使用的音频源
- **统一控制**：音频源选择与录制模式选择并列展示

#### UI 布局
```
┌──────────────────────────────────────┐
│      Screen Recording                │
├──────────────────────────────────────┤
│                                      │
│         Preview Area                 │
│                                      │
├──────────────────────────────────────┤
│ [Screen Mode] [Audio] [Record Btn]  │
└──────────────────────────────────────┘
```

## 文件结构

```
MemScreen/
├── memscreen/
│   ├── audio/
│   │   ├── __init__.py              # 音频模块包初始化
│   │   └── audio_recorder.py        # 核心音频录制器
│   ├── presenters/
│   │   └── recording_presenter.py   # 更新：集成音频录制
│   └── ui/
│       └── kivy_app.py              # 更新：添加音频选择UI
├── docs/
│   └── AUDIO_RECORDING.md           # 完整使用文档
├── test_audio_recording.py          # 音频功能测试脚本
└── pyproject.toml                   # 更新：添加依赖
```

## 依赖项

### 新增依赖
```toml
"pyaudio>=0.2.11",      # 音频录制核心库
"moviepy>=1.0.3",       # 音视频合并
```

### 平台特定依赖

**macOS:**
```bash
brew install portaudio          # PyAudio 所需
brew install blackhole-2ch      # 系统音频录制（可选）
```

**Windows:**
- PyAudio 直接安装
- 系统音频录制需要额外配置

**Linux:**
```bash
sudo apt-get install python3-pyaudio portaudio19-dev
```

## 测试结果

### 自动化测试 (`test_audio_recording.py`)
```
============================================================
Test Summary
============================================================
✓ Device listing: PASSED
✓ Microphone recording: PASSED
ℹ System audio: SKIPPED (requires setup)
```

### 测试功能
1. **设备列表**：正确检测到 4 个音频设备（2 输入 + 2 输出）
2. **麦克风录制**：
   - 成功录制 3 秒音频
   - 捕获 130 帧
   - 文件大小：260 KB
   - 音频电平监控正常

## 使用方法

### 基本使用流程
1. 打开 MemScreen，导航到 **Recording** 标签页
2. 从 **Audio** 下拉菜单选择音频源：
   - **No Audio**：仅录制视频（默认）
   - **Microphone**：录制麦克风音频
   - **System Audio**：录制系统音频（需要配置）
3. 选择录制模式（全屏或自定义区域）
4. 点击 **Start Recording** 开始录制
5. 点击 **Stop Recording** 停止录制
6. 音频会自动与视频合并

### 编程接口
```python
from memscreen.audio import AudioRecorder, AudioSource

# 创建录音器
recorder = AudioRecorder(output_dir="./audio")

# 列出可用设备
devices = recorder.list_audio_devices()

# 开始录音
recorder.start_recording(AudioSource.MICROPHONE)

# 监控音频电平
level = recorder.get_audio_level()

# 停止录音
audio_file = recorder.stop_recording()

# 清理资源
recorder.cleanup()
```

## 技术规格

### 音频参数
- **格式**：WAV（未压缩）
- **采样率**：44.1 kHz
- **声道**：单声道
- **位深度**：16-bit
- **缓冲区大小**：1024 帧

### 视频参数
- **编码器**：H.264 (mp4v)
- **音频编码器**：AAC（合并后）

## 架构设计

### MVP 模式遵循
- **Model**：`AudioRecorder`（音频数据管理）
- **View**：`RecordingScreen`（UI 展示）
- **Presenter**：`RecordingPresenter`（业务逻辑协调）

### 线程模型
- **主线程**：UI 更新
- **录制线程**：屏幕捕获
- **音频线程**：音频录制
- **保存线程**：音视频合并（后台）

## 未来增强功能

1. **音频可视化**：实时波形显示
2. **多音源录制**：同时录制麦克风和系统音频
3. **纯音频模式**：仅录制音频，不录视频
4. **音频编辑**：裁剪、淡入淡出等
5. **增强 Windows 支持**：完整的 WASAPI loopback 支持
6. **音频增益控制**：调整音频输入灵敏度
7. **降噪功能**：自动背景噪声抑制

## 故障排除

### 常见问题

**Q: 提示 "No audio devices found"**
- 确保麦克风已连接
- 检查系统隐私设置（麦克风权限）
- 运行测试脚本查看可用设备

**Q: 系统音频录制失败**
- macOS：安装 BlackHole (`brew install blackhole-2ch`)
- Windows/Linux：参考详细文档配置

**Q: 音频和视频不同步**
- 减少录制间隔
- 关闭 CPU 密集型程序
- 检查磁盘空间

## 文档

- **详细使用文档**：[docs/AUDIO_RECORDING.md](docs/AUDIO_RECORDING.md)
- **测试脚本**：[test_audio_recording.py](test_audio_recording.py)
- **API 文档**：参见各模块 docstring

## 贡献者

- 实现者：Jixiang Luo (jixiangluo85@gmail.com)
- 日期：2026-02-01
- 许可证：MIT

## 总结

成功实现了统一的音频录制系统，具有以下特点：

1. **模块化设计**：独立的音频模块，易于维护和扩展
2. **跨平台支持**：macOS、Windows、Linux
3. **无缝集成**：与现有录制系统完美融合
4. **用户友好**：直观的 UI，简单的操作流程
5. **完整文档**：详细的使用说明和故障排除指南
6. **测试验证**：自动化测试确保功能可靠性

该功能为 MemScreen 增加了重要的多媒体录制能力，使用户能够创建包含音频的完整屏幕录制内容。
