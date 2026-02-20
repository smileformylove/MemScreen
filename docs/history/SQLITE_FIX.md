# ChromaDB sqlite3 

## ❌ 

```
RuntimeError: Your system has an unsupported version of sqlite3.
Chroma requires sqlite3 >= 3.35.0.
```

sqlite3ChromaDB

## 🔍 

sqlite3

```bash
python3 -c "import sqlite3; print(f'sqlite3: {sqlite3.sqlite_version}')"
```

 3.35.0

## ✅ 

### 1 pysqlite3-binary



```bash
pip install pysqlite3-binary
```



```bash
python3 -c "import pysqlite3; print(f'sqlite3: {pysqlite3.sqlite_version}')"
```

### 2sqlite3Ubuntu 20.04+

1sqlite3

```bash
# Ubuntu 20.04
sudo apt-get update
sudo apt-get install -y libsqlite3-dev

# Python
sudo apt-get install --reinstall python3.8
```

### 3sqlite3

sqlite3

```bash
# sqlite3
wget https://www.sqlite.org/2025/sqlite-autoconf-3400000.tar.gz
tar -xzf sqlite-autoconf-3400000.tar.gz
cd sqlite-autoconf-3400000

# 
./configure
make
sudo make install

# 
sudo ldconfig
```

### 4Conda

AnacondaMiniconda

```bash
# pysqlite3-binary
conda install -c conda-forge pysqlite3-binary

# Python
conda update python
```

## 📝 MemScreen

MemScreen**MemScreen-0.5.0-ubuntu-installer.tar.gz**pysqlite3-binary

### MemScreen

MemScreen

```bash
# MemScreen
cd MemScreen-installer

# 
source venv/bin/activate

# pysqlite3-binary
pip install pysqlite3-binary

# 
./run_memscreen.sh
```

## 🔧 

pysqlite3-binaryrequirements.txt

```bash
echo "pysqlite3-binary" >> requirements.txt
pip install -r requirements.txt
```

## 📊 

| ChromaDB  |  sqlite3  |  |
|---------------|------------------|----------|
| < 0.4.0       | 3.31.0          | sqlite3 |
| >= 0.4.0      | 3.35.0          | pysqlite3-binary |
| >= 0.5.0      | 3.37.0          | pysqlite3-binary |

## 💡 



1. ****condavenv
2. ****`pip install --upgrade pysqlite3-binary`
3. ****sqlite3

## 🐛 

### 

****Python

```bash
# Python
which python3

# pip
which pip3

# 
```

### pysqlite3

****Python

```bash
pip uninstall pysqlite3-binary
pip install pysqlite3-binary
```

### 

****

```bash
pip install --upgrade --force-reinstall pysqlite3-binary
```

## ✅ 



```bash
python3 -c "
import sqlite3
import pysqlite3
print(f'sqlite3: {sqlite3.sqlite_version}')
print(f'sqlite3: {pysqlite3.sqlite_version}')
print('✓ sqlite3!' if pysqlite3.sqlite_version >= '3.35.0' else '✗ ')
"
```

## 📚 

- [ChromaDB](https://docs.trychroma.com/)
- [pysqlite3-binary](https://github.com/mkleehammer/pysqlite3)
- [SQLite](https://www.sqlite.org/download.html)

## 🎯 

****

```bash
pip install pysqlite3-binary
```

99%Python
