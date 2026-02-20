# Step-3.5-Flash Model Integration

Step-3.5-Flash  StepFun 

## 🚀 

- **196B ** **11B ** MoE 
- **token**
- ****
- ****
- **** 32768 tokens

## 📋 

### 1.  Docker  Step-3.5-Flash 

```bash
#  FP16 
docker-compose -f docker/docker-compose.step35flash.yml up -d

# 
docker-compose -f docker/docker-compose.step35flash.yml logs -f

# 
docker-compose -f docker/docker-compose.step35flash.yml down
```

### 2.  MemScreen  Step-3.5-Flash

```bash
# 
export MEMSCREEN_LLM_BACKEND=vllm
export MEMSCREEN_VLLM_URL=http://localhost:8001
export MEMSCREEN_VLLM_LLM_MODEL=stepfun-ai/Step-3.5-Flash

#  MemScreen
python start.py
```

### 3. 

```bash
# 
python test_step35flash.py
```

## 🔧 

###  GPU 

#### Tensor Parallel (TP) - 
```bash
export TENSOR_PARALLEL_SIZE=4
docker-compose -f docker/docker-compose.step35flash.yml up -d
```

#### Data Parallel (DP) - 
```yaml
#  docker/docker-compose.step35flash.yml
command: >
  --model stepfun-ai/Step-3.5-Flash
  --data-parallel-size 4
  --enable-expert-parallel
  --reasoning-parser step3p5
  --tool-call-parser step3p5
  --enable-auto-tool-choice
  --trust-remote-code
```

### FP8 

```bash
#  FP8 
docker-compose --profile fp8 -f docker/docker-compose.step35flash.yml up -d
```

****: FP8  TP > 1

### GPU 

```bash
export GPU_MEMORY_UTILIZATION=0.95
docker-compose -f docker/docker-compose.step35flash.yml up -d
```

## 📊 

 4x H200 (TP4 + FP16) 

- ****: 0.79 req/s
- ** token **: 811.94 tok/s
- ** token **: 940.00 tok/s
- ** TTFT**: 422.62 ms
- ** TPOT**: 11.91 ms

## 🎯 

Step-3.5-Flash 

1. ****
   - 
   - 
   - 

2. ****
   - 
   - 
   - 

3. ****
   - API 
   - 
   - 

4. ****
   - 
   - 
   - 

## 🔍 

|  |  |  |  |
|------|------|----------|------|
| `stepfun-ai/Step-3.5-Flash` | FP16 | ~400GB (4x GPU) |  |
| `stepfun-ai/Step-3.5-Flash-FP8` | FP8 | ~200GB |  |
| `stepfun-ai/Step-3.5-Flash-Int4` | Int4 | ~100GB | vLLM  |

## 🐛 

### 1. B200 GPU FP8 MoE 

```bash
# 
export VLLM_USE_FLASHINFER_MOE_FP8=0
```

### 2. 

-  FP8 
-  `max-model-len`
-  `tensor-parallel-size`

### 3. 

```bash
# 
curl http://localhost:8001/health

# 
docker logs memscreen-step35flash
```

## 📚 

- [vLLM ](https://docs.vllm.ai/)
- [StepFun ](https://stepfun.com/)
- [](https://huggingface.co/stepfun-ai/Step-3.5-Flash)

## 🤝 


-  [GitHub Issue](https://github.com/smileformylove/MemScreen/issues)
-  [Discussions](https://github.com/smileformylove/MemScreen/discussions)
