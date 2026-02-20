# MemScreen Quick Start

This guide helps you run MemScreen quickly on macOS, Linux, or Windows.

## Option 1: Fast Start (Recommended)

```bash
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e .
./scripts/start_flutter.sh
```

What `./scripts/start_flutter.sh` does:
- Starts the backend API
- Installs Flutter dependencies (if needed)
- Builds and launches the Flutter app

## Option 2: Manual Start

### 1. Install prerequisites
- Python 3.8+
- Ollama
- Flutter SDK (for Flutter UI)

### 2. Install project

```bash
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e .
```

### 3. Download models

```bash
ollama serve
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large
```

### 4. Start backend

```bash
python -m memscreen.api
```

### 5. Start frontend

```bash
cd frontend/flutter
flutter pub get
flutter run -d macos
```

## Common Issues

### Backend not reachable
- Check API health: `curl http://127.0.0.1:8765/health`
- Verify backend process is running
- Confirm API URL in app settings

### Ollama model missing
```bash
ollama list
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large
```

### macOS screen recording permission
- Open **System Settings → Privacy & Security → Screen Recording**
- Enable permission for Terminal/Python/MemScreen
- Restart the app

## Next Steps
- Main docs: `README.md`
- Flutter details: `docs/FLUTTER.md`
- API details: `docs/API_HTTP.md`
