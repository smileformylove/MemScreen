### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                 ###

import importlib
from typing import Dict, List, Optional, Union

from .base import BaseLlmConfig
from .ollama import OllamaConfig


def load_class(class_type: str):
    """
    Safely load a class from a string path.

    This function replaces the unsafe eval() with importlib for security.
    Only allows importing from the memscreen package.

    Args:
        class_type: String path to class (e.g., "memscreen.llm.ollama.OllamaLLM")

    Returns:
        The class object.

    Raises:
        ImportError: If the class cannot be imported.
        ValueError: If the class path is invalid or outside memscreen package.

    Examples:
        >>> load_class("memscreen.llm.ollama.OllamaLLM")
        <class 'memscreen.llm.ollama.OllamaLLM'>
    """
    import importlib

    if not class_type:
        raise ValueError("class_type cannot be empty")

    # Security: Only allow importing from memscreen package
    if not class_type.startswith("memscreen."):
        raise ValueError(
            f"For security reasons, only classes from the memscreen package can be loaded. "
            f"Got: {class_type}"
        )

    try:
        module_path, class_name = class_type.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(
            f"Failed to load class '{class_type}': {e}"
        )
    except ValueError as e:
        raise ValueError(
            f"Invalid class path '{class_type}': {e}"
        )


class LlmFactory:
    """
    Factory for creating LLM instances with appropriate configurations.
    Supports both old-style BaseLlmConfig and new provider-specific configs.
    """

    # Provider mappings with their config classes
    provider_to_class = {
        "ollama": ("OllamaLLM", OllamaConfig),
        # "openai": ("memscreen.llms.openai.OpenAILLM", OpenAIConfig),
        # "groq": ("memscreen.llms.groq.GroqLLM", BaseLlmConfig),
        # "together": ("memscreen.llms.together.TogetherLLM", BaseLlmConfig),
        # "aws_bedrock": ("memscreen.llms.aws_bedrock.AWSBedrockLLM", BaseLlmConfig),
        "litellm": ("LiteLLM", BaseLlmConfig),
        # "azure_openai": ("memscreen.llms.azure_openai.AzureOpenAILLM", AzureOpenAIConfig),
        # "openai_structured": ("memscreen.llms.openai_structured.OpenAIStructuredLLM", OpenAIConfig),
        # "azure_openai_structured": ("memscreen.llms.azure_openai_structured.AzureOpenAIStructuredLLM", AzureOpenAIConfig),
        # "gemini": ("memscreen.llms.gemini.GeminiLLM", BaseLlmConfig),
        # "deepseek": ("memscreen.llms.deepseek.DeepSeekLLM", DeepSeekConfig),
        # "xai": ("memscreen.llms.xai.XAILLM", BaseLlmConfig),
        # "sarvam": ("memscreen.llms.sarvam.SarvamLLM", BaseLlmConfig),
        "langchain": ("LangchainLLM", BaseLlmConfig),
    }

    @classmethod
    def create(cls, provider_name: str, config: Optional[Union[BaseLlmConfig, Dict]] = None, **kwargs):
        """
        Create an LLM instance with the appropriate configuration.

        Args:
            provider_name (str): The provider name (e.g., 'openai', 'anthropic')
            config: Configuration object or dict. If None, will create default config
            **kwargs: Additional configuration parameters

        Returns:
            Configured LLM instance

        Raises:
            ValueError: If provider is not supported
        """
        if provider_name not in cls.provider_to_class:
            raise ValueError(f"Unsupported Llm provider: {provider_name}")

        class_type, config_class = cls.provider_to_class[provider_name]
        llm_class = load_class(class_type)
        # llm_class = OllamaLLM

        # Handle configuration
        if config is None:
            # Create default config with kwargs
            config = config_class(**kwargs)
        elif isinstance(config, dict):
            # Merge dict config with kwargs
            config.update(kwargs)
            config = config_class(**config)
        elif isinstance(config, BaseLlmConfig):
            # Convert base config to provider-specific config if needed
            if config_class != BaseLlmConfig:
                # Convert to provider-specific config
                config_dict = {
                    "model": config.model,
                    "temperature": config.temperature,
                    "api_key": config.api_key,
                    "max_tokens": config.max_tokens,
                    "top_p": config.top_p,
                    "top_k": config.top_k,
                    "enable_vision": config.enable_vision,
                    "vision_details": config.vision_details,
                    "http_client_proxies": config.http_client,
                }
                config_dict.update(kwargs)
                config = config_class(**config_dict)
            else:
                # Use base config as-is
                pass
        else:
            # Assume it's already the correct config type
            pass

        return llm_class(config)

    @classmethod
    def register_provider(cls, name: str, class_path: str, config_class=None):
        """
        Register a new provider.

        Args:
            name (str): Provider name
            class_path (str): Full path to LLM class
            config_class: Configuration class for the provider (defaults to BaseLlmConfig)
        """
        if config_class is None:
            config_class = BaseLlmConfig
        cls.provider_to_class[name] = (class_path, config_class)

    @classmethod
    def get_supported_providers(cls) -> list:
        """
        Get list of supported providers.

        Returns:
            list: List of supported provider names
        """
        return list(cls.provider_to_class.keys())


__all__ = ["load_class", "LlmFactory"]
