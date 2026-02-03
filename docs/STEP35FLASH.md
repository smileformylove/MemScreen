# Step-3.5-Flash Model Integration

Step-3.5-Flash 是 StepFun 开发的高级大语言模型，专为生产级推理引擎设计。

## 🚀 模型特性

- **196B 参数总量**，但只有 **11B 激活参数**（稀疏 MoE 结构）
- **多token预测机制**，推理速度更快
- **内置推理和工具调用能力**
- **优化用于低延迟、高性价比的长上下文推理**
- **支持超长上下文**（最多 32768 tokens）

## 📋 快速开始

### 1. 使用 Docker 启动 Step-3.5-Flash 服务

```bash
# 启动 FP16 版本（推荐）
docker-compose -f docker/docker-compose.step35flash.yml up -d

# 查看日志
docker-compose -f docker/docker-compose.step35flash.yml logs -f

# 停止服务
docker-compose -f docker/docker-compose.step35flash.yml down
```

### 2. 配置 MemScreen 使用 Step-3.5-Flash

```bash
# 设置环境变量
export MEMSCREEN_LLM_BACKEND=vllm
export MEMSCREEN_VLLM_URL=http://localhost:8001
export MEMSCREEN_VLLM_LLM_MODEL=stepfun-ai/Step-3.5-Flash

# 启动 MemScreen
python start.py
```

### 3. 测试模型

```bash
# 运行测试脚本
python test_step35flash.py
```

## 🔧 高级配置

### 多 GPU 部署

#### Tensor Parallel (TP) - 适合低延迟场景
```bash
export TENSOR_PARALLEL_SIZE=4
docker-compose -f docker/docker-compose.step35flash.yml up -d
```

#### Data Parallel (DP) - 适合高负载场景
```yaml
# 修改 docker/docker-compose.step35flash.yml
command: >
  --model stepfun-ai/Step-3.5-Flash
  --data-parallel-size 4
  --enable-expert-parallel
  --reasoning-parser step3p5
  --tool-call-parser step3p5
  --enable-auto-tool-choice
  --trust-remote-code
```

### FP8 量化版本（更好的内存效率）

```bash
# 启动 FP8 版本
docker-compose --profile fp8 -f docker/docker-compose.step35flash.yml up -d
```

**注意**: FP8 版本不支持 TP > 1

### GPU 内存利用率调整

```bash
export GPU_MEMORY_UTILIZATION=0.95
docker-compose -f docker/docker-compose.step35flash.yml up -d
```

## 📊 性能指标

在 4x H200 (TP4 + FP16) 上的基准测试：

- **请求吞吐**: 0.79 req/s
- **输出 token 吞吐**: 811.94 tok/s
- **峰值 token 吞吐**: 940.00 tok/s
- **平均 TTFT**: 422.62 ms
- **平均 TPOT**: 11.91 ms

## 🎯 适用场景

Step-3.5-Flash 特别适合：

1. **复杂推理任务**
   - 数学问题求解
   - 逻辑推理
   - 多步骤问题解决

2. **长上下文处理**
   - 长文档分析
   - 代码理解
   - 上下文总结

3. **工具调用场景**
   - API 调用
   - 函数执行
   - 自动化工作流

4. **生产环境部署**
   - 低延迟要求
   - 高并发请求
   - 成本敏感场景

## 🔍 模型选项

| 模型 | 精度 | 显存需求 | 特点 |
|------|------|----------|------|
| `stepfun-ai/Step-3.5-Flash` | FP16 | ~400GB (4x GPU) | 推荐，平衡性能和精度 |
| `stepfun-ai/Step-3.5-Flash-FP8` | FP8 | ~200GB | 更好的内存效率 |
| `stepfun-ai/Step-3.5-Flash-Int4` | Int4 | ~100GB | vLLM 暂不支持 |

## 🐛 故障排除

### 1. B200 GPU FP8 MoE 错误

```bash
# 设置环境变量
export VLLM_USE_FLASHINFER_MOE_FP8=0
```

### 2. 显存不足

- 使用 FP8 版本
- 减少 `max-model-len`
- 增加 `tensor-parallel-size`

### 3. 连接超时

```bash
# 检查服务状态
curl http://localhost:8001/health

# 查看容器日志
docker logs memscreen-step35flash
```

## 📚 相关文档

- [vLLM 官方文档](https://docs.vllm.ai/)
- [StepFun 官方网站](https://stepfun.com/)
- [模型卡片](https://huggingface.co/stepfun-ai/Step-3.5-Flash)

## 🤝 贡献

如果遇到问题或有改进建议，请：
- 提交 [GitHub Issue](https://github.com/smileformylove/MemScreen/issues)
- 查看 [Discussions](https://github.com/smileformylove/MemScreen/discussions)
