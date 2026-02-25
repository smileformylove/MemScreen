# Flutter Frontend

MemScreen uses Flutter desktop as the primary UI.

## Recommended start

```bash
./scripts/launch.sh
```

## Manual start

### 1) start backend

```bash
./scripts/launch.sh --mode api
```

### 2) start frontend build/run

```bash
cd frontend/flutter
flutter pub get
flutter run -d macos
```

## API URL

Default backend URL:
- `http://127.0.0.1:8765`

You can reconfigure API URL from the in-app connection UI.

## Packaging

Frontend installer build:

```bash
./scripts/release/build_frontend_macos.sh
```
