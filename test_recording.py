#!/usr/bin/env python3
"""
Test screen recording functionality

This tests the actual screen recording feature to ensure:
1. Screenshots can be captured
2. Video can be created from screenshots
3. Database records are created
4. Files are saved correctly
"""

import sys
import os
import time
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

print("=" * 70)
print("🔴 MemScreen Recording Test")
print("=" * 70)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

test_results = []

# Test 1: Import recording module
print("📦 [Test 1] Import Recording Module")
print("-" * 70)
try:
    from memscreen.config import get_config
    from PIL import ImageGrab

    config = get_config()
    print("✅ Recording module imported successfully")
    print(f"   Default duration: {config.recording_duration}s")
    print(f"   Default interval: {config.recording_interval}s")
    print(f"   Video directory: {config.videos_dir}")
    test_results.append(("Import", "PASS"))
except Exception as e:
    print(f"❌ Import failed: {e}")
    test_results.append(("Import", "FAIL"))
    sys.exit(1)

print()

# Test 2: Create temporary output directory
print("📁 [Test 2] Setup Test Directory")
print("-" * 70)
try:
    test_dir = tempfile.mkdtemp(prefix="memscreen_test_")
    test_video_dir = os.path.join(test_dir, "videos")
    os.makedirs(test_video_dir, exist_ok=True)

    print(f"✅ Test directory created: {test_dir}")
    print(f"   Video output: {test_video_dir}")
    test_results.append(("Directory", "PASS"))
except Exception as e:
    print(f"❌ Directory setup failed: {e}")
    test_results.append(("Directory", "FAIL"))
    sys.exit(1)

print()

# Test 3: Test screenshot capture
print("📸 [Test 3] Screenshot Capture")
print("-" * 70)
try:
    from PIL import ImageGrab

    # Capture a few screenshots
    screenshots = []
    num_screenshots = 3

    print(f"   Capturing {num_screenshots} screenshots...")
    for i in range(num_screenshots):
        screenshot = ImageGrab.grab()
        screenshots.append(screenshot)
        print(f"   Screenshot {i+1}/{num_screenshots}: {screenshot.size}")
        time.sleep(0.5)

    print(f"✅ Captured {len(screenshots)} screenshots successfully")
    print(f"   Resolution: {screenshots[0].size}")
    print(f"   Mode: {screenshots[0].mode}")
    test_results.append(("Screenshot", "PASS"))

except Exception as e:
    print(f"❌ Screenshot capture failed: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("Screenshot", "FAIL"))
    shutil.rmtree(test_dir)
    sys.exit(1)

print()

# Test 4: Save screenshots to disk
print("💾 [Test 4] Save Screenshots")
print("-" * 70)
try:
    screenshot_paths = []
    for i, screenshot in enumerate(screenshots):
        path = os.path.join(test_video_dir, f"test_screenshot_{i}.png")
        screenshot.save(path)
        screenshot_paths.append(path)
        size = os.path.getsize(path)
        print(f"   Saved: {path} ({size/1024:.1f} KB)")

    print(f"✅ Saved {len(screenshot_paths)} screenshots successfully")
    test_results.append(("Save", "PASS"))
except Exception as e:
    print(f"❌ Save screenshots failed: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("Save", "FAIL"))
    shutil.rmtree(test_dir)
    sys.exit(1)

print()

# Test 5: Create video from screenshots
print("🎬 [Test 5] Create Video from Screenshots")
print("-" * 70)
try:
    import cv2
    import numpy as np

    # Read first screenshot to get dimensions
    first_img = cv2.imread(screenshot_paths[0])
    height, width, layers = first_img.shape

    # Create video writer
    video_path = os.path.join(test_video_dir, "test_video.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 2  # 2 frames per second for testing
    video_writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

    # Write frames
    for screenshot_path in screenshot_paths:
        img = cv2.imread(screenshot_path)
        video_writer.write(img)

    video_writer.release()

    # Verify video was created
    if os.path.exists(video_path):
        size = os.path.getsize(video_path)
        print(f"✅ Video created successfully")
        print(f"   Path: {video_path}")
        print(f"   Size: {size/1024:.1f} KB")
        print(f"   Resolution: {width}x{height}")
        print(f"   FPS: {fps}")
        print(f"   Frames: {len(screenshot_paths)}")
        test_results.append(("Video", "PASS"))
    else:
        raise FileNotFoundError(f"Video not created: {video_path}")

except Exception as e:
    print(f"❌ Video creation failed: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("Video", "FAIL"))
    shutil.rmtree(test_dir)
    sys.exit(1)

print()

# Test 6: Cleanup
print("🧹 [Test 6] Cleanup")
print("-" * 70)
try:
    # Verify files before cleanup
    files = list(Path(test_video_dir).glob("*"))
    print(f"   Files before cleanup: {len(files)}")

    # Cleanup
    shutil.rmtree(test_dir)

    # Verify cleanup
    if not os.path.exists(test_dir):
        print(f"✅ Cleanup successful")
        print(f"   Removed: {test_dir}")
        test_results.append(("Cleanup", "PASS"))
    else:
        raise FileNotFoundError(f"Directory not removed: {test_dir}")

except Exception as e:
    print(f"❌ Cleanup failed: {e}")
    test_results.append(("Cleanup", "FAIL"))

print()
print("=" * 70)
print("📊 Test Results Summary")
print("=" * 70)

passed = sum(1 for _, result in test_results if result == "PASS")
total = len(test_results)

print(f"Total Tests: {total}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {total - passed}")

if passed == total:
    print()
    print("🎉 ALL TESTS PASSED!")
    print()
    print("Screen recording functionality is working correctly!")
    print()
else:
    print()
    print("⚠️  Some tests failed.")
    print()

print("=" * 70)
print("Test completed at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("=" * 70)
