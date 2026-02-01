### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                 ###

from typing import Optional, Literal

from .base import BaseEmbedderConfig, EmbeddingBase


__all__ = ["MockEmbeddings"]


class MockEmbeddings(EmbeddingBase):
    def embed(self, text, memory_action: Optional[Literal["add", "search", "update"]] = None):
        """
        Generate a mock embedding with dimension of 10.
        """
        return [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
