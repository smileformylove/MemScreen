# Docker 测试指南

## 前置条件

- Docker Engine 20.10+
- Docker Compose 2.0+
- 至少 8GB 可用磁盘空间
- 推荐 8GB+ RAM

## 快速测试

### 1. 使用测试脚本（推荐）

```bash
# 给脚本执行权限
chmod +x test_docker.sh

# 运行测试
./test_docker.sh
```

测试脚本会自动：
- ✅ 检查 Docker 安装
- ✅ 构建镜像
- ✅ 启动容器
- ✅ 测试 Ollama 服务
- ✅ 验证 Python 依赖
- ✅ 显示容器日志

### 2. 手动测试

#### 步骤 1: 构建镜像

```bash
docker-compose build
```

预期输出：
```
[+] Building 123.4s (15/15) FINISHED
 => => naming to docker.io/library/memscreen-app
```

#### 步骤 2: 启动容器

```bash
docker-compose up -d
```

预期输出：
```
[+] Running 2/2
 ✔ Volume "ollama_models"  Created
 ✔ Container memscreen-app  Started
```

#### 步骤 3: 查看启动日志

```bash
docker-compose logs -f memscreen
```

预期看到：
```
==========================================
🦉 MemScreen Docker 启动脚本
==========================================
📺 启动虚拟显示服务器...
🖥️ 启动窗口管理器...
🤖 启动 Ollama 服务...
✅ Ollama 服务已启动
📥 检查 AI 模型...
   下载 qwen2.5vl:3b (~2GB)...
   下载 mxbai-embed-large (~470MB)...
✅ AI 模型已就绪
🚀 启动 MemScreen 应用...
```

#### 步骤 4: 验证服务

```bash
# 测试 Ollama API
curl http://localhost:11434/api/tags

# 进入容器
docker exec -it memscreen-app bash

# 检查模型
ollama list

# 退出容器
exit
```

## 测试场景

### 场景 1: 基础功能测试

```bash
# 1. 启动容器
docker-compose up -d

# 2. 等待模型下载完成
docker-compose logs -f memscreen | grep "✅"

# 3. 检查应用是否运行
docker ps | grep memscreen-app

# 4. 查看资源使用
docker stats memscreen-app
```

**预期结果:**
- ✅ 容器状态为 `Up`
- ✅ 内存使用 < 4GB
- ✅ CPU 使用正常

### 场景 2: 模型推理测试

```bash
# 进入容器
docker exec -it memscreen-app bash

# 测试视觉模型
echo "测试视觉模型..."
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5vl:3b",
  "prompt": "What is in this image?",
  "stream": false
}'

# 测试嵌入模型
echo "测试嵌入模型..."
curl http://localhost:11434/api/embed -d '{
  "model": "mxbai-embed-large",
  "input": "Hello, MemScreen!"
}'
```

**预期结果:**
- ✅ 视觉模型返回响应
- ✅ 嵌入模型返回向量
- ✅ 响应时间 < 10秒

### 场景 3: 数据持久化测试

```bash
# 1. 添加一些数据
docker exec memscreen-app python -c "
from memscreen.memory import Memory
m = Memory()
m.add(messages=[{'role': 'user', 'content': 'Test'}], user_id='test')
print('Data added')
"

# 2. 停止容器
docker-compose down

# 3. 重新启动
docker-compose up -d

# 4. 验证数据还在
docker exec memscreen-app python -c "
from memscreen.memory import Memory
m = Memory()
results = m.search(query='Test', user_id='test')
print(f'Found {len(results.get(\"results\", []))} results')
"
```

**预期结果:**
- ✅ 第一次找到 1 条结果
- ✅ 重启后仍能找到数据

### 场景 4: 性能测试

```bash
# 测试响应时间
time docker exec memscreen-app python -c "
from memscreen.memory import InputClassifier
classifier = InputClassifier()
result = classifier.classify_input('什么是 Python？')
print(f'分类: {result.category.value}')
print(f'置信度: {result.confidence}')
"
```

**预期结果:**
- ✅ 分类时间 < 100ms
- ✅ 分类结果正确（question）
- ✅ 置信度 > 0.8

## 故障排除

### 问题 1: 容器无法启动

```bash
# 查看详细日志
docker-compose logs memscreen

# 检查容器状态
docker ps -a | grep memscreen
```

**常见原因:**
- 磁盘空间不足
- 内存不足
- 端口冲突 (11434, 5901)

**解决方案:**
```bash
# 清理未使用的资源
docker system prune -a

# 释放空间
docker volume prune

# 更改端口（在 docker-compose.yml 中）
ports:
  - "11435:11434"  # 使用不同的端口
```

### 问题 2: 模型下载失败

```bash
# 手动下载模型
docker exec -it memscreen-app bash
ollama pull qwen2.5vl:3b

# 或使用代理
export OLLAMA_HOST=https://ollama.example.com
ollama pull qwen2.5vl:3b
```

### 问题 3: Ollama 服务无法访问

```bash
# 检查 Ollama 进程
docker exec memscreen-app ps aux | grep ollama

# 重启 Ollama
docker exec memscreen-app pkill ollama
docker exec memscreen-app ollama serve &

# 验证连接
docker exec memscreen-app curl http://localhost:11434/api/tags
```

### 问题 4: 内存不足

```bash
# 限制容器内存
docker-compose down
# 编辑 docker-compose.yml
# 添加:
# services:
#   memscreen:
#     deploy:
#       resources:
#         limits:
#           memory: 4G

docker-compose up -d
```

## 性能基准

### 启动时间

| 操作 | 预期时间 |
|------|---------|
| 构建镜像 | 3-5 分钟 |
| 下载模型 | 5-10 分钟 (首次) |
| 启动容器 | 10-15 秒 |
| 总计 (首次) | 8-15 分钟 |
| 总计 (后续) | 30-60 秒 |

### 资源使用

| 资源 | 空闲 | 运行中 |
|------|------|--------|
| 内存 | ~500MB | ~2GB |
| CPU | < 5% | 10-30% |
| 磁盘 | ~3GB | ~6GB |

### 推理速度

| 操作 | 预期时间 |
|------|---------|
| 文本分类 | < 1ms |
| 视觉分析 | 2-5 秒 |
| 嵌入生成 | < 1 秒 |
| 搜索查询 | < 2 秒 |

## 清理测试环境

```bash
# 停止并删除容器
docker-compose down

# 删除数据卷
docker-compose down -v

# 删除镜像
docker rmi memscreen-app

# 完全清理
docker system prune -a --volumes
```

## 下一步

测试通过后，您可以：

1. **部署到生产环境**
   - 配置 GPU 支持
   - 设置资源限制
   - 启用 HTTPS

2. **优化性能**
   - 调整模型参数
   - 使用模型量化
   - 启用批处理

3. **监控和维护**
   - 设置日志轮转
   - 配置健康检查
   - 设置自动备份

## 支持

遇到问题？
- 查看 [docs/DOCKER.md](DOCKER.md)
- 提交 [GitHub Issue](https://github.com/smileformylove/MemScreen/issues)
