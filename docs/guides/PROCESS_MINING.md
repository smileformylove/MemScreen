# 🎯 键鼠记录功能测试指南

## ✅ 问题已修复

### 发现的问题
1. **数据库是空的** - ProcessMiningPresenter初始化失败
2. **导入错误** - 使用了相对导入（`from ...input_tracker`）
3. **参数错误** - 传递了不存在的`memory_system`参数

### 已完成的修复
1. ✅ 修复导入问题 - 改为绝对导入
2. ✅ 修复参数问题 - 移除`memory_system`
3. ✅ 添加pynput到PyInstaller hiddenimports
4. ✅ 添加平台特定模块（`_darwin`）

---

## 🧪 测试步骤

### 1. 启动应用
应用已经在运行中，或重新打开：
```bash
open /Applications/MemScreen.app
```

### 2. 进入Process Mining标签
点击左侧导航栏的 "Process Mining"

### 3. 点击 "Start Tracking"
- 按钮应该变为红色 "Stop Tracking"
- 显示 "Tracking started" 事件
- 状态更新

### 4. 进行一些操作（非常重要！）
**在后台运行应用时：**
- 打开文本编辑器（TextEdit、Notes等）
- 输入一些文字
- 点击鼠标几次
- 移动鼠标

**注意**：你需要授权应用访问辅助功能：
- 系统偏好设置 → 隐私与安全性 → 辅助功能
- 确保终端或MemScreen.app有权限

### 5. 点击 "Stop Tracking"
- 按钮恢复为紫色 "Start Tracking"
- 显示 "Tracking stopped" 事件

### 6. 查看Session History
- 应该显示一个会话记录
- 包含事件数量、击键次数、点击次数

### 7. 点击会话记录查看详情
- 显示时间范围
- 显示详细事件列表

---

## 🔍 验证数据库

```bash
# 检查数据库中的记录
sqlite3 ~/Documents/project_code/repository/MemScreen/db/input_events.db \
  "SELECT COUNT(*) FROM keyboard_mouse_logs;"

# 查看最近的记录
sqlite3 ~/Documents/project_code/repository/MemScreen/db/input_events.db \
  "SELECT * FROM keyboard_mouse_logs ORDER BY operate_time DESC LIMIT 10;"
```

---

## ⚠️ 权限问题

如果点击"Start Tracking"后没有反应，可能是因为缺少辅助功能权限：

### macOS 辅助功能授权

1. 打开 **系统偏好设置**
2. 进入 **隐私与安全性**
3. 选择 **辅助功能**
4. 找到终端或MemScreen.app
5. 确保已勾选 ✅

### 重新启动应用

授权后：
```bash
# 关闭应用
pkill -9 MemScreen

# 重新打开
open /Applications/MemScreen.app
```

---

## 📊 预期结果

成功运行后，您应该看到：

```
Current Session:
[14:30:15] Tracking started
[14:30:18] Key: 'H' (keypress)
[14:30:18] Key: 'e' (keypress)
[14:30:18] Key: 'l' (keypress)
[14:30:18] Key: 'l' (keypress)
[14:30:18] Key: 'o' (keypress)
[14:30:19] Button pressed (left click)
[14:30:45] Tracking stopped

Events: 7 | Keystrokes: 5 | Mouse Clicks: 1
```

Session History:
- Session #1: 14:30:15 - 14:30:45 | 7 events (5 keys, 1 click)

---

## 🐛 故障排除

### 问题1: 点击Start Tracking没反应
**原因**: 缺少辅助功能权限
**解决**: 授权辅助功能（见上方）

### 问题2: 没有事件记录
**原因**: pynput监听器可能没有启动
**解决**: 检查Console.app查看错误日志

### 问题3: Session History为空
**原因**: 事件保存到数据库失败
**解决**: 检查数据库权限和路径

---

## 📝 技术细节

### 修改的文件
1. **memscreen/presenters/process_mining_presenter.py**
   - 修复相对导入 → 绝对导入

2. **memscreen/ui/kivy_app.py**
   - 移除不存在的`memory_system`参数
   - 添加presenter初始化

3. **pyinstaller/memscreen_macos.spec**
   - 添加pynput相关模块到hiddenimports

### 数据库位置
- 主数据库: `./db/input_events.db`
- 表名: `keyboard_mouse_logs`

---

**现在请测试键鼠记录功能并告诉我结果！** 🎯
