# Docker Configuration Files

This directory contains all Docker-related configuration files for MemScreen.

## 📁 Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Main Docker Compose configuration for MemScreen with Ollama |
| `docker-compose.vllm.yml` | vLLM server configuration for high-performance inference |
| `docker-compose.step35flash.yml` | Step-3.5-Flash advanced reasoning model configuration |
| `test_docker.sh` | Docker deployment and testing script |
| `Dockerfile` (root) | Main Docker image definition |
| `docker-entrypoint.sh` (root) | Container entrypoint script |

## 🚀 Quick Start

### MemScreen with Ollama (Default)

```bash
docker-compose -f docker/docker-compose.yml up -d
```

### vLLM Server (Production)

```bash
docker-compose -f docker/docker-compose.vllm.yml up -d
```

### Step-3.5-Flash (Advanced Reasoning)

```bash
docker-compose -f docker/docker-compose.step35flash.yml up -d
```

## 📖 Documentation

For detailed Docker deployment instructions, see:
- [Docker Deployment Guide](../docs/DOCKER.md)
- [vLLM Backend Documentation](../docs/VLLM_BACKEND.md)
- [Step-3.5-Flash Documentation](../docs/STEP35FLASH.md)

## 🧪 Testing

Run the Docker test script:
```bash
chmod +x docker/test_docker.sh
docker/test_docker.sh
```

## 🔧 Configuration

Each compose file can be customized with environment variables:

- `MODEL` — Model name to use
- `GPU_MEMORY_UTILIZATION` — GPU memory usage ratio (0-1)
- `TENSOR_PARALLEL_SIZE` — Number of GPUs for tensor parallelism
- `VLLM_PORT` — Port for vLLM server (default: 8000)
- `STEP35FLASH_PORT` — Port for Step-3.5-Flash server (default: 8001)

Example:
```bash
export GPU_MEMORY_UTILIZATION=0.95
export TENSOR_PARALLEL_SIZE=4
docker-compose -f docker/docker-compose.vllm.yml up -d
```
