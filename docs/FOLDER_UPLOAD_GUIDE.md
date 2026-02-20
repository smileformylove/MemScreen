# 

## 

MemScreen 

## 

- ✅ **** -  macOSWindowsLinux
- ✅ **** - 
- ✅ **** - 
- ✅ **** - 
- ✅ **** -  UTF-8GBKBig5 
- ✅ **** - 
- ✅ **** - 

## 

### 1. 

```bash
python -m memscreen.ui.kivy_app
```

### 2. "Load Folder"

 **"📁 Load Folder"** 

### 3. 


- 
- 
-  **"Upload Folder"** 

### 4. 


- **** - 
- **** - 
- **** - //

### 5. 


- 
- 
- 

## 

### 

- `.txt`, `.md`, `.markdown`, `.rst`
- `.py`, `.js`, `.ts`, `.java`, `.c`, `.cpp`, `.h`, `.go`, `.rs`
- `.json`, `.yaml`, `.yml`, `.xml`, `.toml`, `.ini`, `.cfg`
- `.sh`, `.bash`, `.zsh`, `.ps1`, `.bat`
- `.csv`, `.log`, `.sql`
- `.html`, `.css`, `.scss`
- `.tex`, `.bib`

### 

- `.png`, `.jpg`, `.gif`, `.svg`
- `.mp4`, `.avi`, `.mov`
- `.zip`, `.tar`, `.gz`, `.rar`
- `.exe`, `.dll`, `.so`

### 


- `__pycache__`, `.git`, `.svn`, `node_modules`
- `venv`, `.venv`, `env`, `.env`
- `.idea`, `.vscode`, `dist`, `build`, `target`

## 



- ****: 100 
- ****: 50 MB

 `memscreen/ui/kivy_app.py`  `_process_folder_batch()` 

## 

### 

- ✅ `////`
- ✅ `.txt`, `.json`
- ✅ UTF-8GBKGB2312Big5 
- ✅ 

### 


- UTF-8 (with/without BOM)
- GBK / GB2312 / GB18030 ()
- Big5 / Big5-HKSCS ()
- Shift-JIS / EUC-JP ()
- EUC-KR ()
- Latin-1 ()

## 

###  1: 

```
/
├── README.md          ← 
├── requirements.txt   ← 
├── src/
│   ├── main.py       ← 
│   └── utils.py      ← 
├── tests/
│   └── test_main.py  ← 
├── .git/             ← 
└── __pycache__/      ← 
```

###  2: 

```
/
├── /
│   ├── .md     ← 
│   └── .md     ← 
├── /
│   ├── example.py    ← 
│   └── config.json   ← 
└── /
    └── .txt      ← 
```

## 

### 

****:
- 
- 
- 

### 

****:
- 
- 
- 

****:
- `ls -l filename`
- 
- 

### 

****:
-  Cancel 
- 
- 

### 

****:
- locale
- macOS:  Terminal 
- Windows:  PowerShell  CMD UTF-8 

## 

### 

```
UI  (Kivy)
  ↓
FolderProcessor ()
  ↓
FileLoader ()
  ↓
Memory  ()
```

### 

- **** (< 1 KB): 
- **** (1-10 MB): < 1 /
- **** (> 10 MB): 1-3 /

### 

- 
- UI  Clock.schedule_once
- 

## 

### 



```bash
# 
python test/test_folder_processor.py

# 
python test/test_batch_upload_manual.py
```

### API 

 FolderProcessor

```python
from memscreen.file_processor import FolderProcessor

# 
processor = FolderProcessor(
    root_folder='/path/to/folder',
    callback=lambda current, total, filename, status: print(f"{current}/{total}: {filename}")
)

# 
results = processor.process_folder(
    recursive=True,
    max_files=100,
    max_size_mb=50
)

# 
print(f": {results['success_count']}")
print(f": {results['failed_count']}")
```

## 

### v0.4.0 (2025-01-30)

- ✨ 
- ✨ 
- ✨ 
- ✨ 
- ✨ 
- 🐛  macOS AppleScript 
- 🔄 
- 📝 

## 


1. 
2. 
3.  Issue 
