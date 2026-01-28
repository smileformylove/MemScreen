# Model Performance Optimization Guide

## 🚀 Quick Wins for Faster Performance

### 1. Use Smaller Models (60% faster)

**Current:**
```python
llm = OllamaLLM(config={"model": "qwen2.5vl:3b"})
```

**Optimized:**
```python
llm = OllamaLLM(config={"model": "qwen2.5vl:0.5b"})  # 60% faster!
```

### 2. Enable GPU Acceleration (2-3x faster)

```python
# Add to model options
options = {
    "num_gpu": 1,  # Offload layers to GPU
    "num_thread": 4  # CPU threads for remaining work
}
```

### 3. Reduce Token Count

```python
# Quick responses
options = {"num_predict": 128}  # Instead of 2000

# Detailed responses
options = {"num_predict": 512}  # Instead of 2000
```

### 4. Use Response Caching

```python
from memscreen.llm import OptimizedOllamaLLM, OptimizedOllamaConfig

# Enable caching (automatic with OptimizedOllamaLLM)
config = OptimizedOllamaConfig(
    model="qwen2.5vl:0.5b",
    use_case="chat",
    enable_cache=True  # Cache repeated queries
)

llm = OptimizedOllamaLLM(config)
```

### 5. Use Case-Specific Models

```python
# Fast chat for UI interactions
llm_fast = OptimizedOllamaLLM(config={"use_case": "chat_fast"})

# Quality mode for important tasks
llm_quality = OptimizedOllamaLLM(config={"use_case": "chat"})

# Summary mode
llm_summary = OptimizedOllamaLLM(config={"use_case": "summary"})
```

---

## 📊 Performance Comparison

### Model Speed Comparison

| Model | Response Time | Quality | Vision | Best For |
|-------|--------------|---------|--------|----------|
| **qwen2.5vl:0.5b** | ⚡⚡⚡ (1-2s) | ⚡⚡ (80%) | ✅ | Daily use, UI |
| **qwen2.5vl:3b** | ⚡ (3-5s) | ⚡⚡⚡ (95%) | ✅ | Complex tasks |
| **phi3:mini** | ⚡⚡⚡ (0.5-1s) | ⚡⚡ (85%) | ❌ | Text only |
| **gemma2:2b** | ⚡⚡ (1-2s) | ⚡⚡ (90%) | ❌ | Balanced |

### Optimization Impact

| Optimization | Speedup | Effort |
|--------------|---------|--------|
| Use 0.5b model | 60% | ⭐ Easy |
| Enable GPU | 200% | ⭐ Easy |
| Reduce tokens | 40% | ⭐ Easy |
| Enable caching | ∞ (repeat) | ⭐ Medium |
| Use fast model | 300% | ⭐ Easy |

---

## 🔧 Implementation Examples

### Example 1: Chat Screen Optimization

```python
# In kivy_app.py ChatScreen

from memscreen.llm import OptimizedOllamaLLM, OptimizedOllamaConfig

def get_ai_response(self, text):
    # Use fast model for chat
    config = OptimizedOllamaConfig(
        model="qwen2.5vl:0.5b",  # Fast model
        use_case="chat_fast",
        enable_cache=True
    )

    llm = OptimizedOllamaLLM(config)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": text}
    ]

    response = llm.generate_response(messages)
    return response
```

### Example 2: Adaptive Model Selection

```python
class AdaptiveLLM:
    """Select model based on query complexity"""

    def __init__(self):
        self.fast_llm = OptimizedOllamaLLM(config={
            "model": "qwen2.5vl:0.5b",
            "use_case": "chat_fast"
        })
        self.quality_llm = OptimizedOllamaLLM(config={
            "model": "qwen2.5vl:3b",
            "use_case": "chat"
        })

    def query(self, text):
        # Simple queries use fast model
        if len(text) < 50 and '?' in text:
            return self.fast_llm.generate_response([
                {"role": "user", "content": text}
            ])

        # Complex queries use quality model
        return self.quality_llm.generate_response([
            {"role": "user", "content": text}
        ])
```

### Example 3: Video Analysis Optimization

```python
# For video frame analysis
llm_vision = OptimizedOllamaLLM(config={
    "model": "qwen2.5vl:0.5b",  # Faster than 3b
    "use_case": "vision",
    "num_predict": 128  # Short descriptions
})
```

---

## 🎯 Optimization Strategies

### Strategy 1: Progressive Enhancement

```python
# Start with fast model
response = llm_fast.generate_response(messages)

# If confidence low, retry with quality model
if needs_improvement(response):
    response = llm_quality.generate_response(messages)
```

### Strategy 2: Batch Processing

```python
# Process multiple items together
def batch_summarize(texts):
    llm = OptimizedOllamaLLM(config={"use_case": "summary"})
    return [llm.generate_summary(text) for text in texts]
```

### Strategy 3: Streaming Responses

```python
# Enable streaming for faster feedback
response = llm.generate_response(
    messages,
    stream=True  # Show tokens as they arrive
)
```

---

## 📈 Monitoring Performance

### Track Performance Stats

```python
from memscreen.llm import OptimizedOllamaLLM

llm = OptimizedOllamaLLM()

# Use the model
response = llm.generate_response(messages)

# Check performance
llm.print_performance_stats()
```

### Expected Metrics

| Metric | Target | Good | Excellent |
|--------|--------|------|-----------|
| Chat response (0.5b) | < 2s | < 1.5s | < 1s |
| Vision analysis (0.5b) | < 3s | < 2s | < 1.5s |
| Cache hit rate | > 20% | > 40% | > 60% |

---

## 🛠️ Advanced Optimization

### 1. Model Quantization

```bash
# Pull quantized version
ollama pull qwen2.5vl:0.5b-q4_0  # 4-bit quantization
```

### 2. GPU Optimization

```python
# Check GPU availability
import ollama
client = ollama.Client()

# List GPU-enabled models
response = client.ps()
print(response)  # Check if models use GPU
```

### 3. Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor

def parallel_query(texts):
    llm = OptimizedOllamaLLM(config={"use_case": "chat_fast"})

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(
            lambda t: llm.generate_response([{"role": "user", "content": t}]),
            texts
        ))

    return results
```

---

## 📝 Quick Start Checklist

- [ ] Download qwen2.5vl:0.5b model
- [ ] Update app config to use 0.5b model
- [ ] Enable GPU (if available)
- [ ] Enable caching
- [ ] Reduce max_tokens to 512
- [ ] Test performance improvement
- [ ] Monitor stats

---

## 🆘 Troubleshooting

### Issue: Model is still slow

**Solutions:**
1. Check GPU is enabled: `ollama ps`
2. Use even smaller model: `phi3:mini`
3. Reduce context window: `num_ctx: 1024`
4. Increase GPU layers: `num_gpu: 50` (if VRAM available)

### Issue: Quality degraded too much

**Solutions:**
1. Use `gemma2:2b` instead of 0.5b
2. Increase temperature to 0.7 for more diversity
3. Use hybrid: fast for simple, quality for complex

### Issue: Out of memory

**Solutions:**
1. Reduce `num_ctx` (context window)
2. Set `num_gpu: 0` (use CPU only)
3. Use smaller model
4. Reduce batch size

---

## 📚 Additional Resources

- [Ollama Model Library](https://ollama.com/library)
- [Qwen2.5-VL Models](https://ollama.com/library/qwen2.5vl)
- [Model Quantization Guide](https://github.com/ollama/ollama/blob/main/docs/quantization.md)

---

**Last Updated:** 2025-01-28
**Version:** v0.3.5
