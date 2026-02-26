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
import ctypes
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
    MIXED = "mixed"
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
        self._startup_check_done = threading.Event()
        self.audio_frames = []
        self.current_file = None
        self.effective_audio_source = AudioSource.NONE
        self.last_error: Optional[str] = None
        self.auto_route_system_output = True
        self.system_audio_gain = float(os.environ.get("MEMSCREEN_SYSTEM_AUDIO_GAIN", "64.0"))
        self.monitor_audio_gain = float(
            os.environ.get("MEMSCREEN_MONITOR_AUDIO_GAIN", str(self.system_audio_gain))
        )
        self._selected_system_device_name: Optional[str] = None
        self._selected_system_output_device_name: Optional[str] = None
        self._selected_system_channels: int = 1
        self._previous_output_device_id: Optional[int] = None
        self._previous_system_output_device_id: Optional[int] = None

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

    def _resolve_microphone_device_index(self) -> Optional[int]:
        """
        Resolve microphone device index with sane defaults.

        If user explicitly set `mic_device_index`, use it.
        Otherwise prefer built-in microphone-like devices over virtual/bluetooth inputs.
        """
        if self.mic_device_index is not None:
            return self.mic_device_index

        devices = self.get_microphone_devices()
        if not devices:
            return None

        def score(device):
            name = str(device.get("name", "")).lower()
            s = 0
            if "microphone" in name or "mic" in name:
                s += 60
            if "macbook" in name or "built-in" in name or "builtin" in name:
                s += 40
            if "blackhole" in name or "soundflower" in name or "loopback" in name or "virtual" in name:
                s -= 120
            if "airpods" in name or "air4" in name or "bluetooth" in name:
                s -= 20
            return s

        best = max(devices, key=score)
        print(f"[AudioRecorder] Auto-selected microphone device: {best['name']} (index={best['index']})")
        return best["index"]

    def set_audio_source(self, source: AudioSource):
        """
        Set the audio source for recording.

        Args:
            source: AudioSource enum (MIXED, MICROPHONE, SYSTEM_AUDIO, NONE)
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

        if not PYAUDIO_AVAILABLE:
            self.last_error = "PyAudio is not available. Install PyAudio to enable audio recording."
            print(f"[AudioRecorder] {self.last_error}")
            return False

        try:
            self.last_error = None
            self.audio_source = source
            self.effective_audio_source = source
            self.is_recording = True
            self.audio_frames = []
            self._startup_check_done.clear()

            # Start recording in background thread
            self.recording_thread = threading.Thread(
                target=self._record_audio,
                daemon=True
            )
            self.recording_thread.start()

            # Wait for startup checks (device open / loopback verify) to complete.
            self._startup_check_done.wait(timeout=1.5)
            if not self.is_recording:
                print("[AudioRecorder] Audio recording failed during startup")
                return False

            print(f"[AudioRecorder] Started recording from {source.value}")
            return True

        except Exception as e:
            print(f"[AudioRecorder] Failed to start recording: {e}")
            self.last_error = str(e)
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
            self._restore_previous_output_device()

            # Save audio to file
            if self.audio_frames:
                filename = self._save_audio()

                print(f"[AudioRecorder] Stopped recording, saved to: {filename}")
                return filename

        except Exception as e:
            print(f"[AudioRecorder] Failed to stop recording: {e}")
            self._restore_previous_output_device()

        return None

    def get_effective_source(self) -> AudioSource:
        """Return the actual audio source used in current/last recording."""
        return self.effective_audio_source

    def get_last_error(self) -> Optional[str]:
        """Return last audio recorder error."""
        return self.last_error

    def diagnose_source(self, source: AudioSource) -> Dict[str, Any]:
        """
        Diagnose audio capture readiness for the requested source.
        """
        result: Dict[str, Any] = {
            "requested_source": source.value,
            "pyaudio_available": PYAUDIO_AVAILABLE,
            "microphone_available": False,
            "system_device_available": False,
            "system_signal_available": False,
            "message": "",
            "recommended_action": "",
        }
        if not PYAUDIO_AVAILABLE:
            result["message"] = "PyAudio is not available."
            result["recommended_action"] = "Install PyAudio."
            return result

        p = self.get_pyaudio()

        mic_stream = self._open_microphone_stream(p)
        if mic_stream is not None:
            result["microphone_available"] = True
            self._close_stream(mic_stream)

        if source in (AudioSource.SYSTEM_AUDIO, AudioSource.MIXED):
            sys_stream, _sys_channels = self._get_system_audio_stream(p)
            if sys_stream is not None:
                result["system_device_available"] = True
                result["system_signal_available"] = not self._stream_is_silent(sys_stream)
                self._close_stream(sys_stream)

        if source == AudioSource.NONE:
            result["message"] = "Audio recording is disabled."
            result["recommended_action"] = ""
        elif source == AudioSource.MICROPHONE:
            if result["microphone_available"]:
                result["message"] = "Microphone is ready."
            else:
                result["message"] = "No microphone input device is available."
                result["recommended_action"] = "Check macOS microphone permissions and input device."
        else:
            if result["system_signal_available"]:
                result["message"] = "System audio signal is ready."
            elif result["system_device_available"]:
                result["message"] = "System loopback device found but no signal is detected."
                result["recommended_action"] = (
                    "Set macOS output to a loopback device (BlackHole/Loopback/Oray) before recording."
                )
            else:
                result["message"] = "No system loopback input device is available."
                result["recommended_action"] = "Install/configure BlackHole/Loopback/Oray first."

        return result

    def get_audio_level(self) -> float:
        """
        Get current audio level (0.0 to 1.0).

        Returns:
            Audio level as float between 0.0 and 1.0
        """
        return self.current_audio_level

    def _record_audio(self):
        """Record audio in background thread"""
        streams = []
        monitor_stream = None
        monitor_channels = 1
        try:
            p = self.get_pyaudio()

            # Configure stream based on source
            if self.audio_source in (AudioSource.SYSTEM_AUDIO, AudioSource.MIXED):
                system_stream, system_channels = self._get_system_audio_stream(p)
                if system_stream is not None:
                    if self.auto_route_system_output:
                        self._route_output_to_selected_system_device()
                        # Re-open loopback stream after routing output.
                        # Some virtual devices only produce usable capture once output
                        # has already switched to that device.
                        self._close_stream(system_stream)
                        system_stream, system_channels = self._get_system_audio_stream(p)
                        if system_stream is not None:
                            loopback_ok = self._verify_loopback_signal(
                                p, system_stream, system_channels
                            )
                            if not loopback_ok:
                                self.last_error = (
                                    "System loopback device is not providing audio signal. "
                                    "Please use BlackHole/Loopback/Soundflower and ensure output "
                                    "is routed to that loopback device."
                                )
                                print(f"[AudioRecorder] {self.last_error}")
                                self._close_stream(system_stream)
                                system_stream = None
                                system_channels = 0
                                # Avoid muting user output if loopback path is unavailable.
                                self._restore_previous_output_device()
                    if system_stream is not None:
                        streams.append(
                            {"name": "system_audio", "stream": system_stream, "channels": system_channels}
                        )

            if self.audio_source in (AudioSource.MICROPHONE, AudioSource.MIXED):
                mic_stream = self._open_microphone_stream(p)
                if mic_stream is not None:
                    streams.append({"name": "microphone", "stream": mic_stream, "channels": 1})

            if self.audio_source == AudioSource.SYSTEM_AUDIO and not streams:
                if not self.last_error:
                    self.last_error = (
                        "No system-audio signal detected. "
                        "Route macOS output to a loopback device (BlackHole/Loopback/Oray) and retry."
                    )
                self._startup_check_done.set()
                self.is_recording = False
                return

            if self.audio_source in (AudioSource.MIXED, AudioSource.MICROPHONE) and not streams:
                self.last_error = "No available audio input stream."
                self._startup_check_done.set()
                self.is_recording = False
                return

            opened_sources = {entry["name"] for entry in streams}
            if opened_sources == {"system_audio", "microphone"}:
                self.effective_audio_source = AudioSource.MIXED
            elif "system_audio" in opened_sources:
                self.effective_audio_source = AudioSource.SYSTEM_AUDIO
            elif "microphone" in opened_sources:
                self.effective_audio_source = AudioSource.MICROPHONE
            else:
                print(f"[AudioRecorder] Unknown audio source: {self.audio_source}")
                self._startup_check_done.set()
                self.is_recording = False
                return

            print(
                f"[AudioRecorder] Recording from {self.audio_source.value} "
                f"(effective={self.effective_audio_source.value}, streams={len(streams)})..."
            )
            self._startup_check_done.set()

            if self._previous_output_device_id is not None:
                monitor_name = self._ca_get_device_name(self._previous_output_device_id)
                if monitor_name:
                    monitor_stream, monitor_channels = self._open_monitor_output_stream(
                        p, monitor_name, preferred_channels=max(2, int(self._selected_system_channels or 1))
                    )
                    if monitor_stream is not None:
                        print(
                            f"[AudioRecorder] Monitoring system audio to: {monitor_name} "
                            f"(channels={monitor_channels})"
                        )

            while self.is_recording:
                try:
                    chunks = []
                    source_chunks = {}
                    alive_streams = []
                    for entry in streams:
                        name = entry["name"]
                        stream = entry["stream"]
                        channels = int(entry.get("channels", 1) or 1)
                        try:
                            data = stream.read(self.chunk, exception_on_overflow=False)
                            data_for_mix = data
                            if name == "system_audio" and self.system_audio_gain != 1.0:
                                data_for_mix = self._apply_pcm_gain(data, self.system_audio_gain)
                            chunks.append((data_for_mix, channels))
                            source_chunks[name] = (data, channels)
                            alive_streams.append(entry)
                        except Exception as stream_error:
                            print(f"[AudioRecorder] Dropping {name} stream after read error: {stream_error}")
                            try:
                                stream.stop_stream()
                                stream.close()
                            except Exception:
                                pass
                    streams = alive_streams
                    if not streams or not chunks:
                        print("[AudioRecorder] No active audio streams left.")
                        break

                    if monitor_stream is not None:
                        sys_chunk = source_chunks.get("system_audio")
                        if sys_chunk is not None:
                            sys_data, sys_channels = sys_chunk
                            self._write_monitor_audio(
                                monitor_stream, sys_data, monitor_channels, source_channels=sys_channels
                            )

                    data = self._mix_audio_chunks(chunks)
                    self.audio_frames.append(data)

                    # Calculate audio level for visualization
                    if NUMPY_AVAILABLE:
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        level = np.abs(audio_data).mean() / 32768.0  # Normalize to 0-1
                        self.current_audio_level = float(level)
                    else:
                        self.current_audio_level = 0.0

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
            self._startup_check_done.set()
            self.is_recording = False
        finally:
            self._startup_check_done.set()
            # Always close streams
            for entry in streams:
                stream = entry["stream"]
                try:
                    stream.stop_stream()
                    stream.close()
                    print("[AudioRecorder] Audio stream closed")
                except Exception as e:
                    print(f"[AudioRecorder] Error closing stream: {e}")
            if monitor_stream is not None:
                try:
                    monitor_stream.stop_stream()
                except Exception:
                    pass
                try:
                    monitor_stream.close()
                    print("[AudioRecorder] Monitor output stream closed")
                except Exception as e:
                    print(f"[AudioRecorder] Error closing monitor stream: {e}")
            self._restore_previous_output_device()

    def _get_system_audio_stream(self, p):
        """
        Get audio stream for system audio (OS-specific).

        Returns:
            (PyAudio stream, channels) or (None, 0) if unavailable
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
            return None, 0

    def _get_macos_system_audio(self, p):
        """
        Get system audio stream on macOS.

        Uses virtual loopback audio devices if available.
        """
        # Look for known virtual loopback devices (priority order).
        devices = self.list_audio_devices()
        candidates = []
        for device in devices:
            if not device.get('is_input'):
                continue
            name = str(device.get('name', '')).lower()
            score = 0
            if 'blackhole' in name:
                score = 120
            elif 'soundflower' in name:
                score = 110
            elif 'loopback' in name:
                score = 100
            elif 'orayvirtualaudio' in name:
                score = 95
            elif 'virtual audio' in name or 'virtualaudio' in name:
                score = 90
            elif 'virtual' in name:
                score = 80
            elif device.get('is_output'):
                # Full-duplex devices can still be loopback-capable.
                score = 60

            if score > 0:
                candidates.append((score, device))

        candidates.sort(key=lambda x: x[0], reverse=True)
        for score, device in candidates:
            try:
                print(
                    f"[AudioRecorder] Trying system-audio device: {device['name']} "
                    f"(index={device['index']}, score={score})"
                )
                # Prefer stereo capture for loopback devices; fall back to mono.
                for channels in (2, 1):
                    if int(device.get('max_input_channels', 0) or 0) < channels:
                        continue
                    try:
                        stream = p.open(
                            format=self.format,
                            channels=channels,
                            rate=self.rate,
                            input=True,
                            input_device_index=device['index'],
                            frames_per_buffer=self.chunk
                        )
                        self._selected_system_device_name = str(device["name"])
                        self._selected_system_channels = channels
                        self._selected_system_output_device_name = self._resolve_output_device_name_for_loopback(
                            devices, self._selected_system_device_name
                        )
                        return stream, channels
                    except Exception as channel_error:
                        print(
                            f"[AudioRecorder] Failed opening {device['name']} as {channels}ch system audio: "
                            f"{channel_error}"
                        )
            except Exception as e:
                print(
                    f"[AudioRecorder] Failed to open {device['name']} as system audio: {e}"
                )

        print("[AudioRecorder] No usable loopback device found for system audio.")
        print("[AudioRecorder] Install one of: BlackHole / Soundflower / Loopback")
        print("[AudioRecorder] Example: brew install blackhole-2ch")
        return None, 0

    def _resolve_output_device_name_for_loopback(self, devices: list, input_name: str) -> Optional[str]:
        """
        Resolve a loopback device's output-side name from its input-side name.
        """
        target = str(input_name).lower()
        exact = None
        fuzzy = None
        for d in devices:
            if not d.get("is_output"):
                continue
            name = str(d.get("name", ""))
            lname = name.lower()
            if lname == target:
                exact = name
                break
            if target in lname or lname in target:
                if fuzzy is None:
                    fuzzy = name
        return exact or fuzzy or input_name

    def _route_output_to_selected_system_device(self):
        """On macOS, route default system output to the selected loopback device."""
        import sys
        if sys.platform != "darwin":
            return
        self._init_coreaudio()
        target_name = self._selected_system_output_device_name or self._selected_system_device_name
        if not target_name:
            return
        current = self._ca_get_default_output_device()
        system_current = self._ca_get_default_system_output_device()
        if not current and not system_current:
            return
        target = self._ca_find_device_by_name(target_name)
        if not target:
            print(f"[AudioRecorder] Cannot find output device for routing: {target_name}")
            return
        target_id, target_exact_name = target
        routed_output = False
        routed_system = False

        if current:
            current_id, current_name = current
            if current_name.lower() != target_exact_name.lower():
                status = self._ca_set_default_output_device(target_id)
                if status == 0:
                    self._previous_output_device_id = current_id
                    routed_output = True
                    print(
                        f"[AudioRecorder] Routed macOS output: '{current_name}' -> '{target_exact_name}'"
                    )
                else:
                    print(
                        f"[AudioRecorder] Failed to route macOS output to '{target_exact_name}' "
                        f"(status={status})"
                    )

        if system_current:
            system_id, system_name = system_current
            if system_name.lower() != target_exact_name.lower():
                status = self._ca_set_default_system_output_device(target_id)
                if status == 0:
                    self._previous_system_output_device_id = system_id
                    routed_system = True
                    print(
                        f"[AudioRecorder] Routed macOS system output: '{system_name}' -> "
                        f"'{target_exact_name}'"
                    )
                else:
                    print(
                        f"[AudioRecorder] Failed to route macOS system output to '{target_exact_name}' "
                        f"(status={status})"
                    )

        # If target is already the default output and no history is available,
        # remember current system-output device as fallback for restore/monitor.
        if (
            current
            and current[1].lower() == target_exact_name.lower()
            and self._previous_output_device_id is None
            and self._previous_system_output_device_id is not None
        ):
            self._previous_output_device_id = self._previous_system_output_device_id

        if not routed_output and not routed_system:
            print("[AudioRecorder] Output already routed to loopback target.")

    def _restore_previous_output_device(self):
        """Restore macOS default output after recording."""
        import sys
        if sys.platform != "darwin":
            return
        self._init_coreaudio()
        if (
            self._previous_output_device_id is None
            and self._previous_system_output_device_id is None
        ):
            return

        device_id = self._previous_output_device_id
        system_device_id = self._previous_system_output_device_id
        self._previous_output_device_id = None
        self._previous_system_output_device_id = None

        if device_id is not None:
            status = self._ca_set_default_output_device(device_id)
            if status == 0:
                restored = self._ca_get_device_name(device_id) or str(device_id)
                print(f"[AudioRecorder] Restored macOS output device: {restored}")
            else:
                print(f"[AudioRecorder] Failed to restore previous macOS output (status={status})")

        if system_device_id is not None:
            status = self._ca_set_default_system_output_device(system_device_id)
            if status == 0:
                restored = self._ca_get_device_name(system_device_id) or str(system_device_id)
                print(f"[AudioRecorder] Restored macOS system output device: {restored}")
            else:
                print(
                    f"[AudioRecorder] Failed to restore previous macOS system output "
                    f"(status={status})"
                )

    def _ca_get_default_output_device(self):
        """Return tuple (device_id, device_name) for macOS default output."""
        self._init_coreaudio()
        if not hasattr(self, "_CA_K_AUDIO_HARDWARE_DEFAULT_OUTPUT_DEVICE"):
            return None
        return self._ca_get_default_device_by_selector(self._CA_K_AUDIO_HARDWARE_DEFAULT_OUTPUT_DEVICE)

    def _ca_get_default_system_output_device(self):
        """Return tuple (device_id, device_name) for macOS default system output."""
        self._init_coreaudio()
        if not hasattr(self, "_CA_K_AUDIO_HARDWARE_DEFAULT_SYSTEM_OUTPUT_DEVICE"):
            return None
        return self._ca_get_default_device_by_selector(
            self._CA_K_AUDIO_HARDWARE_DEFAULT_SYSTEM_OUTPUT_DEVICE
        )

    def _ca_get_default_device_by_selector(self, selector: int):
        """Return tuple (device_id, device_name) for a default-device selector."""
        self._init_coreaudio()
        if not hasattr(self, "_ca"):
            return None
        out_addr = self._ca_property_address(selector)
        out_dev = ctypes.c_uint32(0)
        size = ctypes.c_uint32(ctypes.sizeof(out_dev))
        status = self._ca_audio_object_get_property_data(
            self._CA_K_AUDIO_OBJECT_SYSTEM_OBJECT,
            out_addr,
            size,
            ctypes.byref(out_dev),
        )
        if status != 0:
            return None
        name = self._ca_get_device_name(out_dev.value) or str(out_dev.value)
        return out_dev.value, name

    def _ca_find_device_by_name(self, target_name: str):
        self._init_coreaudio()
        if not hasattr(self, "_ca"):
            return None
        devices = self._ca_list_devices()
        target = target_name.lower()
        for device_id, name in devices:
            if name.lower() == target:
                return device_id, name
        for device_id, name in devices:
            if target in name.lower() or name.lower() in target:
                return device_id, name
        return None

    def _ca_get_device_name(self, device_id: int) -> Optional[str]:
        self._init_coreaudio()
        if not hasattr(self, "_ca"):
            return None
        name_addr = self._ca_property_address(self._CA_K_AUDIO_OBJECT_PROPERTY_NAME)
        cf_string_ref = ctypes.c_void_p()
        size = ctypes.c_uint32(ctypes.sizeof(cf_string_ref))
        status = self._ca_audio_object_get_property_data(
            device_id,
            name_addr,
            size,
            ctypes.byref(cf_string_ref),
        )
        if status != 0 or not cf_string_ref.value:
            return None
        buf = ctypes.create_string_buffer(512)
        ok = self._ca_cf.CFStringGetCString(
            cf_string_ref,
            buf,
            len(buf),
            self._CA_K_CF_STRING_ENCODING_UTF8,
        )
        if not ok:
            return None
        return buf.value.decode("utf-8", "ignore")

    def _ca_list_devices(self):
        self._init_coreaudio()
        if not hasattr(self, "_ca"):
            return []
        dev_addr = self._ca_property_address(self._CA_K_AUDIO_HARDWARE_PROPERTY_DEVICES)
        size = ctypes.c_uint32(0)
        st = self._ca_audio_object_get_property_data_size(
            self._CA_K_AUDIO_OBJECT_SYSTEM_OBJECT, dev_addr, ctypes.byref(size)
        )
        if st != 0 or size.value == 0:
            return []
        count = size.value // ctypes.sizeof(ctypes.c_uint32)
        arr_type = ctypes.c_uint32 * count
        arr = arr_type()
        st = self._ca_audio_object_get_property_data(
            self._CA_K_AUDIO_OBJECT_SYSTEM_OBJECT,
            dev_addr,
            size,
            ctypes.byref(arr),
        )
        if st != 0:
            return []
        out = []
        for i in range(count):
            device_id = int(arr[i])
            name = self._ca_get_device_name(device_id) or str(device_id)
            out.append((device_id, name))
        return out

    def _ca_set_default_output_device(self, device_id: int) -> int:
        self._init_coreaudio()
        if not hasattr(self, "_ca"):
            return -1
        return self._ca_set_default_device(
            self._CA_K_AUDIO_HARDWARE_DEFAULT_OUTPUT_DEVICE, device_id
        )

    def _ca_set_default_system_output_device(self, device_id: int) -> int:
        self._init_coreaudio()
        if not hasattr(self, "_ca"):
            return -1
        return self._ca_set_default_device(
            self._CA_K_AUDIO_HARDWARE_DEFAULT_SYSTEM_OUTPUT_DEVICE, device_id
        )

    def _ca_set_default_device(self, selector: int, device_id: int) -> int:
        out_addr = self._ca_property_address(selector)
        dev = ctypes.c_uint32(device_id)
        return int(
            self._ca_audio_object_set_property_data(
                self._CA_K_AUDIO_OBJECT_SYSTEM_OBJECT,
                out_addr,
                ctypes.c_uint32(ctypes.sizeof(dev)),
                ctypes.byref(dev),
            )
        )

    def _ca_property_address(self, selector: int):
        return self._ca_addr_struct(
            ctypes.c_uint32(selector),
            ctypes.c_uint32(self._CA_K_AUDIO_OBJECT_PROPERTY_SCOPE_GLOBAL),
            ctypes.c_uint32(self._CA_K_AUDIO_OBJECT_PROPERTY_ELEMENT_MAIN),
        )

    def _ca_audio_object_get_property_data_size(self, object_id: int, addr, out_size_ptr):
        return self._ca.AudioObjectGetPropertyDataSize(
            ctypes.c_uint32(object_id),
            ctypes.byref(addr),
            ctypes.c_uint32(0),
            None,
            out_size_ptr,
        )

    def _ca_audio_object_get_property_data(self, object_id: int, addr, io_size, out_ptr):
        return self._ca.AudioObjectGetPropertyData(
            ctypes.c_uint32(object_id),
            ctypes.byref(addr),
            ctypes.c_uint32(0),
            None,
            ctypes.byref(io_size),
            out_ptr,
        )

    def _ca_audio_object_set_property_data(self, object_id: int, addr, data_size, in_ptr):
        return self._ca.AudioObjectSetPropertyData(
            ctypes.c_uint32(object_id),
            ctypes.byref(addr),
            ctypes.c_uint32(0),
            None,
            data_size,
            in_ptr,
        )

    def _init_coreaudio(self):
        if getattr(self, "_ca_initialized", False):
            return
        import sys
        if sys.platform != "darwin":
            self._ca_initialized = True
            return
        self._ca = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreAudio.framework/CoreAudio")
        self._ca_cf = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        self._ca_addr_struct = type(
            "AudioObjectPropertyAddress",
            (ctypes.Structure,),
            {"_fields_": [("mSelector", ctypes.c_uint32), ("mScope", ctypes.c_uint32), ("mElement", ctypes.c_uint32)]},
        )
        self._CA_K_AUDIO_OBJECT_SYSTEM_OBJECT = 1
        self._CA_K_AUDIO_OBJECT_PROPERTY_SCOPE_GLOBAL = 0x676C6F62  # 'glob'
        self._CA_K_AUDIO_OBJECT_PROPERTY_ELEMENT_MAIN = 0
        self._CA_K_AUDIO_HARDWARE_DEFAULT_OUTPUT_DEVICE = 0x644F7574  # 'dOut'
        self._CA_K_AUDIO_HARDWARE_DEFAULT_SYSTEM_OUTPUT_DEVICE = 0x734F7574  # 'sOut'
        self._CA_K_AUDIO_HARDWARE_PROPERTY_DEVICES = 0x64657623  # 'dev#'
        self._CA_K_AUDIO_OBJECT_PROPERTY_NAME = 0x6C6E616D  # 'lnam'
        self._CA_K_CF_STRING_ENCODING_UTF8 = 0x08000100

        self._ca.AudioObjectGetPropertyDataSize.argtypes = [
            ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p
        ]
        self._ca.AudioObjectGetPropertyDataSize.restype = ctypes.c_int32
        self._ca.AudioObjectGetPropertyData.argtypes = [
            ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        ]
        self._ca.AudioObjectGetPropertyData.restype = ctypes.c_int32
        self._ca.AudioObjectSetPropertyData.argtypes = [
            ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p
        ]
        self._ca.AudioObjectSetPropertyData.restype = ctypes.c_int32

        self._ca_cf.CFStringGetCString.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint
        ]
        self._ca_cf.CFStringGetCString.restype = ctypes.c_bool
        self._ca_initialized = True

    def _open_microphone_stream(self, p):
        """Open microphone stream."""
        try:
            mic_index = self._resolve_microphone_device_index()
            return p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=mic_index,
                frames_per_buffer=self.chunk
            )
        except Exception as e:
            print(f"[AudioRecorder] Failed to open microphone stream: {e}")
            return None

    def _close_stream(self, stream):
        """Close a PyAudio stream safely."""
        try:
            stream.stop_stream()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass

    def _mix_audio_chunks(self, chunks):
        """
        Mix multiple PCM chunks into mono int16 chunk.

        Args:
            chunks: list of (bytes, channels)
        """
        if not chunks:
            return b""
        if not NUMPY_AVAILABLE:
            return chunks[0][0]

        mono_arrays = []
        for data, channels in chunks:
            channels = int(channels or 1)
            if not data:
                continue
            arr = np.frombuffer(data, dtype=np.int16).astype(np.int32)
            if channels > 1:
                frame_count = arr.size // channels
                if frame_count <= 0:
                    continue
                arr = arr[: frame_count * channels].reshape(frame_count, channels).mean(axis=1)
            mono_arrays.append(arr)

        if not mono_arrays:
            return b""
        if len(mono_arrays) == 1:
            return np.clip(mono_arrays[0], -32768, 32767).astype(np.int16).tobytes()

        min_len = min(a.size for a in mono_arrays)
        if min_len <= 0:
            return b""
        trimmed = [a[:min_len] for a in mono_arrays]
        mixed = np.sum(trimmed, axis=0) / len(trimmed)
        mixed = np.clip(mixed, -32768, 32767).astype(np.int16)
        return mixed.tobytes()

    def _open_monitor_output_stream(self, p, output_device_name: str, preferred_channels: int = 2):
        """Open an output stream on the previous output device for local monitoring."""
        devices = self.list_audio_devices()
        target = output_device_name.lower()
        candidates = []
        for d in devices:
            if not d.get("is_output"):
                continue
            name = str(d.get("name", ""))
            lname = name.lower()
            if lname == target or target in lname or lname in target:
                candidates.append(d)

        def _candidate_score(d):
            name = str(d.get("name", "")).lower()
            out_ch = int(d.get("max_output_channels", 0) or 0)
            score = out_ch * 10
            # Avoid low-quality headset/hands-free output profiles when possible.
            if "hands-free" in name or "handsfree" in name or "headset" in name or "hfp" in name:
                score -= 50
            return score

        channel_order = [max(1, int(preferred_channels or 1)), 2, 1]
        channel_order = list(dict.fromkeys(channel_order))

        for candidate in sorted(candidates, key=_candidate_score, reverse=True):
            for channels in channel_order:
                if int(candidate.get("max_output_channels", 0) or 0) < channels:
                    continue
                try:
                    stream = p.open(
                        format=self.format,
                        channels=channels,
                        rate=self.rate,
                        output=True,
                        output_device_index=candidate["index"],
                        frames_per_buffer=self.chunk,
                    )
                    return stream, channels
                except Exception:
                    continue

        # Fallback to current default output, best effort.
        for channels in channel_order:
            try:
                stream = p.open(
                    format=self.format,
                    channels=channels,
                    rate=self.rate,
                    output=True,
                    frames_per_buffer=self.chunk,
                )
                return stream, channels
            except Exception:
                continue
        return None, 1

    def _write_monitor_audio(self, stream, data: bytes, channels: int, source_channels: int = 1):
        """Write system-audio chunk to monitor output stream."""
        try:
            out = data
            source_channels = int(source_channels or 1)
            target_channels = int(channels or 1)
            if source_channels != target_channels:
                if NUMPY_AVAILABLE:
                    arr = np.frombuffer(data, dtype=np.int16)
                    if source_channels > 1:
                        frame_count = arr.size // source_channels
                        if frame_count > 0:
                            arr = arr[: frame_count * source_channels].reshape(
                                frame_count, source_channels
                            ).mean(axis=1).astype(np.int16)
                        else:
                            arr = np.array([], dtype=np.int16)
                    if target_channels == 2:
                        out = np.column_stack((arr, arr)).reshape(-1).astype(np.int16).tobytes()
                    else:
                        out = arr.astype(np.int16).tobytes()
                elif source_channels == 1 and target_channels == 2:
                    # Best effort when numpy is unavailable.
                    out = b"".join(data[i:i + 2] * 2 for i in range(0, len(data), 2))
            if self.monitor_audio_gain != 1.0:
                out = self._apply_pcm_gain(out, self.monitor_audio_gain)
            stream.write(out)
        except Exception as e:
            print(f"[AudioRecorder] Monitor playback error: {e}")

    def _stream_is_silent(self, stream, probe_chunks: int = 20, level_threshold: float = 2.0) -> bool:
        """
        Probe initial stream signal level.

        Returns True if all probe samples are near silence.
        """
        if not NUMPY_AVAILABLE:
            # If numpy is not available, avoid false negatives and keep stream.
            return False
        levels = []
        for _ in range(probe_chunks):
            try:
                data = stream.read(self.chunk, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                levels.append(float(np.abs(audio_data).mean()))
            except Exception:
                break
        if not levels:
            return False
        avg_level = sum(levels) / len(levels)
        print(f"[AudioRecorder] Probe level={avg_level:.2f} (threshold={level_threshold})")
        return avg_level < level_threshold

    def _find_output_device_index_by_name(self, output_device_name: str) -> Optional[int]:
        target = str(output_device_name or "").strip().lower()
        if not target:
            return None
        candidates = []
        for d in self.list_audio_devices():
            if not d.get("is_output"):
                continue
            name = str(d.get("name", ""))
            lname = name.lower()
            if lname == target:
                return int(d.get("index"))
            if target in lname or lname in target:
                candidates.append(d)
        if candidates:
            candidates.sort(
                key=lambda d: int(d.get("max_output_channels", 0) or 0),
                reverse=True,
            )
            return int(candidates[0].get("index"))
        return None

    def _apply_pcm_gain(self, data: bytes, gain: float) -> bytes:
        """Apply linear gain to int16 PCM bytes."""
        if not NUMPY_AVAILABLE or gain == 1.0 or not data:
            return data
        arr = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        arr *= float(gain)
        arr = np.clip(arr, -32768, 32767).astype(np.int16)
        return arr.tobytes()

    def _verify_loopback_signal(
        self,
        p,
        stream,
        source_channels: int,
        level_threshold: float = 1.0,
    ) -> bool:
        """
        Verify loopback device actually forwards output signal to its input.

        Strategy:
        - emit a short tone to current default output (already routed to loopback),
        - read back from system input stream,
        - ensure captured level is above threshold.
        """
        if not NUMPY_AVAILABLE:
            return True
        source_channels = max(1, int(source_channels or 1))
        out_channels = 2 if source_channels >= 2 else 1
        tone_stream = None
        try:
            output_device_index = self._find_output_device_index_by_name(
                self._selected_system_output_device_name or self._selected_system_device_name or ""
            )
            tone_stream = p.open(
                format=self.format,
                channels=out_channels,
                rate=self.rate,
                output=True,
                output_device_index=output_device_index,
                frames_per_buffer=self.chunk,
            )
            # Drain stale buffered data before probe.
            for _ in range(3):
                try:
                    stream.read(self.chunk, exception_on_overflow=False)
                except Exception:
                    break

            tone_duration_sec = 0.15
            tone_hz = 880.0
            amp = 0.25
            samples = max(1, int(self.rate * tone_duration_sec))
            t = np.arange(samples, dtype=np.float32) / float(self.rate)
            mono = (np.sin(2.0 * np.pi * tone_hz * t) * amp * 32767.0).astype(np.int16)
            if out_channels == 2:
                tone = np.column_stack((mono, mono)).reshape(-1).astype(np.int16).tobytes()
            else:
                tone = mono.tobytes()
            tone_stream.write(tone)

            levels = []
            for _ in range(12):
                data = stream.read(self.chunk, exception_on_overflow=False)
                arr = np.frombuffer(data, dtype=np.int16)
                if source_channels > 1:
                    frame_count = arr.size // source_channels
                    if frame_count <= 0:
                        continue
                    arr = arr[: frame_count * source_channels].reshape(
                        frame_count, source_channels
                    ).mean(axis=1)
                levels.append(float(np.abs(arr).mean()))
            max_level = max(levels) if levels else 0.0
            print(
                f"[AudioRecorder] Loopback verification max_level={max_level:.2f} "
                f"(threshold={level_threshold})"
            )
            return max_level >= level_threshold
        except Exception as e:
            # Keep recording path resilient if probe fails unexpectedly.
            print(f"[AudioRecorder] Loopback verification skipped due to error: {e}")
            return True
        finally:
            if tone_stream is not None:
                try:
                    tone_stream.stop_stream()
                except Exception:
                    pass
                try:
                    tone_stream.close()
                except Exception:
                    pass

    def _get_windows_system_audio(self, p):
        """
        Get system audio stream on Windows.

        Uses WASAPI loopback recording.
        """
        # Windows WASAPI loopback requires special handling
        # For now, return None - would need pyaudio with WASAPI support
        print("[AudioRecorder] Windows system audio requires WASAPI loopback support")
        return None, 0

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
