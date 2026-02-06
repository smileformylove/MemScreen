# 🔑 键鼠记录权限配置指南

## 问题诊断

测试结果显示：
- ✅ pynput库已成功导入
- ✅ InputTracker初始化成功
- ✅ 数据库表已创建
- ❌ **没有捕获到任何事件** - 原因：缺少macOS辅助功能权限

---

## 🎯 解决方案

### 方案1：授予Terminal权限（开发环境测试）

1. **打开系统偏好设置**
   ```bash
   open /System/Library/PreferencePanes/Security.prefPane
   ```

2. **进入 隐私与安全性 → 辅助功能**

3. **找到 "终端" (Terminal) 并勾选 ✅**

4. **重启终端**（重要！）
   - 关闭所有终端窗口
   - 重新打开终端

5. **再次测试**
   ```bash
   cd ~/Documents/project_code/repository/MemScreen
   python3 test_pynput_simple.py
   ```
   在测试运行期间打字或点击

---

### 方案2：创建一个简单的测试应用

由于macOS的安全限制，打包的应用需要特殊签名才能请求辅助功能权限。

**当前限制**：
- 命令行工具（如打包的应用）无法动态请求辅助功能权限
- 必须在系统设置中手动授权
- 即使授权，PyInstaller打包的应用可能仍有限制

---

## 🔄 推荐的测试方法

### 在开发环境中测试（推荐）

键鼠记录功能在开发环境中最可靠：

```bash
cd ~/Documents/project_code/repository/MemScreen
python3 start.py
```

**优势**：
- ✅ 不需要PyInstaller打包
- ✅ pynput更容易获取权限
- ✅ 可以实时调试

**测试步骤**：
1. 启动应用：`python3 start.py`
2. 进入Process Mining标签
3. 点击"Start Tracking"
4. 打字和点击鼠标
5. 点击"Stop Tracking"
6. 查看Session History

---

## 🔧 永久解决方案

要使打包应用的键鼠记录功能正常工作，需要：

### 选项A：代码签名（推荐）
1. 为应用签名（Apple Developer账号）
2. 在Info.plist中声明辅助功能使用
3. 用户首次运行时自动弹出权限请求

### 选项B：手动授权
1. 用户运行应用前，先在系统设置中授权
2. 提供清晰的授权指南文档

### 选项C：替代方案
使用macOS原生API（CGEvent）代替pynput：
- 需要编写Objective-C/Swift扩展
- 更好的权限处理
- 更可靠

---

## 📝 当前状态

### ✅ 已完成
- ProcessMiningPresenter逻辑完善
- UI界面完整
- 数据库结构正确
- pynput库已包含

### ⚠️ 限制
- macOS安全限制阻止pynput捕获输入
- 需要手动授权辅助功能权限
- 打包应用难以动态请求权限

---

## 🎯 建议

**立即测试**：使用开发环境测试键鼠记录功能

```bash
cd ~/Documents/project_code/repository/MemScreen
python3 start.py
```

1. 授予Terminal辅助功能权限
2. 重启终端
3. 运行上述命令
4. 测试Process Mining功能

这样您可以看到完整的键鼠记录功能是否正常工作！

---

**如果开发环境测试成功，我们可以讨论如何为打包应用实现相同的功能。** 🚀
