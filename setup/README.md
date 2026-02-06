# Setup Directory

This directory contains all installation, deployment, and configuration related files for MemScreen.

## Directory Structure

```
setup/
├── bin/                  # Executable scripts
│   └── run_ui.sh              # Quick UI launcher
│
├── install/              # Installation scripts
│   ├── install_macos.sh       # macOS installation
│   ├── install_ubuntu.sh      # Ubuntu installation
│   ├── uninstall_ubuntu.sh    # Ubuntu uninstallation
│   ├── package_source.sh      # Source packaging
│   └── cleanup_project.sh     # Project cleanup
│
├── docker/               # Docker configurations
│   ├── docker-compose.yml             # Main compose file
│   ├── docker-compose.vllm.yml        # VLLM backend
│   └── docker-compose.step35flash.yml # Step 3.5 Flash
│
└── tools/                # Development tools
    └── optimize_models.py      # Model optimization utilities
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

### Package Source Code

```bash
./setup/install/package_source.sh
```

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
- Tested on Ubuntu 20.04+
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
- [Docker Guide](../docs/guides/DOCKER_TEST.md)
- [Recording Guide](../docs/RECORDING_GUIDE.md)
- [Accessibility Guide](../docs/guides/ACCESSIBILITY.md)
- [Process Mining Guide](../docs/guides/PROCESS_MINING.md)
