#  Agent - 

## 

 Agent  Memory 

## 

### 1. 

 15 

```
- question     → 
- task         → 
- fact         → 
- code         → 
- procedure    → 
- conversation → 
- greeting     → 
- ...
```

### 2. 

 7 

```
- retrieve_fact      →  fact, concept, reference
- find_procedure     →  procedure, workflow, task
- search_conversation →  conversation, general
- locate_code        → 
- find_document      → 
- get_tasks          → 
- general_search     → 
```

### 3. 



|  |  |  |
|---------|---------|------------|
| question | retrieve_fact | smart_search |
| task | - | manage_task |
| code | - | code_assistant |
| procedure | find_procedure | find_procedure |
| greeting | - | greet |
| ... | ... | ... |

## 

### 

```python
from memscreen.agent import IntelligentAgent
from memscreen.memory import Memory, MemoryConfig
import asyncio

# 1.  Memory
config = MemoryConfig(
    enable_dynamic_memory=True,
    # ... 
)
memory = Memory(config)

# 2.  Agent
agent = IntelligentAgent(
    memory_system=memory,
    llm_client=your_llm_client,
    enable_classification=True,
)

# 3. 
async def handle_user_input():
    result = await agent.process_input("")
    print(result)
    # : {
    #     "success": True,
    #     "handler": "manage_task",
    #     "data": {...}
    # }

asyncio.run(handle_user_input())
```

## 

###  1: 

```python
async def demo():
    agent = IntelligentAgent(
        memory_system=memory,
        llm_client=llm_client
    )

    #  →  Memory
    result1 = await agent.process_input("")
    # → handler: "smart_search"

    #  → 
    result2 = await agent.process_input("")
    # → handler: "manage_task"

    #  → 
    result3 = await agent.process_input("def foo(): return bar")
    # → handler: "code_assistant"

    #  → 
    result4 = await agent.process_input("")
    # → handler: "find_procedure"

    #  → 
    result5 = await agent.process_input("")
    # → handler: "greet"
```

###  2: 

```python
class ChatApp:
    def __init__(self):
        #  Agent
        self.agent = IntelligentAgent(
            memory_system=memory,
            llm_client=llm_client,
            enable_classification=True
        )

    async def handle_message(self, user_input: str, user_id: str):
        """
        
        """
        # Agent 
        # 1. 
        # 2. 
        # 3. 
        # 4. 
        result = await self.agent.process_input(
            user_input,
            context={"user_id": user_id}
        )

        # 
        if result["success"]:
            if result["handler"] == "greet":
                return result["data"]["response"]
            elif result["handler"] == "smart_search":
                return self._format_search_results(result["data"])
            elif result["handler"] == "code_assistant":
                return result["data"]["response"]
            else:
                return ""

        return ""

    def _format_search_results(self, search_data):
        """"""
        results = search_data.get("results", [])
        if not results:
            return ""

        response = "\n"
        for i, item in enumerate(results[:5], 1):
            response += f"{i}. {item.get('memory', '')}\n"
        return response
```

###  3: 

```python
async def custom_task_handler(input_text, context, classification, intent):
    """"""
    # 
    priority = classification.metadata.get("priority", "medium")

    # 
    task_data = {
        "task": input_text,
        "priority": priority,
        "created_at": datetime.now().isoformat(),
    }

    # 
    # task_manager.add(task_data)

    return {
        "success": True,
        "data": {"task_id": "12345"},
        "handler": "custom_task",
        "message": f": {priority}"
    }

# 
agent = IntelligentAgent(...)
agent.register_category_handler(
    MemoryCategory.TASK,
    custom_task_handler
)

#  TASK 
result = await agent.process_input("")
# → handler: "custom_task"
```

###  4:  MemScreen 

```python
#  memscreen/ui/kivy_app.py 

class MemScreenApp(App):
    def build(self):
        # ...  ...

        #  Agent
        from memscreen.agent import IntelligentAgent

        self.intelligent_agent = IntelligentAgent(
            memory_system=self.memory,
            llm_client=self.llm_client,
            enable_classification=True
        )

        print("[App] Intelligent Agent initialized")

        # ...  ...

    async def process_user_message(self, message: str, user_id: str):
        """ Agent"""
        result = await self.intelligent_agent.process_input(
            message,
            context={"user_id": user_id, "session_id": self.session_id}
        )

        return self._format_response(result)

    def _format_response(self, result: Dict[str, Any]) -> str:
        """ Agent """
        if not result["success"]:
            return ""

        handler = result.get("handler")

        if handler == "greet":
            return result["data"]["response"]

        elif handler == "smart_search":
            # 
            memories = result["data"].get("results", [])
            return f" {len(memories)} "

        elif handler == "manage_task":
            return ""

        elif handler == "code_assistant":
            return result["data"]["response"]

        else:
            return ""
```

## 

```

    ↓
[]
    ├→ 
    │   └→ []
    │       ├→ retrieve_fact → smart_search → 
    │       ├→ find_procedure → find_procedure → 
    │       └→ search_conversation → search_conversation → 
    │
    ├→ 
    │   └→ manage_task →  → 
    │
    ├→ 
    │   └→ code_assistant → LLM  → 
    │
    ├→ 
    │   └→ find_procedure →  → 
    │
    ├→ 
    │   └→ greet → 
    │
    └→ 
        └→ general_query → LLM  → 
```

## 

 Agent 

```python
stats = agent.get_dispatch_stats()

print(f": {stats['total_dispatches']}")
print(f": {stats['category_counts']}")
print(f": {stats['intent_counts']}")

# :
# {
#     "total_dispatches": 150,
#     "category_counts": {
#         "question": 60,
#         "task": 30,
#         "code": 25,
#         "conversation": 20,
#         "greeting": 15
#     },
#     "intent_counts": {
#         "retrieve_fact": 45,
#         "find_procedure": 30,
#         "search_conversation": 25
#     }
# }
```

## 

|  |  |  Agent |  |
|------|---------|-----------|------|
|  |  if-else |  | **** |
|  |  | LLM+ | **** |
|  |  LLM |  | **3-5x ** |
|  |  |  | **70%  tokens** |
|  |  |  | **** |

## 

### 1.  Memory

```python
config = MemoryConfig(
    enable_dynamic_memory=True,  # 
    dynamic_config={
        "enable_auto_classification": True,
        "enable_intent_classification": True,
    }
)
```

### 2. 

```python
from memscreen.agent import BaseSkill

class MyCustomSkill(BaseSkill):
    async def execute(self, input_text, context, **kwargs):
        # 
        return SkillResult(
            success=True,
            data={"result": "..."},
            metadata={"handler": "my_custom"}
        )

#  Agent
agent.register_skill(MyCustomSkill())
```

### 3. 

```python
# 
stats = agent.get_dispatch_stats()

# 
top_category = max(stats['category_counts'].items(), key=lambda x: x[1])
print(f": {top_category}")

# 
if top_category[0] == "task":
    # 
    pass
```

## 

###  1: 

****:  LLM 

```python
agent = IntelligentAgent(
    memory_system=memory,
    llm_client=llm_client,
    enable_classification=True
)

#  LLM 
result = await agent.process_input(
    input_text,
    use_llm_classification=True  #  LLM
)
```

###  2: 

****: 

```python
async def my_handler(input_text, context, classification, intent):
    # 
    return {"success": True, "data": {...}}

agent.register_category_handler(
    MemoryCategory.QUESTION,
    my_handler
)
```

###  3: 

****:  `_find_dispatch_rule` 

```python
class CustomAgent(IntelligentAgent):
    def _find_dispatch_rule(self, category, intent):
        # 
        # 
        return custom_rule
```

## 

- ** Agent**: [memscreen/agent/intelligent_agent.py](../memscreen/agent/intelligent_agent.py)
- ****: [demo_intelligent_agent.py](../demo_intelligent_agent.py)
- ****: [tests/test_agent.py](../tests/test_agent.py)

## 

1. ✅ 
2. ✅ 
3. ✅ 
4. 🚀 

---

****: v1.0.0
****: 2026-02-02
****: Jixiang Luo
