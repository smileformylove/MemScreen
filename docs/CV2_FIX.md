# cv2 SDL2 Fix for MemScreen

## Problem

When running the packaged MemScreen.app, the application shows:
- **Status**: "cv2 unavailable recording disable"
- **Effect**: Screen recording and preview features are disabled

## Root Cause

The packaged application is missing the SDL2 library required by cv2 (OpenCV). During PyInstaller packaging, the SDL2 library from `cv2/.dylibs/libSDL2-2.0.0.dylib` is not automatically included in the app bundle.

## Solution

### Quick Fix (Already Applied)

The SDL2 library has been manually copied to the packaged applications:
- `/pyinstaller/dist/MemScreen.app`
- `/dist/MemScreen.app`

### Verification

Run the verification script:
```bash
./scripts/verify_cv2_fix.sh
```

Expected output:
```
✓ SDL2 found: .../MemScreen.app/Contents/Frameworks/cv2/.dylibs/libSDL2-2.0.0.dylib
```

### Testing

1. **Close** MemScreen.app if running
2. **Reopen** MemScreen.app
3. **Check status** - should NOT show "cv2 unavailable"
4. **Test recording** - try recording your screen

### Long-term Fix

The PyInstaller spec file has been updated to automatically include SDL2 during builds. However, if issues persist:

1. **After building**, run the automated fix script:
   ```bash
   ./scripts/fix_app_sdl2.sh
   ```

2. **Or manually copy SDL2**:
   ```bash
   # Find SDL2 in Python environment
   PYTHON_SITE=$(python3 -c "import site; print(site.getsitepackages()[0])")
   SDL2_SOURCE="$PYTHON_SITE/cv2/.dylibs/libSDL2-2.0.0.dylib"

   # Copy to app bundles
   cp "$SDL2_SOURCE" /path/to/MemScreen.app/Contents/Frameworks/cv2/.dylibs/
   ```

## Files Modified

1. **pyinstaller/memscreen_macos.spec**
   - Enhanced SDL2 detection logic
   - Added fallback methods for finding cv2 package
   - Improved error reporting

2. **scripts/fix_app_sdl2.sh** (new)
   - Automated post-build SDL2 fix
   - Can be run after PyInstaller build

3. **scripts/verify_cv2_fix.sh** (new)
   - Verification script to check SDL2 in app bundles

## Technical Details

### Why SDL2 is Missing

PyInstaller's cv2 hook doesn't always include all `.dylib` files from cv2's `.dylibs` directory. SDL2 is required for:
- Video I/O operations
- Screen capture functionality
- Video encoding/decoding

### Why Manual Copy Works

By manually copying `libSDL2-2.0.0.dylib` to the app bundle's `cv2/.dylibs` directory, we ensure cv2 can find and load SDL2 when the app runs.

### Dependencies

The SDL2 library in cv2 depends on:
- `/opt/homebrew/opt/sdl2/lib/libSDL2-2.0.0.dylib` (Homebrew installation)
- System frameworks: CoreAudio, Cocoa, IOKit, etc.

**Note**: The app may require SDL2 to be installed via Homebrew on target machines:
```bash
brew install sdl2
```

## Troubleshooting

### Still Shows "cv2 unavailable"

1. Check Console.app for detailed error logs
2. Verify the app is using the updated version
3. Try running from terminal to see stderr output:
   ```bash
   /path/to/MemScreen.app/Contents/MacOS/MemScreen
   ```

### Recording Fails

If status shows cv2 available but recording fails:
1. Check disk space
2. Verify output directory permissions
3. Look for errors in Console.app

### Build Process

To rebuild the app with the updated spec:
```bash
cd pyinstaller
pyinstaller memscreen_macos.spec --clean
./scripts/fix_app_sdl2.sh  # Ensure SDL2 is included
```

## Summary

✓ **Problem**: cv2 unavailable due to missing SDL2
✓ **Solution**: SDL2 copied to app bundles
✓ **Prevention**: Updated PyInstaller spec
✓ **Status**: Ready to test

**Next Step**: Restart MemScreen.app and verify recording works!
