#!/usr/bin/env python3
"""
MemScreen Cross-Platform Build Script
Builds distributable packages for Windows, macOS, and Linux
"""

import os
import sys
import subprocess
import shutil
import platform
import zipfile
from pathlib import Path

# Configuration
APP_NAME = "MemScreen"
APP_VERSION = "0.4.0"
REPO_URL = "https://github.com/smileformylove/MemScreen"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_step(text):
    print(f"{Colors.CYAN}➜{Colors.END} {text}")

def print_success(text):
    print(f"{Colors.GREEN}✓{Colors.END} {text}")

def print_error(text):
    print(f"{Colors.RED}✗{Colors.END} {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")

def run_command(cmd, shell=False):
    """Run a command and return True if successful"""
    try:
        subprocess.run(cmd, check=True, shell=shell)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        return False

def check_dependencies():
    """Check if required build tools are installed"""
    print_step("Checking build dependencies...")

    # Check Python version
    if sys.version_info < (3, 8):
        print_error("Python 3.8 or higher is required")
        return False
    print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Check PyInstaller
    try:
        import PyInstaller
        print_success(f"PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print_warning("PyInstaller not found. Installing...")
        if not run_command([sys.executable, "-m", "pip", "install", "--user", "pyinstaller"]):
            print_error("Failed to install PyInstaller")
            return False

    # Check required Python packages
    required_packages = [
        'kivy', 'torch', 'cv2', 'chromadb', 'ollama'
    ]

    for package in required_packages:
        try:
            __import__(package)
            print_success(f"{package} is installed")
        except ImportError:
            print_warning(f"{package} not found. Installing...")
            # Don't fail, just warn - packages may be bundled differently

    return True

def clean_build_dirs():
    """Clean previous build directories"""
    print_step("Cleaning previous builds...")

    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print_success(f"Removed {dir_name}/")

def build_with_pyinstaller():
    """Build application using PyInstaller"""
    print_step("Building with PyInstaller...")

    spec_file = "MemScreen.spec"
    if not os.path.exists(spec_file):
        print_error(f"Spec file not found: {spec_file}")
        return False

    if not run_command([sys.executable, "-m", "PyInstaller", spec_file, "--clean"]):
        return False

    print_success("PyInstaller build completed")
    return True

def create_readme():
    """Create README.txt for distribution"""
    readme_content = f"""{APP_NAME} - AI-Powered Visual Memory System
Version: {APP_VERSION}
Repository: {REPO_URL}

QUICK START
============

1. Install Ollama:
   - Windows: Download from https://ollama.com/download
   - macOS: brew install ollama
   - Linux: curl -fsSL https://ollama.com/install.sh | sh

2. Download AI Models:
   ollama pull qwen2.5vl:3b
   ollama pull mxbai-embed-large

3. Run {APP_NAME}:
   - Windows: Double-click {APP_NAME}.exe
   - macOS: Double-click {APP_NAME}.app
   - Linux: Run ./{APP_NAME}/{APP_NAME}

SYSTEM REQUIREMENTS
===================

- Operating System:
  * Windows 10 or later
  * macOS 10.15 (Catalina) or later
  * Linux (Ubuntu 20.04+, Debian 11+, Fedora 35+)

- Hardware:
  * 8GB RAM minimum (16GB recommended)
  * 5GB free disk space
  * Modern CPU with AVX support

- Software:
  * Ollama for AI models
  * Internet connection for first-time model download

FEATURES
========

• Screen Recording with OCR
• AI-Powered Content Understanding
• Natural Language Search
• Cross-Platform Support
• Privacy-Focused (All data stays local)

TROUBLESHOOTING
===============

Q: App won't start
A: Make sure Ollama is installed and running:
   ollama serve

Q: Models not downloading
A: Check your internet connection and try again:
   ollama pull qwen2.5vl:3b
   ollama pull mxbai-embed-large

Q: Performance issues
A: Close other applications and ensure you have enough RAM

SUPPORT
=======

• Documentation: {REPO_URL}/wiki
• Issues: {REPO_URL}/issues
• Email: jixiangluo85@gmail.com

LICENSE
=======

MIT License - See LICENSE file for details

Copyright © 2024 Jixiang Luo
"""

    readme_path = os.path.join("dist", "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print_success(f"Created README.txt")
    return readme_path

def create_install_script():
    """Create platform-specific installation script"""
    system = platform.system()

    if system == "Windows":
        script_content = """@echo off
REM MemScreen Dependency Installer for Windows

echo MemScreen - Installing Ollama
echo ================================
echo.

REM Check if Ollama is installed
where ollama >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Ollama is already installed
) else (
    echo Please download and install Ollama from:
    echo https://ollama.com/download
    echo.
    pause
    exit /b 1
)

echo.
echo Downloading AI models...
echo This may take 10-20 minutes depending on your connection
echo.

ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large

echo.
echo ================================
echo Installation complete!
echo You can now launch MemScreen.exe
echo ================================
pause
"""
        script_name = "install_dependencies.bat"
    else:
        script_content = """#!/bin/bash
# MemScreen Dependency Installer for macOS/Linux

echo "MemScreen - Installing Ollama"
echo "================================"
echo ""

# Check if Ollama is installed
if command -v ollama &> /dev/null; then
    echo "✓ Ollama is already installed"
else
    echo "Please install Ollama:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install ollama"
    else
        echo "  curl -fsSL https://ollama.com/install.sh | sh"
    fi
    echo ""
    read -p "Press Enter to open Ollama download page..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "https://ollama.com/download"
    else
        xdg-open "https://ollama.com/download" 2>/dev/null || \
        firefox "https://ollama.com/download" 2>/dev/null || \
        google-chrome "https://ollama.com/download" 2>/dev/null
    fi
    exit 1
fi

echo ""
echo "Downloading AI models..."
echo "This may take 10-20 minutes depending on your connection"
echo ""

ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large

echo ""
echo "================================"
echo "✓ Installation complete!"
echo "You can now launch MemScreen"
echo "================================"
"""
        script_name = "install_dependencies.sh"

    script_path = os.path.join("dist", script_name)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    if system != "Windows":
        os.chmod(script_path, 0o755)

    print_success(f"Created {script_name}")
    return script_path

def create_archive():
    """Create a compressed archive of the built application"""
    print_step("Creating distribution archive...")

    system = platform.system()
    dist_dir = Path("dist")

    if system == "Windows":
        archive_name = f"{APP_NAME}-{APP_VERSION}-windows.zip"
        app_path = dist_dir / APP_NAME / f"{APP_NAME}.exe"
    elif system == "Darwin":
        archive_name = f"{APP_NAME}-{APP_VERSION}-macos.zip"
        app_path = dist_dir / f"{APP_NAME}.app"
    else:  # Linux
        archive_name = f"{APP_NAME}-{APP_VERSION}-linux.zip"
        app_path = dist_dir / APP_NAME / APP_NAME

    if not app_path.exists():
        print_error(f"Application not found at {app_path}")
        return None

    archive_path = dist_dir / archive_name

    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add application
        if system == "Darwin":
            for root, dirs, files in os.walk(app_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dist_dir)
                    zipf.write(file_path, arcname)
        else:
            for root, dirs, files in os.walk(dist_dir / APP_NAME):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dist_dir)
                    zipf.write(file_path, arcname)

        # Add README and install script
        readme_path = dist_dir / "README.txt"
        if readme_path.exists():
            zipf.write(readme_path, "README.txt")

        if system == "Windows":
            script_path = dist_dir / "install_dependencies.bat"
        else:
            script_path = dist_dir / "install_dependencies.sh"

        if script_path.exists():
            zipf.write(script_path, script_path.name)

    print_success(f"Created archive: {archive_path}")
    return archive_path

def print_summary():
    """Print build summary"""
    system = platform.system()

    print_header("Build Summary")

    print(f"{Colors.BOLD}Platform:{Colors.END} {system}")
    print(f"{Colors.BOLD}Version:{Colors.END} {APP_VERSION}")
    print(f"{Colors.BOLD}Output Directory:{Colors.END} dist/")

    print(f"\n{Colors.BOLD}Generated Files:{Colors.END}")

    dist_dir = Path("dist")
    for file in sorted(dist_dir.glob("*")):
        size = file.stat().st_size / (1024 * 1024)  # Size in MB
        print(f"  • {file.name} ({size:.1f} MB)")

    print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
    print(f"  1. Test the application to ensure it works")
    print(f"  2. Create a GitHub release:")
    print(f"     git tag -a v{APP_VERSION} -m 'Release v{APP_VERSION}'")
    print(f"     git push origin v{APP_VERSION}")
    print(f"  3. Upload the archive to GitHub Releases")
    print(f"  4. Announce the release")

    print(f"\n{Colors.GREEN}{Colors.BOLD}Build Complete! 🎉{Colors.END}\n")

def main():
    """Main build process"""
    print_header(f"Building {APP_NAME} v{APP_VERSION}")

    # Check dependencies
    if not check_dependencies():
        print_error("Missing required dependencies")
        sys.exit(1)

    # Clean previous builds
    clean_build_dirs()

    # Build with PyInstaller
    if not build_with_pyinstaller():
        print_error("Build failed")
        sys.exit(1)

    # Create README
    create_readme()

    # Create install script
    create_install_script()

    # Create archive
    archive_path = create_archive()
    if not archive_path:
        print_warning("Archive creation failed, but build succeeded")

    # Print summary
    print_summary()

if __name__ == "__main__":
    main()
