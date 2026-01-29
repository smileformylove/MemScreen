### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-01-29             ###
### license: MIT                 ###

"""
Memory-related models and configurations.

This module contains Pydantic models for Memory configuration and data structures.
"""

import os
from enum import Enum
from typing import Any, Dict, Optional, ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator

# Import graph models if available
try:
    from ..graph.models import GraphConfig
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False
    GraphConfig = None

# Set up the directory path
home_dir = os.path.expanduser("~")
memscreen_dir = os.environ.get("memscreen_DIR") or os.path.join(home_dir, ".memscreen")
os.makedirs(memscreen_dir, exist_ok=True)


class EmbedderConfig(BaseModel):
    """Configuration for embedding models."""

    provider: str = Field(
        description="Provider of the embedding model (e.g., 'ollama', 'openai')",
        default="ollama",
    )
    config: Optional[dict] = Field(description="Configuration for the specific embedding model", default={})

    @field_validator("config")
    def validate_config(cls, v, values):
        provider = values.data.get("provider")
        if provider in [
            "openai",
            "ollama",
            "huggingface",
        ]:
            return v
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")


class LlmConfig(BaseModel):
    """Configuration for language models."""

    provider: str = Field(description="Provider of the LLM (e.g., 'ollama', 'openai')", default="ollama")
    config: Optional[dict] = Field(description="Configuration for the specific LLM", default={})

    @field_validator("config")
    def validate_config(cls, v, values):
        provider = values.data.get("provider")
        if provider in (
            "openai",
            "ollama",
        ):
            return v
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


class ChromaDbConfig(BaseModel):
    """Configuration for ChromaDB vector store."""

    try:
        from chromadb.api.client import Client
    except ImportError:
        raise ImportError("The 'chromadb' library is required. Please install it using 'pip install chromadb'.")
    Client: ClassVar[type] = Client

    collection_name: str = Field("memscreen", description="Default name for the collection")
    client: Optional[Client] = Field(None, description="Existing ChromaDB client instance")
    path: Optional[str] = Field(None, description="Path to the database directory")
    host: Optional[str] = Field(None, description="Database connection remote host")
    port: Optional[int] = Field(None, description="Database connection remote port")

    @model_validator(mode="before")
    def check_host_port_or_path(cls, values):
        host, port, path = values.get("host"), values.get("port"), values.get("path")
        if not path and not (host and port):
            raise ValueError("Either 'host' and 'port' or 'path' must be provided.")
        return values

    @model_validator(mode="before")
    @classmethod
    def validate_extra_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        allowed_fields = set(cls.model_fields.keys())
        input_fields = set(values.keys())
        extra_fields = input_fields - allowed_fields
        if extra_fields:
            raise ValueError(
                f"Extra fields not allowed: {', '.join(extra_fields)}. Please input only the following fields: {', '.join(allowed_fields)}"
            )
        return values

    model_config = {
        "arbitrary_types_allowed": True,
    }


class VectorStoreConfig(BaseModel):
    """Configuration for vector stores."""

    provider: str = Field(
        description="Provider of the vector store (e.g., 'qdrant', 'chroma', 'upstash_vector')",
        default="chroma",
    )
    config: Optional[Dict] = Field(description="Configuration for the specific vector store", default=None)

    _provider_configs: Dict[str, str] = {
        "chroma": "ChromaDbConfig",
        "milvus": "MilvusDBConfig",
    }

    @model_validator(mode="after")
    def validate_and_create_config(self) -> "VectorStoreConfig":
        provider = self.provider
        config = self.config

        if provider not in self._provider_configs:
            raise ValueError(f"Unsupported vector store provider: {provider}")

        if provider == "chroma":
            config_class = ChromaDbConfig
        else:
            module = __import__(
                f"{provider}",
                fromlist=[self._provider_configs[provider]],
            )
            config_class = getattr(module, self._provider_configs[provider])

        if config is None:
            config = {}

        if not isinstance(config, dict):
            if not isinstance(config, config_class):
                raise ValueError(f"Invalid config type for provider {provider}")
            return self

        # also check if path in allowed kays for pydantic model, and whether config extra fields are allowed
        if "path" not in config and "path" in config_class.__annotations__:
            config["path"] = f"/tmp/{provider}"

        self.config = config_class(**config)
        return self


class MemoryItem(BaseModel):
    """Represents a single memory item."""

    id: str = Field(..., description="The unique identifier for the text data")
    memory: str = Field(
        ..., description="The memory deduced from the text data"
    )  # TODO After prompt changes from platform, update this
    hash: Optional[str] = Field(None, description="The hash of the memory")
    # The metadata value can be anything and not just string. Fix it
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the text data")
    score: Optional[float] = Field(None, description="The score associated with the text data")
    created_at: Optional[str] = Field(None, description="The timestamp when the memory was created")
    updated_at: Optional[str] = Field(None, description="The timestamp when the memory was updated")


class MemoryConfig(BaseModel):
    """Configuration for the Memory system."""

    vector_store: VectorStoreConfig = Field(
        description="Configuration for the vector store",
        default_factory=VectorStoreConfig,
    )
    llm: LlmConfig = Field(
        description="Configuration for the language model",
        default_factory=LlmConfig,
    )
    mllm: LlmConfig = Field(
        description="Configuration for the language model",
        default_factory=LlmConfig,
    )
    embedder: EmbedderConfig = Field(
        description="Configuration for the embedding model",
        default_factory=EmbedderConfig,
    )
    history_db_path: str = Field(
        description="Path to the history database",
        default=os.path.join(memscreen_dir, "history.db"),
    )
    enable_graph: bool = Field(
        description="Enable knowledge graph memory",
        default=False,
    )
    graph_store: Optional[GraphConfig] = Field(
        description="Configuration for the graph store",
        default=None,
    )
    version: str = Field(
        description="The version of the API",
        default="v1.1",
    )
    custom_fact_extraction_prompt: Optional[str] = Field(
        description="Custom prompt for the fact extraction",
        default=None,
    )
    custom_update_memory_prompt: Optional[str] = Field(
        description="Custom prompt for the update memory",
        default=None,
    )
    timezone: str = Field(
        description="Timezone for timestamps (e.g., 'US/Pacific', 'UTC')",
        default="US/Pacific",
    )


class MemoryType(Enum):
    """Types of memory supported by the system."""

    SEMANTIC = "semantic_memory"
    EPISODIC = "episodic_memory"
    PROCEDURAL = "procedural_memory"


__all__ = [
    "EmbedderConfig",
    "LlmConfig",
    "ChromaDbConfig",
    "VectorStoreConfig",
    "MemoryItem",
    "MemoryConfig",
    "MemoryType",
]
