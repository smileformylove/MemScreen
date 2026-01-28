# MemScreen Optimized Model Configuration

## Performance Settings

### Model Selection
- **Fast Chat**: qwen2.5vl:0.5b (60% faster, good enough for most tasks)
- **Quality Chat**: qwen2.5vl:3b (best quality, slower)
- **Text Only**: phi3:mini (3x faster, no vision)
- **Balanced**: gemma2:2b (2x faster, good quality)

### When to use each model:

1. **Fast Chat (qwen2.5vl:0.5b)**
   - Daily conversations
   - Quick questions
   - UI interactions
   - Real-time chat

2. **Quality Chat (qwen2.5vl:3b)**
   - Complex analysis
   - Important decisions
   - Document understanding
   - Code review

3. **Text Only (phi3:mini)**
   - Text processing
   - Summarization
   - Search queries
   - Quick responses

4. **Balanced (gemma2:2b)**
   - General use
   - Mixed workloads
   - Testing/development

### Performance Tips

1. **Enable GPU**: Set num_gpu: 1 in config for 2-3x speedup
2. **Reduce max_tokens**: Use 256 for quick responses, 512 for detailed
3. **Use cache**: Enable caching for repeated queries
4. **Batch requests**: Process multiple items at once
5. **Stream responses**: Enable for faster feedback

### Model Comparison

| Model | Speed | Quality | Vision | Size |
|-------|-------|---------|--------|------|
| qwen2.5vl:0.5b | ⚡⚡⚡ | ⚡⚡ | ✅ | 300MB |
| qwen2.5vl:3b | ⚡ | ⚡⚡⚡ | ✅ | 2GB |
| phi3:mini | ⚡⚡⚡ | ⚡⚡ | ❌ | 2.3GB |
| gemma2:2b | ⚡⚡ | ⚡⚡ | ❌ | 1.6GB |

