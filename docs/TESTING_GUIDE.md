# 🧪 MemScreen 

## 



## 

### 1.  ✅
```bash
python3 test_all_features.py
```

****
- ✅ Dependencies
- ✅ Database
- ✅ Ollama
- ✅ Output Directory
- ✅ Memory System

### 2. Ollama  ✅
```bash
ollama list
```

****
```
NAME                                ID              SIZE
mxbai-embed-large:latest            468836162de7    669 MB
qwen2.5vl:3b                        fb90415cde1e    3.2 GB
qwen3:1.7b                          8f68893c685c    1.4 GB
```

## 

###  1:  ✅

```bash
memscreen-ui
```

****
- ✅ 
- ✅  Record 
- ✅ 
- ✅ 

****
```
┌────────────────────────────────────────┐
│  MemScreen - Ask Screen Anything       │
├────────────────────────────────────────┤
│ 🔴 Record  💬 Chat  🎬 Videos  🔍  ⚙️  │ ← 
├────────────────────────────────────────┤
│  Recording Settings                    │
│  Duration: [60]                        │
│  Interval: [2.0]                       │
│  Output: [./db/videos]                 │
│  [🔴 Start Recording]                  │
│  [Screen Preview]                      │
└────────────────────────────────────────┘
```

###  2:  ✅

****
1. Duration=60, Interval=2.0
2.  "🔴 Start Recording"
3. 

****
- ✅  "⏹️ Stop Recording"
- ✅  "● Recording..." ()
- ✅ `Recording: 5s | Remaining: 55s | Frames: 2`
- ✅ 

****
```
Button: ⏹️ Stop Recording ()
Status: ● Recording... ()
Info: Recording: 15s | Remaining: 45s | Frames: 7
```

** 10 **

###  3:  ✅

****
 "⏹️ Stop Recording"

****
- ✅  "🔴 Start Recording"
- ✅  "● Saving video..." ()
- ✅ 

****
```
Success
Recording saved:
./db/videos/recording_20250123_235900.mp4
```

###  4:  ✅

****
1.  "🎬 Videos" 
2. 

****
- ✅ 
- ✅ 
- ✅ 

****
```
2025-01-23 23:59 - 00:10  ()
```

****
```
📁 recording_20250123_235900.mp4
⏱️ 10s | 📊 0.5 MB
```

###  5:  ✅

****
1. 
2.  "▶️ Play"

****
- ✅ 
- ✅ 
- ✅ 
- ✅ 

###  6:  ✅

****
1.  "🔍 Search" 
2. "screen", "recording"
3.  "Search"

****
- ✅ 
- ✅ 
- ✅ 

****
```
🔍 Searching for: recording

1. [1 - ]

2. [2 - ]
```

###  7: AI  ✅

****
1.  "💬 Chat" 
2. ""
3.  "Send"

****
- ✅ 
- ✅ AI 
- ✅ 
- ✅ "AI is thinking..." /

****
```
You: 

AI: 10
 ./db/videos/recording_20250123_235900.mp4

 Videos 
```

## 

### 

```
1.  "Start Recording"
   ↓
2. 
   - ImageGrab.grab() 2
   -  OpenCV BGR 
   - 
   ↓
3. 
   - 
   - 
   - 
   ↓
4.  "Stop Recording"
   ↓
5. 
   -  MP4 
   - 
   -  ()
   ↓
6. 
   - INSERT INTO videos
   - 
   ↓
7. 
   - load_video_list()
   - Videos 
```

### 

```
1. 
   ↓
2.  mem.search()
   ↓
3. 
   - ChromaDB 
   - 
   ↓
4. 
```

### AI 

```
1. 
   ↓
2. 
   -  MEMORY_ANSWER_PROMPT
   - 
   - 
   ↓
3.  Ollama
   - POST /api/chat
   - 
   ↓
4.  UI
   - 
   - 
```

## 

### 

```
./db/
├── screen_capture.db          # SQLite 
├── chroma.sqlite3             # 
├── videos/
│   └── recording_20250123_235900.mp4
└── logs/
    └── memscreen_20250123.log
```

### 

```bash
# 
sqlite3 ./db/screen_capture.db "SELECT * FROM videos"

# 
ls -lh ./db/videos/

# 
ls -lh ./db/chroma.sqlite3
```

## 

###  1: 

****
```bash
sqlite3 ./db/screen_capture.db "SELECT * FROM videos"
```

****
- 
-  Videos 
-  "Refresh" 

###  2: 

****
```bash
ls -lh ./db/chroma.sqlite3
```

****
- 
- 
- 

###  3: AI 

****
```bash
curl http://127.0.0.1:11434/api/tags
```

****
-  Ollama 
- 
-  Chat 

## 

### 

|  | FPS | 10 |
|---------|-----|---------------|
| 0.5   | 2   | ~30 MB        |
| 1.0   | 1   | ~15 MB        |
| 2.0   | 0.5 | ~8 MB         |
| 5.0   | 0.2 | ~3 MB         |

### 

- ~2-3
- ~0.5-1

### AI 

- ~3-5
- ~2-3
- 

## 

### 

- [ ] ✅ 
- [ ] ✅ 
- [ ] ✅ 
- [ ] ✅ 
- [ ] ✅ 
- [ ] ✅ 
- [ ] ✅ AI 

### 

- [ ] 5+
- [ ] 
- [ ] 
- [ ] 

## 


```bash
# 1.  UI
memscreen-ui &

# 2. 
sleep 3

# 3. 
python3 test_all_features.py

# 4. 
# -  10 
# -  Videos 
# -  Search 
# -  Chat 
```

## 


1. ✅ 
2. ✅ 
3. ✅ 
4. ✅  AI 
5. ✅ 

---

**** 🎉
