# 

## 📁 

`memscreen/file_loader.py` 

## ✨ 

### 1. 
- ****: UTF-8, UTF-8-sig, GBK, GB2312, GB18030, Big5, Big5-HKSCS, Shift-JIS, EUC-JP, EUC-KR, Latin-1
- ****:  charset-normalizer  chardet 
- ****: 68.4% (13/19 )

### 2. 
- ✅ 
- ✅ 
- ✅  Windows  Unix 

### 3. 
-  BOM 
- 
- 

## 🔧 API 

### 

```python
from memscreen.file_loader import FileLoader

# 
content = FileLoader.read_file_clean('/path/to/file.txt')
print(content)
```

### 

```python
# 
content, encoding = FileLoader.read_file('/path/to/file.txt')
print(f": {encoding}")
print(f": {content}")

# 
filename = FileLoader.get_filename('/path/to/.txt')
print(f": {filename}")
```

## 📊 



```bash
# 
python -c "
from memscreen.file_loader import FileLoader
content = FileLoader.read_file_clean('~/Desktop//.txt')
print('✓ ')
print(f': {content}')
"
```

## 🎯 

|  |  |  |
|------|------|------|
| UTF-8 |  | ✅  |
| UTF-8-sig |  | ✅  |
| GBK |  | ✅  |
| GB2312 |  | ✅  |
| GB18030 |  | ✅  |
| Big5 |  | ✅  |
| Big5-HKSCS |  | ⚠️  |
| Shift-JIS |  | ✅  |
| EUC-JP |  | ⚠️  |
| EUC-KR |  | ⚠️  |
| Latin-1 |  | ✅  |

## 💡 

###  1: 

```python
from memscreen.file_loader import FileLoader

# 
content = FileLoader.read_file_clean('~/Documents/.txt')
```

###  2: 

```python
# GBK 
content1 = FileLoader.read_file_clean('/path/to/gbk.txt')

# Big5 
content2 = FileLoader.read_file_clean('/path/to/big5.txt')

# Shift-JIS 
content3 = FileLoader.read_file_clean('/path/to/japanese.txt')
```

###  3: 

```python
from memscreen.file_loader import FileLoader

def process_file(file_path):
    """"""
    try:
        content = FileLoader.read_file_clean(file_path)
        # 
        return content
    except Exception as e:
        print(f"Error: {e}")
        return None
```

## 🔍 



```python
import logging
logging.basicConfig(level=logging.DEBUG)

#  FileLoader
content = FileLoader.read_file_clean('/path/to/file.txt')
```



## ⚠️ 

1. ****:  `charset-normalizer`  `chardet`
   ```bash
   pip install charset-normalizer chardet
   ```

2. ****: >100MB

3. ****: 

## 📈 

- **** (<1MB): 
- **** (1-10MB): < 1
- **** (>10MB): 1-3

## 🎓 

### 

```python
#!/usr/bin/env python3
from memscreen.file_loader import FileLoader
import os

def main():
    # 
    test_files = [
        "~/Documents/1.txt",
        "~/Downloads/data.csv",
        "/tmp/test.txt"
    ]

    for file_path in test_files:
        # 
        file_path = os.path.expanduser(file_path)

        if not os.path.exists(file_path):
            print(f"⚠️  : {file_path}")
            continue

        try:
            # 
            content = FileLoader.read_file_clean(file_path)
            filename = FileLoader.get_filename(file_path)

            print(f"✅ {filename}")
            print(f"   : {len(content)} ")
            print(f"   : {content[:50]}...")
            print()

        except Exception as e:
            print(f"❌ : {file_path}")
            print(f"   : {e}")
            print()

if __name__ == '__main__':
    main()
```

## 📞 


- [README.md](README.md) - 
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - 
