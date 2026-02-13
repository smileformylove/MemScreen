"""
Core dependency creation for API server.
Mirrors Kivy's Memory + Presenter initialization so API uses same config and data.
"""

from __future__ import annotations

from typing import Optional, Any, TYPE_CHECKING

from memscreen.config import get_config
from memscreen.memory import Memory
from memscreen.memory.models import MemoryConfig, EmbedderConfig, LlmConfig, VectorStoreConfig

if TYPE_CHECKING:
    from memscreen.presenters.chat_presenter import ChatPresenter
    from memscreen.presenters.recording_presenter import RecordingPresenter
    from memscreen.presenters.video_presenter import VideoPresenter
    from memscreen.presenters.process_mining_presenter import ProcessMiningPresenter


def _get_process_mining_db_path() -> str:
    """Process mining DB path consistent with config (same data dir as Kivy)."""
    cfg = get_config()
    return str(cfg.db_dir / "process_mining.db")


def create_memory() -> Optional[Memory]:
    """Create Memory instance from centralized config (same as Kivy)."""
    try:
        app_config = get_config()
        config = MemoryConfig(
            embedder=EmbedderConfig(
                provider=app_config.get_embedder_config()["provider"],
                config=app_config.get_embedder_config()["config"],
            ),
            vector_store=VectorStoreConfig(
                provider=app_config.get_vector_store_config()["provider"],
                config=app_config.get_vector_store_config()["config"],
            ),
            llm=LlmConfig(
                provider=app_config.get_llm_config()["provider"],
                config=app_config.get_llm_config()["config"],
            ),
            mllm=LlmConfig(
                provider=app_config.get_mllm_config()["provider"],
                config=app_config.get_mllm_config()["config"],
            ),
            history_db_path=str(app_config.db_path),
            timezone=app_config.timezone,
            enable_dynamic_memory=True,
            dynamic_config={
                "enable_auto_classification": True,
                "enable_intent_classification": True,
                "enable_category_weights": True,
                "cache_classification_results": True,
            },
        )
        return Memory(config=config)
    except Exception as e:
        print(f"[API] Memory init failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_chat_presenter(memory: Optional[Memory]) -> Optional["ChatPresenter"]:
    """Create ChatPresenter (view=None for API)."""
    try:
        from memscreen.presenters.chat_presenter import ChatPresenter
        cfg = get_config()
        p = ChatPresenter(
            view=None,
            memory_system=memory,
            ollama_base_url=cfg.ollama_base_url,
        )
        p.initialize()
        return p
    except Exception as e:
        print(f"[API] ChatPresenter init failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_recording_presenter(memory: Optional[Memory]) -> Optional["RecordingPresenter"]:
    """Create RecordingPresenter (view=None)."""
    try:
        from memscreen.presenters.recording_presenter import RecordingPresenter
        cfg = get_config()
        p = RecordingPresenter(
            view=None,
            memory_system=memory,
            db_path=str(cfg.db_path),
        )
        p.initialize()
        return p
    except Exception as e:
        print(f"[API] RecordingPresenter init failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_video_presenter() -> Optional["VideoPresenter"]:
    """Create VideoPresenter (view=None)."""
    try:
        from memscreen.presenters.video_presenter import VideoPresenter
        cfg = get_config()
        p = VideoPresenter(db_path=str(cfg.db_path))
        p.initialize()
        return p
    except Exception as e:
        print(f"[API] VideoPresenter init failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# Lazy singletons (created on first request if needed)
_memory: Optional[Memory] = None
_chat_presenter: Optional["ChatPresenter"] = None
_recording_presenter: Optional["RecordingPresenter"] = None
_video_presenter: Optional["VideoPresenter"] = None


def get_memory() -> Optional[Memory]:
    global _memory
    if _memory is None:
        _memory = create_memory()
    return _memory


def get_chat_presenter() -> Optional["ChatPresenter"]:
    global _chat_presenter
    if _chat_presenter is None:
        _chat_presenter = create_chat_presenter(get_memory())
    return _chat_presenter


def get_recording_presenter() -> Optional["RecordingPresenter"]:
    global _recording_presenter
    if _recording_presenter is None:
        _recording_presenter = create_recording_presenter(get_memory())
    return _recording_presenter


def get_video_presenter() -> Optional["VideoPresenter"]:
    global _video_presenter
    if _video_presenter is None:
        _video_presenter = create_video_presenter()
    return _video_presenter


def create_process_mining_presenter() -> Optional["ProcessMiningPresenter"]:
    """Create ProcessMiningPresenter (view=None) for keyboard/mouse tracking."""
    try:
        from memscreen.presenters.process_mining_presenter import ProcessMiningPresenter
        db_path = _get_process_mining_db_path()
        p = ProcessMiningPresenter(view=None, db_path=db_path)
        p.initialize()
        return p
    except Exception as e:
        print(f"[API] ProcessMiningPresenter init failed: {e}")
        import traceback
        traceback.print_exc()
        return None


_process_mining_presenter: Optional["ProcessMiningPresenter"] = None


def get_process_mining_presenter() -> Optional["ProcessMiningPresenter"]:
    global _process_mining_presenter
    if _process_mining_presenter is None:
        _process_mining_presenter = create_process_mining_presenter()
    return _process_mining_presenter


def get_process_db_path() -> str:
    return _get_process_mining_db_path()
