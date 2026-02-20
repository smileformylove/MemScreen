# MemScreen 

## 📋 

 MemScreen 

### 

|  |  |  |
|------|------|------|
| **** |  |  |
| **Mac** | PythonOllama |  |
| **** | cv2PyInstaller |  |
| **Process** | pynputAccessibilityPyInstaller |  |

---

## ✅ 

### 1. 

#### 1.1 

- **`setup/build/pyinstaller/build_macos.sh`**: macOS
  - 
  - PyInstaller.app
  - SDL2
  - ad-hoc
  - DMG

#### 1.2 

```bash
# macOS
cd pyinstaller
./build_macos.sh

# 
# - dist/MemScreen.app ()
# - dist/MemScreen_0.5.0_macOS.dmg ()
```

### 2. 

#### 2.1 

- `cv2_loader.py` PyInstallercv2
- cv2cv2.cuda, cv2.gapi

#### 2.2 

****: `memscreen/cv2_loader.py`

```python
# PyInstallerNone
if hasattr(sys, '_MEIPASS'):
    print("[cv2_loader] Running in PyInstaller bundle - cv2 is disabled")
    return None

# cv2runtime hook
if hasattr(sys, '_MEIPASS'):
    print("[cv2_loader] Running in PyInstaller bundle - attempting to load cv2...")
    # 
```

****
- `pyinstaller/rthook/pyi_rthook_cv2.py`: cv2 runtime hook
- `pyinstaller/hooks/hook-cv2.py`: cv2 PyInstaller hook
- `pyinstaller/memscreen_macos.spec`: cv2

### 3. Process

#### 3.1 

- pynputmacOSAccessibility
- PyInstallerpynputPyObjC, Quartz, Cocoa

#### 3.2 

****: `pyinstaller/rthook/pyi_rthook_pynput.py`

- PyObjCQuartzCocoa
- 

****: `pyinstaller/memscreen_macos.spec`

```python
# pynput runtime hook
runtime_hooks=[
    ...
    os.path.join(spec_dir, 'rthook/pyi_rthook_pynput.py'),
],
```

****

```
System Settings > Privacy & Security > Accessibility >  MemScreen
```

### 4. 

#### 4.1 


1. DMG
2. DMGMemScreen.appApplications
3. 

#### 4.2 

- Python: .app
- Ollama: 
- AI: 

---

## 🔧 

### macOS

```bash
# 1. 
brew install python3  # Python
pip3 install pyinstaller  # PyInstaller

# 2. 
cd /path/to/MemScreen/pyinstaller
./build_macos.sh

# 3. 
open dist/MemScreen.app

# 4. 
# Apple Developer
codesign --force --deep --sign "Developer ID Application: Your Name" dist/MemScreen.app
xcrun notarytool submit dist/MemScreen_0.5.0_macOS.dmg --apple-id "..." --password "..." --team-id "..."
```

### 

`pyinstaller/build_macos.sh` 

1. ****: PythonPyInstallerspec
2. ****: build/dist/
3. **PyInstaller**: spec.app
4. **SDL2**: cv2SDL2bundle
5. **Ad-hoc**: 
6. ****: app
7. **DMG**: DMG

---

## 📦 

```
MemScreen.app/
├── Contents/
│   ├── Info.plist              # 
│   ├── MacOS/
│   │   └── MemScreen            # 
│   └── Resources/
│       ├── assets/             # logo
│       ├── cv2/                # OpenCV
│       │   ├── .dylibs/        # SDL2
│       │   └── data/           # cv2
│       ├── kivy/               # Kivy GUI
│       │   └── .dylibs/        # KivySDL2
│       ├── memscreen/          # 
│       └── _internal/          # Python
```

---

## 🎯 

### 

1. ****: GitHub ReleasesDMG
2. ****: DMGMemScreen.appApplications
3. ****: MemScreen.app
4. ****: 
   - Screen Recording
   - Accessibilityprocess
   - Microphone

### 


- Ollama
- AI


```bash
# Ollama
brew install ollama

# AI
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large
```

---

## 🚀 

### 

1. **Ollama**
   - : Ollama
   - : 

2. **AI**
   - : ~3GB
   - : 

3. **Apple Developer**
   - : macOS
   - : Apple Developer

### 

1. **Ollama**: Ollama
2. ****: 
3. ****: 
4. ****: 
5. ****: 

---

## 📄 

### 

- `pyinstaller/build_macos.sh` - macOS
- `pyinstaller/rthook/pyi_rthook_pynput.py` - pynput runtime hook

### 

- `memscreen/cv2_loader.py` - PyInstallercv2
- `pyinstaller/memscreen_macos.spec` - pynput runtime hook

### 

- `pyinstaller/rthook/pyi_rthook_cv2.py` - cv2 runtime hook
- `pyinstaller/rthook/pyi_rthook_kivy.py` - Kivy runtime hook
- `pyinstaller/hooks/hook-cv2.py` - cv2 PyInstaller hook

---

## 🎉 

MemScreen

1. ✅ ****: .app
2. ✅ ****: DMG
3. ✅ ****: cv2
4. ✅ **Process**: pynput


1. 
2. 
3. GitHub Releases
4. Apple Developer
