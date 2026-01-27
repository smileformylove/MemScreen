#!/usr/bin/env python3
"""Add existing video files to the database"""

import os
import sqlite3
import cv2

db_path = "./db/screen_capture.db"
video_dir = "./db/videos"

# Get all video files
video_files = []
for filename in os.listdir(video_dir):
    if filename.endswith('.mp4'):
        video_path = os.path.join(video_dir, filename)
        video_files.append(video_path)

print(f"Found {len(video_files)} video files")

# Add to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for video_path in video_files:
    try:
        # Get video info
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = frame_count / fps if fps > 0 else 0
        cap.release()

        # Get file size
        file_size = os.path.getsize(video_path)

        # Extract timestamp from filename
        filename = os.path.basename(video_path)
        # Try to parse timestamp from filename like recording_20260125_131742.mp4
        if 'recording_' in filename or 'segment_' in filename:
            timestamp_str = filename.replace('recording_', '').replace('segment_', '').replace('.mp4', '')
            # Convert to datetime format
            try:
                from datetime import datetime
                dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert into database
        cursor.execute('''
            INSERT INTO recordings (filename, timestamp, frame_count, fps, duration, file_size)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (video_path, timestamp, frame_count, fps, duration, file_size))

        print(f"Added: {filename}")
        print(f"  Frames: {frame_count}, FPS: {fps:.2f}, Duration: {duration:.2f}s")

    except Exception as e:
        print(f"Error processing {video_path}: {e}")

conn.commit()
conn.close()
print("\nDone!")
