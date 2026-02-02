#!/usr/bin/env python3
"""
Step-3.5-Flash Configuration Demo

This script demonstrates how to configure MemScreen to use Step-3.5-Flash,
even if the model is not currently running.
"""

import os
from memscreen.config import MemScreenConfig
from memscreen.llm.vllm import VllmConfig, VllmLLM
from memscreen.llm.factory import LlmFactory


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_configuration():
    """Demonstrate Step-3.5-Flash configuration."""
    print_section("Step-3.5-Flash Configuration Demo")

    # 1. Show default configuration
    config = MemScreenConfig()

    print("✅ MemScreen Default Configuration:")
    print(f"   Default vLLM backend: {config.llm_backend}")
    print(f"   Default reasoning model: {config.vllm_reasoning_model}")
    print(f"   vLLM base URL: {config.vllm_base_url}")
    print(f"   Tensor parallel size: {config.vllm_tensor_parallel_size}")
    print(f"   GPU memory utilization: {config.vllm_gpu_memory_utilization}")

    # 2. Show VllmConfig for Step-3.5-Flash
    print("\n✅ VllmConfig for Step-3.5-Flash:")
    vllm_config = VllmConfig(
        model="stepfun-ai/Step-3.5-Flash",
        vllm_base_url="http://localhost:8001",
        temperature=0.1,
        max_tokens=2048,
        tensor_parallel_size=4,
        gpu_memory_utilization=0.9,
    )

    print(f"   Model: {vllm_config.model}")
    print(f"   Base URL: {vllm_config.vllm_base_url}")
    print(f"   Temperature: {vllm_config.temperature}")
    print(f"   Max tokens: {vllm_config.max_tokens}")
    print(f"   Tensor parallel size: {vllm_config.tensor_parallel_size}")
    print(f"   GPU memory utilization: {vllm_config.gpu_memory_utilization}")

    # 3. Show factory registration
    print("\n✅ Factory Registration:")
    providers = LlmFactory.get_supported_providers()
    print(f"   Supported providers: {providers}")
    print(f"   vLLM registered: {'vllm' in providers}")

    # 4. Show environment variable configuration
    print("\n✅ Environment Variable Configuration:")
    print("   To configure Step-3.5-Flash, set these environment variables:")
    print()
    print("   export MEMSCREEN_LLM_BACKEND=vllm")
    print("   export MEMSCREEN_VLLM_URL=http://localhost:8001")
    print("   export MEMSCREEN_VLLM_LLM_MODEL=stepfun-ai/Step-3.5-Flash")
    print()
    print("   Or create a config file (config.yaml):")
    print("""
   llm:
     backend: vllm
   vllm:
     base_url: http://localhost:8001
     llm_model: stepfun-ai/Step-3.5-Flash
     tensor_parallel_size: 4
     gpu_memory_utilization: 0.9
    """)

    # 5. Show usage in code
    print("\n✅ Programmatic Usage:")
    print("""
from memscreen.llm.factory import LlmFactory
from memscreen.config import MemScreenConfig

# Get configuration
config = MemScreenConfig()

# Method 1: Use factory directly
llm = LlmFactory.create(
    "vllm",
    config={
        "model": config.vllm_reasoning_model,
        "vllm_base_url": "http://localhost:8001"
    }
)

# Method 2: Use config getter
llm_config = config.get_llm_config(backend="vllm")
llm = LlmFactory.create("vllm", config=llm_config["config"])

# Generate response
response = llm.generate_response([
    {"role": "user", "content": "What is 2+2?"}
])
    """)


def demo_model_comparison():
    """Compare different vLLM models."""
    print_section("vLLM Model Comparison")

    models = {
        "Qwen/Qwen2.5-7B-Instruct": {
            "params": "7B",
            "use_case": "General purpose, balanced",
            "vram": "~16GB",
        },
        "Qwen/Qwen2-VL-7B-Instruct": {
            "params": "7B",
            "use_case": "Vision-language tasks",
            "vram": "~16GB",
        },
        "stepfun-ai/Step-3.5-Flash": {
            "params": "196B (11B active)",
            "use_case": "Advanced reasoning, tool calling",
            "vram": "~400GB (4x GPUs)",
        },
    }

    print("\nModel comparison:")
    print(f"{'Model':<40} {'Params':<20} {'VRAM':<15} {'Use Case'}")
    print("-" * 120)

    for model, info in models.items():
        print(f"{model:<40} {info['params']:<20} {info['vram']:<15} {info['use_case']}")


def show_hardware_requirements():
    """Show hardware requirements for Step-3.5-Flash."""
    print_section("Hardware Requirements")

    print("\n🖥️  Minimum Requirements (Step-3.5-Flash):")
    print("   GPUs: 4x NVIDIA H200/H20/B200 (80GB each)")
    print("   Total VRAM: ~400GB")
    print("   System RAM: ~512GB")
    print("   Storage: ~500GB SSD (for model weights)")

    print("\n🖥️  Alternative (Step-3.5-Flash-FP8):")
    print("   GPUs: 2x NVIDIA H200/H20/B200 (80GB each)")
    print("   Total VRAM: ~200GB")
    print("   System RAM: ~256GB")
    print("   Storage: ~300GB SSD")

    print("\n☁️  Cloud Options:")
    print("   AWS: p5.48xlarge (8x A100 80GB)")
    print("   GCP: a3-highgpu-8g (8x H100 80GB)")
    print("   Azure: ND96amsr_A100_v4 (8x A100 80GB)")

    print("\n💡 No GPU? Try these alternatives:")
    print("   1. Use Qwen/Qwen2.5-7B-Instruct (smaller model)")
    print("   2. Use Ollama backend with local models")
    print("   3. Use cloud-based API (OpenAI, Anthropic, etc.)")


def show_quick_start():
    """Show quick start guide."""
    print_section("Quick Start Guide")

    print("\n📋 Prerequisites:")
    print("   1. 4+ NVIDIA GPUs (H200/H20/B200 recommended)")
    print("   2. Docker & Docker Compose installed")
    print("   3. Git clone of MemScreen repository")

    print("\n🚀 Step 1: Start vLLM Server")
    print("""
   # Configure for your GPU setup
   export TENSOR_PARALLEL_SIZE=4  # Number of GPUs
   export GPU_MEMORY_UTILIZATION=0.9

   # Start Step-3.5-Flash service
   docker-compose -f docker-compose.step35flash.yml up -d

   # Wait for model to load (5-10 minutes)
   docker-compose -f docker-compose.step35flash.yml logs -f
    """)

    print("\n🧪 Step 2: Test the Model")
    print("""
   # Run test suite
   python test_step35flash.py
    """)

    print("\n⚙️  Step 3: Configure MemScreen")
    print("""
   # Set environment variables
   export MEMSCREEN_LLM_BACKEND=vllm
   export MEMSCREEN_VLLM_URL=http://localhost:8001
   export MEMSCREEN_VLLM_LLM_MODEL=stepfun-ai/Step-3.5-Flash

   # Start MemScreen
   python start.py
    """)

    print("\n✨ Step 4: Use in AI Chat")
    print("""
   In the AI Chat interface, Step-3.5-Flash will be used for:
   - Complex reasoning tasks
   - Tool calling scenarios
   - Long context understanding
    """)


def main():
    """Run demo."""
    print("\n" + "=" * 60)
    print("  🧠 Step-3.5-Flash Integration Demo")
    print("  Advanced Reasoning Model for MemScreen")
    print("=" * 60)

    demo_configuration()
    demo_model_comparison()
    show_hardware_requirements()
    show_quick_start()

    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    print("\n✅ Configuration added to MemScreen")
    print("✅ Ready to use when Step-3.5-Flash server is available")
    print("✅ Full integration with vLLM backend")
    print("✅ Docker configuration provided")
    print("✅ Test suite created")

    print("\n" + "=" * 60)
    print("  Next Steps")
    print("=" * 60)
    print("\n1. Ensure you have adequate GPU resources")
    print("2. Start Step-3.5-Flash vLLM server:")
    print("      docker-compose -f docker-compose.step35flash.yml up -d")
    print("3. Run tests:")
    print("      python test_step35flash.py")
    print("4. Configure MemScreen:")
    print("      export MEMSCREEN_LLM_BACKEND=vllm")
    print("      export MEMSCREEN_VLLM_LLM_MODEL=stepfun-ai/Step-3.5-Flash")
    print("      python start.py")

    print("\n" + "=" * 60)
    print("  📚 Documentation")
    print("  See docs/STEP35FLASH.md for detailed guide")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
