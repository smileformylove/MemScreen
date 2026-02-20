#!/usr/bin/env python3
"""
Test recording flow - verify capture and database save
"""
import os
import sys
import sqlite3
import tempfile
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent))

def test_recording_flow():
    print("="*70)
    print("🧪 ")
    print("="*70)

    from memscreen.config import get_config
    from memscreen.presenters.recording_presenter import RecordingPresenter
    from datetime import datetime

    # Get config
    config = get_config()
    db_path = config.db_path
    videos_dir = config.videos_dir

    print(f"\n📁 Database: {db_path}")
    print(f"📁 Videos dir: {videos_dir}")
    print(f"📁 DB exists: {db_path.exists()}")

    # Check initial database state
    print("\n🔍 :")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM recordings")
    count = cursor.fetchone()[0]
    print(f"   - : {count}")
    conn.close()

    # Create presenter
    print("\n🎯  RecordingPresenter...")
    presenter = RecordingPresenter(
        view=None,
        memory_system=None,
        db_path=str(db_path),
        output_dir=str(videos_dir),
        audio_dir=str(videos_dir.parent / "audio")
    )

    # Start recording
    print("\n🔴  (5)...")
    result = presenter.start_recording(duration=5, interval=2.0)
    print(f"   - : {result}")

    if not result:
        print("   ❌ ")
        return

    # Record for 5 seconds
    import time
    print(f"   - ... : {presenter.frame_count}")
    for i in range(5):
        time.sleep(1)
        print(f"   - ... : {presenter.frame_count}, : {i+1}")

    # Stop recording
    print("\n⏹️ ...")
    result = presenter.stop_recording()
    print(f"   - : {result}")
    print(f"   - : {len(presenter.recording_frames)}")

    # Wait for save thread to complete
    print("\n⏳ ...")
    if presenter._save_thread:
        presenter._save_thread.join(timeout=30)
        if presenter._save_thread.is_alive():
            print("   ⚠️ ")
        else:
            print("   ✅ ")

    # Check database again
    print("\n🔍 :")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM recordings")
    count = cursor.fetchone()[0]
    print(f"   - : {count}")

    if count > 0:
        cursor.execute("SELECT filename, timestamp, frame_count, duration, file_size FROM recordings ORDER BY rowid DESC LIMIT 1")
        row = cursor.fetchone()
        print(f"   - :")
        print(f"     • : {os.path.basename(row[0])}")
        print(f"     • : {row[1]}")
        print(f"     • : {row[2]}")
        print(f"     • : {row[3]:.2f}s")
        print(f"     • : {row[4] / 1024:.1f} KB")

        # Check if file exists
        if os.path.exists(row[0]):
            print(f"     • : ✅")
        else:
            print(f"     • : ❌ ()")
    else:
        print("   ❌ ")

    conn.close()

    # List video files
    print(f"\n📹 :")
    if videos_dir.exists():
        videos = list(videos_dir.glob("*.mp4"))
        print(f"   -  {len(videos)} ")
        for video in sorted(videos)[-5:]:  # Show last 5
            size_mb = video.stat().st_size / 1024 / 1024
            print(f"     • {video.name} ({size_mb:.2f} MB)")
    else:
        print(f"   ⚠️ : {videos_dir}")

    print("\n" + "="*70)
    print("✅ ")
    print("="*70)


if __name__ == "__main__":
    try:
        test_recording_flow()
    except Exception as e:
        print(f"\n❌ : {e}")
        import traceback
        traceback.print_exc()
