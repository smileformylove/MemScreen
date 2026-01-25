# AI Chat 问题修复

## 🔧 修复的问题

### 1. 默认模型
- **之前**: `qwen2.5:1.7b` (不存在)
- **现在**: `qwen3:1.7b` (已安装的模型)

### 2. 第二次对话卡住的问题

#### 原因分析
1. **对话历史过长** - 每次对话都把所有历史记录发送给AI，导致prompt超出token限制
2. **没有超时保护** - 如果AI没有响应，UI会一直显示"AI is typing"
3. **缺少错误处理** - 没有足够的调试信息和错误提示

#### 解决方案

##### a) 限制对话历史
```python
# 只保留最近4条对话记录
limited_history = self.conversation_history[-4:] if len(self.conversation_history) > 4 else self.conversation_history
```

##### b) 添加超时保护
```python
# 30秒超时检测
if time.time() - self._response_start_time > 30:
    self.chat_history.insert(tk.END, "\n⚠️ Response timeout. Please try again.\n\n")
```

##### c) 增加请求超时
```python
response = requests.post(url, json=payload, stream=True, timeout=120)  # 从60秒增加到120秒
```

##### d) 添加详细调试日志
```python
print(f"[DEBUG] Sending to Ollama: model={model_name}, messages={len(messages)}")
print(f"[DEBUG] Response complete: {len(full_response)} chars, {line_count} lines")
print(f"[ERROR] Ollama request failed: {e}")
```

##### e) 改进错误处理
```python
except (json.JSONDecodeError, KeyError) as e:
    print(f"[DEBUG] Error parsing line {line_count}: {e}")
    pass  # 继续处理下一行
```

## 🧪 测试方法

### 1. 检查Ollama状态
```bash
python3 check_ollama.py
```

### 2. 测试对话流程
1. 打开AI Chat标签
2. 发送第一条消息
3. 等待AI回复
4. 发送第二条消息
5. 观察是否有响应

### 3. 查看调试输出
在终端中会看到：
```
[DEBUG] Sending to Ollama: model=qwen3:1.7b, messages=3
[DEBUG] Response complete: 123 chars, 5 lines
```

## 📋 当前可用模型

根据 `check_ollama.py` 的输出：
1. mxbai-embed-large:latest (0.62 GB) - embedding模型
2. nomic-embed-text:latest (0.26 GB) - embedding模型
3. **qwen2.5vl:3b** (2.98 GB) - 视觉语言模型
4. **qwen3:1.7b** (1.27 GB) - 当前使用 ✅
5. gemma3:270m (0.27 GB) - 小型模型
6. quentinz/bge-base-zh-v1.5:latest (0.19 GB) - 中文embedding

## ⚠️ 如果仍然卡住

### 检查清单

1. **Ollama是否运行**
   ```bash
   curl http://127.0.0.1:11434/api/tags
   ```

2. **模型是否可用**
   ```bash
   ollama list
   ```

3. **查看终端调试输出**
   - 启动UI时会显示 `[DEBUG]` 日志
   - 检查是否有 `[ERROR]` 消息

4. **测试模型直接调用**
   ```bash
   curl http://127.0.0.1:11434/api/generate -d '{
     "model": "qwen3:1.7b",
     "prompt": "Hello"
   }'
   ```

5. **如果模型响应慢**
   - 尝试更小的模型: `gemma3:270m`
   - 或者减少对话历史: 改为 `[-2:]`

## 🚀 后续优化建议

1. **添加模型切换提示** - 在UI中显示当前使用的模型
2. **添加重新生成按钮** - 如果响应不满意可以重新生成
3. **添加清除历史按钮** - 清空对话历史重新开始
4. **添加流式响应控制** - 可以选择是否使用流式输出
5. **添加模型性能监控** - 显示响应时间和token使用
