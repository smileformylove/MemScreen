# MemScreen Flutter Frontend

Optional Flutter client for MemScreen, connected through HTTP API.
Default API URL: `http://127.0.0.1:8765`.

## Quick Start

### Recommended: one command from project root

```bash
./scripts/launch.sh
```

### Manual flow

1. Start backend API:

```bash
python -m memscreen.api
```

2. Run Flutter app:

```bash
cd frontend/flutter
flutter pub get
flutter run -d macos
```

If platform files are missing, run:

```bash
flutter create . --project-name memscreen_flutter
```

## Configuration

- API URL: default is `http://127.0.0.1:8765`.
- If connection fails, use in-app API URL configuration.
- See [docs/FLUTTER.md](../../docs/FLUTTER.md) for details.
