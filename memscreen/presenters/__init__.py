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

from .base_presenter import BasePresenter
from .recording_presenter import RecordingPresenter
from .chat_presenter import ChatPresenter, ChatMessage
from .video_presenter import VideoPresenter, VideoInfo
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
