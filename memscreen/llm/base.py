### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                 ###

import httpx
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union


class BaseLlmConfig(ABC):
    """
    Base configuration for LLMs with only common parameters.
    Provider-specific configurations should be handled by separate config classes.

    This class contains only the parameters that are common across all LLM providers.
    For provider-specific parameters, use the appropriate provider config class.
    """

    def __init__(
        self,
        model: Optional[Union[str, Dict]] = None,
        temperature: float = 0.1,
        api_key: Optional[str] = None,
        max_tokens: int = 2000,
        top_p: float = 0.1,
        top_k: int = 1,
        enable_vision: bool = False,
        vision_details: Optional[str] = "auto",
        http_client_proxies: Optional[Union[Dict, str]] = None,
    ):
        """
        Initialize a base configuration class instance for the LLM.

        Args:
            model: The model identifier to use (e.g., "gpt-4o-mini", "claude-3-5-sonnet-20240620")
                Defaults to None (will be set by provider-specific configs)
            temperature: Controls the randomness of the model's output.
                Higher values (closer to 1) make output more random, lower values make it more deterministic.
                Range: 0.0 to 2.0. Defaults to 0.1
            api_key: API key for the LLM provider. If None, will try to get from environment variables.
                Defaults to None
            max_tokens: Maximum number of tokens to generate in the response.
                Range: 1 to 4096 (varies by model). Defaults to 2000
            top_p: Nucleus sampling parameter. Controls diversity via nucleus sampling.
                Higher values (closer to 1) make word selection more diverse.
                Range: 0.0 to 1.0. Defaults to 0.1
            top_k: Top-k sampling parameter. Limits the number of tokens considered for each step.
                Higher values make word selection more diverse.
                Range: 1 to 40. Defaults to 1
            enable_vision: Whether to enable vision capabilities for the model.
                Only applicable to vision-enabled models. Defaults to False
            vision_details: Level of detail for vision processing.
                Options: "low", "high", "auto". Defaults to "auto"
            http_client_proxies: Proxy settings for HTTP client.
                Can be a dict or string. Defaults to None
        """
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.top_k = top_k
        self.enable_vision = enable_vision
        self.vision_details = vision_details
        self.http_client = httpx.Client(proxies=http_client_proxies) if http_client_proxies else None


class LLMBase(ABC):
    """
    Base class for all LLM providers.
    Handles common functionality and delegates provider-specific logic to subclasses.
    """

    def __init__(self, config: Optional[Union[BaseLlmConfig, Dict]] = None):
        """Initialize a base LLM class

        :param config: LLM configuration option class or dict, defaults to None
        :type config: Optional[Union[BaseLlmConfig, Dict]], optional
        """
        if config is None:
            self.config = BaseLlmConfig()
        elif isinstance(config, dict):
            # Handle dict-based configuration (backward compatibility)
            self.config = BaseLlmConfig(**config)
        else:
            self.config = config

        # Validate configuration
        self._validate_config()

    def _validate_config(self):
        """
        Validate the configuration.
        Override in subclasses to add provider-specific validation.
        """
        if not hasattr(self.config, "model"):
            raise ValueError("Configuration must have a 'model' attribute")

        if not hasattr(self.config, "api_key") and not hasattr(self.config, "api_key"):
            # Check if API key is available via environment variable
            # This will be handled by individual providers
            pass

    def _is_reasoning_model(self, model: str) -> bool:
        """
        Check if the model is a reasoning model or GPT-5 series that doesn't support certain parameters.

        Args:
            model: The model name to check

        Returns:
            bool: True if the model is a reasoning model or GPT-5 series
        """
        reasoning_models = {
            "o1", "o1-preview", "o3-mini", "o3",
            "gpt-5", "gpt-5o", "gpt-5o-mini", "gpt-5o-micro",
        }

        if model.lower() in reasoning_models:
            return True

        model_lower = model.lower()
        if any(reasoning_model in model_lower for reasoning_model in ["gpt-5", "o1", "o3"]):
            return True

        return False

    def _get_supported_params(self, **kwargs) -> Dict:
        """
        Get parameters that are supported by the current model.
        Filters out unsupported parameters for reasoning models and GPT-5 series.

        Args:
            **kwargs: Additional parameters to include

        Returns:
            Dict: Filtered parameters dictionary
        """
        model = getattr(self.config, 'model', '')

        if self._is_reasoning_model(model):
            supported_params = {}

            if "messages" in kwargs:
                supported_params["messages"] = kwargs["messages"]
            if "response_format" in kwargs:
                supported_params["response_format"] = kwargs["response_format"]
            if "tools" in kwargs:
                supported_params["tools"] = kwargs["tools"]
            if "tool_choice" in kwargs:
                supported_params["tool_choice"] = kwargs["tool_choice"]

            return supported_params
        else:
            # For regular models, include all common parameters
            return self._get_common_params(**kwargs)

    @abstractmethod
    def generate_response(
        self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None, tool_choice: str = "auto", **kwargs
    ):
        """
        Generate a response based on the given messages.

        Args:
            messages (list): List of message dicts containing 'role' and 'content'.
            tools (list, optional): List of tools that the model can call. Defaults to None.
            tool_choice (str, optional): Tool choice method. Defaults to "auto".
            **kwargs: Additional provider-specific parameters.

        Returns:
            str or dict: The generated response.
        """
        pass

    def _get_common_params(self, **kwargs) -> Dict:
        """
        Get common parameters that most providers use.

        Returns:
            Dict: Common parameters dictionary.
        """
        params = {
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
        }

        # Add provider-specific parameters from kwargs
        params.update(kwargs)

        return params


__all__ = ["BaseLlmConfig", "LLMBase"]
