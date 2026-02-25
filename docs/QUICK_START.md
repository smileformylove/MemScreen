# Quick Start

## One command (recommended)

```bash
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
python3 -m venv venv
source venv/bin/activate
pip install -e .
./scripts/launch.sh
```

## Optional: model capability setup

```bash
./scripts/release/download_models.sh recommended
```

## Docker backend stack

```bash
./scripts/docker-launch.sh
```

## Health checks

```bash
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:11434/api/tags
```
