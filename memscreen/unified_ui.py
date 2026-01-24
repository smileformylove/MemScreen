### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""
MemScreen Unified UI - Thin wrapper for backward compatibility

This file provides backward compatibility by re-exporting the new modular UI structure.
All actual functionality has been moved to memscreen/ui/ module.
"""

from ttkthemes import ThemedTk

from .memory import Memory
from .ui import MemScreenApp

# Configuration
config = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "qwen3:1.7b",
            "temperature": 0.8,
            "max_tokens": 2000,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "mllm": {
        "provider": "ollama",
        "config": {
            "model": "qwen2.5vl:3b",
            "enable_vision": True,
            "temperature": 0.8,
            "max_tokens": 2000,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "test",
            "path": "db",
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "mxbai-embed-large",
            "ollama_base_url": "http://localhost:11434",
        },
    },
}

mem = Memory.from_config(config)
DB_NAME = "./db/screen_capture.db"


def main():
    """Main entry point - launches the MemScreen UI"""
    root = ThemedTk(theme="arc")
    app = MemScreenApp(root, mem, DB_NAME)
    root.mainloop()


if __name__ == "__main__":
    main()
