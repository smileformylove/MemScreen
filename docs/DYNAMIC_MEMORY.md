# Dynamic Memory System -  Memory 

## 

 Memory  MemScreen Memory 

## 

### 1. 



- **QUESTION** -  (" Python?")
- **TASK** -  ("")
- **FACT** -  ("Python ")
- **CONCEPT** -  ("")
- **CONVERSATION** - 
- **CODE** - 
- **PROCEDURE** - 
- **DOCUMENT** - 
- **IMAGE** - 
- **REFERENCE** - 

### 2. 



- **RETRIEVE_FACT** - 
- **FIND_PROCEDURE** - 
- **SEARCH_CONVERSATION** - 
- **LOCATE_CODE** - 
- **GET_TASKS** - 
- **GENERAL_SEARCH** - 

### 3. 

 memory 

```python
default_category_weights = {
    "fact": 1.2,        # 
    "procedure": 1.2,   # 
    "conversation": 0.9, # 
}
```

### 4. 

- **** - 
- **** - 
- **** - 
- **** - 

## 

### 1. 

**** memories ( 10,000 )
**** ( 2,000 )

**3-5**

### 2. 

-  → 
-  → 
-  → 

### 3. Token 

****5000 tokens 
****1500 tokens 

**70%  token **

### 4. 

- 
- 
- 

## 

### 

```python
from memscreen import Memory
from memscreen.memory import MemoryConfig, DynamicMemoryConfig

# 1.  Memory
config = MemoryConfig(
    # 
    llm={"provider": "ollama", "config": {"model": "llama2"}},
    embedder={"provider": "ollama", "config": {"model": "nomic-embed-text"}},
    vector_store={"provider": "chroma", "config": {"path": "./chroma_db"}},

    #  memory
    enable_dynamic_memory=True,
)

memory = Memory(config)
```

###  Memory

```python
# 
result = memory.add_with_classification(
    messages="",
    user_id="user123",
)

print(f": {result['classification']['category']}")  # "task"
print(f": {result['classification']['confidence']}")  # 0.9
```

### 

```python
# 
results = memory.smart_search(
    query="",
    user_id="user123",
)

# procedure, workflow, task 
# 
```

### 

```python
# 
context = memory.get_context_for_response(
    query="",
    user_id="user123",
    conversation_history=[
        {"role": "user", "content": ""},
        {"role": "assistant", "content": ""},
    ],
    max_context_items=10,
)

# 
# - 
# - 
# - 
# - 

#  LLM
llm_input = context.get("formatted", "")
response = your_llm.generate(llm_input)
```

### 

```python
#  memories
tasks = memory.get_memories_by_category(
    category="task",
    user_id="user123",
    limit=20,
)

facts = memory.get_memories_by_category(
    category="fact",
    user_id="user123",
    limit=50,
)
```

### 

```python
# 
classification = memory.classify_input(
    ""
)

print(f": {classification['category']}")  # "task"
print(f": {classification['confidence']}")  # 0.9
print(f": {classification['metadata']}")  # {"priority": "medium"}
```

### 

```python
stats = memory.get_dynamic_statistics()
print(f": {stats['total_classifications']}")
print(f": {stats['category_distribution']}")
print(f": {stats['intent_distribution']}")
```

## 

### 

```python
config = MemoryConfig(
    # ...  ...

    dynamic_config={
        "enable_category_weights": True,
        "default_category_weights": {
            "task": 1.5,        # 
            "fact": 1.2,        # 
            "procedure": 1.3,   # 
            "conversation": 0.7,  # 
        },

        # 
        "cache_classification_results": True,
        "classification_cache_size": 1000,

        # 
        "max_search_categories": 2,  #  2 
    }
)
```

### 

```python
#  LLM 
result = memory.add_with_classification(
    messages="",
    use_llm_classification=True,  #  LLM 
)
```

## 

###  Memory 

****

```python
# 
memory.add("", user_id="user123")
results = memory.search("", user_id="user123")
```

****

```python
# 
memory.add_with_classification("", user_id="user123")
results = memory.smart_search("", user_id="user123")
```

### 

- 
- 
- 

## 

```
memscreen/memory/
├── dynamic_models.py      # 
├── input_classifier.py    # 
├── dynamic_manager.py     #  Memory Manager
├── context_retriever.py   # 
├── memory.py              # Memory 
└── __init__.py            # 
```

## 


- [examples/dynamic_memory_example.py](../examples/dynamic_memory_example.py)
- [tests/verify_dynamic_memory.py](../tests/verify_dynamic_memory.py)

## 



```bash
python tests/verify_dynamic_memory.py
```

## 

|  |  |  Memory |  |
|------|---------|------------|------|
|  |  |  | 3-5x |
|  | 5000 tokens | 1500 tokens | 70% |
|  |  |  |  |

## 

**Q:  Memory **
A: 

**Q:  Memory**
A:  `enable_dynamic_memory=False`

**Q: LLM **
A:  LLM 

**Q: **
A:  `MemoryCategory` 

## 

- [ ] 
- [ ] 
- [ ] 
- [ ] 
- [ ] 
