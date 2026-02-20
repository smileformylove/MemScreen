# MemScreen 

## 🎉 

 MemScreen 

1. **** - WAL 
2. **** - LRU  35x
3. **** - 
4. **** - 
5. **** - 

---

## 📊 

### 
```
 (): 14.82 ms
 ():   0.42 ms
: 35.5 
```

### 
```
                          
------------------------------------------------------------
               500ms      80ms       6.25x
               500ms      150ms      3.33x
               500ms      380ms      1.32x
               2000ms     800ms      2.5x
```

---

## 🔧 

### 1.  (`memscreen/storage/sqlite.py`)
```python
class BatchWriter:
    """"""
    - : 50 
    - : 1 
    - WAL : 
    - : NORMAL 10000 
```

****:  50-70%

### 2.  (`memscreen/cache.py`)
```python
class IntelligentCache:
    """ LRU """
    - : 1000 
    - TTL: 5 
    - 
    - 
```

****:  35.5x

### 3.  (`memscreen/embeddings/ollama.py`)
```python
def embed_batch(self, texts: list):
    """"""
    - ThreadPoolExecutor: 4 
    - : 
    - : 4x (4)
```

****:  60-80%

### 4.  (`memscreen/llm/model_router.py`)
```python
class IntelligentModelRouter:
    """"""
    - 4  (TINY/SMALL/MEDIUM/LARGE)
    - : 7 
    - : 
```

****:  6x

### 5.  (`memscreen/prompts/chat_prompts.py`)
```python
class ChatPromptBuilder:
    """"""
    - 4  (///)
    - 
    - 
```

****: 

---

## 📁 /

### 
1. `memscreen/cache.py` - 
2. `memscreen/llm/model_router.py` - 
3. `memscreen/prompts/chat_prompts.py` - 
4. `test_performance.py` - 
5. `test_model_routing.py` - 
6. `demo_chat_routing.py` - 
7. `CHAT_OPTIMIZATION.md` - 

### 
1. `memscreen/storage/sqlite.py` -  WAL 
2. `memscreen/memory/memory.py` - 
3. `memscreen/embeddings/base.py` - 
4. `memscreen/embeddings/ollama.py` - 
5. `memscreen/presenters/chat_presenter.py` - 

---

## 🚀 

### 
```python
from memscreen import Memory, MemoryConfig

# 
memory = Memory(MemoryConfig())

# 
memory.add("", user_id="test")  #  TINY 
memory.add("", user_id="test")  #  MEDIUM 
```

### 
```python
config = MemoryConfig(
    # 
    enable_batch_writing=True,      # 
    optimization_enabled=True,         # 
    skip_simple_fact_extraction=True,  # 
    enable_search_cache=True,          # 
    batch_size=50,                     # 
)
```

---

## 📈 

### 
- Python: 3.13
- : qwen2.5vl:3b, gemma2:2b, qwen2:7b
- : SQLite with WAL mode
- CPU: Apple M4

### 
```
                              
------------------------------------------------------------
          200ms      46ms      4.3x
 ()            15ms       15ms      -
 ()      15ms       0.42ms    35.5x
10      180s       86s       2.1x
          500ms      80ms      6.25x
          500ms      380ms     1.3x
```

---

## 💡 

### ✅ 
- 
- 
- 
- 

### ✅ 
- 
- 
- 
- WAL 

### ✅ 
- 
- 
- 
- 

### ✅ 
- 
- 
- 
- 

---

## 🎯 

### 1. 
```python
# TINY (2B)  - :
- 
- 
- 
- 

# SMALL (3B)  - :
- 
- 
- 
- 

# MEDIUM (7B)  - :
- 
- 
- 
- 

# LARGE (14B+)  - :
- 
- 
- 
```

### 2. 
```python
# :
# 1. 
# 2. 
# 3. 

# :
memory.search("", user_id="user1")  # 
memory.search("Python", user_id="user1")  # 

# :
memory.search(f"{datetime.now()}", ...)  # 
memory.search(unique_query, ...)  # 
```

### 3. 
```python
# 
config.batch_size = 100  # 

# 
_search_cache = IntelligentCache(max_size=2000)  # 

#  TTL
_search_cache = IntelligentCache(default_ttl=600)  # 10 TTL
```

---

## 🐛 

1. ****: 
2. ****: 
3. ****: 
4. ****: 

---

## 🔮 

1. ****: 
2. ****: 
3. **A/B **: 
4. ****: 
5. ****: 

---

## 📞 

:
- Email: jixiangluo85@gmail.com
- GitHub: https://github.com/smileformylove/MemScreen/issues

---

****: 1.0.0
****: 2026-01-31
****: MIT
