### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                 ###

import importlib
from typing import Any, Dict


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


class VectorStoreFactory:
    """Factory class for creating vector store instances."""

    provider_to_class = {
        "chroma": "ChromaDB",
        "milvus": "MilvusDB",
    }

    @classmethod
    def create(cls, provider_name: str, config: Dict[str, Any]) -> Any:
        """
        Create a vector store instance.

        Args:
            provider_name: Name of the vector store provider (e.g., "chroma", "milvus")
            config: Configuration dictionary or Pydantic model for the vector store

        Returns:
            An instance of the specified vector store

        Raises:
            ValueError: If the provider name is not supported

        Examples:
            >>> factory = VectorStoreFactory()
            >>> store = factory.create("chroma", {"path": "./db"})
        """
        class_type = cls.provider_to_class.get(provider_name)
        if class_type:
            if not isinstance(config, dict):
                config = config.model_dump()
            vector_store_instance = load_class(class_type)
            # vector_store_instance = ChromaDB
            return vector_store_instance(**config)
        else:
            raise ValueError(f"Unsupported VectorStore provider: {provider_name}")

    @classmethod
    def reset(cls, instance: Any) -> Any:
        """
        Reset a vector store instance.

        Args:
            instance: The vector store instance to reset

        Returns:
            The reset instance
        """
        instance.reset()
        return instance
