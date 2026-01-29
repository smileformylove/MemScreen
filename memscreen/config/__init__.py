"""
Centralized configuration management for MemScreen.

This module provides a unified configuration system that replaces scattered
config dictionaries across multiple files.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, field
import json
import yaml

try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Fallback to dataclass if pydantic not available
    BaseModel = object


class MemScreenConfig:
    """
    Centralized configuration for MemScreen.

    This class provides a single source of truth for all configuration values,
    eliminating duplication across files and enabling easy validation.
    """

    # Default paths
    DEFAULT_DB_DIR = Path("./db")
    DEFAULT_DB_NAME = "screen_capture.db"
    DEFAULT_CHROMA_DB_NAME = "chroma.sqlite3"
    DEFAULT_VIDEOS_DIR = "videos"
    DEFAULT_LOGS_DIR = "logs"

    # Default timezone
    DEFAULT_TIMEZONE = "US/Pacific"

    # Ollama configuration
    DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
    DEFAULT_OLLAMA_LLM_MODEL = "qwen3:1.7b"
    DEFAULT_OLLAMA_VISION_MODEL = "qwen2.5vl:3b"
    DEFAULT_OLLAMA_EMBEDDING_MODEL = "mxbai-embed-large"

    # Recording defaults
    DEFAULT_RECORDING_DURATION = 60  # seconds
    DEFAULT_RECORDING_INTERVAL = 2.0  # seconds
    DEFAULT_SCREENSHOT_INTERVAL = 2.0  # seconds

    # Performance tuning
    KM_BATCH_THRESHOLD = 20  # Keyboard/mouse batch threshold
    FLUSH_INTERVAL = 5.0  # Seconds
    TYPING_SESSION_THRESHOLD = 2.0  # Seconds

    # UI defaults
    CHAT_INPUT_HEIGHT = 3
    PREVIEW_UPDATE_INTERVAL = 1000  # milliseconds

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize configuration from file or defaults.

        Args:
            config_path: Optional path to configuration file (JSON or YAML).
                        If None, uses default values.
        """
        self._config_path = config_path
        self._config: Dict[str, Any] = {}

        if config_path:
            self._load_from_file(config_path)
        else:
            self._load_defaults()

        # Apply environment variable overrides
        self._apply_env_overrides()

    def _load_defaults(self) -> None:
        """Load default configuration values."""
        self._config = {
            # Database configuration
            "db": {
                "dir": str(self.DEFAULT_DB_DIR),
                "name": self.DEFAULT_DB_NAME,
                "chroma_name": self.DEFAULT_CHROMA_DB_NAME,
                "videos_dir": self.DEFAULT_VIDEOS_DIR,
                "logs_dir": self.DEFAULT_LOGS_DIR,
            },
            # Ollama configuration
            "ollama": {
                "base_url": self.DEFAULT_OLLAMA_BASE_URL,
                "llm_model": self.DEFAULT_OLLAMA_LLM_MODEL,
                "vision_model": self.DEFAULT_OLLAMA_VISION_MODEL,
                "embedding_model": self.DEFAULT_OLLAMA_EMBEDDING_MODEL,
            },
            # Recording configuration
            "recording": {
                "duration": self.DEFAULT_RECORDING_DURATION,
                "interval": self.DEFAULT_RECORDING_INTERVAL,
                "screenshot_interval": self.DEFAULT_SCREENSHOT_INTERVAL,
            },
            # Performance configuration
            "performance": {
                "km_batch_threshold": self.KM_BATCH_THRESHOLD,
                "flush_interval": self.FLUSH_INTERVAL,
                "typing_session_threshold": self.TYPING_SESSION_THRESHOLD,
            },
            # UI configuration
            "ui": {
                "chat_input_height": self.CHAT_INPUT_HEIGHT,
                "preview_update_interval": self.PREVIEW_UPDATE_INTERVAL,
            },
            # Timezone configuration
            "timezone": {
                "default": self.DEFAULT_TIMEZONE,
            },
        }

    def _load_from_file(self, config_path: Union[str, Path]) -> None:
        """
        Load configuration from JSON or YAML file.

        Args:
            config_path: Path to configuration file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValueError: If config file format is invalid.
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, 'r') as f:
                if config_path.suffix in ['.yaml', '.yml']:
                    self._config = yaml.safe_load(f)
                elif config_path.suffix == '.json':
                    self._config = json.load(f)
                else:
                    raise ValueError(
                        f"Unsupported config file format: {config_path.suffix}. "
                        "Use .json, .yaml, or .yml"
                    )
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_path}: {e}")

        # Merge with defaults to ensure all keys exist
        defaults = self._get_defaults_dict()
        self._config = self._deep_merge(defaults, self._config)

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # Database directory
        if db_dir := os.getenv("MEMSCREEN_DB_DIR"):
            self._config["db"]["dir"] = db_dir

        # Ollama URL
        if ollama_url := os.getenv("MEMSCREEN_OLLAMA_URL"):
            self._config["ollama"]["base_url"] = ollama_url

        # Models
        if llm_model := os.getenv("MEMSCREEN_LLM_MODEL"):
            self._config["ollama"]["llm_model"] = llm_model

        if vision_model := os.getenv("MEMSCREEN_VISION_MODEL"):
            self._config["ollama"]["vision_model"] = vision_model

        if embedding_model := os.getenv("MEMSCREEN_EMBEDDING_MODEL"):
            self._config["ollama"]["embedding_model"] = embedding_model

    def _get_defaults_dict(self) -> Dict[str, Any]:
        """Get defaults as a dictionary."""
        temp_config = MemScreenConfig(config_path=None)
        return temp_config._config.copy()

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary with defaults.
            override: Dictionary with overrides.

        Returns:
            Merged dictionary.
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = MemScreenConfig._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    # Database properties
    @property
    def db_dir(self) -> Path:
        """Get database directory path."""
        return Path(self._config["db"]["dir"])

    @property
    def db_path(self) -> Path:
        """Get full database file path."""
        return self.db_dir / self._config["db"]["name"]

    @property
    def chroma_db_path(self) -> Path:
        """Get full ChromaDB file path."""
        return self.db_dir / self._config["db"]["chroma_name"]

    @property
    def videos_dir(self) -> Path:
        """Get videos directory path."""
        return self.db_dir / self._config["db"]["videos_dir"]

    @property
    def logs_dir(self) -> Path:
        """Get logs directory path."""
        return self.db_dir / self._config["db"]["logs_dir"]

    # Ollama properties
    @property
    def ollama_base_url(self) -> str:
        """Get Ollama base URL."""
        return self._config["ollama"]["base_url"]

    @property
    def ollama_llm_model(self) -> str:
        """Get default Ollama LLM model."""
        return self._config["ollama"]["llm_model"]

    @property
    def ollama_vision_model(self) -> str:
        """Get default Ollama vision model."""
        return self._config["ollama"]["vision_model"]

    @property
    def ollama_embedding_model(self) -> str:
        """Get default Ollama embedding model."""
        return self._config["ollama"]["embedding_model"]

    # Recording properties
    @property
    def recording_duration(self) -> int:
        """Get default recording duration in seconds."""
        return self._config["recording"]["duration"]

    @property
    def recording_interval(self) -> float:
        """Get default recording interval in seconds."""
        return self._config["recording"]["interval"]

    @property
    def screenshot_interval(self) -> float:
        """Get default screenshot interval in seconds."""
        return self._config["recording"]["screenshot_interval"]

    # Performance properties
    @property
    def km_batch_threshold(self) -> int:
        """Get keyboard/mouse batch threshold."""
        return self._config["performance"]["km_batch_threshold"]

    @property
    def flush_interval(self) -> float:
        """Get flush interval in seconds."""
        return self._config["performance"]["flush_interval"]

    @property
    def typing_session_threshold(self) -> float:
        """Get typing session threshold in seconds."""
        return self._config["performance"]["typing_session_threshold"]

    # UI properties
    @property
    def chat_input_height(self) -> int:
        """Get chat input height."""
        return self._config["ui"]["chat_input_height"]

    @property
    def preview_update_interval(self) -> int:
        """Get preview update interval in milliseconds."""
        return self._config["ui"]["preview_update_interval"]

    # Timezone properties
    @property
    def timezone(self) -> str:
        """Get default timezone."""
        return self._config["timezone"]["default"]

    def get_llm_config(self) -> Dict[str, Any]:
        """
        Get LLM configuration dictionary.

        Returns:
            Configuration dictionary for LLM initialization.
        """
        return {
            "provider": "ollama",
            "config": {
                "model": self.ollama_llm_model,
                "ollama_base_url": self.ollama_base_url,
            }
        }

    def get_mllm_config(self) -> Dict[str, Any]:
        """
        Get Multimodal LLM configuration dictionary.

        Returns:
            Configuration dictionary for MLLM initialization.
        """
        return {
            "provider": "ollama",
            "config": {
                "model": self.ollama_vision_model,
                "ollama_base_url": self.ollama_base_url,
                "enable_vision": True,
            }
        }

    def get_embedder_config(self) -> Dict[str, Any]:
        """
        Get embedder configuration dictionary.

        Returns:
            Configuration dictionary for embedder initialization.
        """
        return {
            "provider": "ollama",
            "config": {
                "model": self.ollama_embedding_model,
                "ollama_base_url": self.ollama_base_url,
            }
        }

    def get_vector_store_config(self) -> Dict[str, Any]:
        """
        Get vector store configuration dictionary.

        Returns:
            Configuration dictionary for vector store initialization.
        """
        return {
            "provider": "chroma",
            "config": {
                "collection_name": "memscreen_collection",
                "path": str(self.db_dir),
            }
        }

    def save_to_file(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save current configuration to file.

        Args:
            config_path: Optional path to save configuration.
                        If None, uses the path configuration was loaded from.
        """
        save_path = Path(config_path or self._config_path)

        if not save_path:
            raise ValueError("No configuration path specified")

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w') as f:
            if save_path.suffix in ['.yaml', '.yml']:
                yaml.safe_dump(self._config, f, default_flow_style=False)
            else:
                json.dump(self._config, f, indent=4)

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if configuration is valid.

        Raises:
            ValueError: If configuration is invalid.
        """
        # Validate paths exist or can be created
        try:
            self.db_dir.mkdir(parents=True, exist_ok=True)
            self.videos_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Cannot create database directories: {e}")

        # Validate numeric ranges
        if self.recording_duration <= 0:
            raise ValueError("recording_duration must be positive")

        if self.recording_interval <= 0:
            raise ValueError("recording_interval must be positive")

        if not (0.1 <= self.recording_interval <= 60.0):
            raise ValueError("recording_interval must be between 0.1 and 60 seconds")

        # Validate Ollama URL format
        if not self.ollama_base_url.startswith(('http://', 'https://')):
            raise ValueError("ollama_base_url must start with http:// or https://")

        return True


# Global configuration instance
_global_config: Optional[MemScreenConfig] = None


def get_config(config_path: Optional[Union[str, Path]] = None,
               reload: bool = False) -> MemScreenConfig:
    """
    Get global configuration instance.

    Args:
        config_path: Optional path to configuration file.
        reload: If True, reload configuration even if already loaded.

    Returns:
        MemScreenConfig instance.
    """
    global _global_config

    if _global_config is None or reload:
        _global_config = MemScreenConfig(config_path=config_path)
        _global_config.validate()

    return _global_config


def reset_config() -> None:
    """Reset global configuration instance."""
    global _global_config
    _global_config = None
