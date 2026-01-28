#!/usr/bin/env python3
"""
Quick performance test for model optimization
"""

import time
import sys
sys.path.insert(0, '.')

def test_model_performance():
    """Test model response time"""
    from memscreen.llm import OllamaLLM, OllamaConfig

    print("🧪 Testing Model Performance")
    print("=" * 60)

    # Test configurations
    configs = [
        {
            "name": "Original (Slow)",
            "model": "qwen2.5vl:3b",
            "max_tokens": 2000,
            "temperature": 0.1,
        },
        {
            "name": "Optimized (Fast) ⭐",
            "model": "qwen3:1.7b",
            "max_tokens": 512,
            "temperature": 0.7,
        },
        {
            "name": "Ultra Fast",
            "model": "qwen3:1.7b",
            "max_tokens": 256,
            "temperature": 0.5,
        },
    ]

    test_prompt = "What is screen recording? Answer in 1-2 sentences."

    print(f"\nTest Prompt: '{test_prompt}'")
    print("\nRunning tests...\n")

    results = []

    for config in configs:
        print(f"Testing: {config['name']}")
        print("-" * 60)

        try:
            # Initialize LLM
            llm_config = OllamaConfig(
                model=config['model'],
                max_tokens=config['max_tokens'],
                temperature=config['temperature']
            )

            llm = OllamaLLM(config=llm_config)

            # Measure time
            start = time.time()
            response = llm.generate_response([
                {"role": "user", "content": test_prompt}
            ])
            duration = time.time() - start

            # Store result
            results.append({
                **config,
                'duration': duration,
                'response_length': len(response),
                'response_preview': response[:100] + '...'
            })

            # Print result
            print(f"✅ Response time: {duration:.2f}s")
            print(f"   Response length: {len(response)} chars")
            print(f"   Preview: {response[:100]}...")

        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({**config, 'error': str(e)})

        print()

    # Summary
    print("=" * 60)
    print("📊 Performance Summary")
    print("=" * 60)

    for i, result in enumerate(results, 1):
        if 'error' not in result:
            speedup = results[0]['duration'] / result['duration'] if result['duration'] > 0 else 0
            print(f"\n{i}. {result['name']}")
            print(f"   Time: {result['duration']:.2f}s")
            print(f"   Speedup: {speedup:.1f}x {'🚀' if speedup > 2 else ''}")
        else:
            print(f"\n{i}. {result['name']}")
            print(f"   ❌ Error: {result['error']}")

    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

    # Recommendation
    if len(results) > 1 and 'error' not in results[1]:
        original = results[0]
        optimized = results[1]

        if 'duration' in original and 'duration' in optimized:
            speedup = original['duration'] / optimized['duration']
            time_saved = original['duration'] - optimized['duration']

            print(f"\n🎯 Recommendation:")
            print(f"   Use '{optimized['name']}' configuration")
            print(f"   Expected speedup: {speedup:.1f}x")
            print(f"   Time saved per query: {time_saved:.2f}s")

            if speedup >= 2:
                print(f"\n   🎉 Great! You'll save ~{int(time_saved)}s per query!")
            elif speedup >= 1.5:
                print(f"\n   👍 Good improvement!")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     🧪 MemScreen Model Performance Test                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    input("Press Enter to start test...")
    test_model_performance()

    print("\n✨ Done!")
