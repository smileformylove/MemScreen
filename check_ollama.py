#!/usr/bin/env python3
"""
Check Ollama connection and available models
"""

import requests
import sys

print("=" * 70)
print("🔍 Ollama Connection Check")
print("=" * 70)
print()

# Test connection
print("1. Testing Ollama connection...")
print("-" * 70)
try:
    response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
    response.raise_for_status()
    print("✅ Ollama is running!")
    print()
except Exception as e:
    print(f"❌ Cannot connect to Ollama: {e}")
    print()
    print("Please start Ollama:")
    print("  - macOS: Open terminal and run: ollama serve")
    print("  - Or start Ollama app")
    sys.exit(1)

# List models
print("2. Available models:")
print("-" * 70)
try:
    models_data = response.json()
    models = models_data.get('models', [])

    if not models:
        print("⚠️  No models found!")
        print()
        print("To install a model, run:")
        print("  ollama pull qwen2.5:1.7b")
        print("  ollama pull qwen2.5:3b")
        print("  ollama pull llama3.2:3b")
    else:
        for i, model in enumerate(models, 1):
            name = model['name']
            size = model.get('size', 0) / (1024**3)  # Convert to GB
            print(f"{i}. {name} ({size:.2f} GB)")

        print()
        print("✅ Found", len(models), "model(s)")

        # Check for qwen2.5
        qwen_models = [m for m in models if 'qwen' in m['name'].lower()]
        if qwen_models:
            print()
            print("💡 Recommended Qwen models:")
            for m in qwen_models:
                print(f"   - {m['name']}")
        else:
            print()
            print("💡 To install Qwen model (recommended):")
            print("   ollama pull qwen2.5:1.7b")

except Exception as e:
    print(f"❌ Error listing models: {e}")

print()
print("=" * 70)
print("✅ Check complete!")
print("=" * 70)
