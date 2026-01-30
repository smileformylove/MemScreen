#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_memory_retrieval():
    from memscreen import Memory
    from memscreen.memory.models import MemoryConfig

    print("\n" + "="*70)
    print("Debug Chat Memory Retrieval")
    print("="*70)

    config = MemoryConfig()
    memory = Memory(config=config)

    # Search all memories
    print("\nSearching for all memories...")
    result = memory.search(
        query="all",
        user_id="default_user",
        limit=20,
        threshold=0.0
    )

    if result and "results" in result:
        memories = result["results"]
        print(f"Found {len(memories)} memories")

        # Count by type
        type_counts = {}
        for mem in memories:
            if isinstance(mem, dict):
                metadata = mem.get("metadata", {})
                mem_type = metadata.get("type", metadata.get("source", "unknown"))
                type_counts[mem_type] = type_counts.get(mem_type, 0) + 1

        print(f"\nMemory types:")
        for mem_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {mem_type}: {count}")
    else:
        print("No memories found!")

    # Test search with threshold=0.3
    print("\nTesting with threshold=0.3...")
    result = memory.search(
        query="what did I do",
        user_id="default_user",
        limit=5,
        threshold=0.3
    )

    if result and "results" in result:
        memories = result["results"]
        print(f"Found {len(memories)} memories with threshold=0.3")
    else:
        print("No results with threshold=0.3")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    debug_memory_retrieval()
