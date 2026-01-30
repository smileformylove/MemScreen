#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '.')

def debug():
    from memscreen import Memory
    from memscreen.memory.models import MemoryConfig

    config = MemoryConfig()
    memory = Memory(config=config)

    # Search all memories
    print("Searching all memories...")
    result = memory.search(query="all", user_id="default_user", limit=20, threshold=0.0)

    if result and "results" in result:
        memories = result["results"]
        print(f"Found {len(memories)} memories\n")

        # Show each memory
        for i, mem in enumerate(memories[:5], 1):
            print(f"Memory {i}:")
            print(f"  Type: {type(mem)}")
            
            if isinstance(mem, dict):
                content = mem.get("memory", mem.get("content", "No content"))[:100]
                score = mem.get("score", 0)
                
                print(f"  Score: {score}")
                print(f"  Content: {content}...")
                
                # Check metadata
                metadata = mem.get("metadata")
                print(f"  Metadata type: {type(metadata)}")
                
                if metadata and isinstance(metadata, dict):
                    mem_type = metadata.get("type", metadata.get("source", "N/A"))
                    print(f"  Memory Type: {mem_type}")
                
                print()
            else:
                print(f"  Unexpected type: {type(mem)}")
                print()

        # Test with ChatScreen parameters
        print("Testing with ChatScreen parameters (threshold=0.3)...")
        result = memory.search(
            query="what did I do",
            user_id="default_user",
            limit=5,
            threshold=0.3
        )

        if result and "results" in result:
            memories = result["results"]
            print(f"Found {len(memories)} memories with threshold=0.3")

            if memories:
                print("\nBuilding context (same as ChatScreen)...")
                context_parts = []
                for mem in memories[:3]:
                    if isinstance(mem, dict):
                        if "memory" in mem:
                            content = mem["memory"]
                        elif "content" in mem:
                            content = mem["content"]
                        else:
                            content = str(mem)
                        context_parts.append(content)

                if context_parts:
                    context = "\n\n".join(context_parts)
                    print(f"Context length: {len(context)} chars")
                    print(f"Context preview:")
                    print(context[:300] + "...")
                else:
                    print("No context built!")
        else:
            print("No results with threshold=0.3")

    else:
        print("No memories found!")

    print("\n" + "="*70)

if __name__ == "__main__":
    debug()
