#!/usr/bin/env python3
"""
Test video recording and display in Video tab
"""

import os
import sys
import sqlite3
import time
import tempfile
from datetime import datetime

print("=" * 70)
print("🎬 Video Tab Test")
print("=" * 70)
print()

# Test database
db_name = "./db/screen_capture.db"
videos_dir = "./db/videos"

print("📋 [Test 1] Check Database and Videos")
print("-" * 70)

# Check if database exists
if os.path.exists(db_name):
    print(f"✅ Database exists: {db_name}")

    # Connect and check videos table
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Check if videos table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
    if cursor.fetchone():
        print("✅ Videos table exists")

        # Count videos
        cursor.execute("SELECT COUNT(*) FROM videos")
        count = cursor.fetchone()[0]
        print(f"   Total videos in database: {count}")

        if count > 0:
            # Get all videos
            cursor.execute("SELECT id, filename, start_time, duration, fps FROM videos ORDER BY start_time DESC LIMIT 5")
            videos = cursor.fetchall()

            print("")
            print("📹 Recent videos:")
            for video in videos:
                video_id, filename, start_time, duration, fps = video
                print(f"   ID {video_id}: {os.path.basename(filename)}")
                print(f"      Start: {start_time}")
                print(f"      Duration: {duration:.1f}s @ {fps:.1f} fps")

                # Check if file exists
                if os.path.exists(filename):
                    size = os.path.getsize(filename) / 1024
                    print(f"      File: ✅ Exists ({size:.1f} KB)")
                else:
                    print(f"      File: ❌ Missing")
                print()
        else:
            print("   ⚠️  No videos in database")
            print("   You need to record some videos first!")
    else:
        print("❌ Videos table does not exist")
        print("   Creating videos table...")

        cursor.execute("""
            CREATE TABLE videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                start_time TEXT,
                end_time TEXT,
                duration REAL,
                fps REAL,
                frame_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✅ Videos table created")

    conn.close()
else:
    print(f"❌ Database not found: {db_name}")
    print("   Creating database...")

    os.makedirs(os.path.dirname(db_name), exist_ok=True)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            start_time TEXT,
            end_time TEXT,
            duration REAL,
            fps REAL,
            frame_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    print("✅ Database and videos table created")

print()

# Test 2: Create a test video
print("🎥 [Test 2] Create Test Video")
print("-" * 70)

try:
    import cv2
    import numpy as np
    from PIL import ImageGrab

    # Create videos directory
    os.makedirs(videos_dir, exist_ok=True)

    # Capture a few test frames
    print("   Capturing test frames...")
    frames = []
    for i in range(5):
        img = ImageGrab.grab()
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        frames.append(frame)
        time.sleep(0.5)
        print(f"   Frame {i+1}/5 captured")

    # Save as video
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(videos_dir, f"test_{timestamp}.mp4")

    print(f"   Saving video to {filename}...")

    height, width = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 2.0
    video = cv2.VideoWriter(filename, fourcc, fps, (width, height))

    for frame in frames:
        video.write(frame)
    video.release()

    file_size = os.path.getsize(filename) / 1024
    print(f"✅ Test video created: {filename}")
    print(f"   Size: {file_size:.1f} KB")
    print(f"   Resolution: {width}x{height}")
    print(f"   Frames: {len(frames)}")

    # Save to database
    print("")
    print("💾 [Test 3] Save to Database")
    print("-" * 70)

    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    duration = len(frames) / fps

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO videos (filename, start_time, duration, fps, frame_count)
        VALUES (?, ?, ?, ?, ?)
    """, (filename, start_time, duration, fps, len(frames)))

    conn.commit()
    video_id = cursor.lastrowid
    conn.close()

    print(f"✅ Video saved to database (ID: {video_id})")

except Exception as e:
    print(f"❌ Error creating test video: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("✅ Test Complete!")
print("=" * 70)
print()
print("Next steps:")
print("1. Launch the UI: python3 start.py")
print("2. Click on the 'Video' tab")
print("3. Click 'Refresh' button")
print("4. You should see the test video in the list")
print()
