# Setup Directory

This directory contains all installation, building, and deployment related files for MemScreen.

## Directory Structure

```
setup/
├── install/              # Installation scripts
│   ├── install_macos.sh      # macOS installation
│   ├── install_ubuntu.sh     # Ubuntu installation
│   ├── uninstall_ubuntu.sh   # Ubuntu uninstallation
│   ├── package_source.sh     # Source packaging
│   └── cleanup_project.sh    # Project cleanup
│
├── build/                # Build and packaging configurations
│   ├── pyinstaller/           # PyInstaller configurations
│   │   ├── build_macos.sh         # macOS build script
│   │   ├── memscreen_macos.spec   # macOS spec file
│   │   ├── memscreen_linux.spec   # Linux spec file
│   │   └── memscreen_windows.spec # Windows spec file
│   └── platforms/             # Platform-specific packaging
│       ├── macos/              # macOS packages
│       ├── linux/              # Linux packages
│       ├── windows/            # Windows packages
│       └── common/             # Common packaging files
│
├── docker/               # Docker configurations
│   ├── docker-compose.yml           # Main compose file
│   ├── docker-compose.vllm.yml      # VLLM backend
│   └── docker-compose.step35flash.yml # Step 3.5 Flash
│
├── tools/                # Build and development tools
│   └── optimize_models.py         # Model optimization utilities
│
└── bin/                  # Executable scripts
    └── run_ui.sh                # Quick UI launcher
```

## Quick Start

### Install MemScreen

**macOS:**
```bash
sudo ./setup/install/install_macos.sh
```

**Ubuntu:**
```bash
sudo ./setup/install/install_ubuntu.sh
```

### Build Application Bundle

**macOS:**
```bash
./setup/build/pyinstaller/build_macos.sh
```

The built app will be in `setup/build/pyinstaller/dist/MemScreen.app`

### Run Docker

```bash
cd setup/docker
docker-compose up
```

## Platform-Specific Notes

### macOS
- Requires macOS 11.0 (Big Sur) or later
- Requires Xcode Command Line Tools for building
- Screen Recording and Accessibility permissions required

### Linux
- Tested on Ubuntu 20.04+, Fedora 33+, Arch Linux
- Requires Python 3.8+
- Some distributions may require additional dependencies

### Windows
- Requires Windows 10 or later (64-bit)
- Requires Python 3.8+ from python.org
- May require Visual C++ Redistributable

## Maintenance

### Clean Build Artifacts
```bash
./setup/install/cleanup_project.sh
```

### Package Source Code
```bash
./setup/install/package_source.sh
```

## Documentation

For complete documentation, see the [docs/](../docs/) directory:
- [Installation Guide](../docs/INSTALLATION.md)
- [macOS Build Guide](../docs/MACOS_BUILD_GUIDE.md)
- [Docker Guide](../docs/DOCKER.md)
- [Audio Recording](../docs/AUDIO_RECORDING.md)
