### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-01-29             ###
### license: MIT                 ###

from typing import Optional, Literal
from ollama import Client
import logging

from .base import BaseEmbedderConfig, EmbeddingBase

logger = logging.getLogger(__name__)

__all__ = ["OllamaEmbedding"]


class OllamaEmbedding(EmbeddingBase):
    def __init__(self, config: Optional[BaseEmbedderConfig] = None):
        super().__init__(config)

        self.config.model = self.config.model or "nomic-embed-text"
        self.config.embedding_dims = self.config.embedding_dims or 512

        self.client = Client(host=self.config.ollama_base_url)
        self._ensure_model_exists()

    def _ensure_model_exists(self):
        """
        Ensure the specified model exists locally. If not, pull it from Ollama.
        """
        local_models = self.client.list()["models"]
        if not any(model.get("name") == self.config.model for model in local_models):
            self.client.pull(self.config.model)

    def embed(self, text, memory_action: Optional[Literal["add", "search", "update"]] = None):
        """
        Get the embedding for the given text using Ollama.

        Args:
            text (str): The text to embed.
            memory_action (optional): The type of embedding to use. Must be one of "add", "search", or "update". Defaults to None.
        Returns:
            list: The embedding vector.
        """
        response = self.client.embeddings(model=self.config.model, prompt=text)
        return response["embedding"]

    def embed_batch(self, texts: list, memory_action: Optional[Literal["add", "search", "update"]] = None):
        """
        OPTIMIZATION: Get embeddings for multiple texts at once using Ollama batch API.
        This is much faster than calling embed() for each text individually.

        Args:
            texts (list): List of texts to embed.
            memory_action (optional): The type of embedding to use. Must be one of "add", "search", or "update". Defaults to None.

        Returns:
            list: List of embedding vectors.
        """
        try:
            # Try to use Ollama's batch embedding endpoint if available
            # Note: Ollama doesn't have a native batch API yet, so we optimize by using
            # concurrent requests with thread pooling
            import concurrent.futures

            # Use ThreadPoolExecutor for parallel embedding generation
            # This significantly speeds up embedding multiple texts
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                embeddings = list(executor.map(
                    lambda text: self.embed(text, memory_action),
                    texts
                ))

            return embeddings

        except Exception as e:
            logger.warning(f"Batch embedding failed, falling back to sequential: {e}")
            # Fallback to sequential processing
            return [self.embed(text, memory_action) for text in texts]
