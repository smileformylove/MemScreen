### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                 ###

from typing import Optional
from .base import BaseEmbedderConfig
from .mock import MockEmbeddings


__all__ = ["EmbedderFactory"]


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
            f"Failed to import class '{class_type}': {str(e)}"
        )


class EmbedderFactory:
    provider_to_class = {
        "openai": "memscreen.embeddings.openai.OpenAIEmbedding",
        "ollama": "memscreen.embeddings.ollama.OllamaEmbedding",
    }

    @classmethod
    def get_supported_providers(cls):
        """Return list of supported embedding providers."""
        return list(cls.provider_to_class.keys())

    @classmethod
    def create(cls, provider_name, config, vector_config: Optional[dict]):
        if provider_name == "upstash_vector" and vector_config and vector_config.enable_embeddings:
            return MockEmbeddings()
        class_type = cls.provider_to_class.get(provider_name)
        if class_type:
            embedder_instance = load_class(class_type)
            # embedder_instance = OllamaEmbedding
            base_config = BaseEmbedderConfig(**config)
            return embedder_instance(base_config)
        else:
            raise ValueError(f"Unsupported Embedder provider: {provider_name}")
