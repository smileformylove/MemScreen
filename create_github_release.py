#!/usr/bin/env python3
"""
MemScreen GitHub Release Creator
Automates the process of creating GitHub releases with build artifacts
"""

import os
import sys
import subprocess
import json
import glob
from pathlib import Path

# Configuration
APP_NAME = "MemScreen"
REPO_OWNER = "smileformylove"
REPO_NAME = "MemScreen"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"{text.center(60)}")
    print(f"{'='*60}\n")

def print_step(text):
    print(f"➜ {text}")

def print_success(text):
    print(f"✓ {text}")

def print_error(text):
    print(f"✗ {text}")

def check_gh_cli():
    """Check if GitHub CLI (gh) is installed"""
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print_success(f"GitHub CLI found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("GitHub CLI (gh) not found")
        print("Install from: https://cli.github.com/")
        return False

def get_current_version():
    """Get current version from pyproject.toml"""
    try:
        with open("pyproject.toml", "r") as f:
            for line in f:
                if line.startswith("version ="):
                    version = line.split("=")[1].strip().strip('"')
                    return version
    except FileNotFoundError:
        pass
    return "0.4.0"

def check_git_status():
    """Check if git working directory is clean"""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            print_error("Git working directory is not clean")
            print("Please commit or stash changes first")
            return False
        return True
    except subprocess.CalledProcessError:
        return False

def create_git_tag(version):
    """Create and push git tag"""
    print_step(f"Creating git tag v{version}...")

    try:
        # Create annotated tag
        subprocess.run(
            ["git", "tag", "-a", f"v{version}", "-m", f"Release v{version}"],
            check=True
        )
        print_success(f"Tag v{version} created")

        # Push tag to remote
        subprocess.run(
            ["git", "push", "origin", f"v{version}"],
            check=True
        )
        print_success(f"Tag v{version} pushed to remote")
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create/push tag: {e}")
        return False

def find_build_artifacts():
    """Find all build artifacts in dist/ directory"""
    artifacts = []

    dist_dir = Path("dist")
    if not dist_dir.exists():
        print_error(f"dist/ directory not found")
        return []

    # Look for archives and installers
    patterns = [
        "*.zip",
        "*.dmg",
        "*.exe",
        "*.tar.gz",
        "*.pkg"
    ]

    for pattern in patterns:
        for artifact in dist_dir.glob(pattern):
            artifacts.append(artifact)

    return sorted(artifacts)

def create_release_notes(version):
    """Generate release notes"""
    release_notes = f"""## {APP_NAME} v{version}

### 🎉 Features

This release includes:
- AI-powered screen recording and analysis
- Natural language search through screen history
- Cross-platform support (Windows, macOS, Linux)
- Privacy-focused local processing
- OCR and computer vision capabilities
- Integration with Ollama for local AI inference

### 📦 Downloads

Choose the appropriate package for your platform:
- **Windows**: `{APP_NAME}-{version}-windows.zip`
- **macOS**: `{APP_NAME}-{version}-macos.zip`
- **Linux**: `{APP_NAME}-{version}-linux.zip`

### 🚀 Installation

1. Download the package for your platform
2. Extract the archive
3. Run `install_dependencies` (Windows: `.bat`, macOS/Linux: `.sh`)
4. Launch `{APP_NAME}`

### 📋 System Requirements

- **Windows**: Windows 10 or later
- **macOS**: macOS 10.15 (Catalina) or later
- **Linux**: Ubuntu 20.04+, Debian 11+, or Fedora 35+
- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 5GB free space
- **Software**: Ollama for AI models

### 🔧 First-Time Setup

After installing {APP_NAME}, you'll need to:

1. Install Ollama: https://ollama.com/download
2. Download AI models:
   ```bash
   ollama pull qwen2.5vl:3b
   ollama pull mxbai-embed-large
   ```
3. Launch {APP_NAME}

### 🐛 Bug Fixes

- Improved cross-platform compatibility
- Enhanced error handling and user feedback
- Better Ollama service management

### 📚 Documentation

- [Quick Start Guide](https://github.com/{REPO_OWNER}/{REPO_NAME}/wiki)
- [Installation Guide](https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/main/README.md)
- [Troubleshooting](https://github.com/{REPO_OWNER}/{REPO_NAME}/issues)

### 🙏 Acknowledgments

Thank you to all contributors and users!

### 📄 License

MIT License - See [LICENSE](https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/main/LICENSE)

---

**Full Changelog**: https://github.com/{REPO_OWNER}/{REPO_NAME}/compare/v{version}...HEAD
"""
    return release_notes

def create_github_release(version, artifacts, release_notes):
    """Create GitHub release and upload artifacts"""
    print_step(f"Creating GitHub release v{version}...")

    try:
        # Create release with assets
        cmd = [
            "gh", "release", "create",
            f"v{version}",
            "--title", f"{APP_NAME} v{version}",
            "--notes", release_notes
        ]

        # Add artifacts
        for artifact in artifacts:
            cmd.append(str(artifact))

        subprocess.run(cmd, check=True)
        print_success(f"GitHub release v{version} created")
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create release: {e}")
        return False

def main():
    """Main process"""
    print_header(f"{APP_NAME} GitHub Release Creator")

    # Check GitHub CLI
    if not check_gh_cli():
        sys.exit(1)

    # Check git status
    if not check_git_status():
        sys.exit(1)

    # Get version
    version = get_current_version()
    print_step(f"Version: {version}")

    # Check for existing tag
    try:
        subprocess.run(
            ["git", "rev-parse", f"v{version}"],
            capture_output=True,
            check=True
        )
        print_warning(f"Tag v{version} already exists")
        response = input("Continue and create release anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted")
            sys.exit(0)
    except subprocess.CalledProcessError:
        pass  # Tag doesn't exist, which is fine

    # Find build artifacts
    artifacts = find_build_artifacts()

    if not artifacts:
        print_error("No build artifacts found in dist/")
        print("Please run build_all.py first")
        sys.exit(1)

    print(f"\nFound {len(artifacts)} artifact(s):")
    for artifact in artifacts:
        size = artifact.stat().st_size / (1024 * 1024)  # Size in MB
        print(f"  • {artifact.name} ({size:.1f} MB)")

    # Generate release notes
    release_notes = create_release_notes(version)

    print(f"\n{'='*60}")
    print("Release Notes Preview:")
    print(f"{'='*60}")
    print(release_notes)
    print(f"{'='*60}\n")

    # Confirm
    response = input("Create release with these artifacts? (y/n): ")
    if response.lower() != 'y':
        print("Aborted")
        sys.exit(0)

    # Create git tag
    if not create_git_tag(version):
        sys.exit(1)

    # Create GitHub release
    if not create_github_release(version, artifacts, release_notes):
        print_error("Failed to create GitHub release")
        print("You can create it manually at:")
        print(f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/new")
        sys.exit(1)

    # Success
    print_header(f"Release v{version} Created Successfully!")
    print(f"View release at:")
    print(f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/tag/v{version}")

if __name__ == "__main__":
    main()
