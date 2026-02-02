### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-02             ###
### license: MIT                 ###

"""
vLLM LLM implementation for MemScreen.

This module provides vLLM backend support with two modes:
1. Server mode: Connect to a running vLLM server (OpenAI-compatible API)
2. Offline mode: Use vLLM's offline batched inference (high throughput)
"""

import logging
from typing import Dict, List, Optional, Union

from .base import BaseLlmConfig, LLMBase

logger = logging.getLogger(__name__)


class VllmConfig(BaseLlmConfig):
    """
    Configuration for vLLM backend.

    Extends BaseLlmConfig with vLLM-specific parameters.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.1,
        api_key: Optional[str] = None,  # For vLLM server API key
        max_tokens: int = 2000,
        top_p: float = 0.1,
        top_k: int = 1,
        enable_vision: bool = False,
        vision_details: Optional[str] = "auto",
        http_client_proxies: Optional[Union[Dict, str]] = None,
        # vLLM-specific parameters
        vllm_base_url: Optional[str] = "http://localhost:8000",
        vllm_api_key: Optional[str] = None,
        use_offline_mode: bool = False,  # Use vllm.LLM() directly instead of server
        tensor_parallel_size: int = 1,  # For multi-GPU
        gpu_memory_utilization: float = 0.9,
        trust_remote_code: bool = True,
        max_model_len: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize vLLM configuration.

        Args:
            model: The model identifier to use (e.g., "Qwen/Qwen2.5-7B-Instruct")
            temperature: Controls randomness of output (0.0 to 2.0). Defaults to 0.1
            api_key: API key for vLLM server (if using server mode)
            max_tokens: Maximum tokens to generate. Defaults to 2000
            top_p: Nucleus sampling parameter. Defaults to 0.1
            top_k: Top-k sampling parameter. Defaults to 1
            enable_vision: Whether to enable vision capabilities. Defaults to False
            vision_details: Level of detail for vision processing. Defaults to "auto"
            http_client_proxies: Proxy settings for HTTP client
            vllm_base_url: URL for vLLM OpenAI-compatible server. Defaults to "http://localhost:8000"
            vllm_api_key: API key for vLLM server authentication
            use_offline_mode: Use vLLM offline batched inference instead of server. Defaults to False
            tensor_parallel_size: Number of GPUs for tensor parallelism. Defaults to 1
            gpu_memory_utilization: GPU memory utilization ratio (0-1). Defaults to 0.9
            trust_remote_code: Whether to trust remote code when loading models. Defaults to True
            max_model_len: Maximum model length. Defaults to None (model default)
            **kwargs: Additional parameters
        """
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

        # vLLM-specific parameters
        self.vllm_base_url = vllm_base_url
        self.vllm_api_key = vllm_api_key
        self.use_offline_mode = use_offline_mode
        self.tensor_parallel_size = tensor_parallel_size
        self.gpu_memory_utilization = gpu_memory_utilization
        self.trust_remote_code = trust_remote_code
        self.max_model_len = max_model_len


class VllmLLM(LLMBase):
    """
    vLLM implementation of LLM backend.

    Supports two modes:
    1. Server mode: Connect to a running vLLM server via OpenAI-compatible API
    2. Offline mode: Use vLLM's offline batched inference for high throughput
    """

    def __init__(self, config: Optional[Union[VllmConfig, Dict]] = None):
        """
        Initialize vLLM backend.

        Args:
            config: VllmConfig instance or configuration dictionary
        """
        # Convert dict to VllmConfig if needed
        if isinstance(config, dict):
            config = VllmConfig(**config)

        super().__init__(config)

        # Set default model if not specified
        if self.config.model is None:
            self.config.model = "Qwen/Qwen2.5-7B-Instruct"
            logger.info(f"No model specified, using default: {self.config.model}")

        # Initialize based on mode
        if self.config.use_offline_mode:
            self._init_offline_mode()
        else:
            self._init_server_mode()

    def _init_offline_mode(self):
        """
        Initialize vLLM in offline mode for batched inference.

        This mode uses vllm.LLM() directly for maximum throughput.
        Best for batch processing and production workloads.
        """
        try:
            from vllm import LLM, SamplingParams

            logger.info(f"Initializing vLLM in offline mode with model: {self.config.model}")

            # Initialize vLLM engine
            self.llm = LLM(
                model=self.config.model,
                tensor_parallel_size=self.config.tensor_parallel_size,
                gpu_memory_utilization=self.config.gpu_memory_utilization,
                trust_remote_code=self.config.trust_remote_code,
                max_model_len=self.config.max_model_len,
            )

            self.SamplingParams = SamplingParams
            self.mode = "offline"
            logger.info("vLLM offline mode initialized successfully")

        except ImportError:
            raise ImportError(
                "vLLM package is not installed. "
                "Install it with: pip install vllm"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize vLLM offline mode: {e}")

    def _init_server_mode(self):
        """
        Initialize vLLM in server mode.

        This mode connects to a running vLLM server via OpenAI-compatible API.
        Best for interactive sessions and development.
        """
        try:
            from openai import OpenAI

            logger.info(
                f"Initializing vLLM in server mode: {self.config.vllm_base_url}"
            )

            # Initialize OpenAI client for vLLM server
            self.client = OpenAI(
                base_url=self.config.vllm_base_url,
                api_key=self.config.vllm_api_key or "EMPTY",
            )
            self.mode = "server"
            logger.info("vLLM server mode initialized successfully")

        except ImportError:
            raise ImportError(
                "OpenAI package is not installed. "
                "Install it with: pip install openai"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize vLLM server mode: {e}")

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
        **kwargs
    ):
        """
        Generate a response based on the given messages.

        Args:
            messages: List of message dicts containing 'role' and 'content'
            tools: List of tools that the model can call (not supported in vLLM)
            tool_choice: Tool choice method (not supported in vLLM)
            **kwargs: Additional parameters

        Returns:
            str: The generated response text
        """
        if self.mode == "offline":
            return self._generate_offline(messages, **kwargs)
        else:
            return self._generate_server(messages, **kwargs)

    def _generate_offline(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate response using offline vLLM mode.

        Args:
            messages: List of message dicts
            **kwargs: Additional parameters

        Returns:
            str: Generated response
        """
        try:
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)

            # Create sampling parameters
            sampling_params = self.SamplingParams(
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                max_tokens=self.config.max_tokens,
                **kwargs
            )

            # Generate
            outputs = self.llm.generate([prompt], sampling_params)

            # Extract response
            if outputs and len(outputs) > 0:
                generated_text = outputs[0].outputs[0].text
                return generated_text.strip()
            else:
                return ""

        except Exception as e:
            logger.error(f"Error in vLLM offline generation: {e}")
            raise

    def _generate_server(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate response using vLLM server API.

        Args:
            messages: List of message dicts
            **kwargs: Additional parameters

        Returns:
            str: Generated response
        """
        try:
            # Call vLLM server via OpenAI-compatible API
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                **kwargs
            )

            # Extract response text
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                return ""

        except Exception as e:
            logger.error(f"Error in vLLM server generation: {e}")
            raise

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert message list to prompt string for offline mode.

        Args:
            messages: List of message dicts

        Returns:
            str: Formatted prompt string
        """
        # Simple conversation format
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            prompt_parts.append(f"{role}: {content}")

        return "\n".join(prompt_parts) + "\nassistant:"

    def _parse_response(self, response) -> str:
        """
        Parse response from vLLM.

        Args:
            response: Raw response from vLLM

        Returns:
            str: Parsed response text
        """
        if isinstance(response, str):
            return response
        elif isinstance(response, dict):
            return response.get("content", "")
        else:
            # Object response (server mode)
            return str(response)


__all__ = ["VllmConfig", "VllmLLM"]
