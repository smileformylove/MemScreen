# Chat 

## 🎯 
 chat 270M/3B/7B

## ✅ 

### 1. **** (`memscreen/llm/model_router.py`)

#### 
```
┌─────────────────────────────────────────────────────────────┐
│ Model Tiers                                                    │
├──────────┬──────────┬──────────┬──────────┬─────────────────────┤
│ TINY     │ SMALL    │ MEDIUM   │ LARGE    │                     │
│ 270M-1B  │ 1B-3B    │ 3B-7B    │ 7B-14B   │                     │
├──────────┼──────────┼──────────┼──────────┼─────────────────────┤
│      │  │  │  │                     │
│  │          │          │          │                     │
│  │          │          │          │                     │
│          │  │  │  │                     │
│          │          │  │          │                     │
├──────────┼──────────┼──────────┼──────────┼─────────────────────┤
│ ~80ms    │ ~150ms   │ ~400ms   │ ~800ms   │             │
│ 0.75     │ 0.85     │ 0.92     │ 0.96     │             │
└──────────┴──────────┴──────────┴──────────┴─────────────────────┘
```

#### 
- **** (0-0.3): 
- **** (0-0.2): 
- **** (0-0.3): //
- **** (0-0.15): 
- **** (0-0.1): 

#### 
```python
 (0-0.15)
→ TINY (gemma2:2b, qwen2:1.5b)
  • : "", "Hi"
  • : ""
  • : ""

 (0.15-0.35)
→ SMALL (qwen2.5vl:3b, llama3.2:3b)
  • : ""
  • : ""
  • : ""

 (0.35-0.6)
→ MEDIUM (qwen2:7b, gemma2:9b)
  • : ""
  • : ""
  • : ""

 (0.6+)
→ LARGE (qwen2.5:14b, llama3:70b)
  • : ""
  • : ""
```

### 2. **** (`memscreen/prompts/chat_prompts.py`)

#### 

****
```python
" MemScreen AI "
" "
```

****
```python
" {} ..."
"..."
"..."
```

****
```python
"
"
"
"
```

### 3. ****



|  | Temperature | Num Predict |  |
|---------|-------------|--------------|------|
|  | 0.3 | 50 tokens |  |
|  | 0.2 | 100 tokens |  |
|  | 0.5-0.7 | 256 tokens |  |
|  | 0.5 | 1024 tokens |  |
|  | 0.9 | 512 tokens |  |

### 4. ****

```python
#  → TINY 
: ""
: gemma2:2b (80ms)

#  → SMALL 
: ""
: qwen2.5vl:3b (150ms)

#  → MEDIUM 
: ""
: qwen2:7b (380ms)

#  → TINY  ()
: ""
: gemma2:2b (80ms)
```

## 📊 

### 
- ****: 80ms  ( 2B )
- ****: 150ms  ( 3B )
- ****: 400ms  ( 7B )
- ****: 800ms  ( 14B )

### 
-  0.75 
- 
- 

### 
- ✅ 
- ✅ 
- ✅ 
- ✅ 
- ✅ 

## 🔧 

### 
```python
from memscreen.presenters.chat_presenter import ChatPresenter

presenter = ChatPresenter()
presenter.send_message("")  #  TINY 
presenter.send_message("")  #  MEDIUM 
```

### 
```python
available_models = [
    "gemma2:2b",      # TINY tier
    "qwen2.5vl:3b",   # SMALL tier
    "qwen2:7b",       # MEDIUM tier
    "qwen2.5:14b",    # LARGE tier
]
```

## 🎁 

### 1. ****
```python
from memscreen.llm.model_router import get_router

router = get_router(available_models)
analysis = router.analyzer.analyze("")
print(f": {analysis.complexity_score}")
print(f": {analysis.tier}")
print(f": {analysis.reasoning_required}")
```

### 2. ****
```python
from memscreen.prompts.chat_prompts import ChatPromptBuilder

# 
prompt = ChatPromptBuilder.build_with_context(
    context="...",
    user_message="",
    query_type="question"
)
```

## 📝 

### 
-  7B 
- 500-2000ms
- 

### 
- 80ms (2B ) - ** 6-25 **
- 150ms (3B ) - ** 3-13 **
- 400ms (7B ) - ****
- 800ms (14B ) - ****

## 🚀 

1. ****: 
2. ****: 
3. **A/B **: 
4. ****: 

---

****:
- `memscreen/llm/model_router.py` - 
- `memscreen/prompts/chat_prompts.py` - 
- `memscreen/presenters/chat_presenter.py` - 
- `test_model_routing.py` - 

****: 
