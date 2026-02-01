# Audio Recording Feature

MemScreen now supports audio recording alongside screen recording!

## Features

- **Microphone Recording**: Record audio from your microphone
- **System Audio Recording**: Record audio from your system (speakers/output)
- **Unified Interface**: Seamlessly integrated into the Recording tab
- **Automatic Merging**: Audio is automatically merged with video recordings
- **Real-time Monitoring**: View audio levels during recording

## Setup

### 1. Install Dependencies

The audio recording feature requires two additional dependencies:

```bash
pip install pyaudio moviepy
```

#### Platform-Specific Installation

**macOS:**
```bash
# Install portaudio (required for pyaudio)
brew install portaudio

# Install pyaudio
pip install pyaudio

# For system audio recording, install BlackHole
brew install blackhole-2ch
```

**Windows:**
```bash
# PyAudio should install directly
pip install pyaudio

# For system audio, you may need additional setup
# See Windows section below
```

**Linux (Ubuntu/Debian):**
```bash
# Install system dependencies
sudo apt-get install python3-pyaudio portaudio19-dev

# Install pyaudio
pip install pyaudio
```

### 2. Verify Audio Devices

Run the test script to verify your audio devices:

```bash
python test_audio_recording.py
```

This will list all available audio devices and test microphone recording.

## Usage

### Basic Recording with Audio

1. Open MemScreen and navigate to the **Recording** tab
2. Select your audio source from the **Audio** dropdown:
   - **No Audio**: Record video only (default)
   - **Microphone**: Record audio from your microphone
   - **System Audio**: Record system audio (requires setup)
3. Choose your recording mode (Full Screen or Custom Region)
4. Click **Start Recording**
5. Speak into your microphone or play audio on your system
6. Click **Stop Recording** when done

The audio will be automatically merged with the video recording.

### Audio Source Options

#### Microphone Recording

Records audio from your default microphone or a selected input device.

**Best for:**
- Narrating tutorials
- Recording voice notes
- Adding commentary to screen recordings

#### System Audio Recording

Records audio playing on your system (from websites, apps, etc.).

**macOS Setup:**
1. Install BlackHole: `brew install blackhole-2ch`
2. Open Audio MIDI Setup (Applications → Utilities → Audio MIDI Setup)
3. Create a Multi-Output Device that includes both BlackHole and your speakers
4. Set the Multi-Output Device as your system output
5. Select "System Audio" in MemScreen

**Best for:**
- Recording online meetings
- Capturing audio from videos
- Recording system sounds and notifications

**Windows Setup:**
System audio recording on Windows requires WASAPI loopback support. This feature is experimental on Windows.

## How It Works

1. **Recording Start**: When you start recording with audio enabled, MemScreen begins capturing both screen frames and audio simultaneously
2. **Background Processing**: Audio is recorded in a separate background thread to ensure smooth performance
3. **Automatic Merging**: When you stop recording, the audio and video are automatically merged using moviepy
4. **Database Storage**: Recording metadata (including audio source) is saved to the database for future reference

## Troubleshooting

### "No audio devices found"

- Ensure your microphone is connected and recognized by your system
- Check system privacy settings (macOS: System Preferences → Security & Privacy → Privacy → Microphone)
- Run `python test_audio_recording.py` to see available devices

### "System audio not available"

- **macOS**: Install BlackHole with `brew install blackhole-2ch`
- **Windows**: System audio recording is experimental; consider using microphone instead
- **Linux**: May require PulseAudio or JACK setup

### Audio is out of sync with video

- Ensure you're not running CPU-intensive tasks during recording
- Try reducing the recording interval (in settings)
- Check available disk space

### "Failed to merge audio and video"

- Ensure moviepy is installed: `pip install moviepy`
- Check that both video and audio files were created successfully
- Look for error messages in the console for more details

## API Usage

You can also use the audio recording functionality programmatically:

```python
from memscreen.audio import AudioRecorder, AudioSource

# Create recorder
recorder = AudioRecorder(output_dir="./audio")

# List available devices
devices = recorder.list_audio_devices()
for device in devices:
    print(f"{device['name']}: {device['index']}")

# Start recording from microphone
recorder.start_recording(AudioSource.MICROPHONE)

# Monitor audio level
level = recorder.get_audio_level()
print(f"Audio level: {level}")

# Stop recording
audio_file = recorder.stop_recording()
print(f"Saved to: {audio_file}")

# Cleanup
recorder.cleanup()
```

## Technical Details

- **Audio Format**: WAV (uncompressed)
- **Sample Rate**: 44.1 kHz
- **Channels**: Mono
- **Bit Depth**: 16-bit
- **Video Codec**: H.264 (mp4v)
- **Audio Codec**: AAC (after merging)

## Future Enhancements

Planned features for future releases:

- [ ] Audio level visualization in UI
- [ ] Multiple audio source recording simultaneously
- [ ] Audio-only recording mode
- [ ] Audio editing/trimming tools
- [ ] Better Windows system audio support
- [ ] Real-time audio waveform display

## Feedback

If you encounter any issues or have suggestions for improving the audio recording feature, please:

1. Check the troubleshooting section above
2. Run the test script to gather diagnostic information
3. Report issues on GitHub: https://github.com/smileformylove/MemScreen/issues

## License

This feature is part of MemScreen and is licensed under the MIT License.
