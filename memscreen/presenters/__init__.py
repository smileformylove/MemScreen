### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""Presenter layer for MVP architecture

This package contains the Presenter classes that act as intermediaries
between the View (UI) and Model (business logic/data).

MVP Pattern:
- View: UI components (tabs) - only handles display and user input
- Presenter: Business logic - coordinates between View and Model
- Model: Data and business rules - Memory, Database, APIs
"""

# Lazy imports to avoid Kivy initialization when importing RecordingPresenter
# Import these only when needed to keep floating_ball_app standalone

from .base_presenter import BasePresenter
from .recording_presenter import RecordingPresenter
from .chat_presenter import ChatPresenter, ChatMessage
from .process_mining_presenter import ProcessMiningPresenter

__all__ = [
    "BasePresenter",
    "RecordingPresenter",
    "ChatPresenter",
    "ChatMessage",
    "VideoPresenter",
    "VideoInfo",
    "ProcessMiningPresenter",
]

def __getattr__(name):
    """Lazy import for Kivy-dependent presenters"""
    if name == "VideoPresenter":
        from .video_presenter import VideoPresenter
        return VideoPresenter
    elif name == "VideoInfo":
        from .video_presenter import VideoInfo
        return VideoInfo
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
