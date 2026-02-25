# Release Packaging (Frontend and Model Capability Decoupled)

This document defines MemScreen's split packaging strategy:

- `Frontend Installer`: end-user app package for direct install on macOS
- `Backend Runtime (No Models)`: local API runtime package
- `Model Bootstrap`: on-demand model download script (optional)

The goal is to avoid shipping large model files in the default installer.

---

## Artifact Strategy

### 1) Frontend Installer (direct install)

Output:
- `MemScreen-frontend-vX.Y.Z-macos.zip`
- `MemScreen-frontend-vX.Y.Z-macos.dmg`

Contains:
- Flutter desktop app (`MemScreen.app`)

Does not contain:
- Python backend runtime
- Ollama model files

Use case:
- User can install UI directly
- UI can connect to any reachable backend API URL

---

### 2) Backend Runtime (No Models)

Output:
- `MemScreen-backend-runtime-vX.Y.Z.tar.gz`

Contains:
- MemScreen Python wheel
- `start_api_only.py`
- `install_backend.sh`
- `download_models.sh`

Does not contain:
- Any pre-downloaded model weights

Use case:
- Self-hosted local API
- Core recording and non-model workflows

---

### 3) Model Bootstrap (optional)

Script:
- `scripts/release/download_models.sh`

Presets:
- `minimal`
- `recommended`
- `full`
- `custom <model...>`

Use case:
- Install model capability only when needed
- Keep default distribution lightweight

---

## Local Build Commands

### Build all artifacts

```bash
./scripts/release/build_all_release_artifacts.sh
```

### Build frontend installer only (macOS)

```bash
./scripts/release/build_frontend_macos.sh
```

### Build signed + notarized frontend installer (macOS)

```bash
export CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
export ENABLE_NOTARIZATION=1
export APPLE_ID="you@example.com"
export APPLE_APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
export APPLE_TEAM_ID="TEAMID"
./scripts/release/build_frontend_macos.sh
```

### Build backend runtime only

```bash
./scripts/release/build_backend_runtime.sh
```

### Download models on demand

```bash
./scripts/release/download_models.sh recommended
```

---

## GitHub Actions Automation

Workflow:
- `.github/workflows/release-packaging.yml`

Behavior:
- `workflow_dispatch`: build artifacts and upload as workflow artifacts
- `push tag v*`: build artifacts, upload, and publish to GitHub Release

Jobs:
- `frontend-macos`: build `.zip` and `.dmg`
- `backend-runtime`: build `.tar.gz` backend runtime package
- `publish-release`: attach both packages to the tagged release

### Optional signing/notarization secrets (for distributable macOS installers)

- `MACOS_CERT_P12_BASE64`: base64-encoded Developer ID certificate (`.p12`)
- `MACOS_CERT_PASSWORD`: password for `.p12`
- `MACOS_CERT_KEYCHAIN_PASSWORD`: temporary keychain password used in CI
- `MACOS_CODESIGN_IDENTITY`: signing identity string
- `APPLE_ID`: Apple account email for notarization
- `APPLE_APP_SPECIFIC_PASSWORD`: app-specific password for notarization
- `APPLE_TEAM_ID`: Apple Developer Team ID

When these are configured, the macOS frontend package is:
1. code signed
2. notarized
3. stapled

---

## Recommended User Delivery

For general users:
1. Download and install `Frontend Installer` first
2. Start backend runtime if local mode is needed
3. Download models only when AI features are required

This keeps first-time installation simple while preserving full local AI extensibility.
