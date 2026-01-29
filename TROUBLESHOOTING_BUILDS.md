# 🔧 MemScreen 构建问题排查和修复

## 问题分析

### 发现的问题

1. **GitHub Actions 工作流缺少依赖安装**
   - ❌ 工作流只安装了 PyInstaller，没有安装项目依赖
   - ❌ PyInstaller 无法找到必需的模块（torch, kivy, pydantic 等）
   - ❌ 导致构建失败或生成空的可执行文件

2. **Windows 压缩命令错误**
   - ❌ 使用了 tar 命令，Windows 上不可用
   - ❌ 应该使用 PowerShell 的 Compress-Archive

3. **Artifact 名称冲突**
   - ❌ 所有平台使用相同的 artifact 名称
   - ❌ 导致文件互相覆盖

4. **Release 文件路径错误**
   - ❌ 使用了 `artifacts/**/*/*.zip` 路径模式
   - ❌ 实际路径应该是 `artifacts/**/*.zip`

## 已应用的修复

### 1. GitHub Actions 工作流修复

```yaml
# 添加了项目依赖安装步骤
- name: Install project dependencies
  shell: bash
  run: |
    if [ -f requirements.txt ]; then
      pip install -r requirements.txt
    else
      pip install torch torchvision pydantic ttkthemes ollama mss matplotlib ...
    fi
```

### 2. Windows 压缩修复

```yaml
# 使用 PowerShell Compress-Archive
- name: Create distribution archive (Windows)
  if: matrix.os == 'windows-latest'
  shell: pwsh
  run: |
    cd dist
    Compress-Archive -Path MemScreen -DestinationPath MemScreen-0.4.0-windows.zip
```

### 3. Artifact 名称修复

```yaml
# 为每个平台使用唯一的名称
name: memscreen-${{ matrix.platform }}
```

### 4. 调试输出

```yaml
# 添加构建输出列表
- name: List build outputs
  shell: bash
  run: |
    ls -la dist/
```

## 验证修复

### 方式 1：通过 GitHub Web UI

1. 访问 Actions 页面：
   ```
   https://github.com/smileformylove/MemScreen/actions
   ```

2. 查看最新的 "Build Release" 工作流运行

3. 检查每个平台的构建状态：
   - ✅ Build on macos-latest
   - ✅ Build on windows-latest
   - ✅ Build on ubuntu-latest

4. 点击 "Create Release" job，查看是否成功

### 方式 2：使用脚本检查

```bash
./check_build.sh
```

### 方式 3：手动检查 Releases 页面

访问：
```
https://github.com/smileformylove/MemScreen/releases
```

检查是否有：
- 📦 v0.4.1 Release
- 📥 三个平台的可下载文件：
  - MemScreen-0.4.0-macos.zip
  - MemScreen-0.4.0-windows.zip
  - MemScreen-0.4.0-linux.zip

## 当前状态

### 已触发构建

- ✅ 标签 `v0.4.1` 已创建并推送
- ✅ GitHub Actions 工作流已触发
- ⏳ 正在构建中（预计 15-30 分钟）

### 构建内容

每个平台的构建包含：

**macOS**:
- MemScreen.app 应用包
- 所有必需的依赖和库
- 预计大小：150-250 MB

**Windows**:
- MemScreen 文件夹（包含 MemScreen.exe）
- 所有必需的 DLL 和依赖
- 预计大小：150-300 MB

**Linux**:
- MemScreen 可执行文件
- 所有必需的共享库
- 预计大小：100-200 MB

## 如果构建仍然失败

### 备选方案 1：手动本地构建

```bash
# macOS
./build_and_release.sh

# 输出在 dist/MemScreen-0.4.1-macos.zip
```

然后手动上传到 GitHub Release。

### 备选方案 2：简化构建

如果完整构建有问题，可以先发布一个最小版本：

1. 只构建 macOS 版本（最稳定）
2. 使用 PyInstaller 的单文件模式：
   ```bash
   pyinstaller --onefile start.py
   ```

### 备选方案 3：发布源代码

如果二进制构建持续失败，可以：
1. 发布源代码压缩包
2. 提供详细的安装说明
3. 用户使用 `pip install` 安装

## 监控构建进度

### 查看实时日志

1. 访问 Actions 页面
2. 点击最新的工作流运行
3. 点击每个 job 查看详细日志
4. 关注以下关键步骤：
   - "Install project dependencies" - 检查是否有错误
   - "Build with PyInstaller" - 查看构建输出
   - "List build outputs" - 确认文件已生成
   - "Create Release" - 确认 Release 已创建

### 常见错误和解决方案

**错误 1: ModuleNotFoundError**
```
解决方案：确保 requirements.txt 包含所有依赖
```

**错误 2: Permission denied**
```
解决方案：在脚本中添加 chmod +x
```

**错误 3: Out of memory**
```
解决方案：减少并行构建，或使用更大的 GitHub Actions runner
```

**错误 4: Timeout**
```
解决方案：添加 timeout-minutes 参数到工作流
```

## 下一步操作

### 短期（立即）

1. ⏳ 等待当前构建完成（15-30 分钟）
2. 🔍 检查构建日志，确认没有错误
3. ✅ 验证 Release 已创建并包含文件

### 中期（如果构建成功）

1. 📥 下载并测试 macOS 版本
2. 🔍 检查是否有依赖问题
3. 📝 更新文档，添加故障排除部分

### 长期（优化）

1. ⚡ 优化构建速度（缓存、并行化）
2. 🧪 添加自动化测试
3. 📦 添加代码签名
4. 🔄 设置 nightly builds

## 相关链接

- **Actions**: https://github.com/smileformylove/MemScreen/actions
- **Releases**: https://github.com/smileformylove/MemScreen/releases
- **工作流文件**: [.github/workflows/build.yml](.github/workflows/build.yml)
- **构建配置**: [MemScreen.spec](MemScreen.spec)

## 总结

主要问题是 GitHub Actions 工作流缺少依赖安装。已修复并重新触发构建。

**预计结果**：
- 15-30 分钟后，v0.4.1 Release 将包含三个平台的可下载文件
- 用户可以直接下载预编译版本，无需安装 Python

**如果失败**：
- 使用 `./build_and_release.sh` 手动构建
- 或联系开发者获取帮助
