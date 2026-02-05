# macOS 前台应用激活方案

## 问题说明

使用 PyInstaller 打包的 Kivy 应用在 macOS 上安装后，双击启动时窗口不会显示。应用实际上在运行（进程存在），但作为后台进程运行，不会自动显示窗口。

## 根本原因

1. **PyInstaller 默认行为**: PyInstaller 在 macOS 上创建的应用默认为后台进程
2. **Info.plist 缺少关键配置**: 缺少 `LSBackgroundOnly` 和 `LSUIElement` 键
3. **应用内部激活失败**: 从应用内部调用 macOS API 激活的可靠性不足

## 解决方案

采用 **Bash 包装脚本** 方案，确保应用作为前台应用启动并激活窗口。

### 实现步骤

#### 1. 创建包装脚本

文件: `packaging/macos/app_wrapper.sh`

```bash
#!/bin/bash
# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 在后台启动实际的可执行文件
"$SCRIPT_DIR/MemScreen.bin" &

# 获取后台进程的 PID
APP_PID=$!

# 等待应用启动
sleep 2

# 使用 AppleScript 激活应用
osascript -e "tell application \"MemScreen\" to activate" 2>/dev/null || true

# 等待后台进程
wait $APP_PID
```

#### 2. 更新 Info.plist

在 `pyinstaller/memscreen_macos.spec` 中添加前台应用配置:

```python
info_plist={
    # ... 其他配置 ...
    'LSBackgroundOnly': False,  # 运行为前台应用
    'LSUIElement': False,  # 显示在 Dock 中并允许获取焦点
    'NSSupportsAutomaticTermination': False,  # 防止自动终止
},
```

#### 3. 在应用内添加激活代码

在 `memscreen/ui/kivy_app.py` 的 `on_start()` 方法中添加:

```python
def on_start(self):
    # 使用 Cocoa API 强制激活应用 (macOS)
    if sys.platform == 'darwin':
        try:
            from Cocoa import NSRunningApplication, NSApplicationActivateIgnoringOtherApps
            app = NSRunningApplication.currentApplication()
            app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
            print("[App] ✓ Activated app using Cocoa API")
        except Exception as e:
            print(f"[App] ⚠ Could not activate with Cocoa: {e}")

    # 请求窗口注意
    try:
        Window.request_attention(window_attention="normal")
    except Exception as e:
        print(f"[App] ⚠ Could not request attention: {e}")
```

#### 4. 自动化构建脚本

文件: `packaging/macos/build_with_wrapper.sh`

```bash
#!/bin/bash
set -e

echo "🔨 Building MemScreen with macOS foreground app support..."

# 1. 使用 PyInstaller 构建
echo "[1/3] Building with PyInstaller..."
pyinstaller pyinstaller/memscreen_macos.spec --noconfirm --clean

# 2. 配置 Info.plist
echo "[2/3] Configuring Info.plist for foreground app..."
plutil -replace LSBackgroundOnly -bool NO dist/MemScreen.app/Contents/Info.plist 2>/dev/null || true
plutil -replace LSUIElement -bool NO dist/MemScreen.app/Contents/Info.plist 2>/dev/null || true
plutil -replace NSSupportsAutomaticTermination -bool NO dist/MemScreen.app/Contents/Info.plist 2>/dev/null || true

# 3. 安装包装脚本
echo "[3/3] Installing activation wrapper..."
chmod +x packaging/macos/app_wrapper.sh
mv dist/MemScreen.app/Contents/MacOS/MemScreen dist/MemScreen.app/Contents/MacOS/MemScreen.bin
cp packaging/macos/app_wrapper.sh dist/MemScreen.app/Contents/MacOS/MemScreen
chmod +x dist/MemScreen.app/Contents/MacOS/MemScreen

echo "✅ Build complete: dist/MemScreen.app"
```

## 使用方法

### 构建应用

```bash
# 构建带包装器的 .app
./packaging/macos/build_with_wrapper.sh

# 或构建完整 DMG
./packaging/macos/build_dmg.sh
```

### 安装和测试

```bash
# 安装到 Applications
cp -R dist/MemScreen.app /Applications/

# 启动应用
open /Applications/MemScreen.app
```

## 技术细节

### 为什么需要包装脚本？

1. **可靠性**: AppleScript 的 `activate` 命令是从外部进程调用的，更可靠
2. **时序**: 包装脚本确保应用完全启动后再尝试激活
3. **独立性**: 不依赖应用内部的代码正确执行

### 文件结构

安装后的应用结构:

```
MemScreen.app/
├── Contents/
│   ├── MacOS/
│   │   ├── MemScreen          # 包装脚本 (主入口)
│   │   └── MemScreen.bin      # 实际的 Python 应用
│   ├── Info.plist             # 包含 LSBackgroundOnly=false
│   └── Resources/
└── ...
```

### 进程名称

启动后，进程名称为 `MemScreen.bin`（这是 Python 解释器的实际名称）。

## 故障排除

### 应用仍然不显示窗口

1. 检查 Info.plist:
   ```bash
   plutil -p /Applications/MemScreen.app/Contents/Info.plist | grep LSBackgroundOnly
   # 应该显示: "LSBackgroundOnly" => 0
   ```

2. 检查包装脚本是否正确安装:
   ```bash
   ls -la /Applications/MemScreen.app/Contents/MacOS/
   # 应该看到: MemScreen 和 MemScreen.bin
   ```

3. 手动测试激活:
   ```bash
   open /Applications/MemScreen.app
   sleep 3
   osascript -e 'tell application "MemScreen" to activate'
   ```

### 查看应用日志

```bash
# 查看最新的 Kivy 日志
tail -100 ~/.kivy/logs/kivy_*.txt | grep -E "(Started|Activated|ERROR)"
```

## 替代方案

### 方案 1: 仅使用 Info.plist

在 Info.plist 中设置 `LSBackgroundOnly: false` 和 `LSUIElement: false`。

**优点**: 简单
**缺点**: 不可靠，某些情况下应用仍不会激活

### 方案 2: 应用内激活

使用 Cocoa API 在应用启动时激活自己。

**优点**: 不依赖外部脚本
**缺点**: PyInstaller 打包的应用中调用可能失败

### 方案 3: py2app

使用 py2app 而不是 PyInstaller。

**优点**: 原生 macOS 工具，更好的集成
**缺点**: 配置复杂，构建时遇到依赖问题

**推荐方案**: Bash 包装脚本（本方案）

## 相关文件

- `packaging/macos/app_wrapper.sh` - 包装脚本
- `packaging/macos/build_with_wrapper.sh` - 构建脚本
- `packaging/macos/build_dmg.sh` - DMG 构建脚本
- `pyinstaller/memscreen_macos.spec` - PyInstaller 配置
- `memscreen/ui/kivy_app.py` - Kivy 应用主类

## 参考资料

- [Apple Developer: Information Property List Key Reference](https://developer.apple.com/documentation/bundleresources/information_property_list)
- [LSBackgroundOnly](https://developer.apple.com/documentation/bundleresources/information_property_list/lsbackgroundonly)
- [PyInstaller macOS Specification](https://pyinstaller.org/en/stable/spec-files.html)
