# MemScreen 

## 

```
MemScreen/
├── start.py                 # 
├── config_example.yaml      # 
├── README.md               # 
├── LICENSE                 # MIT 
│
├── memscreen/              # 
│   ├── ui/                # UI 
│   ├── presenters/        #  (MVP)
│   ├── memory/            # 
│   ├── llm/               # LLM
│   ├── audio/             # 
│   ├── prompts/           # Prompt
│   ├── embeddings/        # 
│   ├── vector_store/      # 
│   ├── config/            # 
│   └── utils/             # 
│
├── tests/                 # 
│   ├── test_hybrid_vision.py
│   ├── test_integration.py
│   ├── test_recording_flow.py
│   ├── test_*.py
│   └── README.md
│
├── examples/              # 
│   ├── demo_optimization.py       # 
│   ├── demo_chat_integration.py
│   ├── demo_dynamic_memory.py
│   ├── demo_intelligent_agent.py
│   └── demo_visual_agent.py
│
├── docs/                  # 
│   ├── integration_guide.py        # 
│   ├── IMPLEMENTATION_SUMMARY.md   # 
│   └── *.md
│
├── setup/                 # 
├── assets/                # 
└── .github/               # GitHub Actions
```

## 

 `~/.memscreen/`

```
~/.memscreen/
├── db/                    # 
│   ├── screen_capture.db  # 
│   ├── memories.db        # 
│   └── chroma.sqlite3     # 
│
├── videos/                # 
├── audio/                 # 
└── logs/                  # 
```

## 

```bash
# 1
python start.py

# 2
./run.sh

# 3 .app (macOS)
open dist/MemScreen.app
```

## 

```bash
# 
python -m pytest tests/

# 
python tests/test_hybrid_vision.py

# 
python tests/test_integration.py

# 
python examples/demo_optimization.py
```

## 

 `config_example.yaml`  `~/.memscreen/config.yaml` 

```bash
mkdir -p ~/.memscreen
cp config_example.yaml ~/.memscreen/config.yaml
```

## 

### UI  (memscreen/ui/)
- `kivy_app.py`: 
- `components.py`: UI

###  (memscreen/presenters/)
- `recording_presenter.py`: 
- `video_presenter.py`: 
- `chat_presenter.py`: 
- `process_mining_presenter.py`: 

###  (memscreen/memory/)
- `memory.py`: 
- `enhanced_memory.py`: 6
- `tiered_memory_manager.py`: 
- `conflict_resolver.py`: 

### LLM (memscreen/llm/)
- `ollama_llm.py`: Ollama LLM
- `model_router.py`: 

###  (memscreen/vector_store/)
- `chroma_store.py`: ChromaDB 
- `multimodal_chroma.py`: 

## 6

1. **** (memscreen/embeddings/vision_encoder.py)
   - SigLIP/CLIP 
   - 
   - 

2. **** (memscreen/memory/hybrid_retriever.py)
   - +
   - RRF 

3. **** (memscreen/memory/tiered_memory_manager.py)
   - Working Memory (1)
   - Short-term Memory (1-7)
   - Long-term Memory (7+)

4. **** (memscreen/memory/conflict_resolver.py)
   - 
   - 

5. **** (memscreen/memory/multigranular_vision_memory.py)
   - Scene/Object/Text 
   - 

6. **** (memscreen/prompts/vision_qa_prompts.py)
   - 
   - 
   - 7b 

## 

### 
1. 
2.  `tests/`
3. 
4.  PR

### 
-  PEP 8
- 
- 
- 

## 

MIT License -  LICENSE 
