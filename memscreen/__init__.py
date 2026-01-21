"""
MemScreen - Ask Screen Anything with AI-Powered Visual Memory

A local, privacy-focused screen recording and analysis system that uses
computer vision and language models to understand and remember your screen content.

Example:
    >>> import memscreen
    >>> memscreen.capture_screen()
    >>> memscreen.query_screen("What did I just capture?")
"""

__version__ = "0.1.0"
__author__ = "Jixiang Luo"
__email__ = "jixiangluo85@gmail.com"

from .memory import Memory
from .chroma import ChromaDB

__all__ = ["Memory", "ChromaDB"]
