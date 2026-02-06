# ChromaDB sqlite3 版本问题解决方案

## ❌ 问题描述

```
RuntimeError: Your system has an unsupported version of sqlite3.
Chroma requires sqlite3 >= 3.35.0.
```

这个错误表示您的系统sqlite3版本太低，无法满足ChromaDB的要求。

## 🔍 检查版本

运行以下命令检查当前的sqlite3版本：

```bash
python3 -c "import sqlite3; print(f'sqlite3版本: {sqlite3.sqlite_version}')"
```

如果版本低于 3.35.0，则需要升级。

## ✅ 解决方案

### 方法1：安装 pysqlite3-binary（推荐）

这是最简单的方法，适用于大多数情况：

```bash
pip install pysqlite3-binary
```

验证安装：

```bash
python3 -c "import pysqlite3; print(f'新版sqlite3: {pysqlite3.sqlite_version}')"
```

### 方法2：升级系统sqlite3（Ubuntu 20.04+）

如果方法1不工作，可以升级系统sqlite3：

```bash
# Ubuntu 20.04
sudo apt-get update
sudo apt-get install -y libsqlite3-dev

# 重新安装Python
sudo apt-get install --reinstall python3.8
```

### 方法3：编译安装sqlite3（高级用户）

如果需要最新的sqlite3版本：

```bash
# 下载sqlite3源码
wget https://www.sqlite.org/2025/sqlite-autoconf-3400000.tar.gz
tar -xzf sqlite-autoconf-3400000.tar.gz
cd sqlite-autoconf-3400000

# 编译安装
./configure
make
sudo make install

# 更新链接
sudo ldconfig
```

### 方法4：使用Conda环境（推荐）

如果使用Anaconda或Miniconda：

```bash
# 安装pysqlite3-binary
conda install -c conda-forge pysqlite3-binary

# 或者升级整个Python
conda update python
```

## 📝 在MemScreen中的应用

此问题已在MemScreen的安装脚本中修复。如果您使用的是**MemScreen-0.5.0-ubuntu-installer.tar.gz**或更高版本，会自动安装pysqlite3-binary。

### 验证MemScreen安装

如果您已安装MemScreen但遇到此问题：

```bash
# 进入MemScreen目录
cd MemScreen-installer

# 激活虚拟环境
source venv/bin/activate

# 安装pysqlite3-binary
pip install pysqlite3-binary

# 重新运行
./run_memscreen.sh
```

## 🔧 永久修复

将pysqlite3-binary添加到requirements.txt：

```bash
echo "pysqlite3-binary" >> requirements.txt
pip install -r requirements.txt
```

## 📊 版本对应表

| ChromaDB 版本 | 最低 sqlite3 版本 | 推荐方案 |
|---------------|------------------|----------|
| < 0.4.0       | 3.31.0          | 系统sqlite3 |
| >= 0.4.0      | 3.35.0          | pysqlite3-binary |
| >= 0.5.0      | 3.37.0          | pysqlite3-binary |

## 💡 预防措施

为了避免此问题，建议：

1. **使用虚拟环境**：conda或venv
2. **定期更新**：`pip install --upgrade pysqlite3-binary`
3. **检查版本**：在安装前检查sqlite3版本

## 🐛 故障排除

### 问题：安装后仍然报错

**解决方案**：确保在正确的Python环境中安装

```bash
# 检查使用的Python
which python3

# 检查pip位置
which pip3

# 应该指向同一个环境
```

### 问题：无法导入pysqlite3

**解决方案**：重装Python包

```bash
pip uninstall pysqlite3-binary
pip install pysqlite3-binary
```

### 问题：仍然使用旧版本

**解决方案**：强制重装

```bash
pip install --upgrade --force-reinstall pysqlite3-binary
```

## ✅ 验证修复

运行以下命令验证问题已解决：

```bash
python3 -c "
import sqlite3
import pysqlite3
print(f'系统sqlite3: {sqlite3.sqlite_version}')
print(f'新版sqlite3: {pysqlite3.sqlite_version}')
print('✓ sqlite3版本满足要求!' if pysqlite3.sqlite_version >= '3.35.0' else '✗ 版本仍然太低')
"
```

## 📚 相关资源

- [ChromaDB文档](https://docs.trychroma.com/)
- [pysqlite3-binary](https://github.com/mkleehammer/pysqlite3)
- [SQLite下载](https://www.sqlite.org/download.html)

## 🎯 总结

**最简单的解决方案：**

```bash
pip install pysqlite3-binary
```

这应该能解决99%的情况。如果问题仍然存在，请检查是否在正确的Python环境中安装。
