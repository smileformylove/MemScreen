# Docker 

## 

- Docker Engine 20.10+
- Docker Compose 2.0+
-  8GB 
-  8GB+ RAM

## 

### 1. 

```bash
# 
chmod +x test_docker.sh

# 
./test_docker.sh
```


- ✅  Docker 
- ✅ 
- ✅ 
- ✅  Ollama 
- ✅  Python 
- ✅ 

### 2. 

####  1: 

```bash
docker-compose build
```


```
[+] Building 123.4s (15/15) FINISHED
 => => naming to docker.io/library/memscreen-app
```

####  2: 

```bash
docker-compose up -d
```


```
[+] Running 2/2
 ✔ Volume "ollama_models"  Created
 ✔ Container memscreen-app  Started
```

####  3: 

```bash
docker-compose logs -f memscreen
```


```
==========================================
🦉 MemScreen Docker 
==========================================
📺 ...
🖥️ ...
🤖  Ollama ...
✅ Ollama 
📥  AI ...
    qwen2.5vl:3b (~2GB)...
    mxbai-embed-large (~470MB)...
✅ AI 
🚀  MemScreen ...
```

####  4: 

```bash
#  Ollama API
curl http://localhost:11434/api/tags

# 
docker exec -it memscreen-app bash

# 
ollama list

# 
exit
```

## 

###  1: 

```bash
# 1. 
docker-compose up -d

# 2. 
docker-compose logs -f memscreen | grep "✅"

# 3. 
docker ps | grep memscreen-app

# 4. 
docker stats memscreen-app
```

**:**
- ✅  `Up`
- ✅  < 4GB
- ✅ CPU 

###  2: 

```bash
# 
docker exec -it memscreen-app bash

# 
echo "..."
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5vl:3b",
  "prompt": "What is in this image?",
  "stream": false
}'

# 
echo "..."
curl http://localhost:11434/api/embed -d '{
  "model": "mxbai-embed-large",
  "input": "Hello, MemScreen!"
}'
```

**:**
- ✅ 
- ✅ 
- ✅  < 10

###  3: 

```bash
# 1. 
docker exec memscreen-app python -c "
from memscreen.memory import Memory
m = Memory()
m.add(messages=[{'role': 'user', 'content': 'Test'}], user_id='test')
print('Data added')
"

# 2. 
docker-compose down

# 3. 
docker-compose up -d

# 4. 
docker exec memscreen-app python -c "
from memscreen.memory import Memory
m = Memory()
results = m.search(query='Test', user_id='test')
print(f'Found {len(results.get(\"results\", []))} results')
"
```

**:**
- ✅  1 
- ✅ 

###  4: 

```bash
# 
time docker exec memscreen-app python -c "
from memscreen.memory import InputClassifier
classifier = InputClassifier()
result = classifier.classify_input(' Python')
print(f': {result.category.value}')
print(f': {result.confidence}')
"
```

**:**
- ✅  < 100ms
- ✅ question
- ✅  > 0.8

## 

###  1: 

```bash
# 
docker-compose logs memscreen

# 
docker ps -a | grep memscreen
```

**:**
- 
- 
-  (11434, 5901)

**:**
```bash
# 
docker system prune -a

# 
docker volume prune

#  docker-compose.yml 
ports:
  - "11435:11434"  # 
```

###  2: 

```bash
# 
docker exec -it memscreen-app bash
ollama pull qwen2.5vl:3b

# 
export OLLAMA_HOST=https://ollama.example.com
ollama pull qwen2.5vl:3b
```

###  3: Ollama 

```bash
#  Ollama 
docker exec memscreen-app ps aux | grep ollama

#  Ollama
docker exec memscreen-app pkill ollama
docker exec memscreen-app ollama serve &

# 
docker exec memscreen-app curl http://localhost:11434/api/tags
```

###  4: 

```bash
# 
docker-compose down
#  docker-compose.yml
# :
# services:
#   memscreen:
#     deploy:
#       resources:
#         limits:
#           memory: 4G

docker-compose up -d
```

## 

### 

|  |  |
|------|---------|
|  | 3-5  |
|  | 5-10  () |
|  | 10-15  |
|  () | 8-15  |
|  () | 30-60  |

### 

|  |  |  |
|------|------|--------|
|  | ~500MB | ~2GB |
| CPU | < 5% | 10-30% |
|  | ~3GB | ~6GB |

### 

|  |  |
|------|---------|
|  | < 1ms |
|  | 2-5  |
|  | < 1  |
|  | < 2  |

## 

```bash
# 
docker-compose down

# 
docker-compose down -v

# 
docker rmi memscreen-app

# 
docker system prune -a --volumes
```

## 



1. ****
   -  GPU 
   - 
   -  HTTPS

2. ****
   - 
   - 
   - 

3. ****
   - 
   - 
   - 

## 


-  [docs/DOCKER.md](DOCKER.md)
-  [GitHub Issue](https://github.com/smileformylove/MemScreen/issues)
