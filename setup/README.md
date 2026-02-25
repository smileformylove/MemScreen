# Setup Directory

This folder now keeps only runtime-related setup assets.

## Current structure

- `setup/start_api_only.py` - backend API entrypoint used by launcher/release runtime
- `setup/runtime/requirements.lite.txt` - lite backend dependencies for packaged app bootstrap
- `setup/docker/` - Docker compose and Docker API image assets

## Common usage

### Start API directly

```bash
python setup/start_api_only.py
```

### Start Docker stack

```bash
./scripts/docker-launch.sh
```

### Build macOS installer package

```bash
./scripts/release/build_all_release_artifacts.sh
```

See `docs/RELEASE_PACKAGING.md` for packaging details.
