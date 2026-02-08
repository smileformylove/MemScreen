# Project Organization - 2026-02-08

## Project Restructuring Summary

This document describes the project organization cleanup performed on February 8, 2026.

## Root Directory

The root directory now contains only essential files:

```
MemScreen/
├── LICENSE              # License file
├── README.md            # Main project README
├── pyproject.toml       # Python project configuration (PEP 518)
├── assets/              # Application assets (logos, icons)
├── config/              # Configuration files
├── db/                  # Database files (gitignored)
├── docs/                # Documentation
├── examples/            # Example scripts
├── memscreen/           # Main application package
├── setup/               # Installation and build files
└── tests/               # Test suite
```

## Directory Structure Changes

### Before
- Root directory contained 15+ files including documentation, configs, and scripts
- Mixed concerns at the root level
- Difficult to navigate

### After
- Root directory contains only 3 files (LICENSE, README.md, pyproject.toml)
- Clear separation of concerns
- Easy to navigate

## File Movements

### Documentation → `docs/`
- `CHANGELOG.md` → `docs/CHANGELOG.md`
- `PROJECT_STRUCTURE.md` → `docs/PROJECT_STRUCTURE.md`
- Cleanup documents → `docs/cleanup/`
  - `CLEANUP_2026_02_08.md`
  - `CLEANUP_SUMMARY.md`

### Configuration → `config/`
- `config_example.yaml` → `config/config_example.yaml`

### Installation Files → `setup/`
- `MANIFEST.in` → `setup/MANIFEST.in`
- `start.py` → `setup/start.py`
- `run.sh` → `setup/run.sh`
- `run.bat` → `setup/run.bat`

### Installation Scripts → `setup/install/`
- `install.sh` → `setup/install/install.sh`
- `setup-dev.sh` → `setup/install/setup-dev.sh`

### Docker Files → `setup/docker/`
- `Dockerfile` → `setup/docker/Dockerfile`
- `docker-entrypoint.sh` → `setup/docker/docker-entrypoint.sh`

### Test Files → `tests/`
- `test_region_select.py` → `tests/test_region_select.py`

## Directory Details

### `docs/`
Contains all project documentation:
- Architecture docs
- Installation guides
- User guides
- API documentation
- Changelog
- `cleanup/` - Cleanup and maintenance documentation

### `config/`
Contains configuration files and examples:
- `config_example.yaml` - Example configuration with all available options

### `setup/`
Contains installation, build, and deployment files:
- `install/` - Installation scripts for different platforms
- `docker/` - Docker configuration files
- `tools/` - Build and packaging tools
- `bin/` - Compiled binaries
- `build/` - Build artifacts (gitignored)
- `MANIFEST.in` - Package manifest
- `start.py` - Application starter
- `run.sh` / `run.bat` - Run scripts
- `README.md` - Setup documentation

### `tests/`
Contains all test files:
- Integration tests
- Unit tests
- Test utilities
- `test_region_select.py` - Region selector test

## Benefits

1. **Cleaner Root**: Only 3 files in root directory
2. **Better Organization**: Logical grouping of related files
3. **Easier Navigation**: Clear directory structure
4. **Professional Layout**: Follows Python project best practices
5. **Maintainability**: Easier to find and update files

## Compatibility

All file movements are transparent to the application:
- Python imports remain unchanged
- Configuration loading updated to use new paths
- Installation scripts updated to use new paths
- Documentation links updated where necessary

## Migration Notes

If you have any scripts or references to old file locations, update them:

### Configuration Files
```python
# Old
config_path = 'config_example.yaml'

# New
config_path = 'config/config_example.yaml'
```

### Setup Files
```bash
# Old
python start.py
./install.sh

# New
python setup/start.py
./setup/install/install.sh
```

### Documentation
```markdown
# Old
See CHANGELOG.md

# New
See [CHANGELOG](docs/CHANGELOG.md)
```

## Future Improvements

Consider further organization:
- Add `scripts/` directory for utility scripts
- Add `tools/` directory for development tools
- Consolidate similar documentation files
- Add index files for better navigation
