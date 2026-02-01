### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""
Audio recording module for MemScreen.

Supports recording from:
- Microphone
- System audio (speakers/output)
"""

from .audio_recorder import AudioRecorder, AudioSource

__all__ = ['AudioRecorder', 'AudioSource']
