# 🎉 MemScreen v0.4.1 - GitHub Release 创建指南

## ✅ 构建已完成！

文件已准备好：
```
dist/MemScreen-0.4.1-macos.zip (18 MB)
```

## 📤 创建 GitHub Release 步骤

### 方式 1：通过浏览器（推荐）

1. **访问创建 Release 页面**
   ```
   https://github.com/smileformylove/MemScreen/releases/new
   ```

2. **填写 Release 信息**

   - **Choose a tag**: 选择 `v0.4.1`
   - **Release title**:
     ```
     MemScreen v0.4.1 - macOS
     ```

   - **Describe this release**:
     ```markdown
     ## 🎉 MemScreen v0.4.1 - macOS Release

     **专为 macOS 用户优化**

     ### 📥 下载
     - `MemScreen-0.4.1-macos.zip` (18 MB)

     ### 🚀 快速安装

     1. 下载并解压 `MemScreen-0.4.1-macos.zip`
     2. 将 `MemScreen.app` 拖到应用程序文件夹
     3. 双击启动 `MemScreen.app`
     4. 首次运行会自动检查并安装 Ollama

     ### ⚙️ 首次运行

     应用会自动：
     - ✅ 检查 Ollama 是否已安装
     - ✅ 下载 AI 模型（qwen2.5vl:3b, mxbai-embed-large）
     - ✅ 配置所有必要的依赖

     ### 📋 系统要求

     - **操作系统**: macOS 10.15 (Catalina) 或更高版本
     - **内存**: 8GB 最低（16GB 推荐）
     - **存储**: 5GB 可用空间
     - **软件**: Ollama（会自动提示安装）

     ### 🔧 安装 Ollama

     如果还没有安装 Ollama：

     ```bash
     # 使用 Homebrew
     brew install ollama

     # 或访问官网下载
     # https://ollama.com/download
     ```

     ### 🤖 下载 AI 模型

     首次运行时，应用会自动下载所需的 AI 模型（约 2.5GB）。

     也可以手动下载：

     ```bash
     ollama pull qwen2.5vl:3b
     ollama pull mxbai-embed-large
     ```

     ### 📚 更多信息

     - [完整文档](https://github.com/smileformylove/MemScreen#readme)
     - [问题反馈](https://github.com/smileformylove/MemScreen/issues)
     - [使用指南](https://github.com/smileformylove/MemScreen/wiki)

     ---
     **注意**: 此版本仅适用于 macOS。Windows 和 Linux 版本将在未来发布。
     ```

3. **上传文件**

   勾选 `Set as a pre-release`（可选）

4. **发布**

   点击绿色的 **"Publish release"** 按钮

### 方式 2：使用命令行（需要 GitHub CLI）

如果安装了 `gh` 命令行工具：

```bash
gh release create v0.4.1 \
  dist/MemScreen-0.4.1-macos.zip \
  --title "MemScreen v0.4.1 - macOS" \
  --notes "See release notes on the page"
```

## 🎯 发布后验证

1. 访问 Releases 页面确认：
   ```
   https://github.com/smileformylove/MemScreen/releases
   ```

2. 下载文件测试：
   - 下载 MemScreen-0.4.1-macos.zip
   - 解压缩
   - 双击测试是否能正常启动

3. 分享链接：
   ```
   https://github.com/smileformylove/MemScreen/releases/tag/v0.4.1
   ```

## 📊 预期结果

发布成功后，用户可以：
- ✅ 直接从 GitHub 下载预编译的 macOS 应用
- ✅ 无需安装 Python 或任何依赖
- ✅ 解压即用，双击启动

## 🔗 快速链接

- **创建 Release**: https://github.com/smileformylove/MemScreen/releases/new
- **查看 Releases**: https://github.com/smileformylove/MemScreen/releases
- **构建状态**: https://github.com/smileformylove/MemScreen/actions
