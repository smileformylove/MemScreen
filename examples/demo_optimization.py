#!/usr/bin/env python3
"""
MemScreen 

6
1. 
2. 
3. 
4. 
5. 
6. 7b
"""

import sys
import tempfile
from pathlib import Path

# 
sys.path.insert(0, str(Path(__file__).parent))


def demo_vision_encoder():
    """1"""
    print("\n" + "="*60)
    print("🎯 1")
    print("="*60)

    from memscreen.embeddings.vision_encoder import VisionEncoder, VisionEncoderConfig

    # 
    config = VisionEncoderConfig(
        model_type="clip",  # CLIP
        cache_size=10,
    )

    # 
    encoder = VisionEncoder(config)

    print(f"✅ ")
    print(f"   - : {config.model_type}")
    print(f"   - : {config.embedding_dims}")
    print(f"   - : {config.cache_size}")

    # 
    from PIL import Image
    import numpy as np

    test_img = Image.new('RGB', (100, 100), color='red')
    test_path = Path(tempfile.gettempdir()) / "test_image.png"
    test_img.save(test_path)

    print(f"\n✅ : {test_path}")

    # 
    visual_hash = encoder.compute_visual_hash(str(test_path))
    print(f"\n✅ : {visual_hash}")

    # 
    features = encoder.extract_visual_features(str(test_path))
    print(f"\n✅ :")
    print(f"   - : {features['brightness']:.2f}")
    print(f"   - : {features['contrast']:.2f}")
    print(f"   - : {features['aspect_ratio']:.2f}")
    print(f"   - : {features['layout_density']:.2f}")
    print(f"   - : {features['dominant_colors']}")

    # 
    test_path.unlink()


def demo_multimodal_store():
    """2"""
    print("\n" + "="*60)
    print("🎯 2")
    print("="*60)

    from memscreen.vector_store.multimodal_chroma import MultimodalChromaDB

    # 
    import tempfile
    db_path = tempfile.mkdtemp()

    # 
    store = MultimodalChromaDB(
        collection_name="demo_multimodal",
        text_embedding_dims=512,
        vision_embedding_dims=768,
        path=db_path,
    )

    print(f"✅ ")
    print(f"   - : 512")
    print(f"   - : 768")
    print(f"   - : {db_path}")

    # 
    ids = ["mem1", "mem2", "mem3"]
    text_embeddings = [[0.1] * 512, [0.2] * 512, [0.3] * 512]
    vision_embeddings = [[0.15] * 768, [0.25] * 768, [0.35] * 768]
    payloads = [
        {"content": "", "category": "coding"},
        {"content": "", "category": "browsing"},
        {"content": "", "category": "document"},
    ]

    store.insert_multimodal(
        ids=ids,
        text_embeddings=text_embeddings,
        vision_embeddings=vision_embeddings,
        payloads=payloads,
    )

    print(f"\n✅  {len(ids)} ")

    # 
    query_text = [0.2] * 512
    query_vision = [0.25] * 768

    results = store.search_hybrid(
        query_text_embedding=query_text,
        query_vision_embedding=query_vision,
        limit=2,
    )

    print(f"\n✅  {len(results)} ")
    for i, r in enumerate(results, 1):
        if r.payload:
            print(f"   {i}. {r.payload.get('content', 'N/A')} (score={r.score:.3f})")

    # 
    stats = store.get_stats()
    print(f"\n✅ :")
    print(f"   - : {stats['text_count']}")
    print(f"   - : {stats['vision_count']}")
    print(f"   - : {stats['total_count']}")

    # 
    store.reset()
    import shutil
    shutil.rmtree(db_path)


def demo_importance_scorer():
    """3"""
    print("\n" + "="*60)
    print("🎯 3")
    print("="*60)

    from memscreen.memory.importance_scorer import ImportanceScorer

    scorer = ImportanceScorer()

    print(f"✅ ")

    # 
    memories = [
        {
            "content": "Python",
            "metadata": {"category": "fact"},
            "access_count": 10,
            "created_at": __import__('datetime').datetime.now(),
        },
        {
            "content": "",
            "metadata": {"category": "greeting"},
            "access_count": 1,
            "created_at": __import__('datetime').datetime.now(),
        },
    ]

    for i, mem in enumerate(memories, 1):
        score = scorer.score_memory(
            content=mem["content"],
            metadata=mem["metadata"],
            access_count=mem["access_count"],
            created_at=mem["created_at"],
        )
        tier = scorer.get_tier_for_score(score)
        print(f"\n✅ {i}:")
        print(f"   - : {mem['content']}")
        print(f"   - : {mem['metadata']['category']}")
        print(f"   - : {mem['access_count']}")
        print(f"   - : {score:.3f}")
        print(f"   - : {tier}")


def demo_conflict_resolver():
    """4"""
    print("\n" + "="*60)
    print("🎯 4")
    print("="*60)

    import hashlib
    import json

    # LLM
    class MockEmbedder:
        def embed(self, text, action):
            # 
            return [0.1] * 512

    class MockLLM:
        def generate_response(self, messages, **kwargs):
            # 
            import json
            return json.dumps({
                "type": "equivalent",
                "confidence": 0.9,
                "reasoning": "Similar meaning",
                "suggestion": "skip"
            })

    from memscreen.memory.conflict_resolver import ConflictResolver

    resolver = ConflictResolver(
        embedding_model=MockEmbedder(),
        llm=MockLLM(),
    )

    print(f"✅ ")

    # 
    new_memory = "Python"
    existing_memories = [
        {
            "id": "mem1",
            "data": "Python is a programming language",
            "hash": hashlib.md5("Python is a programming language".encode()).hexdigest(),
            "embedding": [0.1] * 512,
        },
        {
            "id": "mem2",
            "data": "JavaScript is a programming language",
            "embedding": [0.2] * 512,
        },
    ]

    import hashlib
    conflicts = resolver.detect_conflict(new_memory, existing_memories)

    print(f"\n✅  {len(conflicts)} ")

    for conflict in conflicts:
        print(f"\n   : {conflict['conflict_type']}")
        print(f"   : {conflict['confidence']:.2f}")
        print(f"   : {conflict['resolution']}")

        # 
        resolution = resolver.resolve_conflict(conflict, new_memory)
        print(f"   : {resolution['action']}")
        print(f"   : {resolution['reason']}")


def demo_tiered_memory():
    """5"""
    print("\n" + "="*60)
    print("🎯 5")
    print("="*60)

    from memscreen.memory.tiered_memory_manager import TieredMemoryManager, TieredMemoryConfig

    # 
    class MockEmbedder:
        def embed(self, text, action):
            return [0.1] * 512

    class MockLLM:
        def generate_response(self, messages, **kwargs):
            return "Summary"

    # 
    import tempfile
    db_path = tempfile.mkdtemp()

    config = TieredMemoryConfig(
        enable_working_memory=False,  # 
        short_term_days=7,
    )

    manager = TieredMemoryManager(
        vector_store=None,  # 
        embedding_model=MockEmbedder(),
        llm=MockLLM(),
        config=config,
    )

    print(f"✅ ")
    print(f"   - Working Memory: {'' if config.enable_working_memory else ''}")
    print(f"   - Short-term: {config.short_term_days}")
    print(f"   - : {config.working_capacity}/{config.short_term_capacity}")

    # 
    from datetime import datetime

    scores = [
        (0.8, ""),
        (0.5, ""),
        (0.3, ""),
    ]

    print(f"\n✅ :")
    for score, desc in scores:
        tier = manager.scorer.get_tier_for_score(score)
        print(f"   -  {score:.1f}: {desc} → {tier}")


def demo_vision_qa():
    """6"""
    print("\n" + "="*60)
    print("🎯 6")
    print("="*60)

    # prompts.py
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "vision_qa_prompts",
        Path(__file__).parent / "memscreen" / "prompts" / "vision_qa_prompts.py"
    )
    vision_qa_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vision_qa_module)

    VisionQAPromptBuilder = vision_qa_module.VisionQAPromptBuilder
    builder = VisionQAPromptBuilder()

    print(f"✅ Prompt")

    # 
    visual_context = [
        {
            "description": "VSCodePython",
            "timestamp": "2026-02-06T10:30:00",
            "granularity": "scene",
            "score": 0.9,
            "scene_type": "coding",
        },
        {
            "description": "",
            "timestamp": "2026-02-06T10:25:00",
            "granularity": "scene",
            "score": 0.7,
            "scene_type": "browsing",
        },
    ]

    # 
    queries = [
        "",
        "",
        "",
    ]

    for query in queries:
        query_type = builder._classify_query_type(query)
        print(f"\n✅ : {query}")
        print(f"   - : {query_type}")

    # Prompt
    messages = builder.build_prompt_for_7b(
        query="",
        visual_context=visual_context,
        conversation_history=[],
    )

    print(f"\n✅ Prompt: {len(messages)}")
    print(f"   - : {len(messages[0]['content'])} ")
    if len(messages) > 1:
        print(f"   - : {len(messages[1]['content'])} ")


def demo_context_optimizer():
    """7"""
    print("\n" + "="*60)
    print("🎯 77b")
    print("="*60)

    from memscreen.memory.vision_context_optimizer import VisionContextOptimizer

    optimizer = VisionContextOptimizer()

    print(f"✅ ")

    # 
    from datetime import datetime, timedelta

    now = datetime.now()
    visual_memories = [
        {
            "description": "" * 10,  # 
            "timestamp": (now - timedelta(minutes=5)).isoformat(),
            "score": 0.9,
            "created_at": (now - timedelta(minutes=5)).isoformat(),
        },
        {
            "description": "" * 10,
            "timestamp": (now - timedelta(days=2)).isoformat(),
            "score": 0.7,
            "created_at": (now - timedelta(days=2)).isoformat(),
        },
        {
            "description": "" * 10,
            "timestamp": (now - timedelta(days=10)).isoformat(),
            "score": 0.5,
            "created_at": (now - timedelta(days=10)).isoformat(),
        },
    ]

    print(f"\n✅ : {len(visual_memories)} ")

    # 
    optimized = optimizer.optimize_context_for_7b(
        visual_memories=visual_memories,
        query="",
        max_tokens=1000,  # 
    )

    print(f"✅ : {len(optimized)} ")

    for i, mem in enumerate(optimized, 1):
        original_len = len(mem.get('description', ''))
        compressed_len = len(mem.get('description', ''))
        print(f"   {i}. : {original_len} → {compressed_len} ")


def main():
    """"""
    print("\n" + "="*60)
    print("🚀 MemScreen ")
    print("="*60)
    print("\n6...\n")

    try:
        demo_vision_encoder()
        demo_multimodal_store()
        demo_importance_scorer()
        demo_conflict_resolver()
        demo_tiered_memory()
        demo_vision_qa()
        demo_context_optimizer()

        print("\n" + "="*60)
        print("✅ ")
        print("="*60)
        print("\n")
        print("  ✅ SigLIP/CLIP ")
        print("  ✅ ")
        print("  ✅ ")
        print("  ✅ ")
        print("  ✅ ")
        print("  ✅ ")
        print("  ✅ 7b")
        print("\n: .claude/plans/IMPLEMENTATION_SUMMARY.md")
        print()

    except Exception as e:
        print(f"\n❌ : {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
