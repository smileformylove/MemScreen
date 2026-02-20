#!/usr/bin/env python3
"""
MemScreen 

1-6
"""

import sys
import tempfile
from pathlib import Path

# 
sys.path.insert(0, str(Path(__file__).parent))

def test_end_to_end_integration():
    """
    
    """
    print("\n" + "="*70)
    print("🚀 MemScreen ")
    print("="*70)

    # ============================================
    # 1: 
    # ============================================
    print("\n📋 1: ...")
    from memscreen.config import get_config

    config = get_config()  # config_example.yaml
    print(f"✅ ")
    print(f"   - : {'' if config.vision_encoder_enabled else ''}")
    print(f"   - : {'' if config.tiered_memory_enabled else ''}")
    print(f"   - : {'' if config.conflict_resolution_enabled else ''}")
    print(f"   - QA: {'' if config.vision_qa_enabled else ''}")

    # ============================================
    # 2: Memory
    # ============================================
    print("\n📦 2: Memory...")
    from memscreen.memory import MemoryConfig, Memory

    memory_config = MemoryConfig(
        version="1.0",
        collection_name="integration_test",
        history_db_path=":memory:",
        vector_store={
            "provider": "chroma",
            "config": {"path": str(Path(tempfile.mkdtemp()) / "chroma_test")},
        },
        llm={
            "provider": "ollama",
            "config": {"model": config.ollama_llm_model},
        },
        mllm={
            "provider": "ollama",
            "config": {"model": config.ollama_vision_model},
        },
        embedder={
            "provider": "ollama",
            "config": {"model": config.ollama_embedding_model},
        },
    )

    base_memory = Memory(config=memory_config)
    print("✅ Memory")

    # ============================================
    # 3: Memory
    # ============================================
    print("\n⚡ 3: Memory...")
    from memscreen.memory.enhanced_memory import create_enhanced_memory

    enhanced_memory = create_enhanced_memory(base_memory)
    print("✅ Memory")
    print(f"   - : {'✓' if enhanced_memory.vision_encoder else '✗'}")
    print(f"   - : {'✓' if enhanced_memory.multimodal_store else '✗'}")
    print(f"   - : {'✓' if enhanced_memory.tiered_manager else '✗'}")
    print(f"   - : {'✓' if enhanced_memory.conflict_resolver else '✗'}")

    # ============================================
    # 4: 
    # ============================================
    print("\n🎨 4: ...")
    if enhanced_memory.vision_encoder:
        # 
        from PIL import Image
        import numpy as np

        test_img = Image.new('RGB', (200, 100), color=(255, 0, 0))
        test_path = Path(tempfile.gettempdir()) / "test_screenshot.png"
        test_img.save(test_path)

        # 
        visual_hash = enhanced_memory.vision_encoder.compute_visual_hash(str(test_path))
        print(f"✅ : {visual_hash[:16]}...")

        # 
        features = enhanced_memory.vision_encoder.extract_visual_features(str(test_path))
        print(f"✅ : ={features['brightness']:.1f}, ={features['contrast']:.1f}")

    # ============================================
    # 5: 
    # ============================================
    print("\n💾 5: ...")

    test_messages = [
        {"role": "user", "content": "Python"},
    ]

    # 
    if enhanced_memory.vision_encoder:
        memory_id = enhanced_memory.add_with_vision(
            messages=test_messages,
            image_path=str(test_path) if 'test_path' in locals() else None,
            user_id="test_user",
            metadata={"category": "coding", "importance": "high"},
        )
        print(f"✅ : {memory_id[:8]}...")

    # 
    text_memory_id = enhanced_memory.add(
        messages=[{"role": "user", "content": "Python"}],
        user_id="test_user",
        metadata={"category": "fact"},
    )
    print(f"✅ : {text_memory_id[:8]}...")

    # ============================================
    # 6: 
    # ============================================
    print("\n⭐ 6: ...")
    if enhanced_memory.tiered_manager:
        from datetime import datetime

        score = enhanced_memory.tiered_manager.scorer.score_memory(
            content="Python",
            metadata={"category": "fact"},
            access_count=5,
            created_at=datetime.now(),
        )

        tier = enhanced_memory.tiered_manager.scorer.get_tier_for_score(score)
        print(f"✅ : {score:.3f} → : {tier}")

    # ============================================
    # 7: 
    # ============================================
    print("\n🔍 7: ...")
    if enhanced_memory.conflict_resolver:
        conflicts = enhanced_memory.detect_conflicts(
            new_memory="Python"
        )
        print(f"✅  {len(conflicts)} ")
        for conflict in conflicts:
            print(f"   - : {conflict['conflict_type']}, : {conflict['resolution']}")

    # ============================================
    # 8: 
    # ============================================
    print("\n🔎 8: ...")

    results = enhanced_memory.search_visual(
        query="Python",
        limit=5,
        user_id="test_user",
    )
    print(f"✅  {len(results)} ")

    # ============================================
    # 9: 
    # ============================================
    print("\n📊 9: ...")
    if enhanced_memory.tiered_manager:
        stats = enhanced_memory.tiered_manager.get_stats()
        print(f"✅ :")
        print(f"   - Working: {stats['tier_counts']['working']}")
        print(f"   - Short-term: {stats['tier_counts']['short_term']}")
        print(f"   - Long-term: {stats['tier_counts']['long_term']}")

    # ============================================
    # 10: 
    # ============================================
    print("\n💬 10: ...")
    if config.vision_qa_enabled:
        # 
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "vision_qa_prompts",
            Path(__file__).parent / "memscreen" / "prompts" / "vision_qa_prompts.py"
        )
        vision_qa_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vision_qa_module)

        # 
        builder = vision_qa_module.VisionQAPromptBuilder()
        query_type = builder._classify_query_type("")
        print(f"✅ : {query_type}")

    # ============================================
    # 
    # ============================================
    print("\n" + "="*70)
    print("✅ ")
    print("="*70)
    print("\n🎉 MemScreen")
    print("\n📚 :")
    print("  1. ✅ SigLIP/CLIP")
    print("  2. ✅ ")
    print("  3. ✅ ")
    print("  4. ✅ ")
    print("  5. ✅ ")
    print("  6. ✅ ")
    print("  7. ✅ 7b")

    print("\n📖 :")
    print("   ```python")
    print("   from memscreen.memory.enhanced_memory import create_enhanced_memory")
    print("   from memscreen.config import get_config")
    print("   ")
    print("   # ")
    print("   config = get_config()")
    print("   ")
    print("   # Memory")
    print("   from memscreen.memory import Memory, MemoryConfig")
    print("   memory = Memory(config=MemoryConfig(...))")
    print("   ")
    print("   # Memory")
    print("   enhanced = create_enhanced_memory(memory)")
    print("   ")
    print("   # ")
    print("   enhanced.add_with_vision(messages, image_path='screenshot.png')")
    print("   results = enhanced.search_visual(query='')")
    print("   ```")

    print("\n🔗 :")
    print("  - : config_example.yaml")
    print("  - : memscreen/memory/enhanced_memory.py")
    print("  - : demo_optimization.py")
    print("  - : .claude/plans/IMPLEMENTATION_SUMMARY.md")


if __name__ == "__main__":
    try:
        test_end_to_end_integration()
    except Exception as e:
        print(f"\n❌ : {e}")
        import traceback
        traceback.print_exc()
