### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                 ###

import os
from typing import Optional, Literal
from ollama import Client
import logging
import httpx

from .base import BaseEmbedderConfig, EmbeddingBase

logger = logging.getLogger(__name__)

__all__ = ["OllamaEmbedding"]


class OllamaEmbedding(EmbeddingBase):
    def __init__(self, config: Optional[BaseEmbedderConfig] = None):
        super().__init__(config)

        self.config.model = self.config.model or "nomic-embed-text"
        self.config.embedding_dims = self.config.embedding_dims or 512

        # Create ollama client
        self.client = Client(host=self.config.ollama_base_url)

        # Fix for macOS system proxy issue: replace the internal httpx client
        # The ollama library uses httpx which picks up system proxy settings
        # If the proxy (127.0.0.1:7890) is not running, requests fail with 502
        try:
            # Store the base_url from the original client
            original_base_url = self.client._client.base_url

            # Create a new httpx client with trust_env=False
            new_httpx_client = httpx.Client(
                base_url=original_base_url,  # Preserve the base URL
                trust_env=False,  # Don't read system proxy settings
                timeout=30.0
            )

            # Replace the internal client
            self.client._client = new_httpx_client
            logger.info("Ollama client patched to bypass system proxy")
        except Exception as e:
            logger.warning(f"Failed to patch Ollama client: {e}")

        self._ensure_model_exists()

    def _ensure_model_exists(self):
        """
        Ensure the specified model exists locally. If not, pull it from Ollama.

        Note: This is optional - if the check fails (e.g., due to ollama client compatibility),
        the embedder will still work if the model is already available.
        """
        try:
            local_models = self.client.list()["models"]
            if not any(model.get("name") == self.config.model for model in local_models):
                self.client.pull(self.config.model)
        except Exception as e:
            # Compatibility issue between ollama Python client and server
            # Log warning but don't fail initialization
            logger.warning(
                f"Could not verify embedding model exists: {e}. "
                f"This is likely a compatibility issue between ollama Python client and server. "
                f"The embedder will still work if model '{self.config.model}' is available."
            )

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
