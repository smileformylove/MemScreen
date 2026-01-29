#!/usr/bin/env python3
"""
MemScreen Quick Launcher
Simple script to launch MemScreen UI with full memory support
"""

from memscreen.ui import MemScreenApp
from memscreen import Memory
from memscreen.memory.models import MemoryConfig, EmbedderConfig, LlmConfig, VectorStoreConfig
from memscreen.embeddings import MockEmbeddings
from memscreen.config import get_config
import tkinter as tk

def main():
    """Launch MemScreen UI"""
    print("🚀 Starting MemScreen UI...")
    print("📱 Initializing memory system...")

    # Create real memory system with Ollama embeddings
    try:
        # Use centralized config system
        app_config = get_config()

        # Create MemoryConfig from centralized config
        config = MemoryConfig(
            embedder=EmbedderConfig(
                provider=app_config.get_embedder_config()["provider"],
                config=app_config.get_embedder_config()["config"]
            ),
            vector_store=VectorStoreConfig(
                provider=app_config.get_vector_store_config()["provider"],
                config=app_config.get_vector_store_config()["config"]
            ),
            llm=LlmConfig(
                provider=app_config.get_llm_config()["provider"],
                config=app_config.get_llm_config()["config"]
            ),
            mllm=LlmConfig(
                provider=app_config.get_mllm_config()["provider"],
                config=app_config.get_mllm_config()["config"]
            ),
            history_db_path=str(app_config.db_path),
            timezone=app_config.timezone if hasattr(app_config, 'timezone') else "US/Pacific"
        )

        mem = Memory(config=config)
        print("✅ Memory system ready (using centralized config with Ollama embeddings)")
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
