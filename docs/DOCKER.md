# Docker 部署指南

## 🐳 使用 Docker 部署 MemScreen

Docker 可以简化安装过程，确保环境一致性，并避免依赖冲突。

## 前置要求

- Docker Engine 20.10+
- Docker Compose 2.0+ (可选)
- 至少 8GB 可用磁盘空间
- 推荐 8GB+ RAM

## 快速开始

### 方法 1: 使用 Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen

# 2. 构建并启动
docker-compose -f docker/docker-compose.yml up -d

# 3. 查看日志
docker-compose -f docker/docker-compose.yml logs -f memscreen

# 4. 停止服务
docker-compose -f docker/docker-compose.yml down
```

### 方法 2: 使用 Docker 命令

```bash
# 1. 构建镜像
docker build -t memscreen:latest .

# 2. 运行容器
docker run -d \
  --name memscreen-app \
  -p 5901:5901 \
  -p 11434:11434 \
  -v memscreen_data:/app/db \
  -v ollama_models:/root/.ollama \
  memscreen:latest

# 3. 查看日志
docker logs -f memscreen-app

# 4. 停止容器
docker stop memscreen-app
docker rm memscreen-app
```

## 配置选项

### 环境变量

在 `docker/docker-compose.yml` 中可以配置：

```yaml
environment:
  - DISPLAY=:99                    # 虚拟显示
  - OLLAMA_HOST=0.0.0.0:11434      # Ollama 服务地址
  - OLLAMA_NUM_PARALLEL=2          # 并行处理数量
```

### GPU 支持

如果您有 NVIDIA GPU，取消注释 `docker/docker-compose.yml` 中的 GPU 配置：

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### 数据持久化

数据存储在 Docker 卷中：

```bash
# 查看卷
docker volume ls | grep memscreen

# 备份数据
docker run --rm -v memscreen_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/memscreen-backup.tar.gz /data

# 恢复数据
docker run --rm -v memscreen_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/memscreen-backup.tar.gz -C /
```

## 网络访问

### 本地访问

容器内的应用使用虚拟显示，您需要：

1. **通过 VNC 访问**：
   ```bash
   # 安装 VNC 客户端
   # 连接到 localhost:5901
   ```

2. **启用 noVNC（Web 访问）**：
   ```bash
   # 在 docker/docker-compose.yml 中取消注释 novnc 服务
   docker-compose -f docker/docker-compose.yml up -d
   # 访问 http://localhost:6080
   ```

### 远程访问

```bash
# 暴露 VNC 端口
docker run -d -p 5901:5901 memscreen:latest

# 通过 SSH 隧道访问
ssh -L 5901:localhost:5901 user@remote-server
```

## AI 模型管理

### 首次启动

容器会自动下载以下模型：
- `qwen2.5vl:3b` (~2GB) - 视觉模型
- `mxbai-embed-large` (~470MB) - 文本嵌入

### 手动管理模型

```bash
# 进入容器
docker exec -it memscreen-app bash

# 列出已安装模型
ollama list

# 下载更多模型
ollama pull llama3.2:3b

# 删除模型
ollama rm qwen2.5vl:3b
```

### 使用模型缓存

默认配置会在容器间共享模型（通过 `ollama_models` 卷）。

## 性能优化

### 1. 使用主机网络（Linux）

```bash
docker run --network host memscreen:latest
```

### 2. 限制资源使用

```yaml
services:
  memscreen:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### 3. 调整 Ollama 参数

```bash
docker exec -it memscreen-app bash
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=2
ollama serve
```

## 故障排除

### 容器无法启动

```bash
# 查看详细日志
docker-compose logs -f --tail=100 memscreen

# 检查容器状态
docker ps -a | grep memscreen
```

### Ollama 连接失败

```bash
# 检查 Ollama 是否运行
docker exec memscreen-app curl http://localhost:11434/api/tags

# 重启 Ollama
docker exec memscreen-app pkill ollama
docker exec memscreen-app ollama serve &
```

### GUI 显示问题

```bash
# 检查 Xvfb
docker exec memscreen-app ps aux | grep Xvfb

# 重启显示服务
docker exec memscreen-app pkill Xvfb
docker exec memscreen-app Xvfb :99 -screen 0 1920x1080x24 &
```

### 模型下载失败

```bash
# 手动下载模型
docker exec -it memscreen-app bash
ollama pull qwen2.5vl:3b

# 使用镜像代理
export OLLAMA_HOST=https://ollama.example.com
```

## 开发模式

### 挂载源代码

```bash
docker run -it -v $(pwd):/app memscreen:latest bash
```

### 热重载

```bash
# 使用开发模式启动
docker-compose -f docker-compose.dev.yml up
```

## 更新和维护

### 更新应用

```bash
# 1. 停止容器
docker-compose -f docker/docker-compose.yml down

# 2. 拉取最新代码
git pull

# 3. 重新构建
docker-compose -f docker/docker-compose.yml build --no-cache

# 4. 启动新版本
docker-compose -f docker/docker-compose.yml up -d
```

### 清理旧镜像

```bash
# 删除未使用的镜像
docker image prune -a

# 删除未使用的卷
docker volume prune
```

## 生产部署

### 使用 Docker Swarm

```bash
docker stack deploy -c docker/docker-compose.yml memscreen
```

### 使用 Kubernetes

参考 `k8s/` 目录中的配置文件。

## 安全建议

1. **不要在容器中运行特权命令**
2. **使用只读文件系统**（如果可能）
3. **限制容器资源**
4. **定期更新镜像**
5. **使用非 root 用户运行**

```yaml
services:
  memscreen:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
```

## 相关文档

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Ollama Docker 指南](https://github.com/ollama/ollama/blob/main/docker/README.md)

## 支持

遇到问题？
- [GitHub Issues](https://github.com/smileformylove/MemScreen/issues)
- [文档](docs/)
- [Discussions](https://github.com/smileformylove/MemScreen/discussions)
