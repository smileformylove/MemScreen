#!/usr/bin/env python3
"""
MemScreen Quick Launcher
Simple script to launch MemScreen UI with full memory support
"""

from memscreen.ui import MemScreenApp
from memscreen import Memory
from memscreen.memory.models import MemoryConfig, EmbedderConfig, LlmConfig, VectorStoreConfig
from memscreen.embeddings import MockEmbeddings
import tkinter as tk

def main():
    """Launch MemScreen UI"""
    print("🚀 Starting MemScreen UI...")
    print("📱 Initializing memory system...")

    # Create real memory system with Ollama embeddings
    try:
        # Create configuration with all required components
        config = MemoryConfig(
            embedder=EmbedderConfig(
                provider="ollama",
                config={
                    "model": "nomic-embed-text",  # Lightweight embedding model
                    "ollama_base_url": "http://127.0.0.1:11434"
                }
            ),
            vector_store=VectorStoreConfig(
                provider="chroma",
                config={
                    "collection_name": "memscreen_records",
                    "path": "./db/chroma_db"
                }
            ),
            llm=LlmConfig(
                provider="ollama",
                config={
                    "model": "qwen2.5vl:3b",
                    "ollama_base_url": "http://127.0.0.1:11434"
                }
            ),
            history_db_path="./db/memscreen_history.db"
        )

        mem = Memory(config=config)
        print("✅ Memory system ready (using Ollama embeddings)")
    except Exception as e:
        print(f"⚠️  Warning: Memory init failed: {e}")
        import traceback
        traceback.print_exc()
        print("📱 Falling back to mock memory...")

        # Fallback to mock memory
        class MockMemory:
            def search(self, query, user_id='user1'):
                return []
            def add(self, *args, **kwargs):
                return 'test_id'

        mem = MockMemory()

    print("")

    # Create main window
    root = tk.Tk()
    root.title("MemScreen v0.2")

    # Create app with real memory
    app = MemScreenApp(root, mem=mem)

    print("✅ MemScreen UI launched!")
    print("   - 5 tabs available: Recording, Chat, Video, Search, Settings")
    print("   - Video recordings will be added to memory automatically")
    print("   - Chat can search through recordings and answer questions")
    print("   - Close the window to exit")
    print("")

    # Start the UI
    root.mainloop()

    print("👋 MemScreen UI closed. Goodbye!")

if __name__ == "__main__":
    main()
