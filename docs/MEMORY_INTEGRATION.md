# Memory系统统一管理指南

## 📊 当前状态检查

### ✅ 已实现的集成

1. **录屏 → Memory**
   - 位置: `recording_presenter.py:498-541`
   - 内容: 视频元数据、OCR文本、内容摘要
   - metadata包含: filename, frame_count, fps, duration, timestamp, ocr_text

2. **OCR → Memory**
   - 位置: `recording_presenter.py:543-602`
   - 方法: 使用qwen2.5vl:3b对视频帧进行OCR
   - 集成: OCR文本保存到录屏memory中

3. **Chat → Memory**
   - 位置: `kivy_app.py:443-480`
   - 内容: 用户问题和AI回复
   - metadata包含: timestamp, model, source

### 🔍 发现的问题

1. **OCR模型太慢**
   - 当前使用: qwen2.5vl:3b
   - 建议: 使用更快的模型或异步处理

2. **Memory检索可以更智能**
   - 当前: 简单的关键词搜索
   - 建议: 按类型过滤、优先级排序

3. **缺少统一管理**
   - 当前: 各模块独立调用memory
   - 建议: 使用Memory Manager统一管理

## 🎯 优化方案

### 1. 使用Memory Manager

**创建统一入口:**
```python
# 在kivy_app.py的__init__中
self.memory_manager = get_memory_manager(self.memory)
```

**优化Chat检索:**
```python
# 当前实现（kivy_app.py:384-417）
context = ""
if self.memory_system:
    search_result = self.memory_system.search(...)
    # 手动构建context

# 优化后使用Memory Manager
if self.memory_manager:
    context = self.memory_manager.get_chat_context(
        query=text,
        max_results=3
    )
```

### 2. 优化OCR速度

**当前:**
```python
# 使用qwen2.5vl:3b (慢，3-5秒/帧)
model = "qwen2.5vl:3b"
```

**优化方案A: 使用更快的模型**
```python
# 使用qwen3:1.7b (快2倍)
model = "qwen3:1.7b"
```

**优化方案B: 异步OCR**
```python
# 在后台线程中进行OCR
def ocr_async(frames):
    results = []
    for frame in frames:
        text = extract_text(frame, model="qwen3:1.7b")
        results.append(text)
    return results

thread = threading.Thread(target=ocr_async, args=(frames,))
thread.start()
```

**优化方案C: 减少采样帧数**
```python
# 当前: 采样5帧
num_samples = min(5, total_frames)

# 优化: 根据视频长度动态调整
if duration < 10:
    num_samples = 3  # 短视频采样少
elif duration < 30:
    num_samples = 5
else:
    num_samples = 7  # 长视频多采样
```

### 3. 增强Memory利用

**场景1: 活动查询**
```python
# 用户问: "我最近在做什么？"
# Memory Manager应该检索所有录屏记忆
activities = self.memory_manager.get_user_activities_summary(limit=10)
```

**场景2: 内容查询**
```python
# 用户问: "我之前录制的视频里有提到Python吗？"
# 搜索所有有OCR文本的录屏
results = self.memory_manager.search_memories(
    query="Python",
    memory_types=["screen_recording"],
    limit=5
)
```

**场景3: 对话上下文**
```python
# 用户继续讨论之前的话题
# Memory Manager自动检索相关对话
context = self.memory_manager.get_chat_context(
    query=current_message,
    max_results=5
)
```

## 🔧 实施步骤

### 第1步: 更新导入

**在kivy_app.py开头添加:**
```python
from memscreen.memory.manager import get_memory_manager
```

### 第2步: 初始化Memory Manager

**在MemScreenApp.build()中:**
```python
# 在创建memory后
self.memory = Memory(config=config)

# 创建memory manager
from memscreen.memory.manager import get_memory_manager
self.memory_manager = get_memory_manager(self.memory)
print("[App] Memory Manager initialized")
```

### 第3步: 更新RecordingPresenter

**使用Memory Manager保存录屏:**
```python
# 在recording_presenter.py中
from memscreen.memory.manager import get_memory_manager

class RecordingPresenter:
    def __init__(self, ...):
        self.memory_manager = get_memory_manager(self.memory_system)

    def _add_video_to_memory(self, filename, frame_count, fps, ocr_text=""):
        # 使用Memory Manager
        success = self.memory_manager.save_recording(
            filename=filename,
            frame_count=frame_count,
            fps=fps,
            ocr_text=ocr_text,
            content_summary=self._get_content_summary(ocr_text)
        )
        return success
```

### 第4步: 优化OCR

**使用更快的模型:**
```python
def _extract_text_from_frame(self, frame):
    # 使用更快的模型
    response = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={
            "model": "qwen3:1.7b",  # 更快
            "prompt": "Extract all visible text. Be concise.",
            "images": [img_str],
            "stream": False,
            "options": {
                "num_predict": 256,  # 限制输出长度
                "temperature": 0.3
            }
        },
        timeout=30  # 减少超时时间
    )
```

## 📊 预期效果

### 性能提升

| 操作 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| OCR处理（5帧） | 15-25秒 | 5-10秒 | 2-3x ⚡ |
| Memory检索 | 0.5-1秒 | 0.2-0.5秒 | 2x ⚡ |
| Chat上下文加载 | 每次检索 | 缓存+智能过滤 | 3x ⚡ |

### 功能增强

- ✅ 统一的memory管理
- ✅ 更快的OCR处理
- ✅ 智能的memory检索
- ✅ 类型过滤（录屏/对话/OCR）
- ✅ 缓存优化
- ✅ 统计和监控

## 🧪 测试验证

### 测试1: 录屏记忆
```
1. 录制一段屏幕（包含文字内容）
2. 等待OCR处理完成
3. 在AI Chat中问: "我刚才录制了什么？"
预期: AI能够描述录制内容
```

### 测试2: OCR记忆
```
1. 录制包含代码的屏幕
2. 在AI Chat中问: "我录制的代码里有关于Python吗？"
预期: AI能够从OCR文本中找到Python相关内容
```

### 测试3: 对话记忆
```
1. 多轮对话（建立记忆）
2. 新会话中问: "我们之前讨论了什么？"
预期: AI能够回忆起之前的对话内容
```

## 📝 总结

**当前状态:**
- ✅ 录屏已集成memory
- ✅ OCR已集成memory
- ✅ Chat已集成memory

**需要优化:**
- 🔧 OCR速度（使用更快的模型）
- 🔧 统一管理（使用Memory Manager）
- 🔧 智能检索（类型过滤、缓存）

**下一步:**
1. 实施Memory Manager
2. 优化OCR模型
3. 添加memory统计UI
4. 测试完整流程

---

**优先级排序:**
1. 🔴 高优先级: OCR速度优化（影响用户体验）
2. 🟡 中优先级: Memory Manager（代码质量）
3. 🟢 低优先级: 统计UI（锦上添花）
