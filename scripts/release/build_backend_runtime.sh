#!/usr/bin/env bash
# Build backend runtime package without bundled models.
# Users can download models on demand using download_models.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DIST_ROOT="$PROJECT_ROOT/dist/release/backend"
WORK_DIR="$DIST_ROOT/work"
WHEEL_DIR="$WORK_DIR/wheels"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[backend-package] python3 is required."
  exit 1
fi

VERSION="$(awk -F'"' '/^__version__ = /{print $2}' "$PROJECT_ROOT/memscreen/version.py")"
if [[ -z "$VERSION" ]]; then
  echo "[backend-package] Failed to parse version from memscreen/version.py"
  exit 1
fi

BUNDLE_NAME="MemScreen-backend-runtime-v${VERSION}"
BUNDLE_DIR="$WORK_DIR/$BUNDLE_NAME"
TAR_OUT="$DIST_ROOT/${BUNDLE_NAME}.tar.gz"

rm -rf "$WORK_DIR"
mkdir -p "$WHEEL_DIR" "$DIST_ROOT"

echo "[backend-package] building wheel"
python3 -m pip install -U pip >/dev/null
python3 -m pip wheel --no-deps "$PROJECT_ROOT" -w "$WHEEL_DIR" >/dev/null

WHEEL_FILE="$(find "$WHEEL_DIR" -maxdepth 1 -name "memscreen-${VERSION}-*.whl" | head -n 1)"
if [[ -z "$WHEEL_FILE" ]]; then
  echo "[backend-package] memscreen wheel not found in $WHEEL_DIR"
  exit 1
fi

mkdir -p "$BUNDLE_DIR/wheels"
cp "$WHEEL_FILE" "$BUNDLE_DIR/wheels/"
cp "$PROJECT_ROOT/setup/start_api_only.py" "$BUNDLE_DIR/"
cp "$PROJECT_ROOT/scripts/release/download_models.sh" "$BUNDLE_DIR/"

cat > "$BUNDLE_DIR/install_backend.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-$SCRIPT_DIR/.venv}"

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install -U pip

WHEEL_FILE="$(find "$SCRIPT_DIR/wheels" -maxdepth 1 -name "memscreen-*.whl" | head -n 1)"
if [[ -z "$WHEEL_FILE" ]]; then
  echo "[install-backend] memscreen wheel not found."
  exit 1
fi

python -m pip install "$WHEEL_FILE"

cat <<'TXT'
[install-backend] Done.
Start backend:
  source .venv/bin/activate
  python start_api_only.py
TXT
SH

cat > "$BUNDLE_DIR/README.md" <<'MD'
# MemScreen Backend Runtime (No Models Bundled)

This package contains:
- MemScreen Python backend wheel
- API start script (`start_api_only.py`)
- Optional model bootstrap script (`download_models.sh`)

## 1) Install backend runtime

```bash
./install_backend.sh
```

## 2) Start API

```bash
source .venv/bin/activate
python start_api_only.py
```

Default API URL:
- `http://127.0.0.1:8765`

## 3) Optional: install local models on demand

```bash
./download_models.sh recommended
```

Model download is optional. Recording and non-model core workflows can run without it.
MD

chmod +x "$BUNDLE_DIR/install_backend.sh"
chmod +x "$BUNDLE_DIR/download_models.sh"

rm -f "$TAR_OUT"
(cd "$WORK_DIR" && tar -czf "$TAR_OUT" "$BUNDLE_NAME")

echo "[backend-package] Done"
echo "  artifact: $TAR_OUT"
