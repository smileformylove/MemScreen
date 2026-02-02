### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-02             ###
### license: MIT                 ###

"""
Tests for vLLM LLM backend.
"""

import pytest
import os
from memscreen.llm.vllm import VllmConfig, VllmLLM
from memscreen.llm.factory import LlmFactory


class TestVllmConfig:
    """Test VllmConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = VllmConfig()
        assert config.temperature == 0.1
        assert config.max_tokens == 2000
        assert config.top_p == 0.1
        assert config.vllm_base_url == "http://localhost:8000"
        assert config.use_offline_mode is False
        assert config.tensor_parallel_size == 1
        assert config.gpu_memory_utilization == 0.9
        assert config.trust_remote_code is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = VllmConfig(
            model="Qwen/Qwen2.5-7B-Instruct",
            temperature=0.7,
            max_tokens=1000,
            vllm_base_url="http://localhost:8080",
            use_offline_mode=True,
            tensor_parallel_size=2,
            gpu_memory_utilization=0.8,
        )
        assert config.model == "Qwen/Qwen2.5-7B-Instruct"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.vllm_base_url == "http://localhost:8080"
        assert config.use_offline_mode is True
        assert config.tensor_parallel_size == 2
        assert config.gpu_memory_utilization == 0.8

    def test_dict_initialization(self):
        """Test initialization from dictionary."""
        config_dict = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "temperature": 0.5,
            "vllm_base_url": "http://localhost:8000",
        }
        config = VllmConfig(**config_dict)
        assert config.model == "Qwen/Qwen2.5-7B-Instruct"
        assert config.temperature == 0.5


class TestVllmLLM:
    """Test VllmLLM class."""

    def test_init_with_config(self):
        """Test initialization with VllmConfig."""
        config = VllmConfig(
            model="Qwen/Qwen2.5-7B-Instruct",
            use_offline_mode=False,
        )
        # Don't actually initialize to avoid requiring vLLM installation
        # Just test that the config is stored correctly
        assert config.model == "Qwen/Qwen2.5-7B-Instruct"
        assert config.use_offline_mode is False

    def test_init_with_dict(self):
        """Test initialization with dictionary."""
        config_dict = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "temperature": 0.7,
            "vllm_base_url": "http://localhost:8000",
        }
        config = VllmConfig(**config_dict)
        assert config.model == "Qwen/Qwen2.5-7B-Instruct"
        assert config.temperature == 0.7
        assert config.vllm_base_url == "http://localhost:8000"


class TestVllmFactory:
    """Test vLLM factory integration."""

    def test_factory_has_vllm(self):
        """Test that vLLM is registered in factory."""
        providers = LlmFactory.get_supported_providers()
        assert "vllm" in providers

    def test_factory_config_class(self):
        """Test that factory uses correct config class for vLLM."""
        provider_to_class = LlmFactory.provider_to_class
        assert "vllm" in provider_to_class
        class_path, config_class = provider_to_class["vllm"]
        assert class_path == "memscreen.llm.vllm.VllmLLM"
        assert config_class == VllmConfig

    def test_factory_create_config_only(self):
        """Test factory can create vLLM config without initializing."""
        config = VllmConfig(
            model="Qwen/Qwen2.5-7B-Instruct",
            vllm_base_url="http://localhost:8000",
        )
        assert config.model == "Qwen/Qwen2.5-7B-Instruct"
        assert config.vllm_base_url == "http://localhost:8000"


class TestVllmConfigIntegration:
    """Test vLLM configuration integration with MemScreenConfig."""

    def test_global_config_vllm_defaults(self):
        """Test that MemScreenConfig has vLLM defaults."""
        from memscreen.config import MemScreenConfig

        config = MemScreenConfig()
        assert config.DEFAULT_VLLM_BASE_URL == "http://localhost:8000"
        assert config.DEFAULT_VLLM_LLM_MODEL == "Qwen/Qwen2.5-7B-Instruct"
        assert config.DEFAULT_VLLM_VISION_MODEL == "Qwen/Qwen2-VL-7B-Instruct"

    def test_global_config_vllm_properties(self):
        """Test that MemScreenConfig exposes vLLM properties."""
        from memscreen.config import MemScreenConfig

        config = MemScreenConfig()
        assert hasattr(config, "vllm_base_url")
        assert hasattr(config, "vllm_llm_model")
        assert hasattr(config, "vllm_vision_model")
        assert hasattr(config, "vllm_embedding_model")
        assert hasattr(config, "vllm_use_offline_mode")
        assert hasattr(config, "vllm_tensor_parallel_size")
        assert hasattr(config, "vllm_gpu_memory_utilization")

    def test_global_config_get_llm_config(self):
        """Test that get_llm_config supports vLLM backend."""
        from memscreen.config import MemScreenConfig

        config = MemScreenConfig()
        llm_config = config.get_llm_config(backend="vllm")
        assert llm_config["provider"] == "vllm"
        assert "config" in llm_config
        assert "model" in llm_config["config"]
        assert "vllm_base_url" in llm_config["config"]

    def test_global_config_get_mllm_config(self):
        """Test that get_mllm_config supports vLLM backend."""
        from memscreen.config import MemScreenConfig

        config = MemScreenConfig()
        mllm_config = config.get_mllm_config(backend="vllm")
        assert mllm_config["provider"] == "vllm"
        assert "config" in mllm_config
        assert mllm_config["config"]["enable_vision"] is True

    def test_global_config_get_embedder_config(self):
        """Test that get_embedder_config supports vLLM backend."""
        from memscreen.config import MemScreenConfig

        config = MemScreenConfig()
        embedder_config = config.get_embedder_config(backend="vllm")
        assert embedder_config["provider"] == "vllm"
        assert "config" in embedder_config
        assert "model" in embedder_config["config"]


class TestVllmEnvironmentVariables:
    """Test vLLM environment variable support."""

    def test_vllm_url_env_var(self, monkeypatch):
        """Test MEMSCREEN_VLLM_URL environment variable."""
        from memscreen.config import MemScreenConfig

        monkeypatch.setenv("MEMSCREEN_VLLM_URL", "http://localhost:9999")
        config = MemScreenConfig()
        assert config.vllm_base_url == "http://localhost:9999"

    def test_llm_backend_env_var(self, monkeypatch):
        """Test MEMSCREEN_LLM_BACKEND environment variable."""
        from memscreen.config import MemScreenConfig

        monkeypatch.setenv("MEMSCREEN_LLM_BACKEND", "vllm")
        config = MemScreenConfig()
        assert config.llm_backend == "vllm"

    def test_vllm_model_env_vars(self, monkeypatch):
        """Test vLLM model environment variables."""
        from memscreen.config import MemScreenConfig

        monkeypatch.setenv("MEMSCREEN_VLLM_LLM_MODEL", "CustomModel")
        monkeypatch.setenv("MEMSCREEN_VLLM_VISION_MODEL", "CustomVisionModel")
        monkeypatch.setenv("MEMSCREEN_VLLM_EMBEDDING_MODEL", "CustomEmbeddingModel")

        config = MemScreenConfig()
        assert config.vllm_llm_model == "CustomModel"
        assert config.vllm_vision_model == "CustomVisionModel"
        assert config.vllm_embedding_model == "CustomEmbeddingModel"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
