### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-01-29             ###
### license: MIT                 ###

from abc import ABC, abstractmethod
from typing import Optional, Union, Dict, Literal
import httpx


__all__ = ["BaseEmbedderConfig", "EmbeddingBase"]


class BaseEmbedderConfig(ABC):
    """
    Config for Embeddings.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        embedding_dims: Optional[int] = None,
        # Ollama specific
        ollama_base_url: Optional[str] = None,
        # Openai specific
        openai_base_url: Optional[str] = None,
        # Huggingface specific
        model_kwargs: Optional[dict] = None,
        huggingface_base_url: Optional[str] = None,
        # AzureOpenAI specific
        # azure_kwargs: Optional[AzureConfig] = {},
        azure_kwargs: Optional[str] = {},
        http_client_proxies: Optional[Union[Dict, str]] = None,
        # VertexAI specific
        vertex_credentials_json: Optional[str] = None,
        memory_add_embedding_type: Optional[str] = None,
        memory_update_embedding_type: Optional[str] = None,
        memory_search_embedding_type: Optional[str] = None,
        # Gemini specific
        output_dimensionality: Optional[str] = None,
        # LM Studio specific
        lmstudio_base_url: Optional[str] = "http://localhost:1234/v1",
        # AWS Bedrock specific
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: Optional[str] = "us-west-2",
    ):
        """
        Initializes a configuration class instance for the Embeddings.

        :param model: Embedding model to use, defaults to None
        :type model: Optional[str], optional
        :param api_key: API key to be use, defaults to None
        :type api_key: Optional[str], optional
        :param embedding_dims: The number of dimensions in the embedding, defaults to None
        :type embedding_dims: Optional[int], optional
        :param ollama_base_url: Base URL for the Ollama API, defaults to None
        :type ollama_base_url: Optional[str], optional
        :param model_kwargs: key-value arguments for the huggingface embedding model, defaults a dict inside init
        :type model_kwargs: Optional[Dict[str, Any]], defaults a dict inside init
        :param huggingface_base_url: Huggingface base URL to be use, defaults to None
        :type huggingface_base_url: Optional[str], optional
        :param openai_base_url: Openai base URL to be use, defaults to "https://api.openai.com/v1"
        :type openai_base_url: Optional[str], optional
        :param azure_kwargs: key-value arguments for the AzureOpenAI embedding model, defaults a dict inside init
        :type azure_kwargs: Optional[Dict[str, Any]], defaults a dict inside init
        :param http_client_proxies: The proxy server settings used to create self.http_client, defaults to None
        :type http_client_proxies: Optional[Dict | str], optional
        :param vertex_credentials_json: The path to the Vertex AI credentials JSON file, defaults to None
        :type vertex_credentials_json: Optional[str], optional
        :param memory_add_embedding_type: The type of embedding to use for the add memory action, defaults to None
        :type memory_add_embedding_type: Optional[str], optional
        :param memory_update_embedding_type: The type of embedding to use for the update memory action, defaults to None
        :type memory_update_embedding_type: Optional[str], optional
        :param memory_search_embedding_type: The type of embedding to use for the search memory action, defaults to None
        :type memory_search_embedding_type: Optional[str], optional
        :param lmstudio_base_url: LM Studio base URL to be use, defaults to "http://localhost:1234/v1"
        :type lmstudio_base_url: Optional[str], optional
        """

        self.model = model
        self.api_key = api_key
        self.openai_base_url = openai_base_url
        self.embedding_dims = embedding_dims

        # AzureOpenAI specific
        self.http_client = httpx.Client(proxies=http_client_proxies) if http_client_proxies else None

        # Ollama specific
        self.ollama_base_url = ollama_base_url

        # Huggingface specific
        self.model_kwargs = model_kwargs or {}
        self.huggingface_base_url = huggingface_base_url
        # AzureOpenAI specific
        # self.azure_kwargs = AzureConfig(**azure_kwargs) or {}

        # VertexAI specific
        self.vertex_credentials_json = vertex_credentials_json
        self.memory_add_embedding_type = memory_add_embedding_type
        self.memory_update_embedding_type = memory_update_embedding_type
        self.memory_search_embedding_type = memory_search_embedding_type

        # Gemini specific
        self.output_dimensionality = output_dimensionality

        # LM Studio specific
        self.lmstudio_base_url = lmstudio_base_url

        # AWS Bedrock specific
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region


class EmbeddingBase(ABC):
    """Initialized a base embedding class

    :param config: Embedding configuration option class, defaults to None
    :type config: Optional[BaseEmbedderConfig], optional
    """

    def __init__(self, config: Optional[BaseEmbedderConfig] = None):
        if config is None:
            self.config = BaseEmbedderConfig()
        else:
            self.config = config

    @abstractmethod
    def embed(self, text, memory_action: Optional[Literal["add", "search", "update"]]):
        """
        Get the embedding for the given text.

        Args:
            text (str): The text to embed.
            memory_action (optional): The type of embedding to use. Must be one of "add", "search", or "update". Defaults to None.
        Returns:
            list: The embedding vector.
        """
        pass

    def embed_batch(self, texts: list, memory_action: Optional[Literal["add", "search", "update"]] = None):
        """
        OPTIMIZATION: Get embeddings for multiple texts at once for better performance.
        Default implementation calls embed() for each text. Override this method
        in subclasses for true batch processing.

        Args:
            texts (list): List of texts to embed.
            memory_action (optional): The type of embedding to use. Must be one of "add", "search", or "update". Defaults to None.

        Returns:
            list: List of embedding vectors.
        """
        # Default implementation - just call embed() for each text
        return [self.embed(text, memory_action) for text in texts]
