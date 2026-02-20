# MemScreen Flutter Frontend

MemScreen provides a Flutter desktop client that communicates with the backend over HTTP.

## Prerequisites
- Flutter SDK 3.0+
- Python 3.8+
- MemScreen backend dependencies installed

## Start with one command (recommended)

```bash
./scripts/start_flutter.sh
```

This script will:
- Start backend API at `http://127.0.0.1:8765`
- Install Flutter dependencies
- Build and run the Flutter app

## Manual startup

### 1) Start backend

```bash
conda activate MemScreen
python -m memscreen.api
```

### 2) Start Flutter app

```bash
cd frontend/flutter
flutter pub get
flutter run -d macos
```

## API configuration
- Default API URL: `http://127.0.0.1:8765`
- You can update API URL in the app settings when needed.

## Frontend structure

```text
frontend/flutter/
├── lib/
│   ├── main.dart
│   ├── app_state.dart
│   ├── api/
│   ├── connection/
│   └── screens/
├── pubspec.yaml
└── README.md
```

## Main screens
- Chat
- Process
- Recording
- Videos
- Settings

## Related docs
- API reference: `docs/API_HTTP.md`
- Main project overview: `README.md`
