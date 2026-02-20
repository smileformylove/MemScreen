#!/usr/bin/env python3
"""
MemScreen 


"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    """"""
    print("\n" + "="*70)
    print("📘 MemScreen ")
    print("="*70)
    print("\n6\n")

    # ============================================
    # 1: 
    # ============================================
    print("\n" + "🎨 1: ")
    print("-" * 70)
    print("\n📦 :")
    print("   pip install sentence-transformers  # SigLIP/CLIP")
    print("   pip install imagehash  # ")

    print("\n💻 :")
    print("```python")
    print("from memscreen.embeddings.vision_encoder import VisionEncoder, VisionEncoderConfig")
    print("")
    print("# ")
    print("config = VisionEncoderConfig(model_type='siglip')")
    print("encoder = VisionEncoder(config)")
    print("")
    print("# ")
    print("embedding = encoder.encode_image('screenshot.png')")
    print("")
    print("# ")
    print("visual_hash = encoder.compute_visual_hash('screenshot.png')")
    print("")
    print("# ")
    print("features = encoder.extract_visual_features('screenshot.png')")
    print("```")

    # ============================================
    # 2: 
    # ============================================
    print("\n" + "🔍 2: +")
    print("-" * 70)

    print("\n💻 :")
    print("```python")
    print("from memscreen.vector_store.multimodal_chroma import MultimodalChromaDB")
    print("from memscreen.memory.hybrid_retriever import HybridVisionRetriever")
    print("")
    print("# ")
    print("store = MultimodalChromaDB(")
    print("    collection_name='memories',")
    print("    text_embedding_dims=512,")
    print("    vision_embedding_dims=512")
    print(")")
    print("")
    print("# ")
    print("retriever = HybridVisionRetriever(")
    print("    text_embedder=embedder,")
    print("    vision_encoder=vision_encoder,")
    print("    vector_store=store")
    print(")")
    print("")
    print("# ")
    print("results = retriever.retrieve(")
    print("    query='',")
    print("    image_path='query.png',  # ")
    print("    limit=10")
    print(")")
    print("```")

    # ============================================
    # 3: 
    # ============================================
    print("\n" + "📊 3: ")
    print("-" * 70)

    print("\n💻 :")
    print("```python")
    print("from memscreen.memory.tiered_memory_manager import TieredMemoryManager")
    print("from memscreen.memory.importance_scorer import ImportanceScorer")
    print("")
    print("# ")
    print("scorer = ImportanceScorer()")
    print("")
    print("# ")
    print("score = scorer.score_memory(")
    print("    content='API',")
    print("    metadata={'category': 'fact'},")
    print("    access_count=10")
    print(")")
    print("")
    print("# ")
    print("tier = scorer.get_tier_for_score(score)")
    print("# tier = 'working' | 'short_term' | 'long_term'")
    print("```")

    # ============================================
    # 4: 
    # ============================================
    print("\n" + "🔍 4: ")
    print("-" * 70)

    print("\n💻 :")
    print("```python")
    print("from memscreen.memory.conflict_resolver import ConflictResolver")
    print("")
    print("resolver = ConflictResolver(")
    print("    embedding_model=embedder,")
    print("    llm=llm")
    print(")")
    print("")
    print("# ")
    print("conflicts = resolver.detect_conflict(")
    print("    new_memory='Python',")
    print("    existing_memories=[...]")
    print(")")
    print("")
    print("# ")
    print("for conflict in conflicts:")
    print("    resolution = resolver.resolve_conflict(conflict, new_memory)")
    print("    if resolution['action'] == 'merge':")
    print("        # ")
    print("        merged = resolution['merged_content']")
    print("```")

    # ============================================
    # 5: 
    # ============================================
    print("\n" + "💬 5: ")
    print("-" * 70)

    print("\n💡 :")
    print("   - find/content/action")
    print("   - ")
    print("   - 7b3000-4000 tokens")
    print("   - CoT")

    print("\n💻 :")
    print("```python")
    print("# Prompt")
    print("from memscreen.prompts.vision_qa_prompts import VisionQAPromptBuilder")
    print("")
    print("builder = VisionQAPromptBuilder()")
    print("")
    print("# Prompt")
    print("messages = builder.build_prompt_for_7b(")
    print("    query='',")
    print("    visual_context=[...],")
    print("    conversation_history=[...]")
    print(")")
    print("```")

    # ============================================
    # 
    # ============================================
    print("\n" + "="*70)
    print("🚀 ")
    print("="*70)

    print("\n📋 :")

    print("\n1️⃣  (config_example.yaml):")
    print("```yaml")
    print("# ")
    print("vision_encoder:")
    print("  enabled: true")
    print("  model_type: 'siglip'")
    print("")
    print("tiered_memory:")
    print("  enabled: true")
    print("  enable_working_memory: false  # ")
    print("")
    print("conflict_resolution:")
    print("  enabled: true")
    print("```")

    print("\n2️⃣ :")
    print("```python")
    print("from memscreen.memory.enhanced_memory import create_enhanced_memory")
    print("from memscreen.config import get_config")
    print("")
    print("# Memory")
    print("from memscreen.memory import Memory, MemoryConfig")
    print("memory = Memory(config=MemoryConfig())")
    print("")
    print("# Memory")
    print("enhanced = create_enhanced_memory(memory)")
    print("")
    print("# ")
    print("# 1. ")
    print("enhanced.add_with_vision(")
    print("    messages=[{'content': ''}],")
    print("    image_path='screenshot.png'")
    print(")")
    print("")
    print("# 2. ")
    print("results = enhanced.search_visual(")
    print("    query='',")
    print("    image_path='query.png'")
    print(")")
    print("")
    print("# 3. ")
    print("tier = enhanced.get_memory_tier(memory_id)")
    print("")
    print("# 4. ")
    print("conflicts = enhanced.detect_conflicts('')")
    print("```")

    print("\n3️⃣ :")
    print("```bash")
    print("# ")
    print("python demo_optimization.py")
    print("")
    print("# ")
    print("python -m unittest tests.test_hybrid_vision -v")
    print("```")

    # ============================================
    # 
    # ============================================
    print("\n" + "="*70)
    print("✅ ")
    print("="*70)

    print("\n📊 :")
    print("   ✅  30-50%")
    print("   ✅  40-60%")
    print("   ✅  3-5")
    print("   ✅ Token -30%")

    print("\n📚 :")
    print("   📄 : config_example.yaml")
    print("   📄 : .claude/plans/IMPLEMENTATION_SUMMARY.md")
    print("   📄 : memscreen/memory/enhanced_memory.py")
    print("   📄 : demo_optimization.py")
    print("   📄 : tests/test_hybrid_vision.py")

    print("\n💡 :")
    print("   • ")
    print("   • ")
    print("   • ")
    print("   • ")

    print("\n🔗 :")
    print("   1.  config_example.yaml")
    print("   2.  python demo_optimization.py ")
    print("   3. ")
    print("   4.  integration_guide.py ")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ : {e}")
        import traceback
        traceback.print_exc()
