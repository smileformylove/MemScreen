# MemScreen v0.4.0 - 

## 📊 

### ✅  (11/13)
- ✅ Ollama
- ✅ Vision
- ✅ Embedder
- ✅ 
- ✅ Agent
- ✅ 
- ✅ 
- ✅ JSON
- ✅ Token
- ✅ 

### ⚠️  (2)
1. **LlmFactory API** - `create``get_instance`
2. **EmbedderFactory API** - `create``get_instance`



---

## 🎯 

### qwen2.5vl:3b 

#### ✅ 
- **** -  ~80-90%
- **** - 
- **** - 0.2-1.630-50
- **Token** - 200+
- **JSON** - JSON

#### ⚠️ 
- **** - 
- **** - Context window ~4K tokens
- **** - 
- **** - 

---

## 🔧 

### 1. Agent



****: `memscreen/presenters/agent_executor_v2.py`

****:
- ✅ JSON
- ✅ Token
- ✅ Fallback
- ✅ 
- ✅ Temperature

****:
```python
# Token
self.max_tokens = 512  # 
self.context_window = 4096  # 
self.temperature = 0.6  # 

# Vision
vision_prompt = "200"

# JSON
summary_prompt = "150..."
```

### 2. 

#### : `diagnose_and_fix.py`
- Ollama
- 
- Token
- JSONVision
- 

#### : `optimize_local_models.py`
- 
- 
- 
- 
- 

#### : `test_system_comprehensive.py`
- 8
- 13
- 
- 

---

## 💡 

### 📝 

#### ✅ 

****:
```
""
""
""
```

****:
```
"Python"
"asyncio"
""
```

****:
```
""
"5"
```

#### ❌ 

****:
```
"
"
```
→ : 3B

****:
```
""
```
→ : context

****:
```
"11[100]"
```
→ : token

---

## ⚙️ 

###  ()

 `agent_executor_v2.py` :
```python
self.max_tokens = 200
self.temperature = 0.4

# Vision settings
"num_predict": 150,
"temperature": 0.5
```

****:
- : 5-15
- : 

###  ()

```python
self.max_tokens = 400
self.temperature = 0.7

# Vision settings
"num_predict": 400,
"temperature": 0.8
```

****:
- : 30-60
- : 

###  ()

```python
self.max_tokens = 300
self.temperature = 0.6

# Vision settings
"num_predict": 300,
"temperature": 0.6
```

****:
- : 15-40
- : 

---

## 🚀 

### 1. 
```python
#  _execute_search 
return {
    "results": search_results[:3]  # 3
}
```

### 2. 
```python
#  _execute_summarize_simple 
content = item.get("content", "")[:300]  # 300
```

### 3. 
```python
# ❌ 
"UIJSON"

# ✅ 
""
```

### 4. 
```python
# ❌ 
"50"

# ✅ 
"" → ""
```

---

## 📈 

### 

7B+
- ✅ 
- ✅ >1000
- ✅ 
- ✅ >90%

### 

**** (3B):
- RAM: 8GB
- VRAM: 4GB
- : 

**** (7B):
- RAM: 16GB
- VRAM: 8GB
- : qwen2.5vl:7b
- : 

**** (13B+):
- RAM: 32GB
- VRAM: 16GB
- : mixtral:8x7b
- : 

### 
```bash
# 7B Vision Model
ollama pull qwen2.5vl:7b

# 
ollama pull llama3.2:11b

# 
ollama pull mixtral:8x7b
```

---

## 🐛 

### 1: 

****:  >60

****:
- 
- 
- 

****:
```bash
# Ollama
ollama list

# Ollama
# (macOS)
brew services restart ollama

# 
```

### 2: JSON

****: `json.JSONDecodeError`

****: JSON

****:
-  `agent_executor_v2.py` ()
- 
- 

### 3: 

****: 

****:
- 
- /
- 

****:
- 
- 
- 

### 4: 

****: `OutOfMemoryError`

****:
```python
# batch size
"num_predict": 150  # 300150

# 
search_results[:3]  # [:5][:3]

# 
```

---

## 📚 

### 
- `memscreen/presenters/agent_executor.py` - Agent
- `memscreen/presenters/agent_executor_v2.py` - Agent

### 
- `test_system_comprehensive.py` - 
- `diagnose_and_fix.py` - 
- `optimize_local_models.py` - 
- `test_screen_analysis.py` - 

### 
- `README.md` - 
- `LOCAL_MODEL_OPTIMIZATION.md` - 

---

## 🎓 

### DO ✅
1. 
2. 3-5
3. 200
4. 10-60
5. JSON
6. 
7. 

### DON'T ❌
1. 
2. 
3. JSON
4. 
5. 
6. 

---

## 🎉 

MemScreen v0.4.0  qwen2.5vl:3b 

✅ ****:
- 
- 
- 
- 

⚠️ ****:
- 5-10
- 
- 

❌ ****:
- 
- >1000
- 
- 

****:  `agent_executor_v2.py`

---

*: 2026-01-29*
*MemScreen: v0.4.0*
*: qwen2.5vl:3b*
