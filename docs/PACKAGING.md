# MemScreen 

## 📦 

```
MemScreen/
├── pyproject.toml          # 
├── MANIFEST.in             # 
├── README.md              # 
├── LICENSE                # MIT 
├── PACKAGING.md           # 
├── memscreen/             # Python 
│   ├── __init__.py       # 
│   ├── memscreen.py       # 
│   ├── chat_ui.py        # 
│   ├── screenshot_ui.py   # 
│   ├── process_mining.py # 
│   ├── memory.py         # 
│   ├── chroma.py         # 
│   ├── telemetry.py      # 
│   ├── utils.py          # 
│   ├── prompts.py        # AI 
│   └── test_memory.py   # 
└── dist/                 # git
    ├── memscreen-0.1.0-py3-none-any.whl
    └── memscreen-0.1.0.tar.gz
```

## 🚀 

###  1:  PyPI 

```bash
pip install memscreen
```

###  2:  GitHub 

```bash
pip install git+https://github.com/smileformylove/MemScreen.git
```

###  3:  wheel 

```bash
#  wheel 
python -m build

# 
pip install dist/memscreen-0.1.0-py3-none-any.whl
```

###  4: 

```bash
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
pip install -e .
```

## 📋 



|  |  |  |
|------|------|------|
| `memscreen` |  |  |
| `memscreen-chat` |  |  |
| `memscreen-screenshots` |  |  |
| `memscreen-process-mining` |  |  |

## 🔧 

- **Python**: >= 3.8
- ****: macOS / Linux / Windows
- ****:
  - RAM: 4GB+ 8GB+
  - GPU:  AI 
- ****:  [Ollama](https://ollama.com) 

## 📦 



```
torch>=2.0.0          # PyTorch 
torchvision>=0.15.0   # 
pydantic>=2.0.0       # 
ttkthemes>=3.0.0      # GUI 
ollama>=0.3.0         #  LLM 
mss>=9.0.0           # 
matplotlib>=3.0.0     # 
openai>=1.0.0         # AI API 
opencv-python>=4.0.0   # 
Pillow>=9.0.0         # 
numpy>=1.20.0         # 
easyocr>=1.0.0        # OCR 
pynput>=1.6.0         # 
```

## 🛠️ 

### 

```bash
# 
pip install --upgrade build setuptools wheel

#  wheel 
python -m build

#  dist/ 
# - memscreen-0.1.0-py3-none-any.whl
# - memscreen-0.1.0.tar.gz
```

###  PyPI

```bash
# 1.  twine
pip install twine

# 2. 
twine check dist/*

# 3.  PyPI
twine upload --repository testpypi dist/*

# 4.  PyPI
twine upload dist/*
```

### 

```bash
pip install -e ".[dev]"
```


- pytest
- black
- flake8

## 📚 

### 
```bash
# 
memscreen

# 
memscreen --duration 120 --interval 5 --screenshot-interval 1.0
```

### 
```bash
memscreen-chat
```

### 
```bash
memscreen-screenshots
```

### 
```bash
memscreen-process-mining
```

## ⚠️ 

1. **** AI 
   ```bash
   ollama pull qwen3:1.7b
   ollama pull qwen2.5vl:3b
   ollama pull mxbai-embed-large:latest
   ```

2. ****
   - 
   - macOS:  →  → 
   - Windows: 
   - Linux: 

3. **GPU **
   ```bash
   #  CUDA  PyTorch
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

## 🐛 

### 
```bash
# 
pip uninstall memscreen
pip install memscreen --force-reinstall
```

### macOS
```bash
# 
#  →  →  → 
#  Terminal  Python 
```

### Ollama 
```bash
#  Ollama 
ollama serve

# 
ollama list
```

## 📖 

- ****: [README.md](README.md)
- ****: https://github.com/smileformylove/MemScreen
- ****: https://github.com/smileformylove/MemScreen/issues
- ****: MIT
