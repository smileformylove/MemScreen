# macOS 

## 

 PyInstaller  Kivy  macOS 

## 

1. **PyInstaller **: PyInstaller  macOS 
2. **Info.plist **:  `LSBackgroundOnly`  `LSUIElement` 
3. ****:  macOS API 

## 

 ** + Kivy Window.request_attention()** 

### 

#### 1. 

: `packaging/macos/app_wrapper.sh`

```bash
#!/bin/bash
# MemScreen launcher wrapper
# 
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#  exec  Python 
exec "$SCRIPT_DIR/MemScreen.bin"
```

****:  `exec`  (`&`)
-  macOS 
-  shell 
-  PID

#### 2.  Info.plist

 `pyinstaller/memscreen_macos.spec` :

```python
info_plist={
    # ...  ...
    'LSBackgroundOnly': False,  # 
    'LSUIElement': False,  #  Dock 
    'NSSupportsAutomaticTermination': False,  # 
},
```

#### 3. 

 `memscreen/ui/kivy_app.py`  `on_start()` :

```python
def on_start(self):
    print("[App] Started - Light purple theme, all black text")

    # Request attention to bring window to front on macOS
    try:
        Window.request_attention(window_attention="normal")
        print("[App] ✓ Window attention requested")
    except Exception as e:
        print(f"[App] ⚠ Could not request attention: {e}")
```

****:  Cocoa API (`NSRunningApplication`) PyInstaller  Kivy  `Window.request_attention()` 

#### 4. 

: `packaging/macos/build_with_wrapper.sh`

```bash
#!/bin/bash
set -e

echo "🔨 Building MemScreen with macOS foreground app support..."

# 1.  PyInstaller 
echo "[1/3] Building with PyInstaller..."
pyinstaller pyinstaller/memscreen_macos.spec --noconfirm --clean

# 2.  Info.plist
echo "[2/3] Configuring Info.plist for foreground app..."
plutil -replace LSBackgroundOnly -bool NO dist/MemScreen.app/Contents/Info.plist 2>/dev/null || true
plutil -replace LSUIElement -bool NO dist/MemScreen.app/Contents/Info.plist 2>/dev/null || true
plutil -replace NSSupportsAutomaticTermination -bool NO dist/MemScreen.app/Contents/Info.plist 2>/dev/null || true

# 3. 
echo "[3/3] Installing activation wrapper..."
chmod +x packaging/macos/app_wrapper.sh
mv dist/MemScreen.app/Contents/MacOS/MemScreen dist/MemScreen.app/Contents/MacOS/MemScreen.bin
cp packaging/macos/app_wrapper.sh dist/MemScreen.app/Contents/MacOS/MemScreen
chmod +x dist/MemScreen.app/Contents/MacOS/MemScreen

echo "✅ Build complete: dist/MemScreen.app"
```

## 

### 

```bash
#  .app
./packaging/macos/build_with_wrapper.sh

#  DMG
./packaging/macos/build_dmg.sh
```

### 

```bash
#  Applications
cp -R dist/MemScreen.app /Applications/

# 
open /Applications/MemScreen.app
```

## 

### 

1. ****: `exec`  shell 
2. ****: macOS 
3. ****:  Kivy  `Window.request_attention()`  AppleScript

### 

:

```
MemScreen.app/
├── Contents/
│   ├── MacOS/
│   │   ├── MemScreen          #  ()
│   │   └── MemScreen.bin      #  Python 
│   ├── Info.plist             #  LSBackgroundOnly=false
│   └── Resources/
└── ...
```

### 

 `MemScreen.bin` Python 

## 

### 

1.  Info.plist:
   ```bash
   plutil -p /Applications/MemScreen.app/Contents/Info.plist | grep LSBackgroundOnly
   # : "LSBackgroundOnly" => 0
   ```

2. :
   ```bash
   ls -la /Applications/MemScreen.app/Contents/MacOS/
   # : MemScreen  MemScreen.bin
   ```

3. :
   ```bash
   open /Applications/MemScreen.app
   sleep 3
   osascript -e 'tell application "MemScreen" to activate'
   ```

### 

```bash
#  Kivy 
tail -100 ~/.kivy/logs/kivy_*.txt | grep -E "(Started|Activated|ERROR)"
```

## 

###  1:  Info.plist

 Info.plist  `LSBackgroundOnly: false`  `LSUIElement: false`

****: 
****: 

###  2: 

 Cocoa API 

****: 
****: PyInstaller 

###  3: py2app

 py2app  PyInstaller

****:  macOS 
****: 

****: Bash 

## 

- `packaging/macos/app_wrapper.sh` - 
- `packaging/macos/build_with_wrapper.sh` - 
- `packaging/macos/build_dmg.sh` - DMG 
- `pyinstaller/memscreen_macos.spec` - PyInstaller 
- `memscreen/ui/kivy_app.py` - Kivy 

## 

- [Apple Developer: Information Property List Key Reference](https://developer.apple.com/documentation/bundleresources/information_property_list)
- [LSBackgroundOnly](https://developer.apple.com/documentation/bundleresources/information_property_list/lsbackgroundonly)
- [PyInstaller macOS Specification](https://pyinstaller.org/en/stable/spec-files.html)
