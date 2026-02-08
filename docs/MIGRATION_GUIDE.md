# 🔄 Migration Guide - v0.6.0

## 📅 Date: February 8, 2026

## 🎯 Overview

Version 0.6.0 includes a major project reorganization. If you're upgrading from an earlier version, some file paths have changed.

---

## 📂 File Location Changes

### Quick Reference Table

| Old Location | New Location |
|--------------|--------------|
| `start.py` | `setup/start.py` |
| `run.sh` | `setup/run.sh` |
| `run.bat` | `setup/run.bat` |
| `install.sh` | `setup/install/install.sh` |
| `setup-dev.sh` | `setup/install/setup-dev.sh` |
| `config_example.yaml` | `config/config_example.yaml` |
| `MANIFEST.in` | `setup/MANIFEST.in` |
| `Dockerfile` | `setup/docker/Dockerfile` |
| `docker-entrypoint.sh` | `setup/docker/docker-entrypoint.sh` |
| `CHANGELOG.md` | `docs/CHANGELOG.md` |
| `PROJECT_STRUCTURE.md` | `docs/PROJECT_STRUCTURE.md` |

---

## 🚀 Update Your Commands

### Starting the Application

#### Before (v0.5.x)
```bash
python start.py
# or
./run.sh
```

#### After (v0.6.0)
```bash
python setup/start.py
# or
./setup/run.sh
```

### Installing

#### Before (v0.5.x)
```bash
./install.sh
```

#### After (v0.6.0)
```bash
./setup/install/install.sh
```

### Configuration Files

#### Before (v0.5.x)
```python
config_path = 'config_example.yaml'
```

#### After (v0.6.0)
```python
config_path = 'config/config_example.yaml'
```

### Docker

#### Before (v0.5.x)
```bash
docker build -t memscreen .
docker run -v ~/.memscreen:/root/.memscreen memscreen
```

#### After (v0.6.0)
```bash
docker build -f setup/docker/Dockerfile -t memscreen .
docker run -v ~/.memscreen:/root/.memscreen memscreen
```

---

## 📖 Documentation Links

All documentation links have been updated in README.md. If you have hardcoded links in your own documentation or scripts:

#### Before (v0.5.x)
```markdown
See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
See [CHANGELOG](CHANGELOG.md)
```

#### After (v0.6.0)
```markdown
See [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
See [CHANGELOG](docs/CHANGELOG.md)
```

---

## 🔄 Automated Migration Script

If you want to automatically update your local references:

```bash
# Create a backup
cp -r MemScreen MemScreen.backup

# Run the migration script (if available)
python setup/tools/migrate_paths.py

# Or manually update using sed
find . -name "*.py" -o -name "*.sh" -o -name "*.md" | xargs sed -i '' 's|python start.py|python setup/start.py|g'
find . -name "*.py" -o -name "*.sh" -o -name "*.md" | xargs sed -i '' 's|./run.sh|./setup/run.sh|g'
find . -name "*.py" -o -name "*.sh" -o -name "*.md" | xargs sed -i '' 's|config_example\.yaml|config/config_example.yaml|g'
```

---

## ✅ Checklist for Upgrading

- [ ] Update startup commands in scripts
- [ ] Update configuration file paths
- [ ] Update Docker commands
- [ ] Update documentation links
- [ ] Update CI/CD pipelines
- [ ] Update any hardcoded paths in custom scripts

---

## 💡 Common Issues

### Issue: "File not found" error

**Solution**: Update your command to use the new path:
```bash
# Old
python start.py

# New
python setup/start.py
```

### Issue: "Configuration not loading"

**Solution**: Update config path:
```python
# Old
config_path = 'config_example.yaml'

# New
config_path = 'config/config_example.yaml'
```

### Issue: "Docker build fails"

**Solution**: Use new Dockerfile path:
```bash
# Old
docker build -t memscreen .

# New
docker build -f setup/docker/Dockerfile -t memscreen .
```

---

## 🆘 Need Help?

If you encounter any issues during migration:

1. 📖 Check the [Cleanup Documentation](docs/cleanup/CLEANUP_COMPLETE.md)
2. 🐛 [Report an issue](https://github.com/smileformylove/MemScreen/issues)
3. 💬 Start a [discussion](https://github.com/smileformylove/MemScreen/discussions)

---

## 📊 Summary

- **12 files moved** to new locations
- **Root directory simplified**: 15 files → 3 files
- **Better organization**: docs/, config/, setup/
- **Breaking changes**: Yes (file locations only)
- **API changes**: None

---

## ✨ Benefits

Despite the file location changes, v0.6.0 brings:

1. ✨ **Cleaner root directory** - Only 3 essential files
2. 📚 **Better documentation** - Centralized in `docs/`
3. 🛠️ **Easier maintenance** - Logical file organization
4. 🎯 **Professional structure** - Follows Python best practices

**All functionality remains the same - only file locations have changed!**

---

**Need more details?** See [CLEANUP_COMPLETE.md](docs/cleanup/CLEANUP_COMPLETE.md)
