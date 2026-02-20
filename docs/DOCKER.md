# Docker 

## 🐳  Docker  MemScreen

Docker 

## 

- Docker Engine 20.10+
- Docker Compose 2.0+ ()
-  8GB 
-  8GB+ RAM

## 

###  1:  Docker Compose

```bash
# 1. 
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen

# 2. 
docker-compose -f docker/docker-compose.yml up -d

# 3. 
docker-compose -f docker/docker-compose.yml logs -f memscreen

# 4. 
docker-compose -f docker/docker-compose.yml down
```

###  2:  Docker 

```bash
# 1. 
docker build -t memscreen:latest .

# 2. 
docker run -d \
  --name memscreen-app \
  -p 5901:5901 \
  -p 11434:11434 \
  -v memscreen_data:/app/db \
  -v ollama_models:/root/.ollama \
  memscreen:latest

# 3. 
docker logs -f memscreen-app

# 4. 
docker stop memscreen-app
docker rm memscreen-app
```

## 

### 

 `docker/docker-compose.yml` 

```yaml
environment:
  - DISPLAY=:99                    # 
  - OLLAMA_HOST=0.0.0.0:11434      # Ollama 
  - OLLAMA_NUM_PARALLEL=2          # 
```

### GPU 

 NVIDIA GPU `docker/docker-compose.yml`  GPU 

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### 

 Docker 

```bash
# 
docker volume ls | grep memscreen

# 
docker run --rm -v memscreen_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/memscreen-backup.tar.gz /data

# 
docker run --rm -v memscreen_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/memscreen-backup.tar.gz -C /
```

## 

### 



1. ** VNC **
   ```bash
   #  VNC 
   #  localhost:5901
   ```

2. ** noVNCWeb **
   ```bash
   #  docker/docker-compose.yml  novnc 
   docker-compose -f docker/docker-compose.yml up -d
   #  http://localhost:6080
   ```

### 

```bash
#  VNC 
docker run -d -p 5901:5901 memscreen:latest

#  SSH 
ssh -L 5901:localhost:5901 user@remote-server
```

## AI 

### 


- `qwen2.5vl:3b` (~2GB) - 
- `mxbai-embed-large` (~470MB) - 

### 

```bash
# 
docker exec -it memscreen-app bash

# 
ollama list

# 
ollama pull llama3.2:3b

# 
ollama rm qwen2.5vl:3b
```

### 

 `ollama_models` 

## 

### 1. Linux

```bash
docker run --network host memscreen:latest
```

### 2. 

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

### 3.  Ollama 

```bash
docker exec -it memscreen-app bash
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=2
ollama serve
```

## 

### 

```bash
# 
docker-compose logs -f --tail=100 memscreen

# 
docker ps -a | grep memscreen
```

### Ollama 

```bash
#  Ollama 
docker exec memscreen-app curl http://localhost:11434/api/tags

#  Ollama
docker exec memscreen-app pkill ollama
docker exec memscreen-app ollama serve &
```

### GUI 

```bash
#  Xvfb
docker exec memscreen-app ps aux | grep Xvfb

# 
docker exec memscreen-app pkill Xvfb
docker exec memscreen-app Xvfb :99 -screen 0 1920x1080x24 &
```

### 

```bash
# 
docker exec -it memscreen-app bash
ollama pull qwen2.5vl:3b

# 
export OLLAMA_HOST=https://ollama.example.com
```

## 

### 

```bash
docker run -it -v $(pwd):/app memscreen:latest bash
```

### 

```bash
# 
docker-compose -f docker-compose.dev.yml up
```

## 

### 

```bash
# 1. 
docker-compose -f docker/docker-compose.yml down

# 2. 
git pull

# 3. 
docker-compose -f docker/docker-compose.yml build --no-cache

# 4. 
docker-compose -f docker/docker-compose.yml up -d
```

### 

```bash
# 
docker image prune -a

# 
docker volume prune
```

## 

###  Docker Swarm

```bash
docker stack deploy -c docker/docker-compose.yml memscreen
```

###  Kubernetes

 `k8s/` 

## 

1. ****
2. ****
3. ****
4. ****
5. ** root **

```yaml
services:
  memscreen:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
```

## 

- [Docker ](https://docs.docker.com/)
- [Docker Compose ](https://docs.docker.com/compose/)
- [Ollama Docker ](https://github.com/ollama/ollama/blob/main/docker/README.md)

## 


- [GitHub Issues](https://github.com/smileformylove/MemScreen/issues)
- [](docs/)
- [Discussions](https://github.com/smileformylove/MemScreen/discussions)
