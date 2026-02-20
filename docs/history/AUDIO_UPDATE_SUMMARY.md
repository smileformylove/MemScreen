# 

## 

 MemScreen 

## 

### 1.  (`memscreen/audio/`)

#### `AudioRecorder`
- ****
- ****
  - macOS BlackHole 
  - Windows WASAPI loopback 
  - Linux PulseAudio/JACK 
- ****0.0-1.0
- ****

#### `AudioSource`
```python
class AudioSource(Enum):
    MICROPHONE = "microphone"    # 
    SYSTEM_AUDIO = "system_audio"  # 
    NONE = "none"                # 
```

### 2. Presenter  (`memscreen/presenters/recording_presenter.py`)

#### 
- ****`set_audio_source(source: AudioSource)`
- ****`get_audio_sources()`
- ****
- ****
- ****

#### 
```sql
ALTER TABLE recordings ADD COLUMN audio_file TEXT;
ALTER TABLE recordings ADD COLUMN audio_source TEXT;
```

### 3. UI  (`memscreen/ui/kivy_app.py`)

#### RecordingScreen 
- ****
  - No Audio
  - Microphone
  - System Audio
- ****
- ****

#### UI 
```
┌──────────────────────────────────────┐
│      Screen Recording                │
├──────────────────────────────────────┤
│                                      │
│         Preview Area                 │
│                                      │
├──────────────────────────────────────┤
│ [Screen Mode] [Audio] [Record Btn]  │
└──────────────────────────────────────┘
```

## 

```
MemScreen/
├── memscreen/
│   ├── audio/
│   │   ├── __init__.py              # 
│   │   └── audio_recorder.py        # 
│   ├── presenters/
│   │   └── recording_presenter.py   # 
│   └── ui/
│       └── kivy_app.py              # UI
├── docs/
│   └── AUDIO_RECORDING.md           # 
├── test_audio_recording.py          # 
└── pyproject.toml                   # 
```

## 

### 
```toml
"pyaudio>=0.2.11",      # 
"moviepy>=1.0.3",       # 
```

### 

**macOS:**
```bash
brew install portaudio          # PyAudio 
brew install blackhole-2ch      # 
```

**Windows:**
- PyAudio 
- 

**Linux:**
```bash
sudo apt-get install python3-pyaudio portaudio19-dev
```

## 

###  (`test_audio_recording.py`)
```
============================================================
Test Summary
============================================================
✓ Device listing: PASSED
✓ Microphone recording: PASSED
ℹ System audio: SKIPPED (requires setup)
```

### 
1. **** 4 2  + 2 
2. ****
   -  3 
   -  130 
   - 260 KB
   - 

## 

### 
1.  MemScreen **Recording** 
2.  **Audio** 
   - **No Audio**
   - **Microphone**
   - **System Audio**
3. 
4.  **Start Recording** 
5.  **Stop Recording** 
6. 

### 
```python
from memscreen.audio import AudioRecorder, AudioSource

# 
recorder = AudioRecorder(output_dir="./audio")

# 
devices = recorder.list_audio_devices()

# 
recorder.start_recording(AudioSource.MICROPHONE)

# 
level = recorder.get_audio_level()

# 
audio_file = recorder.stop_recording()

# 
recorder.cleanup()
```

## 

### 
- ****WAV
- ****44.1 kHz
- ****
- ****16-bit
- ****1024 

### 
- ****H.264 (mp4v)
- ****AAC

## 

### MVP 
- **Model**`AudioRecorder`
- **View**`RecordingScreen`UI 
- **Presenter**`RecordingPresenter`

### 
- ****UI 
- ****
- ****
- ****

## 

1. ****
2. ****
3. ****
4. ****
5. ** Windows ** WASAPI loopback 
6. ****
7. ****

## 

### 

**Q:  "No audio devices found"**
- 
- 
- 

**Q: **
- macOS BlackHole (`brew install blackhole-2ch`)
- Windows/Linux

**Q: **
- 
-  CPU 
- 

## 

- ****[docs/AUDIO_RECORDING.md](docs/AUDIO_RECORDING.md)
- ****[test_audio_recording.py](test_audio_recording.py)
- **API ** docstring

## 

- Jixiang Luo (jixiangluo85@gmail.com)
- 2026-02-01
- MIT

## 



1. ****
2. ****macOSWindowsLinux
3. ****
4. **** UI
5. ****
6. ****

 MemScreen 
