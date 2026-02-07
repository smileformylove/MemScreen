# 录屏悬浮球功能说明

## 功能概述

录屏悬浮球是一个精致的小型圆形控件,用于在录屏时提供便捷的控制方式。

- **macOS**: 使用原生 NSPanel 实现真正的独立悬浮窗口,始终置顶于所有窗口
- **其他平台**: 采用窗口缩小方案,悬浮球显示在缩小后的窗口中

## 使用方法

### 1. 开始录屏
- 在主界面点击"Start Recording"按钮
- 主窗口自动最小化
- 悬浮球出现在屏幕右上角(可拖动到任意位置)

### 2. 悬浮球操作 (macOS 原生版本)

#### 拖拽移动
- 鼠标左键按住悬浮球可以拖动到屏幕任意位置
- 悬浮球会自动检测拖动阈值,区分点击和拖动

#### 左键点击
- **左键单击**: 显示主窗口并恢复焦点
- 可在设置中更改为其他功能(如切换录制/暂停)

#### 右键菜单
- 右键点击悬浮球打开控制菜单
- 菜单选项包括:
  - **⏹ Stop Recording**: 停止录屏并保存
  - **⏸ Pause / ▶ Resume**: 暂停/继续录屏
  - **🏠 Main Window**: 返回主窗口
  - **录制信息**: 显示帧数和时长

### 3. 停止录屏
- 方式1: 右键悬浮球 → Stop Recording
- 方式2: 左键点击悬浮球 → 主窗口 → Stop Recording
- 方式3: 通过 Dock 图标恢复主窗口 → Stop Recording

## 视觉状态

悬浮球会根据录屏状态显示不同的颜色和图标:

| 状态 | 颜色 | 图标 | 说明 |
|------|------|------|------|
| 准备就绪 | 紫色 | ○ | 未开始录制 |
| 录制中 | 红色 | ● | 正在录制 |
| 暂停 | 黄色 | II | 录制暂停 |

## 技术实现

### 文件结构
```
memscreen/ui/
├── floating_ball.py        # K版本悬浮球组件 (跨平台)
├── floating_ball_native.py # macOS 原生悬浮球 (NSPanel)
├── floating_ball_simple.py # 简化版悬浮球
└── kivy_app.py             # 录屏界面集成
```

### macOS 原生实现

#### FloatingBallWindow 类 ([memscreen/ui/floating_ball_native.py](memscreen/ui/floating_ball_native.py))

**核心特性**:
1. **独立窗口**: 继承自 NSPanel,完全独立于主窗口
2. **始终置顶**: 使用 NSFloatingWindowLevel 确保在所有窗口之上
3. **跨空间显示**: 在所有桌面空间和全屏应用中都可见
4. **智能交互**: 区分拖动和点击,提供流畅的用户体验

**关键技术点**:

```python
# 窗口级别设置
self.setLevel_(NSWindowLevelFloating)

# 面板行为
self.setFloatingPanel_(True)  # 悬浮在其他窗口之上
self.setBecomesKeyOnlyIfNeeded_(True)  # 不窃取焦点
self.setHidesOnDeactivate_(False)  # 失去焦点时不隐藏

# 空间行为
self.setCollectionBehavior_(
    (1 << 6) |  # NSWindowCollectionBehaviorCanJoinAllSpaces
    (1 << 8) |  # NSWindowCollectionBehaviorFullScreenAuxiliary
    (1 << 10)   # NSWindowCollectionBehaviorIgnoresCycle
)
```

**交互处理**:
- **拖动检测**: 使用 5 像素的拖动阈值区分点击和拖动
- **左键点击**: 触发主窗口回调,恢复应用界面
- **右键菜单**: 提供完整的录制控制功能

### 跨平台实现

当原生悬浮球不可用时,自动降级到窗口缩小方案:

1. **FloatingBallWindow类** ([memscreen/ui/floating_ball.py](memscreen/ui/floating_ball.py))
   - 继承自Kivy的Widget
   - 支持拖拽和右键菜单
   - 录制状态管理
   - 视觉效果(渐变、高光、脉冲动画)

2. **RecordingScreen集成**
   - `_show_floating_ball()`: 显示悬浮球并将主窗口缩小到120×120px
   - `_hide_floating_ball()`: 隐藏悬浮球并恢复主窗口大小

### 设计特点
- **圆形设计**: 80px直径的圆形悬浮球
- **视觉效果**: 渐变背景、高光反射、半透明外发光
- **动画**: 录制时60fps脉冲动画 (Kivy版本)
- **交互**: 流畅的拖拽体验
- **状态反馈**: 颜色和图标直观显示录制状态

## 使用建议

### macOS 用户
1. **悬浮球位置**: 可以拖动到屏幕任意位置,切换应用后仍然可见
2. **快速控制**: 右键菜单提供所有常用操作
3. **返回主界面**: 左键点击悬浮球或选择"Main Window"
4. **多空间支持**: 在不同桌面空间和全屏应用中都能看到悬浮球

### 其他平台用户
1. **窗口位置**: 初始位置在右上角,可以拖动窗口到任意位置
2. **悬浮球位置**: 可以在窗口内拖动悬浮球
3. **快速控制**: 右键菜单提供所有常用操作
4. **返回主界面**: 点击"Main Window"恢复完整界面

## 技术限制

### macOS 原生实现
- ✅ 真正的独立悬浮窗口
- ✅ 始终置顶于所有应用
- ✅ 在所有桌面空间可见
- ✅ 在全屏应用中可见
- ✅ 不依赖主窗口状态

### 跨平台实现
由于Kivy框架的限制,非 macOS 平台采用**窗口缩小**方案:
- 优点: 简单、可靠、跨平台兼容
- 缺点: 悬浮球仍在窗口内,不是真正的独立窗口

## 未来改进方向

- [ ] 添加暂停/继续功能的完整实现
- [ ] 支持自定义悬浮球大小和颜色
- [ ] 添加计时器显示(录制时长)
- [ ] 支持快捷键控制
- [ ] 添加更多右键菜单选项(如截图、标记区域等)
- [x] ~~考虑使用原生API实现真正的独立悬浮窗口~~ (macOS 已实现)
- [ ] Windows 原生实现 (使用 Layered Window)
- [ ] Linux 原生实现 (使用 X11/Wayland)
