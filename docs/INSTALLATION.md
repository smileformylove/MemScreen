# Installation

This project is optimized for macOS with Flutter frontend + FastAPI backend.

## Recommended (one command)

```bash
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
python3 -m venv venv
source venv/bin/activate
pip install -e .
./scripts/launch.sh
```

What it does:
- prepares Python runtime
- starts backend API (`http://127.0.0.1:8765`)
- builds and launches Flutter macOS app

## Backend only

```bash
./scripts/launch.sh --mode api
```

## Flutter + existing backend

```bash
./scripts/launch.sh --mode flutter
```

## Optional model setup

Model capability is optional and not bundled in release runtime packages.

```bash
./scripts/release/download_models.sh recommended
```

## macOS permissions

Grant these permissions when prompted:
- Screen Recording
- Accessibility (for key/mouse tracking)
- Microphone (if microphone recording is enabled)
