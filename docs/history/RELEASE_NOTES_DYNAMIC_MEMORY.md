#  Memory  - 

## 

 Memory  MemScreen 

## ✅ 

### 1. 

|  |  |  |
|------|------|------|
|  | [dynamic_models.py](memscreen/memory/dynamic_models.py) |  |
|  | [input_classifier.py](memscreen/memory/input_classifier.py) |  |
|  | [dynamic_manager.py](memscreen/memory/dynamic_manager.py) |  |
|  | [context_retriever.py](memscreen/memory/context_retriever.py) |  |
| Memory  | [memory.py](memscreen/memory/memory.py) |  |
|  | [kivy_app.py](memscreen/ui/kivy_app.py) |  |

### 2. 

#### 15
- ✅ question - 
- ✅ task - 
- ✅ fact - 
- ✅ concept - 
- ✅ code - 
- ✅ procedure - 
- ✅ conversation - 
- ✅ greeting - 
- ✅ document - 
- ✅ image - 
- ✅ ...

#### 7
- ✅ retrieve_fact - 
- ✅ find_procedure - 
- ✅ search_conversation - 
- ✅ locate_code - 
- ✅ find_document - 
- ✅ get_tasks - 
- ✅ general_search - 

####  API 
```python
memory.add_with_classification()     # 
memory.smart_search()                # 
memory.get_context_for_response()    # 
memory.get_memories_by_category()    # 
memory.classify_input()              # 
memory.get_dynamic_statistics()      # 
```

### 3. 

```
✅ 
✅ 
✅ 
✅ 
✅ 
✅ 
✅ 
✅ 
```

## 📊 

|  |  |  Memory |  |
|------|---------|------------|------|
|  |  (10K) |  (2K) | **3-5x** ⚡ |
|  | 5000 tokens | 1500 tokens | **-70%** 💰 |
|  |  |  | **** 🎯 |

## 🌐 

- ✅ 
- ✅ 
- ✅ 

## 🚀 

### 

```python
from memscreen import Memory
from memscreen.memory import MemoryConfig

#  kivy_app.py 
config = MemoryConfig(
    enable_dynamic_memory=True,  # ← 
    dynamic_config={
        "enable_auto_classification": True,
        "enable_intent_classification": True,
        "enable_category_weights": True,
    }
)
memory = Memory(config)
```

###  Memory

```python
result = memory.add_with_classification(
    "",
    user_id="user123",
)
#  "task" 
```

### 

```python
results = memory.smart_search(
    "",
    user_id="user123",
)
#  procedure, workflow, task 
#  3-5 
```

### 

```python
context = memory.get_context_for_response(
    "",
    user_id="user123",
    conversation_history=[...],
)
# 
#  70% tokens
```

## 📚 

- ****: [docs/DYNAMIC_MEMORY.md](docs/DYNAMIC_MEMORY.md)
- ****: [examples/dynamic_memory_example.py](examples/dynamic_memory_example.py)
- ****: [demo_dynamic_memory.py](demo_dynamic_memory.py)
- ****: [quick_test_dynamic_memory.py](quick_test_dynamic_memory.py)
- ****: [test_memory_integration.py](test_memory_integration.py)

## 🧪 



```bash
# 
python demo_dynamic_memory.py

# 
python quick_test_dynamic_memory.py

# 
python test_memory_integration.py

# 
python tests/verify_dynamic_memory.py
```

## 🔄 

✅ ****
- 
- 
- 

## 📝 

```
memscreen/memory/
├── __init__.py              ← 
├── models.py                ← 
├── memory.py                ← 
├── dynamic_models.py        ← 
├── input_classifier.py      ← 
├── dynamic_manager.py       ← 
└── context_retriever.py     ← 

memscreen/ui/
└── kivy_app.py              ← 

docs/
└── DYNAMIC_MEMORY.md        ← 

examples/
└── dynamic_memory_example.py ← 

tests/
├── test_dynamic_memory.py    ← 
└── verify_dynamic_memory.py  ← 

/
├── demo_dynamic_memory.py     ← 
├── quick_test_dynamic_memory.py ← 
└── test_memory_integration.py  ← 
```

## 🎉 

1. ✅ 
2. ✅ 
3. ✅ 
4. 🚀 

## 💡 

-  Memory 
- 
- 
- 

---

****: v0.5.0
****: 2026-02-02
****: Jixiang Luo
****: MIT
