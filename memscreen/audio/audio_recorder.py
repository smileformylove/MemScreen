### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""
Audio Recorder Module

Supports recording from:
- Microphone
- System audio (speakers/output)
"""

import os
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None
import wave
import threading
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None
from typing import Optional, Dict, Any
from enum import Enum


class AudioSource(Enum):
    """Audio source types"""
    MICROPHONE = "microphone"
    SYSTEM_AUDIO = "system_audio"
    NONE = "none"


class AudioRecorder:
    """
    Unified audio recorder supporting microphone and system audio.

    Features:
    - Microphone recording (cross-platform)
    - System audio recording (macOS/Windows)
    - Real-time audio level monitoring
    - Background recording thread
    """

    def __init__(self, output_dir: str = "./db/audio"):
        """
        Initialize audio recorder.

        Args:
            output_dir: Directory to save audio files
        """
        self.output_dir = output_dir
        self.audio_source = AudioSource.NONE
        self.is_recording = False
        self.recording_thread = None
        self.audio_frames = []
        self.current_file = None

        # Check if PyAudio is available
        if not PYAUDIO_AVAILABLE:
            print("[AudioRecorder] PyAudio not available. Audio recording disabled.")
            self.format = None
            self.channels = 1  # Mono
            self.rate = 44100  # Sample rate
            self.chunk = 1024  # Chunk size
            self.pyaudio_instance = None
            self.current_audio_level = 0.0
            self.audio_level_callback = None
            self.mic_device_index = None
            self.system_device_index = None
            os.makedirs(self.output_dir, exist_ok=True)
            return

        # Audio settings
        self.format = pyaudio.paInt16
        self.channels = 1  # Mono
        self.rate = 44100  # Sample rate
        self.chunk = 1024  # Chunk size

        # PyAudio instance (lazy loaded)
        self.pyaudio_instance = None

        # Audio level monitoring
        self.current_audio_level = 0.0
        self.audio_level_callback = None

        # Device info
        self.mic_device_index = None
        self.system_device_index = None

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

    def get_pyaudio(self):
        """Get or create PyAudio instance"""
        if not PYAUDIO_AVAILABLE:
            raise RuntimeError("PyAudio is not installed. Audio recording is disabled.")
        if self.pyaudio_instance is None:
            self.pyaudio_instance = pyaudio.PyAudio()
        return self.pyaudio_instance

    def list_audio_devices(self) -> list:
        """List all available audio devices"""
        if not PYAUDIO_AVAILABLE:
            print("[AudioRecorder] PyAudio not available. Cannot list audio devices.")
            return []
        try:
            p = self.get_pyaudio()
            devices = []

            for i in range(p.get_device_count()):
                try:
                    info = p.get_device_info_by_index(i)
                    # Handle both dictionary and object-like access
                    if isinstance(info, dict):
                        max_input = info.get('maxInputChannels', 0)
                        max_output = info.get('maxOutputChannels', 0)
                        name = info.get('name', 'Unknown Device')
                    else:
                        max_input = getattr(info, 'maxInputChannels', 0)
                        max_output = getattr(info, 'maxOutputChannels', 0)
                        name = getattr(info, 'name', 'Unknown Device')

                    devices.append({
                        'index': i,
                        'name': name,
                        'max_input_channels': max_input,
                        'max_output_channels': max_output,
                        'is_input': max_input > 0,
                        'is_output': max_output > 0
                    })
                except Exception as e:
                    print(f"[AudioRecorder] Error getting device {i}: {e}")
                    continue

            return devices
        except Exception as e:
            print(f"[AudioRecorder] Error listing devices: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_microphone_devices(self) -> list:
        """Get list of microphone input devices"""
        devices = self.list_audio_devices()
        return [d for d in devices if d['is_input']]

    def set_microphone_device(self, device_index: Optional[int] = None):
        """
        Set microphone device to use.

        Args:
            device_index: Device index, or None for default
        """
        self.mic_device_index = device_index
        print(f"[AudioRecorder] Microphone device set to: {device_index or 'default'}")

    def set_audio_source(self, source: AudioSource):
        """
        Set the audio source for recording.

        Args:
            source: AudioSource enum (MICROPHONE, SYSTEM_AUDIO, NONE)
        """
        self.audio_source = source
        print(f"[AudioRecorder] Audio source set to: {source.value}")

    def start_recording(self, source: AudioSource) -> bool:
        """
        Start audio recording.

        Args:
            source: Audio source to record from

        Returns:
            True if recording started successfully
        """
        if self.is_recording:
            print("[AudioRecorder] Already recording")
            return False

        if source == AudioSource.NONE:
            print("[AudioRecorder] No audio source selected")
            return False

        try:
            self.audio_source = source
            self.is_recording = True
            self.audio_frames = []

            # Start recording in background thread
            self.recording_thread = threading.Thread(
                target=self._record_audio,
                daemon=True
            )
            self.recording_thread.start()

            print(f"[AudioRecorder] Started recording from {source.value}")
            return True

        except Exception as e:
            print(f"[AudioRecorder] Failed to start recording: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> Optional[str]:
        """
        Stop audio recording and save to file.

        Returns:
            Path to saved audio file, or None if failed
        """
        if not self.is_recording:
            return None

        try:
            self.is_recording = False

            # Wait for recording thread to finish
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=5)

            # Save audio to file
            if self.audio_frames:
                filename = self._save_audio()

                print(f"[AudioRecorder] Stopped recording, saved to: {filename}")
                return filename

        except Exception as e:
            print(f"[AudioRecorder] Failed to stop recording: {e}")

        return None

    def get_audio_level(self) -> float:
        """
        Get current audio level (0.0 to 1.0).

        Returns:
            Audio level as float between 0.0 and 1.0
        """
        return self.current_audio_level

    def _record_audio(self):
        """Record audio in background thread"""
        stream = None
        try:
            p = self.get_pyaudio()

            # Configure stream based on source
            if self.audio_source == AudioSource.MICROPHONE:
                print(f"[AudioRecorder] Opening microphone stream (device: {self.mic_device_index or 'default'})...")
                stream = p.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    input_device_index=self.mic_device_index,
                    frames_per_buffer=self.chunk
                )
                print(f"[AudioRecorder] Microphone stream opened successfully")
            elif self.audio_source == AudioSource.SYSTEM_AUDIO:
                # System audio recording (OS-specific)
                stream = self._get_system_audio_stream(p)
                if stream is None:
                    print("[AudioRecorder] System audio not available on this platform")
                    self.is_recording = False
                    return
            else:
                print(f"[AudioRecorder] Unknown audio source: {self.audio_source}")
                self.is_recording = False
                return

            print(f"[AudioRecorder] Recording from {self.audio_source.value}...")

            while self.is_recording:
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    self.audio_frames.append(data)

                    # Calculate audio level for visualization
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    level = np.abs(audio_data).mean() / 32768.0  # Normalize to 0-1
                    self.current_audio_level = float(level)

                    # Call callback if set
                    if self.audio_level_callback:
                        self.audio_level_callback(self.current_audio_level)

                except Exception as e:
                    print(f"[AudioRecorder] Error reading audio: {e}")
                    import traceback
                    traceback.print_exc()
                    break

            print(f"[AudioRecorder] Recording loop finished, frames captured: {len(self.audio_frames)}")

        except Exception as e:
            print(f"[AudioRecorder] Recording error: {e}")
            import traceback
            traceback.print_exc()
            self.is_recording = False
        finally:
            # Always close stream
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                    print("[AudioRecorder] Audio stream closed")
                except Exception as e:
                    print(f"[AudioRecorder] Error closing stream: {e}")

    def _get_system_audio_stream(self, p):
        """
        Get audio stream for system audio (OS-specific).

        Returns:
            PyAudio stream or None if not available
        """
        import sys

        if sys.platform == 'darwin':  # macOS
            # On macOS, we can use BlackHole or Soundflower
            # Or use built-in devices with loopback
            return self._get_macos_system_audio(p)
        elif sys.platform == 'win32':  # Windows
            # Windows has WASAPI loopback
            return self._get_windows_system_audio(p)
        else:
            print(f"[AudioRecorder] System audio not supported on {sys.platform}")
            return None

    def _get_macos_system_audio(self, p):
        """
        Get system audio stream on macOS.

        Uses BlackHole virtual audio device if available.
        """
        # Look for BlackHole device
        devices = self.list_audio_devices()

        for device in devices:
            if 'blackhole' in device['name'].lower():
                print(f"[AudioRecorder] Found BlackHole device: {device['name']}")
                return p.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    input_device_index=device['index'],
                    frames_per_buffer=self.chunk
                )

        # Check if BlackHole is installed
        print("[AudioRecorder] BlackHole not found. Install with:")
        print("  brew install blackhole-2ch")
        print("[AudioRecorder] Falling back to default input device")
        return None

    def _get_windows_system_audio(self, p):
        """
        Get system audio stream on Windows.

        Uses WASAPI loopback recording.
        """
        # Windows WASAPI loopback requires special handling
        # For now, return None - would need pyaudio with WASAPI support
        print("[AudioRecorder] Windows system audio requires WASAPI loopback support")
        return None

    def _save_audio(self) -> str:
        """
        Save recorded audio to WAV file.

        Returns:
            Path to saved audio file
        """
        from datetime import datetime

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"audio_{timestamp}.wav")

        # Save as WAV
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.get_pyaudio().get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.audio_frames))

        return filename

    def cleanup(self):
        """Clean up resources"""
        self.is_recording = False

        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5)

        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
            self.pyaudio_instance = None

        print("[AudioRecorder] Cleaned up resources")


def test_audio_recorder():
    """Test the audio recorder"""
    import time

    recorder = AudioRecorder()

    # List devices
    print("\nAvailable audio devices:")
    devices = recorder.list_audio_devices()
    for device in devices:
        print(f"  [{device['index']}] {device['name']} - "
              f"Input: {device['max_input_channels']}, Output: {device['max_output_channels']}")

    # Test microphone recording
    print("\nTesting microphone recording (5 seconds)...")
    recorder.set_audio_source(AudioSource.MICROPHONE)

    if recorder.start_recording(AudioSource.MICROPHONE):
        for i in range(50):
            level = recorder.get_audio_level()
            print(f"Audio level: {level:.3f}")
            time.sleep(0.1)

        filename = recorder.stop_recording()
        print(f"Saved to: {filename}")

    recorder.cleanup()


if __name__ == "__main__":
    test_audio_recorder()
