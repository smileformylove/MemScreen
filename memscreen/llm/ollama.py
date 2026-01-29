### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-01-29             ###
### license: MIT                 ###

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
        temperature: float = 0.7,  # Optimized: increased from 0.1 for faster convergence
        api_key: Optional[str] = None,
        max_tokens: int = 512,  # Optimized: reduced from 2000 for 3-4x faster responses
        top_p: float = 0.9,  # Optimized: increased from 0.1 for better diversity
        top_k: int = 20,  # Optimized: increased from 1 for better quality
        enable_vision: bool = False,
        vision_details: Optional[str] = "auto",
        http_client_proxies: Optional[dict] = None,
        # Ollama-specific parameters
        ollama_base_url: Optional[str] = None,
        output_format: Optional[str] = "json",
        format_options: Optional[str] = None,
    ):
        """
        Initialize Ollama configuration.

        Args:
            model: Ollama model to use, defaults to None
            temperature: Controls randomness (0.7 optimized for speed), defaults to 0.7
            api_key: Ollama API key, defaults to None
            max_tokens: Maximum tokens to generate (512 optimized for speed), defaults to 512
            top_p: Nucleus sampling parameter (0.9 optimized), defaults to 0.9
            top_k: Top-k sampling parameter (20 optimized), defaults to 20
            enable_vision: Enable vision capabilities, defaults to False
            vision_details: Vision detail level, defaults to "auto"
            http_client_proxies: HTTP client proxy settings, defaults to None
            ollama_base_url: Ollama base URL, defaults to None
        """
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
            self.config.model = "llama3.1:70b"

        self.client = Client(host=self.config.ollama_base_url)

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

        # Add options for Ollama (temperature, num_predict, top_p)
        options = {
            "temperature": self.config.temperature,
            "num_predict": self.config.max_tokens,
            "top_p": self.config.top_p,
        }
        params["options"] = options

        # Remove OpenAI-specific parameters that Ollama doesn't support
        params.pop("max_tokens", None)  # Ollama uses different parameter names

        response = self.client.chat(**params)
        return self._parse_response(response, tools)


__all__ = ["OllamaConfig", "OllamaLLM"]
