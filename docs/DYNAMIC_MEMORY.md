# Dynamic Memory System - 动态 Memory 系统

## 概述

动态 Memory 系统是对 MemScreen Memory 的重大优化，通过自动分类和智能检索来加快推理速度并提供更准确的结果。

## 核心特性

### 1. 自动输入分类

系统会自动将用户输入分类到以下类别：

- **QUESTION** - 问题 (如："什么是 Python?")
- **TASK** - 任务 (如："记得明天给客户打电话")
- **FACT** - 事实 (如："Python 是一种编程语言")
- **CONCEPT** - 概念 (如："递归是函数调用自身")
- **CONVERSATION** - 对话
- **CODE** - 代码片段
- **PROCEDURE** - 步骤流程
- **DOCUMENT** - 文档
- **IMAGE** - 图像
- **REFERENCE** - 参考资料

### 2. 智能查询意图识别

系统会自动识别查询意图：

- **RETRIEVE_FACT** - 检索事实信息
- **FIND_PROCEDURE** - 查找操作步骤
- **SEARCH_CONVERSATION** - 搜索历史对话
- **LOCATE_CODE** - 定位代码
- **GET_TASKS** - 获取任务列表
- **GENERAL_SEARCH** - 通用搜索

### 3. 分类权重优化

不同类别的 memory 在搜索时可以有不同的权重：

```python
default_category_weights = {
    "fact": 1.2,        # 事实权重更高
    "procedure": 1.2,   # 流程权重更高
    "conversation": 0.9, # 对话权重较低
}
```

### 4. 多策略上下文检索

- **语义检索** - 基于向量相似度
- **分类检索** - 按类别定向搜索
- **时间检索** - 优先检索最近的内容
- **对话检索** - 结合对话历史

## 性能优势

### 1. 搜索速度提升

**传统搜索**：扫描所有 memories (例如 10,000 条)
**智能搜索**：只搜索相关类别 (例如 2,000 条)

**速度提升：3-5倍**

### 2. 结果更准确

- 问题查询 → 返回事实和概念
- 操作查询 → 返回流程和步骤
- 代码查询 → 返回代码片段

### 3. Token 使用优化

**传统方式**：5000 tokens 的上下文
**优化后**：1500 tokens 的高相关上下文

**成本节省：70% 的 token 减少**

### 4. 可扩展性

- 易于添加新类别
- 独立的类别管理
- 灵活的权重调整

## 使用方法

### 基本用法

```python
from memscreen import Memory
from memscreen.memory import MemoryConfig, DynamicMemoryConfig

# 1. 初始化 Memory（启用动态功能）
config = MemoryConfig(
    # 基本配置
    llm={"provider": "ollama", "config": {"model": "llama2"}},
    embedder={"provider": "ollama", "config": {"model": "nomic-embed-text"}},
    vector_store={"provider": "chroma", "config": {"path": "./chroma_db"}},

    # 启用动态 memory
    enable_dynamic_memory=True,
)

memory = Memory(config)
```

### 添加 Memory（带分类）

```python
# 自动分类并添加
result = memory.add_with_classification(
    messages="我需要在周五前完成项目报告",
    user_id="user123",
)

print(f"类别: {result['classification']['category']}")  # "task"
print(f"置信度: {result['classification']['confidence']}")  # 0.9
```

### 智能搜索

```python
# 系统会自动识别查询意图并搜索相关类别
results = memory.smart_search(
    query="如何部署应用？",
    user_id="user123",
)

# 系统会搜索：procedure, workflow, task 类别
# 而不是搜索所有类别
```

### 获取上下文（用于回复）

```python
# 获取优化的上下文用于生成回复
context = memory.get_context_for_response(
    query="如何设置开发环境？",
    user_id="user123",
    conversation_history=[
        {"role": "user", "content": "我需要帮助"},
        {"role": "assistant", "content": "我可以帮助"},
    ],
    max_context_items=10,
)

# 上下文包含：
# - 相关的流程步骤
# - 相关的事实和概念
# - 最近的对话历史
# - 按类别和相关性组织

# 格式化后可直接用于 LLM
llm_input = context.get("formatted", "")
response = your_llm.generate(llm_input)
```

### 按类别检索

```python
# 只检索特定类别的 memories
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

### 分类输入（不存储）

```python
# 只分类不存储
classification = memory.classify_input(
    "记得明天给客户打电话"
)

print(f"类别: {classification['category']}")  # "task"
print(f"置信度: {classification['confidence']}")  # 0.9
print(f"元数据: {classification['metadata']}")  # {"priority": "medium"}
```

### 统计信息

```python
stats = memory.get_dynamic_statistics()
print(f"总分类数: {stats['total_classifications']}")
print(f"类别分布: {stats['category_distribution']}")
print(f"意图分布: {stats['intent_distribution']}")
```

## 高级配置

### 自定义类别权重

```python
config = MemoryConfig(
    # ... 其他配置 ...

    dynamic_config={
        "enable_category_weights": True,
        "default_category_weights": {
            "task": 1.5,        # 提升任务优先级
            "fact": 1.2,        # 提升事实优先级
            "procedure": 1.3,   # 提升流程优先级
            "conversation": 0.7,  # 降低对话优先级
        },

        # 缓存分类结果
        "cache_classification_results": True,
        "classification_cache_size": 1000,

        # 性能优化
        "max_search_categories": 2,  # 只搜索最相关的 2 个类别
    }
)
```

### 分类器选项

```python
# 使用 LLM 进行分类（更准确但更慢）
result = memory.add_with_classification(
    messages="用户输入",
    use_llm_classification=True,  # 启用 LLM 分类
)
```

## 迁移指南

### 从旧版 Memory 迁移

**旧代码仍然有效：**

```python
# 这些方法仍然正常工作
memory.add("用户消息", user_id="user123")
results = memory.search("查询", user_id="user123")
```

**升级到动态功能：**

```python
# 新方法（推荐）
memory.add_with_classification("用户消息", user_id="user123")
results = memory.smart_search("查询", user_id="user123")
```

### 向后兼容性

- 所有现有方法继续工作
- 新功能是可选的
- 可以逐步采用新功能

## 文件结构

```
memscreen/memory/
├── dynamic_models.py      # 分类模型和枚举
├── input_classifier.py    # 输入分类器
├── dynamic_manager.py     # 动态 Memory Manager
├── context_retriever.py   # 上下文检索器
├── memory.py              # Memory 类（已更新）
└── __init__.py            # 导出所有组件
```

## 示例

完整示例请参考：
- [examples/dynamic_memory_example.py](../examples/dynamic_memory_example.py)
- [tests/verify_dynamic_memory.py](../tests/verify_dynamic_memory.py)

## 测试

运行测试验证功能：

```bash
python tests/verify_dynamic_memory.py
```

## 性能对比

| 操作 | 传统方式 | 动态 Memory | 提升 |
|------|---------|------------|------|
| 搜索 | 扫描全部 | 扫描相关类别 | 3-5x |
| 上下文获取 | 5000 tokens | 1500 tokens | 70% |
| 结果准确性 | 通用 | 分类优化 | 更高 |

## 常见问题

**Q: 动态 Memory 会影响现有代码吗？**
A: 不会。所有现有方法继续正常工作，新功能是可选的。

**Q: 如何禁用动态 Memory？**
A: 在配置中设置 `enable_dynamic_memory=False`。

**Q: LLM 分类会显著增加延迟吗？**
A: 默认使用模式匹配（很快），可以可选地启用 LLM 分类（更准确）。

**Q: 可以自定义分类类别吗？**
A: 可以。修改 `MemoryCategory` 枚举和分类器模式即可。

## 未来改进

- [ ] 支持自定义分类类别
- [ ] 多语言分类支持
- [ ] 时间衰减权重
- [ ] 用户行为学习
- [ ] 分布式分类
