### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                 ###

import os
from typing import Dict, List, Optional, Union

from ollama import Client

from .base import BaseLlmConfig, LLMBase


class OllamaConfig(BaseLlmConfig):
    """
    Configuration class for Ollama-specific parameters.
    Inherits from BaseLlmConfig and adds Ollama-specific settings.
    """

    def __init__(
        self,
        # Base parameters
        model: Optional[str] = None,
        temperature: float = 0.45,  # Optimized: lower for 2-3x faster convergence
        api_key: Optional[str] = None,
        max_tokens: int = 384,  # Optimized: balanced for speed and quality
        top_p: float = 0.85,  # Optimized: balanced for speed and diversity
        top_k: int = 25,  # Optimized: good balance
        enable_vision: bool = False,
        vision_details: Optional[str] = "auto",
        http_client_proxies: Optional[dict] = None,
        # Ollama-specific parameters (aliased names)
        num_predict: Optional[int] = None,  # Alias for max_tokens (Ollama naming)
        num_ctx: Optional[int] = None,  # Context window size
        num_gpu: Optional[int] = None,  # GPU layers
        num_thread: Optional[int] = None,  # CPU threads
        repeat_penalty: Optional[float] = None,  # Repeat penalty
        # Additional Ollama-specific parameters
        ollama_base_url: Optional[str] = None,
        output_format: Optional[str] = "json",
        format_options: Optional[str] = None,
    ):
        """
        Initialize Ollama configuration.

        Args:
            model: Ollama model to use, defaults to None
            temperature: Controls randomness (0.45 optimized for speed + naturalness), defaults to 0.45
            api_key: Ollama API key, defaults to None
            max_tokens: Maximum tokens to generate (384 optimized for speed), defaults to 384
            top_p: Nucleus sampling parameter (0.85 optimized), defaults to 0.85
            top_k: Top-k sampling parameter (25 optimized), defaults to 25
            enable_vision: Enable vision capabilities, defaults to False
            vision_details: Vision detail level, defaults to "auto"
            http_client_proxies: HTTP client proxy settings, defaults to None
            num_predict: Alias for max_tokens (Ollama's parameter name)
            num_ctx: Context window size
            num_gpu: Number of GPU layers
            num_thread: Number of CPU threads
            repeat_penalty: Repeat penalty for generated text
            ollama_base_url: Ollama base URL, defaults to None
        """
        # Handle num_predict alias - if provided, use it for max_tokens
        if num_predict is not None:
            max_tokens = num_predict

        # Initialize base parameters
        super().__init__(
            model=model,
            temperature=temperature,
            api_key=api_key,
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            enable_vision=enable_vision,
            vision_details=vision_details,
            http_client_proxies=http_client_proxies,
        )

        # Ollama-specific parameters
        self.ollama_base_url = ollama_base_url
        self.num_ctx = num_ctx
        self.num_gpu = num_gpu
        self.num_thread = num_thread
        self.repeat_penalty = repeat_penalty
        # self.output_format =
        self.format_options = """
        {
            "json_schema": {
            "type": "object",
            "properties": {
                "response": {"type": "string"},
                "confidence": {"type": "number"},
                "entities": {"type": "array"}
            }
            }
        }
        """


class OllamaLLM(LLMBase):
    def __init__(self, config: Optional[Union[BaseLlmConfig, OllamaConfig, Dict]] = None):
        # Convert to OllamaConfig if needed
        if config is None:
            config = OllamaConfig()
        elif isinstance(config, dict):
            config = OllamaConfig(**config)
        elif isinstance(config, BaseLlmConfig) and not isinstance(config, OllamaConfig):
            # Convert BaseLlmConfig to OllamaConfig
            config = OllamaConfig(
                model=config.model,
                temperature=config.temperature,
                api_key=config.api_key,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                top_k=config.top_k,
                enable_vision=config.enable_vision,
                vision_details=config.vision_details,
                http_client_proxies=config.http_client,
            )

        super().__init__(config)

        if not self.config.model:
            self.config.model = "qwen2.5vl:7b"

        # Create ollama client
        self.client = Client(host=self.config.ollama_base_url)

        # Fix for macOS system proxy issue: replace the internal httpx client
        # The ollama library uses httpx which picks up system proxy settings
        # If the proxy (127.0.0.1:7890) is not running, requests fail with 502
        try:
            import httpx
            import logging
            logger = logging.getLogger(__name__)

            # Store the base_url from the original client
            original_base_url = self.client._client.base_url

            # Create a new httpx client with trust_env=False
            new_httpx_client = httpx.Client(
                base_url=original_base_url,  # Preserve the base URL
                trust_env=False,  # Don't read system proxy settings
                timeout=60.0
            )

            # Replace the internal client
            self.client._client = new_httpx_client
            logger.info("Ollama LLM client patched to bypass system proxy")

        except Exception as e:
            pass  # Fall back to default client behavior

    def _parse_response(self, response, tools):
        """
        Process the response based on whether tools are used or not.

        Args:
            response: The raw response from API.
            tools: The list of tools provided in the request.

        Returns:
            str or dict: The processed response.
        """
        if tools:
            processed_response = {
                "content": response["message"]["content"] if isinstance(response, dict) else response.message.content,
                "tool_calls": [],
            }

            # Ollama doesn't support tool calls in the same way, so we return the content
            return processed_response
        else:
            # Handle both dict and object responses
            if isinstance(response, dict):
                return response["message"]["content"]
            else:
                return response.message.content

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        response_format=None,
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
        **kwargs,
    ):
        """
        Generate a response based on the given messages using Ollama.

        Args:
            messages (list): List of message dicts containing 'role' and 'content'.
            response_format (str or object, optional): Format of the response. Defaults to "text".
            tools (list, optional): List of tools that the model can call. Defaults to None.
            tool_choice (str, optional): Tool choice method. Defaults to "auto".
            **kwargs: Additional Ollama-specific parameters.

        Returns:
            str: The generated response.
        """
        # Build parameters for Ollama
        params = {
            "model": self.config.model,
            "messages": messages,
        }

        # Add options for Ollama (temperature, num_predict, top_p, etc.)
        options = {
            "temperature": self.config.temperature,
            "num_predict": self.config.max_tokens,
            "top_p": self.config.top_p,
        }

        # Add optional Ollama-specific parameters if they exist
        if hasattr(self.config, 'top_k') and self.config.top_k:
            options["top_k"] = self.config.top_k
        if hasattr(self.config, 'num_ctx') and self.config.num_ctx:
            options["num_ctx"] = self.config.num_ctx
        if hasattr(self.config, 'num_gpu') and self.config.num_gpu is not None:
            options["num_gpu"] = self.config.num_gpu
        if hasattr(self.config, 'num_thread') and self.config.num_thread:
            options["num_thread"] = self.config.num_thread
        if hasattr(self.config, 'repeat_penalty') and self.config.repeat_penalty:
            options["repeat_penalty"] = self.config.repeat_penalty

        params["options"] = options

        # Remove OpenAI-specific parameters that Ollama doesn't support
        params.pop("max_tokens", None)  # Ollama uses different parameter names

        response = self.client.chat(**params)
        return self._parse_response(response, tools)


__all__ = ["OllamaConfig", "OllamaLLM"]
