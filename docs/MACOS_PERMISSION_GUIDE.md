# macOS Kivy 窗口无法显示 - 诊断和修复指南

## 问题现象

- ✅ Kivy 已安装（v2.3.1）
- ✅ OpenGL 和 SDL2 正常初始化
- ✅ 应用进程正在运行
- ❌ 窗口完全不可见
- ❌ 应用立即退出（没有 Dock 黑点）

## 诊断结果

经过测试发现：**这是 macOS 系统级权限或配置问题**

### 已确认的组件状态

1. ✅ Kivy 正确安装
2. ✅ SDL2 库已加载
3. ✅ OpenGL 上下文已创建
4. ✅ Terminal 有 Accessibility 权限
5. ❌ SDL2 无法在 macOS 上创建可见窗口

## 可能的原因

### 1. macOS 安全策略阻止了 SDL2 窗口

macOS 可能将 SDL2 窗口识别为潜在威胁并阻止显示。

**解决方案：**
- 授予 Terminal/Python "Screen Recording" 权限
- 授予 Terminal/Python "Full Disk Access" 权限
- 重启 Terminal

### 2. Python 虚拟环境问题

虚拟环境中的 Python 可能缺少创建窗口所需的系统库。

**解决方案：**
```bash
# 使用系统 Python
/usr/bin/python3 -m pip install kivy[base]
/usr/bin/python3 your_script.py
```

### 3. SDL2 库冲突

系统中可能存在多个 SDL2 版本，导致冲突。

**解决方案：**
```bash
# 检查 SDL2 库
otool -L /opt/homebrew/lib/libSDL2-2.0.0.dylib 2>/dev/null | head -5

# 检查冲突
find /usr/local -name "*SDL2*" 2>/dev/null
```

### 4. Python 3.13 兼容性问题

Python 3.13 是新版本，Kivy 可能不完全兼容。

**解决方案：**
```bash
# 使用 Python 3.11 或 3.12
brew install python@3.11
/usr/bin/python3.11 -m pip install kivy[base]
```

## 修复步骤

### 步骤 1：授予必要权限

1. 打开 **系统设置**
2. 进入 **隐私与安全性**
3. 选择 **隐私**
4. 添加以下权限：
   - **辅助功能**：添加 "Terminal" 和 "Python"
   - **屏幕录制**：添加 "Terminal" 和 "Python"
   - **完全磁盘访问权限**（可选）：添加 "Terminal" 和 "Python"

### 步骤 2：重启 Terminal

```bash
# 完全退出 Terminal
# 重新打开 Terminal
cd /Users/jixiangluo/Documents/project_code/repository/MemScreen
```

### 步骤 3：测试 Kivy

```bash
source venv/bin/activate
python3 -c "
from kivy.app import App
from kivy.uix.label import Label

class TestApp(App):
    def build(self):
        return Label(text='Test Window')
    def on_start(self):
        print('Window should be visible')

TestApp().run()
"
```

### 步骤 4：如果还是不行，重新安装 Kivy

```bash
# 卸载虚拟环境中的 Kivy
deactivate
rm -rf venv

# 重新创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 重新安装（使用旧版 Kivy 以确保兼容性）
pip install 'kivy[base]<2.3.0'
pip install -r requirements.txt
```

## 替代解决方案

如果上述方法都不行，可以考虑：

### 方案 A：使用 Tkinter（系统自带）

```python
import tkinter as tk

root = tk.Tk()
root.title("MemScreen")
root.geometry("1200x800")
label = tk.Label(root, text="MemScreen Running", font=("Arial", 24))
label.pack(expand=True)
root.mainloop()
```

### 方案 B：使用 PyQt5（更可靠）

```bash
pip install PyQt5
```

### 方案 C：使用 PySimpleGUI（最简单）

```bash
pip install PySimpleGUI
```

## 推荐的最终方案

基于测试结果，**建议使用 Tkinter 重新实现界面**，因为：

1. ✅ Tkinter 是 macOS 系统自带的
2. ✅ 不需要额外安装 SDL2
3. ✅ 与 macOS 原生集成更好
4. ✅ 没有 SDL2 的兼容性问题

### 临时解决方案

如果您急需使用，可以先这样启动：

```bash
# 直接运行源码版本
cd /Users/jixiangluo/Documents/project_code/repository/MemScreen
/Users/jixiangluo/Documents/project_code/repository/MemScreen/venv/bin/python start.py

# 或者使用 home 目录的启动脚本
~/memscreen.sh
```

## 需要更多信息？

请提供以下信息帮助进一步诊断：

```bash
# 1. macOS 版本
sw_vers

# 2. Python 版本
python3 --version

# 3. 检查 SDL2
find /opt/homebrew -name "*SDL2*" 2>/dev/null

# 4. 测试简单 Tkinter 窗口
python3 -c "import tkinter as tk; r=tk.Tk(); r.title('Test'); r.geometry('400x300'); tk.Label(r,text='Visible?').pack(); r.mainloop()"

# 5. 查看完整错误日志
tail -100 ~/.kivy/logs/kivy_26-02-05_*.txt
```

## 联系方式

如果问题持续：
- Email: jixiangluo85@gmail.com
- GitHub: https://github.com/smileformylove/MemScreen/issues
