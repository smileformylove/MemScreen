### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                 ###

"""
Storage module for MemScreen.

This module provides database management classes for storing memory history.
"""

from .sqlite import SQLiteManager

__all__ = ["SQLiteManager"]
