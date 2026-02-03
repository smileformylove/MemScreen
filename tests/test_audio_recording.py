### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""
Test script for audio recording functionality
"""

import sys
import os

# Add memscreen to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memscreen.audio import AudioRecorder, AudioSource


def test_list_devices():
    """Test listing audio devices"""
    print("=" * 60)
    print("Testing Audio Device Listing")
    print("=" * 60)

    recorder = AudioRecorder()
    devices = recorder.list_audio_devices()

    print(f"\nFound {len(devices)} audio devices:\n")

    input_devices = [d for d in devices if d['is_input']]
    output_devices = [d for d in devices if d['is_output']]

    print("Input Devices (Microphones):")
    for device in input_devices:
        print(f"  [{device['index']}] {device['name']}")

    print("\nOutput Devices (Speakers):")
    for device in output_devices:
        print(f"  [{device['index']}] {device['name']}")

    return recorder, len(input_devices) > 0


def test_microphone_recording(recorder):
    """Test microphone recording"""
    print("\n" + "=" * 60)
    print("Testing Microphone Recording (3 seconds)")
    print("=" * 60)

    import time

    print("\nStarting microphone recording...")
    print("Speak into your microphone now!")

    if recorder.start_recording(AudioSource.MICROPHONE):
        # Monitor audio levels
        for i in range(30):
            level = recorder.get_audio_level()
            if i % 10 == 0:
                bar_length = int(level * 50)
                bar = "█" * bar_length
                print(f"[{i/10:.1f}s] Audio Level: [{bar:<50}] {level:.3f}")
            time.sleep(0.1)

        print("\nStopping recording...")
        filename = recorder.stop_recording()

        if filename:
            file_size = os.path.getsize(filename)
            print(f"✓ Audio saved to: {filename}")
            print(f"  File size: {file_size / 1024:.1f} KB")
            return True
        else:
            print("✗ Failed to save audio")
            return False
    else:
        print("✗ Failed to start recording")
        return False


def test_system_audio():
    """Test system audio recording"""
    print("\n" + "=" * 60)
    print("Testing System Audio Recording")
    print("=" * 60)

    print("\nNote: System audio recording requires special setup:")
    print("  - macOS: Install BlackHole with: brew install blackhole-2ch")
    print("  - Windows: Requires WASAPI loopback support")
    print("\nSkipping system audio test in this demo.")


def main():
    """Run all tests"""
    print("\n🎤 MemScreen Audio Recording Test\n")

    try:
        # Test 1: List devices
        recorder, has_mic = test_list_devices()

        if not has_mic:
            print("\n⚠ No input devices found. Cannot test microphone recording.")
            print("Please connect a microphone and try again.")
            return

        # Test 2: Microphone recording (automatic test)
        print("\nAutomatically testing microphone recording (3 seconds)...")
        print("Please speak into your microphone now!")
        import time
        time.sleep(1)  # Give user time to read

        success = test_microphone_recording(recorder)

        if success:
            print("\n✓ Microphone recording test PASSED")
        else:
            print("\n✗ Microphone recording test FAILED")

        # Test 3: System audio info
        test_system_audio()

        # Cleanup
        recorder.cleanup()

        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"✓ Device listing: PASSED")
        print(f"{'✓' if success else '✗'} Microphone recording: {'PASSED' if success else 'FAILED'}")
        print(f"ℹ System audio: SKIPPED (requires setup)")
        print("\nTo use audio recording in MemScreen:")
        print("1. Select 'Microphone' or 'System Audio' in the Recording tab")
        print("2. Start recording as usual")
        print("3. Audio will be automatically merged with video")
        print("\nFor system audio on macOS, install BlackHole:")
        print("  brew install blackhole-2ch")
        print("\n")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
