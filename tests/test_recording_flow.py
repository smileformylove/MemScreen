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
    print("🧪 测试录制流程")
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
    print("\n🔍 初始数据库状态:")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM recordings")
    count = cursor.fetchone()[0]
    print(f"   - 记录数: {count}")
    conn.close()

    # Create presenter
    print("\n🎯 创建 RecordingPresenter...")
    presenter = RecordingPresenter(
        view=None,
        memory_system=None,
        db_path=str(db_path),
        output_dir=str(videos_dir),
        audio_dir=str(videos_dir.parent / "audio")
    )

    # Start recording
    print("\n🔴 开始录制 (5秒)...")
    result = presenter.start_recording(duration=5, interval=2.0)
    print(f"   - 录制开始: {result}")

    if not result:
        print("   ❌ 录制启动失败！")
        return

    # Record for 5 seconds
    import time
    print(f"   - 录制中... 帧数: {presenter.frame_count}")
    for i in range(5):
        time.sleep(1)
        print(f"   - 录制中... 帧数: {presenter.frame_count}, 已录制: {i+1}秒")

    # Stop recording
    print("\n⏹️ 停止录制...")
    result = presenter.stop_recording()
    print(f"   - 录制停止: {result}")
    print(f"   - 总帧数: {len(presenter.recording_frames)}")

    # Wait for save thread to complete
    print("\n⏳ 等待保存线程完成...")
    if presenter._save_thread:
        presenter._save_thread.join(timeout=30)
        if presenter._save_thread.is_alive():
            print("   ⚠️ 保存线程超时")
        else:
            print("   ✅ 保存线程完成")

    # Check database again
    print("\n🔍 保存后数据库状态:")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM recordings")
    count = cursor.fetchone()[0]
    print(f"   - 记录数: {count}")

    if count > 0:
        cursor.execute("SELECT filename, timestamp, frame_count, duration, file_size FROM recordings ORDER BY rowid DESC LIMIT 1")
        row = cursor.fetchone()
        print(f"   - 最新记录:")
        print(f"     • 文件: {os.path.basename(row[0])}")
        print(f"     • 时间: {row[1]}")
        print(f"     • 帧数: {row[2]}")
        print(f"     • 时长: {row[3]:.2f}s")
        print(f"     • 大小: {row[4] / 1024:.1f} KB")

        # Check if file exists
        if os.path.exists(row[0]):
            print(f"     • 文件存在: ✅")
        else:
            print(f"     • 文件存在: ❌ (文件缺失)")
    else:
        print("   ❌ 没有找到记录！")

    conn.close()

    # List video files
    print(f"\n📹 视频文件目录:")
    if videos_dir.exists():
        videos = list(videos_dir.glob("*.mp4"))
        print(f"   - 找到 {len(videos)} 个视频文件")
        for video in sorted(videos)[-5:]:  # Show last 5
            size_mb = video.stat().st_size / 1024 / 1024
            print(f"     • {video.name} ({size_mb:.2f} MB)")
    else:
        print(f"   ⚠️ 目录不存在: {videos_dir}")

    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)


if __name__ == "__main__":
    try:
        test_recording_flow()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
