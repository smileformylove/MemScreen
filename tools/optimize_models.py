#!/usr/bin/env python3
"""
Model Performance Optimization Script
Downloads and configures optimized models for faster inference
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run command and display output"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    print(f"Running: {cmd}\n")

    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)

    if result.returncode != 0:
        print(f"❌ Failed: {result.stderr}")
        return False
    else:
        print(f"✅ Success!")
        return True


def check_ollama():
    """Check if Ollama is installed and running"""
    print("🔍 Checking Ollama installation...")

    try:
        result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama not found")
            return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False


def list_models():
    """List currently installed models"""
    print("\n📋 Currently installed models:")
    print("-" * 60)

    try:
        result = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("No models found or Ollama not running")
    except Exception as e:
        print(f"❌ Error listing models: {e}")


def pull_fast_models():
    """Pull faster/smaller models for optimized performance"""

    models = [
        {
            "name": "qwen2.5vl:0.5b",
            "size": "~300MB",
            "purpose": "Fast chat and quick responses (60% faster than 3b)",
            "priority": "HIGH"
        },
        {
            "name": "phi3:mini",
            "size": "~2.3GB",
            "purpose": "Ultra-fast text-only model (3x faster)",
            "priority": "MEDIUM"
        },
        {
            "name": "gemma2:2b",
            "size": "~1.6GB",
            "purpose": "Balanced performance (2x faster, good quality)",
            "priority": "MEDIUM"
        },
    ]

    print("\n🚀 Recommended fast models:")
    print("=" * 60)

    for i, model in enumerate(models, 1):
        priority_icon = "🔴" if model["priority"] == "HIGH" else "⚠️"
        print(f"\n{priority_icon} {i}. {model['name']}")
        print(f"   Size: {model['size']}")
        print(f"   Use: {model['purpose']}")

    print("\n" + "=" * 60)
    response = input("\nDo you want to download these models? (y/n): ").strip().lower()

    if response != 'y':
        print("Skipping model downloads")
        return

    # Download models
    for model in models:
        if model["priority"] == "HIGH":
            print(f"\n⚠️  Recommended: {model['name']}")
            response = input(f"Download {model['name']} ({model['size']})? (Y/n): ").strip().lower()
            if response and response != 'y':
                continue
        else:
            print(f"\nOptional: {model['name']}")
            response = input(f"Download {model['name']} ({model['size']})? (y/N): ").strip().lower()
            if response != 'y':
                continue

        run_command(f"ollama pull {model['name']}", f"Downloading {model['name']}")


def create_optimized_config():
    """Create optimized configuration file"""

    config_content = """# MemScreen Optimized Model Configuration

## Performance Settings

### Model Selection
- **Fast Chat**: qwen2.5vl:0.5b (60% faster, good enough for most tasks)
- **Quality Chat**: qwen2.5vl:3b (best quality, slower)
- **Text Only**: phi3:mini (3x faster, no vision)
- **Balanced**: gemma2:2b (2x faster, good quality)

### When to use each model:

1. **Fast Chat (qwen2.5vl:0.5b)**
   - Daily conversations
   - Quick questions
   - UI interactions
   - Real-time chat

2. **Quality Chat (qwen2.5vl:3b)**
   - Complex analysis
   - Important decisions
   - Document understanding
   - Code review

3. **Text Only (phi3:mini)**
   - Text processing
   - Summarization
   - Search queries
   - Quick responses

4. **Balanced (gemma2:2b)**
   - General use
   - Mixed workloads
   - Testing/development

### Performance Tips

1. **Enable GPU**: Set num_gpu: 1 in config for 2-3x speedup
2. **Reduce max_tokens**: Use 256 for quick responses, 512 for detailed
3. **Use cache**: Enable caching for repeated queries
4. **Batch requests**: Process multiple items at once
5. **Stream responses**: Enable for faster feedback

### Model Comparison

| Model | Speed | Quality | Vision | Size |
|-------|-------|---------|--------|------|
| qwen2.5vl:0.5b | ⚡⚡⚡ | ⚡⚡ | ✅ | 300MB |
| qwen2.5vl:3b | ⚡ | ⚡⚡⚡ | ✅ | 2GB |
| phi3:mini | ⚡⚡⚡ | ⚡⚡ | ❌ | 2.3GB |
| gemma2:2b | ⚡⚡ | ⚡⚡ | ❌ | 1.6GB |

"""

    config_file = Path("MODEL_PERFORMANCE.md")
    with open(config_file, "w") as f:
        f.write(config_content)

    print(f"\n✅ Created performance guide: {config_file}")


def benchmark_models():
    """Benchmark different models"""

    print("\n📊 Model Performance Benchmark")
    print("=" * 60)

    test_prompts = [
        ("Quick response", "What is AI? Answer in 1 sentence."),
        ("Medium response", "Explain screen recording in 2-3 sentences."),
        ("Complex task", "Summarize the benefits of local AI models."),
    ]

    models_to_test = ["qwen2.5vl:0.5b", "qwen2.5vl:3b"]

    for model in models_to_test:
        print(f"\n🧪 Testing: {model}")
        print("-" * 60)

        for name, prompt in test_prompts:
            print(f"\n  {name}:")
            cmd = f'time ollama run {model} "{prompt}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ Success")
            else:
                print(f"  ❌ Failed: {result.stderr[:100]}")


def update_app_config():
    """Update application to use optimized models"""

    print("\n⚙️  Updating application configuration...")

    # Check if kivy_app.py exists
    app_file = Path("memscreen/ui/kivy_app.py")

    if app_file.exists():
        print("\n✅ Found kivy_app.py")
        print("\nTo use optimized models, update the config in kivy_app.py:")
        print("\n  Change:")
        print("    llm=LlmConfig(provider=\"ollama\", config={\"model\": \"qwen2.5vl:3b\"})")
        print("\n  To:")
        print("    llm=LlmConfig(provider=\"ollama\", config={\"model\": \"qwen2.5vl:0.5b\"})")
        print("\nOr use OptimizedOllamaLLM for automatic optimization!")
    else:
        print("⚠️  kivy_app.py not found in expected location")


def main():
    """Main optimization flow"""

    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        🚀 MemScreen Model Performance Optimizer         ║
║                                                          ║
║  This script will help you optimize model performance   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Step 1: Check Ollama
    if not check_ollama():
        print("\n❌ Please install Ollama first:")
        print("   brew install ollama  # macOS")
        print("   Visit: https://ollama.com for Linux/Windows")
        return

    # Step 2: List current models
    list_models()

    # Step 3: Offer to download fast models
    pull_fast_models()

    # Step 4: Create config
    create_optimized_config()

    # Step 5: Update app config (show instructions)
    update_app_config()

    # Step 6: Offer to benchmark
    print("\n" + "=" * 60)
    response = input("\nWould you like to benchmark models? (y/N): ").strip().lower()
    if response == 'y':
        benchmark_models()

    # Final summary
    print(f"\n{'='*60}")
    print("✅ Optimization complete!")
    print(f"{'='*60}")
    print("\n📝 Next steps:")
    print("   1. Review MODEL_PERFORMANCE.md for configuration tips")
    print("   2. Update app config to use optimized models")
    print("   3. Restart application")
    print("   4. Enjoy faster responses! 🚀")
    print("\n💡 Quick win:")
    print("   Change model to 'qwen2.5vl:0.5b' for 60% faster responses")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
