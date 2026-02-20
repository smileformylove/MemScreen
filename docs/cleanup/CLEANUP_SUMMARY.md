# 

## 

### 1. 
- ✅ `demo_optimization.py` → `examples/demo_optimization.py`
- ✅ `integration_guide.py` → `docs/integration_guide.py`
- ✅ `test_integration.py` → `tests/test_integration.py`
- ✅ `test_recording_flow.py` → `tests/test_recording_flow.py`

### 2. 
- ✅ `db/` -  ~/.memscreen/db/
- ✅ `dist/` - 
- ✅ `build/` - 

### 3. 
- ✅ `PROJECT_STRUCTURE.md` - 
- ✅  `.gitignore` - 
- ✅  `README.md` - 

## 

```
MemScreen/
├── start.py                 # 
├── config_example.yaml      # 
├── README.md               # 
├── LICENSE                 # MIT 
├── PROJECT_STRUCTURE.md    # 
├── run.sh                  # 
│
├── memscreen/              # 
│   ├── ui/                # UI 
│   ├── presenters/        # 
│   ├── memory/            # 
│   └── ...
│
├── tests/                 # 
│   ├── test_*.py
│   └── README.md
│
├── examples/              # 
│   └── demo_*.py
│
├── docs/                  # 
│   └── *.md
│
├── setup/                 # 
├── assets/                # 
└── .github/               # CI/CD
```

## 

```
~/.memscreen/
├── db/                    # 
│   ├── screen_capture.db
│   ├── memories.db
│   └── chroma.sqlite3
├── videos/                # 
├── audio/                 # 
└── logs/                  # 
```

## Git 

`.gitignore` 
- Python 
-  (*.db, *.sqlite)
-  (dist/, build/)
- IDE 
-  (.memscreen/)

## 

### 
```bash
# 
python -m pytest tests/

# 
python tests/test_hybrid_vision.py
python tests/test_integration.py
python tests/test_recording_flow.py
```

### 
```bash
# 
python examples/demo_optimization.py

# 
python examples/demo_chat_integration.py
python examples/demo_visual_agent.py
```

## 

```bash
# 1
python start.py

# 2
./run.sh
```

## 


- ✅  `tests/`
- ✅  `examples/`
- ✅  `docs/`
- ✅ 
- ✅ .gitignore 


