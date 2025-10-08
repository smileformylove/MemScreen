from memory import Memory
import os

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

m = Memory.from_config(config)
messages = [
    {"role": "user", "content": "I like playing football."},
]

result = m.add(messages=messages, user_id="alice")
print(result)

# Get all memories for alice
all_memories = m.get_all(user_id="alice")
print(all_memories)

# Get all memories for memscreen
all_memories = m.get_all(user_id="screenshot")
print(all_memories)

# search
related_memories = m.search(query="what does alice like?", user_id="alice")
print(related_memories['results'][0]['memory'])

# # search
# related_memories = m.search(query="what is screenshot doing?", user_id="screenshot")
# print(related_memories)