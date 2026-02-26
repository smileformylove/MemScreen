# Release Packaging (Single Package, No Models Bundled)

MemScreen now ships as **one macOS installer package**.

Design target:
- user downloads one package
- user launches one app
- non-model features work without downloading models
- model capability remains optional/on-demand

---

## Artifact

Output:
- `MemScreen-vX.Y.Z-macos.dmg`

Contains:
- `MemScreen.app` (Flutter desktop UI)
- embedded backend bootstrap scripts and backend source
- embedded lite runtime requirements (`setup/runtime/requirements.lite.txt`)

Does not contain:
- pre-downloaded Ollama model weights

---

## Runtime Behavior

On app launch:
1. app wrapper checks `http://127.0.0.1:8765/health`
2. if backend is unavailable, it starts embedded backend bootstrap in background
3. bootstrap creates `~/.memscreen/runtime/.venv` and installs lite runtime dependencies
4. backend API starts locally, Flutter can reconnect immediately from the UI
5. backend startup always prioritizes bundled backend source (`MemScreen.app/Contents/Resources/backend/src`)

First launch can take longer because local backend runtime is prepared.

Logs:
- `~/.memscreen/logs/backend_bootstrap.log`
- `~/.memscreen/logs/api_from_app.log`
- `~/.memscreen/logs/app_wrapper.log`

---

## Local Build Command

```bash
./scripts/release/build_frontend_macos.sh
```

Or via aggregate command:

```bash
./scripts/release/build_all_release_artifacts.sh
```

---

## Optional Signing/Notarization

```bash
export CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
export ENABLE_NOTARIZATION=1
export APPLE_ID="you@example.com"
export APPLE_APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
export APPLE_TEAM_ID="TEAMID"
./scripts/release/build_frontend_macos.sh
```

---

## Optional Model Bootstrap

Model files are intentionally excluded from installer.

After app installation, models can be pulled with bundled script:
- `MemScreen.app/Contents/Resources/backend/download_models.sh`

---

## GitHub Actions

Workflow:
- `.github/workflows/release-packaging.yml`

Behavior:
- `workflow_dispatch`: build installer and upload artifact
- `push tag v*`: build installer and publish GitHub release asset
- before upload/release, installer smoke test must pass:
  - mount dmg
  - run embedded backend bootstrap
  - verify `/health` + `/recording/screens` + `/recording/status`

Current release output is a single macOS installer package.
