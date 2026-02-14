### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""Presenter for AI Chat functionality (MVP Pattern)"""

import json
import os
import queue
import re
import sqlite3
import hashlib
import subprocess
import threading
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable, Tuple
import asyncio

from .base_presenter import BasePresenter
from .agent_executor import AgentExecutor
from memscreen.cv2_loader import get_cv2

# Import Agent system (kept for compatibility)
try:
    from ..agent.base_agent import BaseAgent, AgentConfig
    from ..agent.intelligent_agent import IntelligentAgent
    from ..skills.memory.search_skill import SearchMemorySkill
    from ..skills.analysis.summary_skill import SummarySkill
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    INTELLIGENT_AGENT_AVAILABLE = False
    print("[ChatPresenter] Agent system not available, using standard chat mode")
else:
    INTELLIGENT_AGENT_AVAILABLE = True


class ChatMessage:
    """Represents a single chat message"""

    def __init__(self, role: str, content: str, timestamp: str = None):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "role": self.role,
            "content": self.content
        }


class ChatPresenter(BasePresenter):
    """
    Presenter for AI Chat functionality.

    Responsibilities:
    - Manage conversation state
    - Call Ollama API for AI responses
    - Search memory for context
    - Stream responses
    - Manage model list

    View (ChatTab) responsibilities:
    - Display chat messages
    - Show typing indicator
    - Handle user input
    - Update model dropdown
    """

    def __init__(self, view=None, memory_system=None, ollama_base_url="http://127.0.0.1:11434"):
        """
        Initialize chat presenter.

        Args:
            view: ChatTab view instance
            memory_system: Memory system for context search
            ollama_base_url: Base URL for Ollama API
        """
        super().__init__(view, memory_system)
        self.memory_system = memory_system  # Store memory_system reference
        self.ollama_base_url = ollama_base_url

        # Chat state
        self.conversation_history: List[ChatMessage] = []
        self.current_model = "qwen3:1.7b"
        self.available_models = []

        # Streaming state
        self.is_streaming = False
        self.stream_queue = None
        self.stream_thread = None

        # Agent system (seamlessly integrated)
        self.agent = None
        self.intelligent_agent = None  # NEW: Intelligent Agent with auto-classification
        self.use_agent_mode = False  # Can be toggled by user
        self.use_intelligent_agent = True  # NEW: Auto-use intelligent agent

        # NEW: Rule-based Agent Executor (more reliable)
        self.agent_executor = AgentExecutor(
            memory_system=memory_system,
            ollama_base_url=ollama_base_url,
            current_model="qwen3:1.7b"
        )

        # OPTIMIZATION: Reusable event loop for async operations
        self._event_loop = None

        # OPTIMIZATION: Response cache for repeated queries
        self._response_cache = {}  # query_hash -> response
        self._cache_max_size = 100

        # OPTIMIZATION: Smart search limit (reduce results for faster processing)
        self._smart_search_limit = 5  # Only get top 5 results

        # Tiered-memory configuration for chat context
        self.auto_model_selection = True
        self.working_memory_hours = 2
        self.short_term_days = 7
        self.max_tier_items = {
            "working": 4,
            "short_term": 4,
            "long_term": 3,
        }

        self._is_initialized = False
        self._easyocr_reader = None
        self._video_ocr_cache: Dict[str, Dict[str, Any]] = {}
        self._visual_frame_cache: Dict[str, Dict[str, Any]] = {}
        self._model_pull_attempted = set()
        self.auto_pull_missing_models = True
        self.max_auto_pull_seconds = 240

        # Initialize agents if available
        if AGENT_AVAILABLE:
            try:
                # Create a simple LLM client wrapper
                class LLMClient:
                    def __init__(self, base_url):
                        self.base_url = base_url

                    def generate_response(self, messages, **kwargs):
                        # Synchronous wrapper for async compatibility
                        import requests
                        # Extract the last message content for simpler interface
                        if messages and len(messages) > 0:
                            content = messages[-1].get("content", "")
                        else:
                            content = str(messages)

                        # Use Ollama generate endpoint
                        response = requests.post(
                            f"{self.base_url}/api/generate",
                            json={
                                "model": "qwen3:1.7b",
                                "prompt": content,
                                "stream": False
                            },
                            timeout=120
                        )
                        if response.status_code == 200:
                            data = response.json()
                            return data.get("response", "")
                        return ""

                llm_client = LLMClient(ollama_base_url)

                # Create legacy BaseAgent
                agent_config = AgentConfig(
                    name="MemScreen Chat Agent",
                    version="1.0.0",
                    enable_memory=True
                )

                self.agent = BaseAgent(
                    memory_system=memory_system,
                    llm_client=llm_client,
                    config=agent_config
                )

                # Register skills
                self.agent.register_skill(SearchMemorySkill())
                self.agent.register_skill(SummarySkill())

                print("[ChatPresenter] Base Agent initialized")

                # NEW: Create Intelligent Agent with auto-classification
                if INTELLIGENT_AGENT_AVAILABLE:
                    try:
                        intelligent_config = AgentConfig(
                            name="MemScreen Intelligent Agent",
                            version="2.0.0",
                            enable_memory=True,
                            max_parallel_steps=1
                        )

                        self.intelligent_agent = IntelligentAgent(
                            memory_system=memory_system,
                            llm_client=llm_client,
                            config=intelligent_config,
                            enable_classification=True
                        )

                        # Register the same skills
                        self.intelligent_agent.register_skill(SearchMemorySkill())
                        self.intelligent_agent.register_skill(SummarySkill())

                        print("[ChatPresenter] ✅ Intelligent Agent initialized (auto-classification enabled)")
                    except Exception as e:
                        print(f"[ChatPresenter] Intelligent Agent initialization failed: {e}")
                        self.intelligent_agent = None

            except Exception as e:
                print(f"[ChatPresenter] Agent initialization failed: {e}")
                self.agent = None
                self.intelligent_agent = None

    def initialize(self):
        """Initialize presenter and load models"""
        try:
            self._load_available_models()
            self._is_initialized = True
            print("[ChatPresenter] Initialized successfully")
            threading.Thread(target=self._warmup_visual_evidence, daemon=True).start()
        except Exception as e:
            self.handle_error(e, "Failed to initialize ChatPresenter")
            raise

    def cleanup(self):
        """Clean up resources"""
        # Stop any ongoing streaming
        if self.is_streaming:
            self._stop_streaming()

        # Clean up event loop
        if self._event_loop and not self._event_loop.is_closed():
            self._event_loop.close()

        self._is_initialized = False

    def _get_event_loop(self):
        """Get or create reusable event loop"""
        if self._event_loop is None or self._event_loop.is_closed():
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)
        return self._event_loop

    def _warmup_visual_evidence(self) -> None:
        """Warm up OCR reader/cache in background to reduce first visual-query latency."""
        try:
            reader = self._get_easyocr_reader()
            if not reader:
                return
            rows = self._load_recent_recordings_from_db(limit=1)
            if rows:
                self._quick_extract_video_text(rows[0].get("filename", ""))
                print("[Chat] Visual evidence warmup complete")
        except Exception as warm_err:
            print(f"[Chat] Visual evidence warmup failed: {warm_err}")

    def _get_cached_response(self, query: str) -> Optional[str]:
        """Get cached response if available"""
        import hashlib
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return self._response_cache.get(query_hash)

    def _cache_response(self, query: str, response: str):
        """Cache a response"""
        import hashlib
        query_hash = hashlib.md5(query.encode()).hexdigest()

        # Simple cache eviction if full
        if len(self._response_cache) >= self._cache_max_size:
            # Remove oldest entry (first key)
            oldest_key = next(iter(self._response_cache))
            del self._response_cache[oldest_key]

        self._response_cache[query_hash] = response

    # ==================== Public API for View ====================

    def get_conversation_history(self) -> List[ChatMessage]:
        """Get current conversation history"""
        return self.conversation_history.copy()

    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return self.available_models.copy()

    def get_current_model(self) -> str:
        """Get currently selected model"""
        return self.current_model

    def set_model(self, model_name: str) -> bool:
        """
        Set the current model.

        Args:
            model_name: Name of the model to use

        Returns:
            True if model was set successfully
        """
        if model_name in self.available_models:
            self.current_model = model_name
            return True
        return False

    def set_agent_mode(self, enabled: bool) -> bool:
        """
        Enable or disable Agent mode for complex tasks.

        Args:
            enabled: Whether to enable Agent mode

        Returns:
            True if Agent is available and mode was set
        """
        if not AGENT_AVAILABLE or not self.agent:
            return False

        self.use_agent_mode = enabled
        mode_str = "enabled" if enabled else "disabled"
        print(f"[ChatPresenter] Agent mode {mode_str}")
        return True

    def is_agent_available(self) -> bool:
        """Check if Agent system is available"""
        return AGENT_AVAILABLE and self.agent is not None

    def _should_use_agent(self, user_message: str) -> bool:
        """
        Detect if user message requires Agent capabilities.

        Args:
            user_message: The user's message

        Returns:
            True if Agent should be used for this task
        """
        if not self.agent or not AGENT_AVAILABLE:
            return False

        user_msg_lower = user_message.lower()

        # Complex task patterns (action + context combinations)
        complex_patterns = [
            # Report/Summary patterns
            (r"(生成|创建|形成).{0,5}(报告|报表|总结|汇总)", "Report generation"),
            (r"(总结|汇总|分析).{0,10}(过去|最近|本周|上周|今天|昨天|几天)", "Temporal summary"),
            (r"(分析|研究|梳理).{0,10}(流程|模式|习惯|工作)", "Workflow analysis"),

            # Multi-step patterns
            (r"(搜索|查找|找).{0,10}(并|并且|然后|接着).{0,10}(总结|汇总|分析)", "Search + process"),
            (r"(帮我|help).{0,20}(生成|创建|分析|总结)", "Complex help request"),

            # Comprehensive queries
            (r"找出所有|find all", "Comprehensive search"),
            (r"全部|所有|everything", "All items query"),

            # Workflow analysis
            (r"工作流程|workflow|操作模式|习惯分析", "Workflow analysis"),
        ]

        # Check complex patterns first
        import re
        for pattern, description in complex_patterns:
            if re.search(pattern, user_msg_lower, re.IGNORECASE):
                print(f"[ChatPresenter] ✅ Detected Agent task: {description}")
                print(f"[ChatPresenter]    Message: {user_message[:50]}...")
                return True

        # Simple keywords that MUST be combined with task verbs
        temporal_keywords = ["昨天", "今天", "过去", "最近", "本周", "上周", "yesterday", "today", "past", "recent"]
        task_verbs = ["总结", "分析", "汇总", "报告", "生成", "summary", "analyze", "report", "generate"]

        has_temporal = any(kw in user_msg_lower for kw in temporal_keywords)
        has_task_verb = any(verb in user_msg_lower for verb in task_verbs)

        if has_temporal and has_task_verb:
            print(f"[ChatPresenter] ✅ Detected Agent task: Temporal + Task verb")
            print(f"[ChatPresenter]    Message: {user_message[:50]}...")
            return True

        # "帮我" alone is not enough - need additional complexity indicators
        if "帮我" in user_msg_lower or "help me" in user_msg_lower:
            # Only trigger if it's clearly a complex task
            complex_indicators = ["分析", "总结", "报告", "生成", "查找所有", "流程", "模式",
                                   "analyze", "summary", "report", "generate", "find all", "workflow"]
            if any(ind in user_msg_lower for ind in complex_indicators):
                print(f"[ChatPresenter] ✅ Detected Agent task: Complex help request")
                print(f"[ChatPresenter]    Message: {user_message[:50]}...")
                return True
            else:
                print(f"[ChatPresenter] ℹ️  Simple help request, using standard chat")
                return False

        print(f"[ChatPresenter] ℹ️  Using standard chat for: {user_message[:50]}...")
        return False

    def send_message(self, user_message: str, use_agent: bool = None) -> bool:
        """
        Send a user message and get AI response.

        Args:
            user_message: The user's message
            use_agent: Whether to use Agent system (None = auto-detect)

        Returns:
            True if message was sent successfully
        """
        if not user_message.strip():
            self.show_error("Please enter a message")
            return False

        try:
            # Add user message to history
            user_msg = ChatMessage("user", user_message)
            self.conversation_history.append(user_msg)

            # Notify view
            if self.view:
                self.view.on_message_added("user", user_message)

            # NEW: Try Intelligent Agent first (auto-classification)
            if self.intelligent_agent and self.use_intelligent_agent:
                print(f"[ChatPresenter] 🧠 Using Intelligent Agent for: {user_message[:50]}...")
                return self._execute_with_intelligent_agent(user_message)

            # Auto-detect if Agent should be used
            should_use_agent = use_agent
            if should_use_agent is None:
                should_use_agent = self._should_use_agent(user_message)

            # Use Agent for complex tasks if enabled (using agent_executor)
            if should_use_agent and self.agent_executor:
                print(f"[ChatPresenter] 🤖 Using Agent mode for: {user_message[:50]}...")
                return self._execute_with_agent(user_message)

            # Standard chat flow
            print(f"[ChatPresenter] Using standard chat for: {user_message[:50]}...")

            # Search memory for context
            context = self._search_memory(user_message)

            # Build messages for API
            messages = self._build_messages(user_message, context)

            # Start streaming response
            self._start_streaming(messages)

            return True

        except Exception as e:
            self.handle_error(e, "Failed to send message")
            return False

    def _extract_memory_content(self, memory_item: Dict[str, Any]) -> str:
        """Get normalized text content from one memory search result item."""
        content = ""
        if isinstance(memory_item, dict):
            content = (
                memory_item.get("memory")
                or memory_item.get("content")
                or str(memory_item)
            )
        else:
            content = str(memory_item)

        content = " ".join(str(content).split())
        return content

    def _parse_memory_timestamp(self, metadata: Dict[str, Any]) -> Optional[datetime]:
        """Parse memory timestamp from multiple known formats."""
        raw_ts = (
            metadata.get("seen_at")
            or metadata.get("timestamp")
            or metadata.get("created_at")
            or ""
        )
        if not raw_ts:
            return None

        if isinstance(raw_ts, (int, float)):
            try:
                return datetime.fromtimestamp(raw_ts)
            except Exception:
                return None

        ts = str(raw_ts).strip().replace("Z", "+00:00")
        parse_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
        ]
        parsed_dt: Optional[datetime] = None

        try:
            parsed_dt = datetime.fromisoformat(ts)
        except Exception:
            pass

        if parsed_dt is None:
            for fmt in parse_formats:
                try:
                    parsed_dt = datetime.strptime(ts, fmt)
                    break
                except Exception:
                    continue

        if parsed_dt is None:
            return None

        # Normalize to local naive datetime to avoid aware/naive comparison errors.
        if parsed_dt.tzinfo is not None:
            try:
                parsed_dt = parsed_dt.astimezone().replace(tzinfo=None)
            except Exception:
                parsed_dt = parsed_dt.replace(tzinfo=None)

        return parsed_dt

    def _is_memory_sensitive_query(self, query: str) -> bool:
        """
        Check if query should bypass response cache.

        Temporal/screen-memory questions should always hit memory search to avoid stale answers.
        """
        q = query.lower()
        keywords = [
            "什么时候", "何时", "今天", "昨天", "最近", "刚才", "刚刚",
            "上午", "中午", "下午", "晚上", "夜里",
            "看到", "看到了", "屏幕", "录屏", "录像", "哪里", "在哪", "位置", "出现",
            "在看什么", "看了什么", "论文", "paper", "pdf", "arxiv",
            "when", "today", "yesterday", "recent", "just now",
            "morning", "afternoon", "evening", "night",
            "saw", "seen", "screen", "recording", "timeline", "what did i watch", "where",
        ]
        return any(k in q for k in keywords)

    def _is_visual_detail_query(self, query: str) -> bool:
        """Whether query asks for concrete visual details from recordings."""
        q = query.lower()
        keywords = [
            "屏幕上看了什么", "看到了什么", "具体内容", "详细", "细节",
            "有哪些字", "哪些字", "哪些物体", "物体", "画面", "整体描述",
            "视频有什么", "这个视频", "这段视频",
            "论文", "paper", "pdf", "arxiv", "title", "abstract",
            "what did i see", "what was on screen", "details",
        ]
        return any(k in q for k in keywords)

    def _is_visual_location_query(self, query: str) -> bool:
        """Whether query asks where/when a text or object appeared."""
        q = query.lower()
        keywords = [
            "在哪里", "在哪", "什么地方", "哪个位置", "位置", "坐标", "出现在",
            "什么时候出现", "何时出现", "对应时间", "对应位置", "在哪一帧",
            "where", "which frame", "which timestamp", "where did", "appeared",
        ]
        return any(k in q for k in keywords)

    def _is_activity_summary_query(self, query: str) -> bool:
        """Whether query asks for retrospective summary/suggestions."""
        q = query.lower()
        keywords = [
            "总结", "回顾", "复盘", "过去做了什么", "我做了什么", "这段时间",
            "给我建议", "下一步建议", "工作总结", "今天都做了什么",
            "summary", "recap", "what did i do", "suggestion", "suggestions",
        ]
        return any(k in q for k in keywords)

    def _extract_visual_target_phrase(self, query: str) -> str:
        """Extract a text/object target phrase from location queries."""
        q = " ".join(query.strip().split())
        quoted = re.search(r"[\"“'‘](.+?)[\"”'’]", q)
        if quoted:
            val = quoted.group(1).strip()
            if val:
                return val
        patterns = [
            r"(.+?)出现在什么地方",
            r"(.+?)出现在哪里",
            r"(.+?)在哪里",
            r"(.+?)在哪个位置",
            r"where did (.+?) appear",
        ]
        for pat in patterns:
            m = re.search(pat, q, flags=re.IGNORECASE)
            if not m:
                continue
            target = m.group(1).strip(" ：:，,。.?？!")
            if target:
                return target
        return ""

    def _is_identity_query(self, query: str) -> bool:
        """Whether user is asking assistant identity/capability."""
        q = query.lower().strip()
        keys = [
            "你是谁", "你是啥", "你叫什么", "你能做什么", "介绍一下你",
            "who are you", "what are you", "what can you do",
        ]
        return any(k in q for k in keys)

    def _is_recent_focus_query(self, query: str) -> bool:
        """Whether query clearly focuses on very recent screen content."""
        q = query.lower()
        recent_tokens = ["刚刚", "刚才", "刚", "最近", "现在", "just now", "recently", "latest"]
        return any(tok in q for tok in recent_tokens)

    def _is_embedding_model(self, model_name: str) -> bool:
        """Whether a model is embedding-only and unsuitable for chat generation."""
        name = model_name.lower()
        embedding_tokens = ["embed", "embedding", "bge", "gte", "e5", "nomic-embed"]
        return any(tok in name for tok in embedding_tokens)

    def _is_vision_model(self, model_name: str) -> bool:
        name = model_name.lower()
        return ("vl" in name) or ("vision" in name)

    def _pick_default_chat_model(self, models: List[str]) -> str:
        """Pick a sane default generation model from available models."""
        if not models:
            return "qwen3:1.7b"
        candidates = [m for m in models if not self._is_embedding_model(m)]
        if not candidates:
            candidates = list(models)

        non_vision = [m for m in candidates if not self._is_vision_model(m)]
        pool = non_vision if non_vision else candidates
        pool.sort(key=lambda m: self._parse_model_size_b(m), reverse=True)
        return pool[0]

    def _parse_model_size_b(self, model_name: str) -> float:
        """Best-effort parse model size from model tag (supports B and M)."""
        name = model_name.lower()
        m_b = re.search(r"(\d+(?:\.\d+)?)b", name)
        if m_b:
            try:
                return float(m_b.group(1))
            except Exception:
                return 0.0
        m_m = re.search(r"(\d+(?:\.\d+)?)m", name)
        if m_m:
            try:
                return float(m_m.group(1)) / 1000.0
            except Exception:
                return 0.0
        return 0.0

    def _select_best_vision_model(self) -> str:
        """Select strongest available vision model for frame understanding."""
        if not self.available_models:
            self._load_available_models()
        vision_models = [
            m for m in self.available_models
            if self._is_vision_model(m) and not self._is_embedding_model(m)
        ]
        if vision_models:
            vision_models.sort(key=lambda m: self._parse_model_size_b(m), reverse=True)
            return vision_models[0]
        # Fallback to known default
        if "qwen2.5vl:3b" in self.available_models:
            return "qwen2.5vl:3b"
        return self.current_model or "qwen3:1.7b"

    def _ensure_model_available(self, model_name: str, allow_pull: bool = True) -> bool:
        """Ensure a model exists locally; optionally trigger `ollama pull` once."""
        if not model_name:
            return False
        if model_name in self.available_models:
            return True

        self._load_available_models()
        if model_name in self.available_models:
            return True

        if not allow_pull or not self.auto_pull_missing_models:
            return False
        if model_name in self._model_pull_attempted:
            return False
        self._model_pull_attempted.add(model_name)

        try:
            print(f"[Chat] Model {model_name} missing, trying `ollama pull`...")
            pull = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=self.max_auto_pull_seconds,
            )
            if pull.returncode != 0:
                stderr = (pull.stderr or "").strip()
                print(f"[Chat] ollama pull failed for {model_name}: {stderr[:300]}")
                return False
            self._load_available_models()
            ok = model_name in self.available_models
            print(f"[Chat] ollama pull completed for {model_name}: available={ok}")
            return ok
        except Exception as pull_err:
            print(f"[Chat] ollama pull error for {model_name}: {pull_err}")
            return False

    def _get_vision_model_candidates(self, prefer_fast: bool = False) -> List[str]:
        """Return vision model candidates (quality-first or speed-first)."""
        if not self.available_models:
            self._load_available_models()

        vision_models = [
            m for m in self.available_models
            if self._is_vision_model(m) and not self._is_embedding_model(m)
        ]
        vision_models.sort(key=lambda m: self._parse_model_size_b(m), reverse=not prefer_fast)

        preferred = ["qwen2.5vl:7b", "qwen2.5vl:3b"]
        for model in preferred:
            if model not in vision_models and self._ensure_model_available(model, allow_pull=True):
                vision_models.append(model)

        if prefer_fast:
            ordered = ["qwen2.5vl:3b", "qwen2.5vl:7b"]
        else:
            ordered = ["qwen2.5vl:7b", "qwen2.5vl:3b"]

        deduped: List[str] = []
        seen = set()
        for model in ordered + vision_models:
            if model in seen:
                continue
            seen.add(model)
            if self._is_vision_model(model):
                deduped.append(model)
        return deduped

    def _select_large_text_model(self) -> str:
        """Select a larger generation model for detailed visual-memory synthesis."""
        if not self.available_models:
            self._load_available_models()
        if not self.available_models:
            return "qwen3:1.7b"

        chat_models = [m for m in self.available_models if not self._is_embedding_model(m)]
        if not chat_models:
            return "qwen3:1.7b"

        # Prefer >=7B non-vision models; if unavailable, allow large vision models.
        non_vision = [m for m in chat_models if not self._is_vision_model(m)]
        strong_non_vision = [m for m in non_vision if self._parse_model_size_b(m) >= 7.0]
        if strong_non_vision:
            strong_non_vision.sort(key=lambda m: self._parse_model_size_b(m), reverse=True)
            return strong_non_vision[0]

        strong_any = [m for m in chat_models if self._parse_model_size_b(m) >= 7.0]
        if strong_any:
            strong_any.sort(key=lambda m: self._parse_model_size_b(m), reverse=True)
            return strong_any[0]

        strong_mid = [m for m in non_vision if self._parse_model_size_b(m) >= 3.0]
        pool = strong_mid if strong_mid else (non_vision if non_vision else chat_models)
        pool.sort(key=lambda m: self._parse_model_size_b(m), reverse=True)
        return pool[0]

    def _ollama_generate_once(
        self,
        *,
        model: str,
        prompt: str,
        images: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: float = 12.0,
    ) -> str:
        """Single Ollama generate call with normalized response handling."""
        try:
            payload: Dict[str, Any] = {
                "model": model,
                "prompt": prompt,
                "stream": False,
            }
            if images:
                payload["images"] = images
            if options:
                payload["options"] = options
            resp = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=timeout,
            )
            if resp.status_code != 200:
                return ""
            data = resp.json()
            return str(data.get("response", "")).strip()
        except Exception:
            return ""

    def _load_recent_recordings_from_db(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fallback source for recording timeline when vector memory is not ready yet."""
        try:
            from memscreen.config import get_config

            db_path = str(get_config().db_path)
            if not os.path.exists(db_path):
                return []

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT filename, timestamp, duration, frame_count
                FROM recordings
                ORDER BY rowid DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            conn.close()

            results: List[Dict[str, Any]] = []
            for row in rows:
                filename = row[0] or ""
                timestamp = row[1] or ""
                duration = row[2] or 0
                frame_count = row[3] or 0
                results.append(
                    {
                        "filename": filename,
                        "basename": os.path.basename(filename) if filename else "",
                        "timestamp": str(timestamp),
                        "duration": float(duration) if duration is not None else 0.0,
                        "frame_count": int(frame_count) if frame_count is not None else 0,
                    }
                )
            return results
        except Exception as db_err:
            print(f"[Chat] Recording DB fallback load failed: {db_err}")
            return []

    def _infer_time_window(self, query: str) -> Optional[Tuple[int, int]]:
        """Infer hour window from natural language query."""
        q = query.lower()
        if "上午" in q or "morning" in q:
            return 6, 12
        if "中午" in q or "noon" in q:
            return 11, 14
        if "下午" in q or "afternoon" in q:
            return 12, 18
        if "晚上" in q or "夜里" in q or "evening" in q or "night" in q:
            return 18, 24
        return None

    def _filter_recordings_by_time_window(
        self, rows: List[Dict[str, Any]], window: Optional[Tuple[int, int]]
    ) -> List[Dict[str, Any]]:
        if not window:
            return rows
        start_h, end_h = window
        filtered: List[Dict[str, Any]] = []
        for row in rows:
            ts_raw = row.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(str(ts_raw).replace(" ", "T"))
            except Exception:
                try:
                    ts = datetime.strptime(str(ts_raw), "%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue
            if start_h <= ts.hour < end_h:
                filtered.append(row)
        return filtered

    def _infer_query_tag_hints(self, query: str) -> List[str]:
        """Infer semantic tag hints from user query for recording-ranking."""
        q = (query or "").lower()
        hints: List[str] = []
        rules = {
            "coding": ["code", "coding", "vscode", "xcode", "python", "写代码", "代码"],
            "terminal": ["terminal", "shell", "bash", "zsh", "命令行"],
            "debugging": ["error", "exception", "bug", "报错", "异常", "错误", "失败"],
            "meeting": ["meeting", "zoom", "teams", "会议", "腾讯会议", "飞书会议"],
            "research": ["research", "paper", "arxiv", "论文", "文献", "调研"],
            "document": ["doc", "document", "pdf", "文档", "笔记"],
            "browser": ["browser", "chrome", "safari", "网页", "浏览器"],
            "chat": ["chat", "message", "slack", "discord", "微信", "消息", "沟通"],
            "design": ["design", "figma", "sketch", "photoshop", "设计"],
            "presentation": ["ppt", "slides", "keynote", "演示", "汇报"],
            "dashboard": ["dashboard", "grafana", "analytics", "看板", "统计"],
        }
        for tag, keywords in rules.items():
            if any(k in q for k in keywords):
                hints.append(tag)
        return hints

    def _extract_recording_tags_from_meta(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract normalized semantic tags from recording metadata."""
        out: List[str] = []

        raw_tags = metadata.get("tags")
        if isinstance(raw_tags, str):
            for part in raw_tags.split(","):
                p = part.strip().lower()
                if p:
                    out.append(p)
        elif isinstance(raw_tags, list):
            for part in raw_tags:
                p = str(part).strip().lower()
                if p:
                    out.append(p)

        raw_content_tags = metadata.get("content_tags_json") or metadata.get("content_tags")
        if isinstance(raw_content_tags, str):
            text = raw_content_tags.strip()
            if text:
                try:
                    arr = json.loads(text)
                    if isinstance(arr, list):
                        for x in arr:
                            p = str(x).strip().lower()
                            if p:
                                out.append(p)
                except Exception:
                    for part in text.split(","):
                        p = part.strip().lower()
                        if p:
                            out.append(p)
        elif isinstance(raw_content_tags, list):
            for x in raw_content_tags:
                p = str(x).strip().lower()
                if p:
                    out.append(p)

        normalized: List[str] = []
        seen = set()
        for t in out:
            if t.startswith("semantic:"):
                t = t[len("semantic:"):]
            if t.startswith("topic:"):
                t = t[len("topic:"):]
            if t and t not in seen:
                seen.add(t)
                normalized.append(t)
        return normalized

    def _recording_tag_match_score(self, metadata: Dict[str, Any], query: str) -> int:
        """Score how well one recording metadata matches query semantic tags."""
        hints = self._infer_query_tag_hints(query)
        if not hints:
            return 0
        tags = set(self._extract_recording_tags_from_meta(metadata))
        score = 0
        for hint in hints:
            if hint in tags:
                score += 5
        if metadata.get("analysis_status") == "ready":
            score += 1
        return score

    def _get_easyocr_reader(self):
        """Lazy-load easyocr reader for text extraction."""
        if self._easyocr_reader is not None:
            return self._easyocr_reader
        try:
            import easyocr  # type: ignore
            self._easyocr_reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
            return self._easyocr_reader
        except Exception as e:
            print(f"[Chat] easyocr unavailable: {e}")
            self._easyocr_reader = False
            return None

    def _quick_extract_video_text(self, video_path: str, dense: bool = False) -> str:
        """Extract probable title/keywords from a video using OCR on sampled frames."""
        try:
            import time
            cv2 = get_cv2()
            if cv2 is None or not os.path.exists(video_path):
                return ""

            mtime = os.path.getmtime(video_path)
            cache_key = f"{video_path}|dense={int(dense)}"
            cached = self._video_ocr_cache.get(cache_key)
            if cached and cached.get("mtime") == mtime:
                return str(cached.get("text", ""))

            reader = self._get_easyocr_reader()
            if not reader:
                return ""

            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            if total_frames <= 0:
                cap.release()
                return ""

            ratios = (
                0.08, 0.2, 0.32, 0.45, 0.58, 0.7, 0.82, 0.92
            ) if dense else (0.2, 0.5, 0.8)
            idxs = sorted({max(0, min(total_frames - 1, int(total_frames * r))) for r in ratios})
            frame_candidates: List[Tuple[int, List[str]]] = []
            start_ts = time.time()
            time_budget = 8.0 if dense else 4.5
            for idx in idxs:
                if (time.time() - start_ts) > time_budget:
                    break
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame = cap.read()
                if not ok:
                    continue
                # Downscale for OCR speed.
                h, w = frame.shape[:2]
                if w > 1400:
                    new_w = 1400
                    new_h = int(h * (new_w / w))
                    frame = cv2.resize(frame, (new_w, new_h))
                try:
                    results = reader.readtext(frame, detail=0, paragraph=True)
                except Exception:
                    results = []
                items: List[str] = []
                for t in results[: (8 if dense else 6)]:
                    t = " ".join(str(t).split())
                    if len(t) >= 4:
                        items.append(t)
                if not items:
                    continue

                informative = 0
                for text in items:
                    if re.search(r"[\u4e00-\u9fff]{2,}", text) or re.search(r"[A-Za-z]{3,}", text):
                        informative += 1
                score = sum(min(len(t), 48) for t in items) + informative * 20
                frame_candidates.append((score, items))

            cap.release()
            if not frame_candidates:
                self._video_ocr_cache[cache_key] = {"mtime": mtime, "text": ""}
                return ""

            frame_candidates.sort(key=lambda x: x[0], reverse=True)
            top_frames = frame_candidates[: (3 if dense else len(frame_candidates))]
            texts: List[str] = []
            for _, items in top_frames:
                texts.extend(items)

            # Deduplicate near-identical snippets while preserving order.
            unique_texts: List[str] = []
            seen = set()
            for t in texts:
                key = t.lower()
                if key in seen:
                    continue
                seen.add(key)
                unique_texts.append(t)
                if len(unique_texts) >= (18 if dense else 10):
                    break

            merged = " | ".join(unique_texts)
            max_len = 900 if dense else 400
            if len(merged) > max_len:
                merged = merged[:max_len] + "..."

            self._video_ocr_cache[cache_key] = {"mtime": mtime, "text": merged}
            if len(self._video_ocr_cache) > 80:
                # Remove one oldest inserted item to cap memory.
                oldest_key = next(iter(self._video_ocr_cache))
                del self._video_ocr_cache[oldest_key]
            return merged
        except Exception as e:
            print(f"[Chat] quick video OCR failed: {e}")
            return ""

    def _extract_query_keywords(self, query: str) -> List[str]:
        """Extract simple keywords for lightweight matching against OCR text."""
        q = query.lower()
        tokens = re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]{2,}", q)
        stop_tokens = {
            "什么时候", "什么", "刚刚", "刚才", "最近", "今天", "昨天",
            "上午", "下午", "中午", "晚上", "夜里", "看到", "看了", "在看", "屏幕",
            "what", "when", "today", "yesterday", "recent", "screen", "recording",
        }
        out: List[str] = []
        for tok in tokens:
            if tok in stop_tokens:
                continue
            if len(tok) < 2:
                continue
            out.append(tok)
        return out[:8]

    def _extract_ocr_snippets(
        self,
        ocr_text: str,
        query_keywords: List[str],
        max_items: int = 4,
    ) -> List[str]:
        """Pick the most relevant OCR snippets for detailed visual answer."""
        raw_parts = [p.strip() for p in ocr_text.split("|") if p.strip()]
        if not raw_parts:
            return []

        research_hints = [
            "abstract", "introduction", "method", "results", "conclusion",
            "arxiv", "doi", "paper", "pdf", "论文", "题目", "关键词",
            "福昕", "editor", "search",
        ]
        ui_hints = [
            "file", "edit", "view", "help", "terminal", "bash", "zsh", "chrome", "safari",
            "vscode", "python", "git", "error", "warning", "desktop",
        ]

        scored: List[Tuple[int, str]] = []
        seen = set()
        for part in raw_parts:
            part = " ".join(part.split())
            key = part.lower()
            if key in seen:
                continue
            seen.add(key)
            if len(part) < 4:
                continue

            # Drop very noisy OCR fragments with too many symbols.
            valid_chars = sum(ch.isalnum() or ("\u4e00" <= ch <= "\u9fff") for ch in part)
            if len(part) >= 12 and (valid_chars / max(len(part), 1)) < 0.32:
                continue
            has_chinese = bool(re.search(r"[\u4e00-\u9fff]{2,}", part))
            has_alpha_word = bool(re.search(r"[A-Za-z]{3,}", part))
            if not has_chinese and not has_alpha_word:
                continue
            noisy_alnum = bool(re.fullmatch(r"[A-Za-z0-9_.'-]+", part))
            if noisy_alnum and not has_alpha_word and len(part) < 8:
                continue

            score = 0
            if any(kw in key for kw in query_keywords if kw):
                score += 4
            if any(h in key for h in research_hints):
                score += 3
            if any(h in key for h in ui_hints):
                score += 2
            if len(part) >= 16:
                score += 1
            if any(c.isdigit() for c in part):
                score += 1

            if len(part) > 90:
                part = part[:90] + "..."
            scored.append((score, part))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [s for _, s in scored[:max_items]]
        return selected

    def _dedupe_text_items(self, items: List[str], limit: int = 8) -> List[str]:
        """Deduplicate noisy OCR/vision text fragments while preserving order."""
        out: List[str] = []
        seen = set()
        for item in items:
            text = " ".join(str(item).split()).strip()
            if len(text) < 3:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(text)
            if len(out) >= limit:
                break
        return out

    def _build_scene_overview(
        self,
        objects: List[str],
        text_items: List[str],
        scene_summaries: List[str],
    ) -> str:
        """Build a concrete overall scene description from extracted evidence."""
        merged = " ".join(text_items).lower()
        if any(k in merged for k in ["arxiv", "abstract", "pdf", "论文", "福昕"]):
            action = "画面以论文/PDF阅读为主"
        elif any(k in merged for k in ["terminal", "bash", "zsh", "ps aux", "grep"]):
            action = "画面以终端命令操作为主"
        elif any(k in merged for k in ["vscode", "python", "git", "code"]):
            action = "画面以代码编辑与开发为主"
        elif any(k in merged for k in ["chrome", "safari", "firefox", "browser"]):
            action = "画面以浏览器浏览为主"
        else:
            action = "画面以桌面窗口操作为主"

        obj_part = "、".join(objects[:5]) if objects else "窗口、菜单栏、工具栏"
        text_count = len(text_items)
        if scene_summaries:
            return f"{action}；可见元素包括{obj_part}；识别到{text_count}条文字线索。{scene_summaries[0]}"
        return f"{action}；可见元素包括{obj_part}；识别到{text_count}条文字线索。"

    def _sample_video_frames(self, video_path: str, max_samples: int = 2) -> List[Tuple[float, Any]]:
        """Sample a few frames from video for vision analysis."""
        cv2 = get_cv2()
        if cv2 is None or not os.path.exists(video_path):
            return []

        try:
            mtime = os.path.getmtime(video_path)
            cache_key = f"{video_path}:{max_samples}"
            cached = self._visual_frame_cache.get(cache_key)
            if cached and cached.get("mtime") == mtime:
                return cached.get("frames", [])

            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
            if total_frames <= 0:
                cap.release()
                return []

            ratios = [0.35, 0.75] if max_samples > 1 else [0.5]
            idxs = []
            for r in ratios[:max_samples]:
                idxs.append(max(0, min(total_frames - 1, int(total_frames * r))))
            idxs = sorted(set(idxs))

            out: List[Tuple[float, Any]] = []
            for idx in idxs:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame = cap.read()
                if not ok:
                    continue
                t_sec = (idx / fps) if fps > 0 else 0.0
                out.append((t_sec, frame))

            cap.release()
            self._visual_frame_cache[cache_key] = {"mtime": mtime, "frames": out}
            if len(self._visual_frame_cache) > 80:
                oldest_key = next(iter(self._visual_frame_cache))
                del self._visual_frame_cache[oldest_key]
            return out
        except Exception as e:
            print(f"[Chat] sample video frames failed: {e}")
            return []

    def _analyze_frame_with_vision(self, frame: Any, model_name: str) -> Dict[str, Any]:
        """Analyze one frame with vision model and return structured info."""
        cv2 = get_cv2()
        if cv2 is None:
            return {"objects": [], "visible_text": [], "summary": ""}

        try:
            import base64

            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 72])
            img_str = base64.b64encode(buffer).decode("utf-8")

            prompt = (
                "Analyze this screenshot. Return strict JSON with keys:\n"
                "objects: array of visible UI objects/icons/buttons/windows (max 8);\n"
                "visible_text: array of text snippets exactly as seen (max 10);\n"
                "summary: one concise sentence describing what is on screen.\n"
                "Do not output anything except valid JSON."
            )
            def _call(model: str, timeout_s: float) -> Dict[str, Any]:
                resp = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "images": [img_str],
                        "stream": False,
                        "options": {
                            "num_predict": 240,
                            "temperature": 0.1,
                            "top_p": 0.8,
                        },
                    },
                    timeout=timeout_s,
                )
                if resp.status_code != 200:
                    return {"objects": [], "visible_text": [], "summary": ""}
                content = (resp.json().get("response") or "").strip()
                m = re.search(r"\{[\s\S]*\}", content)
                if not m:
                    return {"objects": [], "visible_text": [], "summary": content[:120]}
                payload = json.loads(m.group(0))
                objects = payload.get("objects", []) or []
                visible_text = payload.get("visible_text", []) or []
                summary = payload.get("summary", "") or ""
                objects = [str(x).strip() for x in objects if str(x).strip()][:8]
                visible_text = [str(x).strip() for x in visible_text if str(x).strip()][:10]
                summary = str(summary).strip()[:200]
                return {"objects": objects, "visible_text": visible_text, "summary": summary}

            result = _call(model_name, timeout_s=6.0)
            if result.get("objects") or result.get("visible_text") or result.get("summary"):
                return result

            # Fallback: if large vision model is slow/unavailable, try a lighter vision model once.
            if not self.available_models:
                self._load_available_models()
            backups = [
                m for m in self.available_models
                if self._is_vision_model(m) and not self._is_embedding_model(m) and m != model_name
            ]
            backups.sort(key=lambda m: self._parse_model_size_b(m))
            if backups:
                try:
                    return _call(backups[0], timeout_s=4.0)
                except Exception:
                    pass
            return {"objects": [], "visible_text": [], "summary": ""}
        except Exception as e:
            print(f"[Chat] vision frame analysis failed: {e}")
            return {"objects": [], "visible_text": [], "summary": ""}

    def _infer_objects_from_text(self, snippets: List[str]) -> List[str]:
        """Infer UI objects from OCR snippets when vision object extraction is missing."""
        merged = " ".join(snippets).lower()
        mapping = [
            (["pdf", "福昕", "foxit"], "PDF文档窗口"),
            (["search", "查找"], "搜索栏"),
            (["terminal", "bash", "zsh", "shell", "ps aux", "grep"], "终端窗口"),
            (["vscode", "code"], "代码编辑器"),
            (["chrome", "safari", "firefox", "browser"], "浏览器窗口"),
            (["wecom", "企业微信"], "通讯应用窗口"),
            (["desktop"], "桌面"),
            (["flutter", "memscreen"], "应用主窗口"),
            (["file", "edit", "view", "help", "编辑", "视图", "帮助"], "菜单栏"),
            (["tool", "toolbar", "工具"], "工具栏按钮"),
            (["page", "页", "缩放"], "页面视图区域"),
        ]
        out: List[str] = []
        for keys, label in mapping:
            if any(k in merged for k in keys):
                out.append(label)
            if len(out) >= 6:
                break
        return out

    def _extract_specific_recording_hint(self, query: str) -> Dict[str, str]:
        """Extract explicit filename/timestamp hints from query."""
        q = query.strip()
        hint: Dict[str, str] = {}
        file_m = re.search(r"(recording_\d{8}_\d{6}\.mp4)", q, flags=re.IGNORECASE)
        if file_m:
            hint["basename"] = file_m.group(1)
        ts_m = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", q)
        if ts_m:
            hint["timestamp"] = ts_m.group(1)
        return hint

    def _extract_frame_timeline_text(
        self,
        video_path: str,
        *,
        max_points: int = 4,
    ) -> List[Dict[str, Any]]:
        """Extract OCR snippets with in-video offsets for stronger evidence."""
        try:
            cv2 = get_cv2()
            if cv2 is None or not os.path.exists(video_path):
                return []
            reader = self._get_easyocr_reader()
            if not reader:
                return []

            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
            if total_frames <= 0:
                cap.release()
                return []

            if total_frames <= 8:
                idxs = list(range(total_frames))
            else:
                ratios = [0.08, 0.3, 0.55, 0.82]
                idxs = sorted({max(0, min(total_frames - 1, int(total_frames * r))) for r in ratios})

            rows: List[Dict[str, Any]] = []
            for idx in idxs:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame = cap.read()
                if not ok:
                    continue
                h, w = frame.shape[:2]
                if w > 1400:
                    new_w = 1400
                    new_h = int(h * (new_w / w))
                    frame = cv2.resize(frame, (new_w, new_h))
                try:
                    results = reader.readtext(frame, detail=0, paragraph=True)
                except Exception:
                    results = []
                items = []
                for item in results[:6]:
                    txt = " ".join(str(item).split())
                    if len(txt) >= 4:
                        items.append(txt)
                if not items:
                    continue
                picked = self._extract_ocr_snippets(" | ".join(items), [], max_items=2)
                if not picked:
                    picked = items[:2]
                text = "；".join(picked)
                if not text:
                    continue
                t_sec = (idx / fps) if fps > 0 else 0.0
                rows.append(
                    {
                        "frame_index": len(rows),
                        "source_frame": int(idx),
                        "time_offset": round(float(t_sec), 2),
                        "text": text,
                    }
                )
                if len(rows) >= max_points:
                    break
            cap.release()
            return rows
        except Exception as e:
            print(f"[Chat] extract frame timeline text failed: {e}")
            return []

    def _grid_location_label(self, x: float, y: float, width: float, height: float) -> str:
        """Map a point to a simple 3x3 screen-grid location label."""
        if width <= 0 or height <= 0:
            return "未知"
        col = 0 if x < (width / 3.0) else (1 if x < (2 * width / 3.0) else 2)
        row = 0 if y < (height / 3.0) else (1 if y < (2 * height / 3.0) else 2)
        labels = {
            (0, 0): "左上",
            (1, 0): "上方",
            (2, 0): "右上",
            (0, 1): "左侧",
            (1, 1): "中间",
            (2, 1): "右侧",
            (0, 2): "左下",
            (1, 2): "下方",
            (2, 2): "右下",
        }
        return labels.get((col, row), "未知")

    def _normalize_location_label(self, raw: str) -> str:
        """Normalize free-form location labels to compact Chinese tags."""
        text = " ".join(str(raw).lower().split())
        mappings = [
            (["top-left", "left top", "upper left", "左上"], "左上"),
            (["top-center", "top center", "upper center", "上方"], "上方"),
            (["top-right", "right top", "upper right", "右上"], "右上"),
            (["middle-left", "center-left", "left center", "左侧"], "左侧"),
            (["center", "middle", "中间", "中央"], "中间"),
            (["middle-right", "center-right", "right center", "右侧"], "右侧"),
            (["bottom-left", "lower left", "左下"], "左下"),
            (["bottom-center", "bottom center", "lower center", "下方"], "下方"),
            (["bottom-right", "lower right", "右下"], "右下"),
        ]
        for keys, label in mappings:
            if any(k in text for k in keys):
                return label
        return "未知"

    def _extract_frame_ocr_blocks(self, frame: Any, max_items: int = 10) -> List[Dict[str, Any]]:
        """Extract OCR blocks with approximate on-screen location."""
        cv2 = get_cv2()
        reader = self._get_easyocr_reader()
        if cv2 is None or reader is None or frame is None:
            return []

        try:
            h, w = frame.shape[:2]
            img = frame
            if w > 1600:
                new_w = 1600
                new_h = int(h * (new_w / w))
                img = cv2.resize(frame, (new_w, new_h))
                h, w = img.shape[:2]

            try:
                # detail=1 provides bbox + confidence for localization.
                raw_rows = reader.readtext(img, detail=1, paragraph=False)
            except Exception:
                raw_rows = []

            blocks: List[Dict[str, Any]] = []
            for row in raw_rows:
                if not isinstance(row, (list, tuple)) or len(row) < 2:
                    continue
                bbox = row[0]
                text = " ".join(str(row[1]).split())
                conf = float(row[2]) if len(row) > 2 else 0.0
                if len(text) < 2:
                    continue
                if not re.search(r"[A-Za-z0-9\u4e00-\u9fff]", text):
                    continue

                xs = []
                ys = []
                if isinstance(bbox, (list, tuple)):
                    for point in bbox:
                        if isinstance(point, (list, tuple)) and len(point) >= 2:
                            xs.append(float(point[0]))
                            ys.append(float(point[1]))
                cx = (sum(xs) / len(xs)) if xs else (w / 2.0)
                cy = (sum(ys) / len(ys)) if ys else (h / 2.0)
                loc = self._grid_location_label(cx, cy, w, h)
                blocks.append(
                    {
                        "text": text[:140],
                        "confidence": round(conf, 3),
                        "location": loc,
                    }
                )

            if not blocks:
                try:
                    fallback_rows = reader.readtext(img, detail=0, paragraph=True)
                except Exception:
                    fallback_rows = []
                for item in fallback_rows[:max_items]:
                    text = " ".join(str(item).split())
                    if len(text) >= 2:
                        blocks.append({"text": text[:140], "confidence": 0.0, "location": "未知"})

            blocks.sort(key=lambda b: (float(b.get("confidence", 0.0)), len(str(b.get("text", "")))), reverse=True)
            seen = set()
            out: List[Dict[str, Any]] = []
            for block in blocks:
                key = str(block.get("text", "")).lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(block)
                if len(out) >= max_items:
                    break
            return out
        except Exception as e:
            print(f"[Chat] frame OCR blocks extraction failed: {e}")
            return []

    def _sample_video_frames_dense(self, video_path: str, max_samples: int = 6) -> List[Dict[str, Any]]:
        """Sample frames for harness-style multi-step visual analysis."""
        cv2 = get_cv2()
        if cv2 is None or not os.path.exists(video_path):
            return []
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
            if total_frames <= 0:
                cap.release()
                return []

            if total_frames <= max_samples:
                idxs = list(range(total_frames))
            else:
                ratios = [0.02, 0.14, 0.28, 0.42, 0.56, 0.7, 0.84, 0.96]
                idxs = [max(0, min(total_frames - 1, int(total_frames * r))) for r in ratios]
                idxs = sorted(set(idxs))[:max_samples]

            out: List[Dict[str, Any]] = []
            for idx in idxs:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame = cap.read()
                if not ok:
                    continue
                out.append(
                    {
                        "source_frame": int(idx),
                        "time_offset": round((idx / fps) if fps > 0 else 0.0, 2),
                        "frame": frame,
                    }
                )
            cap.release()
            return out
        except Exception as e:
            print(f"[Chat] dense frame sampling failed: {e}")
            return []

    def _parse_json_payload(self, raw_text: str) -> Dict[str, Any]:
        """Extract first JSON object from model text."""
        if not raw_text:
            return {}
        try:
            direct = json.loads(raw_text)
            if isinstance(direct, dict):
                return direct
        except Exception:
            pass
        m = re.search(r"\{[\s\S]*\}", raw_text)
        if not m:
            return {}
        try:
            parsed = json.loads(m.group(0))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {}
        return {}

    def _analyze_frame_with_vision_harness(
        self,
        frame: Any,
        query: str,
        model_candidates: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run one harness chain step: structured frame understanding with model fallback."""
        cv2 = get_cv2()
        if cv2 is None or frame is None:
            return {"objects": [], "visible_text": [], "activity": "", "model": ""}
        try:
            import base64

            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 72])
            img_str = base64.b64encode(buffer).decode("utf-8")
            candidates = model_candidates or self._get_vision_model_candidates()
            if not candidates:
                return {"objects": [], "visible_text": [], "activity": "", "model": ""}

            prompt = (
                "You are a visual evidence extractor for a long-running agent harness.\n"
                f"User query: {query}\n"
                "Return strict JSON only with keys:\n"
                "objects: array of {name, location};\n"
                "visible_text: array of {text, location};\n"
                "activity: one concise sentence.\n"
                "Location must be one of: top-left, top-center, top-right, middle-left, center, middle-right, "
                "bottom-left, bottom-center, bottom-right.\n"
                "Only include items clearly visible in this frame. No markdown."
            )

            for model in candidates:
                if not self._ensure_model_available(model, allow_pull=True):
                    continue
                content = self._ollama_generate_once(
                    model=model,
                    prompt=prompt,
                    images=[img_str],
                    options={
                        "num_predict": 260,
                        "temperature": 0.1,
                        "top_p": 0.8,
                        "top_k": 20,
                    },
                    timeout=12.0 if self._parse_model_size_b(model) >= 7.0 else 8.0,
                )
                payload = self._parse_json_payload(content)
                if not payload:
                    continue

                objects_raw = payload.get("objects", []) or []
                text_raw = payload.get("visible_text", []) or []
                objects: List[Dict[str, str]] = []
                visible_text: List[Dict[str, str]] = []

                for item in objects_raw[:10]:
                    if isinstance(item, dict):
                        name = " ".join(str(item.get("name", "")).split())
                        loc = self._normalize_location_label(item.get("location", ""))
                    else:
                        name = " ".join(str(item).split())
                        loc = "未知"
                    if name:
                        objects.append({"name": name[:80], "location": loc})

                for item in text_raw[:12]:
                    if isinstance(item, dict):
                        text = " ".join(str(item.get("text", "")).split())
                        loc = self._normalize_location_label(item.get("location", ""))
                    else:
                        text = " ".join(str(item).split())
                        loc = "未知"
                    if len(text) >= 2:
                        visible_text.append({"text": text[:120], "location": loc})

                activity = " ".join(str(payload.get("activity", "")).split())[:200]
                if objects or visible_text or activity:
                    return {
                        "objects": objects[:8],
                        "visible_text": visible_text[:10],
                        "activity": activity,
                        "model": model,
                    }
            return {"objects": [], "visible_text": [], "activity": "", "model": ""}
        except Exception as e:
            print(f"[Chat] harness vision analysis failed: {e}")
            return {"objects": [], "visible_text": [], "activity": "", "model": ""}

    def _target_text_match(self, target: str, candidate: str) -> bool:
        """Loose match for user-mentioned text/object target."""
        t = " ".join(str(target).lower().split())
        c = " ".join(str(candidate).lower().split())
        if not t or not c:
            return False
        if t in c:
            return True
        toks = re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]{1,}", t)
        toks = [tok for tok in toks if len(tok) >= 2]
        if not toks:
            return False
        hits = sum(1 for tok in toks if tok in c)
        return hits >= max(1, min(2, len(toks)))

    def _extract_target_hits_from_frames(
        self,
        target_phrase: str,
        frame_rows: List[Dict[str, Any]],
        max_hits: int = 8,
    ) -> List[Dict[str, Any]]:
        """Find where a specific text/object appeared across frame evidence."""
        if not target_phrase:
            return []
        hits: List[Dict[str, Any]] = []
        seen = set()
        for row in frame_rows:
            frame_index = int(row.get("frame_index", 0))
            offset = float(row.get("time_offset", 0.0))

            for block in row.get("ocr_blocks", []) or []:
                text = str(block.get("text", ""))
                if not self._target_text_match(target_phrase, text):
                    continue
                key = (frame_index, text.lower(), str(block.get("location", "未知")))
                if key in seen:
                    continue
                seen.add(key)
                hits.append(
                    {
                        "frame_index": frame_index,
                        "time_offset": offset,
                        "location": block.get("location", "未知"),
                        "evidence": text[:120],
                        "source": "ocr",
                    }
                )

            for item in row.get("vision_text_entries", []) or []:
                text = str(item.get("text", ""))
                if not self._target_text_match(target_phrase, text):
                    continue
                key = (frame_index, text.lower(), str(item.get("location", "未知")))
                if key in seen:
                    continue
                seen.add(key)
                hits.append(
                    {
                        "frame_index": frame_index,
                        "time_offset": offset,
                        "location": item.get("location", "未知"),
                        "evidence": text[:120],
                        "source": "vision_text",
                    }
                )

            for item in row.get("object_entries", []) or []:
                name = str(item.get("name", ""))
                if not self._target_text_match(target_phrase, name):
                    continue
                key = (frame_index, name.lower(), str(item.get("location", "未知")))
                if key in seen:
                    continue
                seen.add(key)
                hits.append(
                    {
                        "frame_index": frame_index,
                        "time_offset": offset,
                        "location": item.get("location", "未知"),
                        "evidence": name[:120],
                        "source": "object",
                    }
                )

            if len(hits) >= max_hits:
                break
        hits.sort(key=lambda x: (x.get("time_offset", 0.0), x.get("frame_index", 0)))
        return hits[:max_hits]

    def _update_recording_memory_from_harness(
        self,
        video_row: Dict[str, Any],
        frame_rows: List[Dict[str, Any]],
        overview: str,
    ) -> None:
        """Push richer frame timeline back into memory for future grounded QA."""
        if not self.memory_system or not frame_rows:
            return
        try:
            filename = str(video_row.get("filename", ""))
            basename = os.path.basename(filename)
            if not basename:
                return

            result = self.memory_system.search(
                query=basename,
                user_id="default_user",
                filters={"type": "screen_recording"},
                limit=8,
                threshold=0.0,
            )
            rows: List[Dict[str, Any]] = []
            if isinstance(result, dict):
                rows = result.get("results", []) or []
            elif isinstance(result, list):
                rows = result
            if not rows:
                return

            target_item = None
            for row in rows:
                meta = row.get("metadata", {}) if isinstance(row, dict) else {}
                row_file = os.path.basename(str(meta.get("filename", "")))
                if row_file == basename:
                    target_item = row
                    break
            if not target_item:
                return

            memory_id = str(target_item.get("id", "")).strip()
            if not memory_id:
                return
            vector_store = getattr(self.memory_system, "vector_store", None)
            embedding_model = getattr(self.memory_system, "embedding_model", None)
            if vector_store is None or embedding_model is None:
                return
            existing = vector_store.get(vector_id=memory_id)
            if existing is None:
                return

            compact_timeline = []
            frame_json_rows = []
            text_pool = []
            for row in frame_rows[:8]:
                offset = float(row.get("time_offset", 0.0))
                row_text = " ".join(str(row.get("text", "")).split())[:200]
                if row_text:
                    compact_timeline.append(f"+{offset:.2f}s:{row_text}")
                    text_pool.append(row_text)
                frame_json_rows.append(
                    {
                        "frame_index": int(row.get("frame_index", 0)),
                        "source_frame": int(row.get("source_frame", 0)),
                        "time_offset": offset,
                        "text": row_text,
                        "objects": row.get("objects", [])[:8],
                    }
                )

            timeline_text = " | ".join(compact_timeline)
            ocr_text = " | ".join(self._dedupe_text_items(text_pool, limit=10))
            payload = dict(getattr(existing, "payload", {}) or {})
            payload.update(
                {
                    "content_description": overview[:300],
                    "timeline_text": timeline_text[:1800],
                    "frame_details_json": json.dumps(frame_json_rows, ensure_ascii=False),
                    "analysis_status": "ready",
                    "ocr_text": ocr_text[:1500],
                    "category": "screen_recording",
                    "tags": "screen_recording,timeline_ready,ocr_enriched,harness_v1",
                    "updated_at": datetime.now().isoformat(),
                }
            )

            memory_text = (
                f"Screen recording {basename} enriched by visual harness.\n"
                f"Timeline: {timeline_text}\n"
                f"Overview: {overview}"
            ).strip()
            payload["data"] = memory_text
            payload["hash"] = hashlib.md5(memory_text.encode()).hexdigest()

            embeddings = embedding_model.embed(memory_text, "update")
            vector_store.update(vector_id=memory_id, vector=embeddings, payload=payload)
        except Exception as e:
            print(f"[Chat] update memory from harness failed: {e}")

    def _collect_visual_harness_evidence(
        self,
        query: str,
        max_videos: int = 2,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Run a multi-stage harness chain and return structured visual evidence."""
        import time

        rows = self._load_recent_recordings_from_db(limit=10)
        stats = {"candidate_videos": 0, "analyzed_videos": 0, "analyzed_frames": 0}
        if not rows:
            return [], stats

        specific_hint = self._extract_specific_recording_hint(query)
        target_phrase = self._extract_visual_target_phrase(query)
        paper_like = any(k in query.lower() for k in ["论文", "paper", "pdf", "arxiv", "title", "abstract"])
        location_query = self._is_visual_location_query(query)
        window = self._infer_time_window(query)
        candidate_rows = self._filter_recordings_by_time_window(rows, window) or rows

        if specific_hint:
            matched: List[Dict[str, Any]] = []
            for row in rows:
                basename = str(row.get("basename", ""))
                ts = str(row.get("timestamp", ""))
                if specific_hint.get("basename") and basename == specific_hint["basename"]:
                    matched.append(row)
                    continue
                if specific_hint.get("timestamp") and ts.startswith(specific_hint["timestamp"]):
                    matched.append(row)
            if matched:
                candidate_rows = matched[:1]
        else:
            if paper_like:
                candidate_rows = sorted(candidate_rows, key=lambda r: float(r.get("duration", 0.0)), reverse=True)
            else:
                candidate_rows = sorted(candidate_rows, key=lambda r: str(r.get("timestamp", "")), reverse=True)

        # Keep online latency bounded (API timeout=180s). Broad queries analyze fewer videos.
        if specific_hint:
            max_videos = 1
        elif not location_query and not target_phrase:
            max_videos = min(max_videos, 1)
        candidate_rows = candidate_rows[:max_videos]
        stats["candidate_videos"] = len(candidate_rows)
        prefer_fast_vision = not (specific_hint or location_query or target_phrase)
        vision_candidates = self._get_vision_model_candidates(prefer_fast=prefer_fast_vision)
        start_ts = time.time()
        max_elapsed = 120.0 if specific_hint else 75.0

        evidence_list: List[Dict[str, Any]] = []
        for vidx, row in enumerate(candidate_rows):
            if (time.time() - start_ts) > max_elapsed:
                print("[Chat] visual harness time budget reached, stop scanning more videos")
                break
            video_path = str(row.get("filename", ""))
            if not video_path:
                continue
            dense = bool(specific_hint) or vidx == 0
            frame_samples = self._sample_video_frames_dense(
                video_path,
                max_samples=6 if specific_hint else (4 if (location_query or target_phrase) else 3),
            )
            if not frame_samples:
                continue

            frame_rows: List[Dict[str, Any]] = []
            objects_pool: List[str] = []
            object_entries_pool: List[Dict[str, str]] = []
            text_pool: List[str] = []
            summary_pool: List[str] = []
            vision_frame_budget = 3 if specific_hint else (2 if (location_query or target_phrase) else 0)

            for fidx, frame_info in enumerate(frame_samples):
                if (time.time() - start_ts) > max_elapsed:
                    print("[Chat] visual harness frame budget timeout, stop scanning frames")
                    break
                frame = frame_info.get("frame")
                ocr_blocks = self._extract_frame_ocr_blocks(frame, max_items=8)
                stats["analyzed_frames"] += 1

                vision_payload = {"objects": [], "visible_text": [], "activity": "", "model": ""}
                if fidx < vision_frame_budget:
                    vision_payload = self._analyze_frame_with_vision_harness(
                        frame,
                        query=query,
                        model_candidates=vision_candidates,
                    )

                ocr_texts = [str(b.get("text", "")) for b in ocr_blocks if str(b.get("text", ""))]
                vis_text_entries = vision_payload.get("visible_text", []) or []
                vis_texts = [str(item.get("text", "")) for item in vis_text_entries if str(item.get("text", ""))]
                object_entries = vision_payload.get("objects", []) or []
                object_names = [str(item.get("name", "")) for item in object_entries if str(item.get("name", ""))]

                merged_text = self._dedupe_text_items(ocr_texts + vis_texts, limit=6)
                text_line = "；".join(merged_text[:3])
                frame_rows.append(
                    {
                        "frame_index": fidx,
                        "source_frame": int(frame_info.get("source_frame", 0)),
                        "time_offset": float(frame_info.get("time_offset", 0.0)),
                        "text": text_line,
                        "ocr_blocks": ocr_blocks,
                        "vision_text_entries": vis_text_entries,
                        "object_entries": object_entries,
                        "objects": object_names[:8],
                        "summary": vision_payload.get("activity", ""),
                        "model": vision_payload.get("model", ""),
                    }
                )

                for item in merged_text:
                    text_pool.append(item)
                for obj in object_names:
                    if obj and obj not in objects_pool:
                        objects_pool.append(obj)
                for obj in object_entries:
                    if isinstance(obj, dict):
                        object_entries_pool.append(
                            {
                                "name": str(obj.get("name", ""))[:80],
                                "location": str(obj.get("location", "未知")),
                            }
                        )
                summary = str(vision_payload.get("activity", "")).strip()
                if summary:
                    summary_pool.append(f"+{float(frame_info.get('time_offset', 0.0)):.1f}s: {summary}")

            if not frame_rows:
                continue

            text_items = self._dedupe_text_items(text_pool, limit=12)
            if not objects_pool and text_items:
                objects_pool = self._infer_objects_from_text(text_items)
            scene_overview = self._build_scene_overview(objects_pool, text_items, summary_pool)

            compact_rows = []
            for item in frame_rows[:6]:
                compact_rows.append(
                    {
                        "frame_index": int(item.get("frame_index", 0)),
                        "source_frame": int(item.get("source_frame", 0)),
                        "time_offset": round(float(item.get("time_offset", 0.0)), 2),
                        "text": str(item.get("text", "")),
                    }
                )

            target_hits = self._extract_target_hits_from_frames(target_phrase, frame_rows, max_hits=10)
            evidence_list.append(
                {
                    "timestamp": row.get("timestamp", "Unknown time"),
                    "basename": row.get("basename", ""),
                    "filename": row.get("filename", ""),
                    "duration": row.get("duration", 0.0),
                    "ocr_snippets": text_items,
                    "objects": objects_pool[:10],
                    "object_entries": object_entries_pool[:10],
                    "scene_summaries": summary_pool[:4],
                    "overall_description": scene_overview,
                    "frame_timeline_text": compact_rows,
                    "frame_rows": frame_rows,
                    "target_hits": target_hits,
                }
            )

            # Keep memory timeline fresh with richer OCR/visual details.
            if dense:
                self._update_recording_memory_from_harness(row, frame_rows, scene_overview)

        stats["analyzed_videos"] = len(evidence_list)
        return evidence_list, stats

    def _format_visual_harness_response(
        self,
        query: str,
        evidence_list: List[Dict[str, Any]],
        memory_context: str = "",
    ) -> str:
        """Render harness evidence into deterministic, evidence-first answer."""
        if not evidence_list:
            return (
                "没有找到可用录屏来回答这个视觉问题。\n"
                "建议：先录制一次包含目标画面的操作，再重新提问。"
            )

        target_phrase = self._extract_visual_target_phrase(query)
        lines = ["我按“检索视频→逐帧抽取→OCR/视觉交叉验证”的链路整理了证据："]
        main_rows: List[List[str]] = []
        for ev in evidence_list:
            text_items = ev.get("ocr_snippets", []) or []
            objects = ev.get("objects", []) or []
            overall = str(ev.get("overall_description", "")).strip()
            main_rows.append([
                str(ev.get("timestamp", "")),
                str(ev.get("basename", "")),
                f"{float(ev.get('duration', 0.0)):.1f}s",
                "；".join(text_items[:6]) if text_items else "未识别到清晰文本",
                "、".join(objects[:6]) if objects else "",
                overall[:140],
            ])
        lines.append(self._build_markdown_table(["时间", "视频", "时长", "可见文字", "主要元素", "整体描述"], main_rows))

        for ev in evidence_list:
            hits = ev.get("target_hits", []) or []
            if target_phrase:
                if hits:
                    lines.append(f"   命中位置（目标：{target_phrase}）：")
                    hit_rows: List[List[str]] = []
                    for hit in hits[:8]:
                        hit_rows.append([
                            f"frame{int(hit.get('frame_index', 0))}",
                            f"+{float(hit.get('time_offset', 0.0)):.1f}s",
                            str(hit.get('location', '未知')),
                            str(hit.get('evidence', ''))[:120],
                        ])
                    lines.append(self._build_markdown_table(["帧", "偏移", "位置", "证据"], hit_rows))
                else:
                    lines.append(f"   命中位置（目标：{target_phrase}）：当前视频未命中")
            else:
                frame_rows = ev.get("frame_timeline_text", []) or []
                if frame_rows:
                    fr_rows: List[List[str]] = []
                    for row in frame_rows[:6]:
                        fr_rows.append([
                            f"frame{int(row.get('frame_index', 0))}",
                            f"+{float(row.get('time_offset', 0.0)):.1f}s",
                            str(row.get('text', ''))[:140],
                        ])
                    lines.append(self._build_markdown_table(["帧", "偏移", "证据文字"], fr_rows))

        memory_lines = self._extract_memory_evidence_lines(memory_context, limit=6)
        if not memory_lines:
            memory_lines = self._collect_memory_recording_evidence(query, limit=4)
        if memory_lines:
            lines.append("\n记忆系统证据（Memory）：")
            lines.append(self._build_memory_evidence_table(memory_lines[:6]))

        lines.append("\n建议：")
        if target_phrase:
            lines.append("1. 先打开上述视频定位命中时间点，确认该文字/物体是否连续出现。")
            lines.append("2. 如果要更精准，请补充完整关键词（如完整标题、按钮名或报错词）。")
        else:
            lines.append("1. 打开同一视频按上述逐帧时间点复核。")
            lines.append("2. 继续问“这个词/物体出现在哪一帧”，我会返回更精确位置证据。")
        return "\n".join(lines)

    def _build_markdown_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Build a simple markdown table block."""
        if not headers:
            return ""
        header_line = "| " + " | ".join(headers) + " |"
        separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
        body_lines = []
        for row in rows:
            safe_row = [str(c).replace("\n", " ").replace("|", "/") for c in row]
            if len(safe_row) < len(headers):
                safe_row.extend([""] * (len(headers) - len(safe_row)))
            body_lines.append("| " + " | ".join(safe_row[: len(headers)]) + " |")
        if not body_lines:
            body_lines.append("| " + " | ".join([""] * len(headers)) + " |")
        return "\n".join([header_line, separator_line] + body_lines)

    def _build_memory_evidence_table(self, memory_lines: List[str]) -> str:
        """Convert compact memory evidence lines to markdown table for readability."""
        rows: List[List[str]] = []
        for line in memory_lines:
            text = str(line).strip()
            if text.startswith("- "):
                text = text[2:].strip()
            # Expected format:
            # 2026-... basename.mp4：hint...
            when = ""
            file_name = ""
            evidence = text
            try:
                head, tail = text.split("：", 1)
                evidence = tail.strip()
                parts = head.strip().split(" ")
                if len(parts) >= 3:
                    when = " ".join(parts[:2]).strip()
                    file_name = " ".join(parts[2:]).strip()
                elif len(parts) == 2:
                    when = parts[0].strip()
                    file_name = parts[1].strip()
                else:
                    file_name = head.strip()
            except ValueError:
                pass
            rows.append([when, file_name, evidence])
        return self._build_markdown_table(["时间", "录屏文件", "证据摘要"], rows)

    def _collect_visual_detail_evidence(self, query: str, max_videos: int = 2) -> List[Dict[str, Any]]:
        """Collect rich visual evidence from recent recordings."""
        rows = self._load_recent_recordings_from_db(limit=8)
        if not rows:
            return []

        window = self._infer_time_window(query)
        filtered = self._filter_recordings_by_time_window(rows, window)
        recent_focus = self._is_recent_focus_query(query)
        paper_like = any(k in query.lower() for k in ["论文", "paper", "pdf", "arxiv", "title", "abstract"])

        specific_hint = self._extract_specific_recording_hint(query)
        candidate_rows = filtered if filtered else rows
        if specific_hint:
            matched: List[Dict[str, Any]] = []
            for row in rows:
                basename = str(row.get("basename", ""))
                ts = str(row.get("timestamp", ""))
                if specific_hint.get("basename") and basename == specific_hint["basename"]:
                    matched.append(row)
                    continue
                if specific_hint.get("timestamp") and ts.startswith(specific_hint["timestamp"]):
                    matched.append(row)
            if matched:
                # When user points to exact video/timestamp, prioritize only that target.
                candidate_rows = matched[:1]

        if recent_focus:
            def _row_time_key(row: Dict[str, Any]) -> float:
                ts = self._parse_memory_timestamp({"timestamp": row.get("timestamp", "")})
                return ts.timestamp() if ts else 0.0
            candidate_rows = sorted(candidate_rows, key=_row_time_key, reverse=True)
        elif paper_like:
            candidate_rows = sorted(candidate_rows, key=lambda r: float(r.get("duration", 0.0)), reverse=True)
        else:
            # Blend recency and readability: prefer recent first, then duration.
            candidate_rows = sorted(
                candidate_rows,
                key=lambda r: (str(r.get("timestamp", "")), float(r.get("duration", 0.0))),
                reverse=True,
            )

        candidate_rows = candidate_rows[:max_videos]
        q_keywords = self._extract_query_keywords(query)
        vision_model = self._select_best_vision_model()

        evidence_list: List[Dict[str, Any]] = []
        for idx, row in enumerate(candidate_rows):
            video_path = row.get("filename", "")
            force_dense = bool(specific_hint) or (idx == 0)
            ocr_text = self._quick_extract_video_text(video_path, dense=force_dense)
            ocr_snippets = self._extract_ocr_snippets(ocr_text, q_keywords, max_items=8)
            frame_timeline_text = self._extract_frame_timeline_text(
                video_path,
                max_points=4 if force_dense else 2,
            )

            frame_infos = self._sample_video_frames(video_path, max_samples=1)
            obj_set: List[str] = []
            txt_set: List[str] = []
            scene_summaries: List[str] = []
            for t_sec, frame in frame_infos:
                vis = self._analyze_frame_with_vision(frame, vision_model)
                for o in vis.get("objects", []):
                    if o and o not in obj_set:
                        obj_set.append(o)
                for t in vis.get("visible_text", []):
                    t = " ".join(str(t).split())
                    if t and t not in txt_set:
                        txt_set.append(t)
                summary = vis.get("summary", "")
                if summary:
                    scene_summaries.append(f"+{t_sec:.1f}s: {summary}")

            if not obj_set and ocr_snippets:
                obj_set = self._infer_objects_from_text(ocr_snippets)

            text_items = self._dedupe_text_items(ocr_snippets + txt_set, limit=10)
            scene_overview = self._build_scene_overview(obj_set, text_items, scene_summaries)

            evidence_list.append(
                {
                    "timestamp": row.get("timestamp", "Unknown time"),
                    "basename": row.get("basename", ""),
                    "duration": row.get("duration", 0.0),
                    "ocr_snippets": text_items,
                    "objects": obj_set[:8],
                    "visible_text": txt_set[:8],
                    "scene_summaries": scene_summaries[:3],
                    "overall_description": scene_overview,
                    "frame_timeline_text": frame_timeline_text,
                }
            )
        return evidence_list

    def _format_visual_detail_fallback(self, query: str, evidence_list: List[Dict[str, Any]]) -> str:
        """Deterministic detailed answer fallback."""
        if not evidence_list:
            return (
                "没有找到可用录屏来回答这个视觉细节问题。\n"
                "建议：先录制一次包含目标画面的操作，再重新提问。"
            )

        specific_hint = self._extract_specific_recording_hint(query)
        frame_mode = bool(specific_hint)
        lines = ["我基于最近录屏给你整理了可核验的画面证据："]
        main_rows: List[List[str]] = []
        for i, ev in enumerate(evidence_list, 1):
            text_items = ev.get("ocr_snippets", []) or ev.get("visible_text", [])
            objs = ev.get("objects", [])
            overall = ev.get("overall_description", "")
            if not overall and ev.get("scene_summaries", []):
                overall = " | ".join((ev.get("scene_summaries", []) or [])[:2])
            main_rows.append([
                str(ev.get('timestamp', '')),
                str(ev.get('basename', '')),
                f"{float(ev.get('duration', 0.0)):.1f}s",
                "；".join(text_items[:6]) if text_items else "未识别到清晰文本",
                "、".join(objs[:8]) if objs else "窗口、工具栏、文档区域（粗略）",
                str(overall)[:140],
            ])
        lines.append(self._build_markdown_table(["时间", "视频", "时长", "可见文字", "主要元素", "整体描述"], main_rows))

        for ev in evidence_list:
            frame_rows = ev.get("frame_timeline_text", []) or []
            if frame_rows and frame_mode:
                fr_rows: List[List[str]] = []
                for row in frame_rows[:4]:
                    fr_rows.append([
                        f"frame{int(row.get('frame_index', 0))}",
                        f"+{float(row.get('time_offset', 0.0)):.1f}s",
                        str(row.get('text', ''))[:140],
                    ])
                lines.append(self._build_markdown_table(["帧", "偏移", "证据文字"], fr_rows))
            elif frame_rows:
                compact = []
                for row in frame_rows[:3]:
                    compact.append(f"+{float(row.get('time_offset', 0.0)):.1f}s {row.get('text', '')}")
                if compact:
                    lines.append("   关键帧内容：" + " | ".join(compact))

        lines.append("建议：")
        lines.append("1. 打开上述视频并定位同一时间点复核。")
        lines.append("2. 如果需要更准确结果，请补充“应用名/论文关键词/报错词”。")
        return "\n".join(lines)

    def _extract_memory_evidence_lines(self, context: str, limit: int = 6) -> List[str]:
        """Extract concise evidence lines from tiered memory context."""
        if not context:
            return []
        lines: List[str] = []
        for raw in context.splitlines():
            line = raw.strip()
            if not line.startswith("- "):
                continue
            if len(line) > 220:
                line = line[:220] + "..."
            lines.append(line)
            if len(lines) >= limit:
                break
        return lines

    def _collect_memory_recording_evidence(self, query: str, limit: int = 4) -> List[str]:
        """Pull recording evidence directly from memory system for visual queries."""
        if not self.memory_system:
            return []
        try:
            specific_hint = self._extract_specific_recording_hint(query)
            result = self.memory_system.search(
                query=query,
                user_id="default_user",
                filters={"type": "screen_recording"},
                limit=limit,
                threshold=0.0,
            )
            rows: List[Dict[str, Any]] = []
            if isinstance(result, dict):
                rows = result.get("results", []) or []
            elif isinstance(result, list):
                rows = result

            def _rank(item: Dict[str, Any]) -> Tuple[int, str]:
                md = item.get("metadata", {}) if isinstance(item, dict) else {}
                status = str(md.get("analysis_status", "")).lower()
                ts = str(md.get("timestamp") or md.get("seen_at") or "")
                tag_score = self._recording_tag_match_score(md, query)
                # tag hits first, then ready first, then newer first
                return (-tag_score, 0 if status == "ready" else 1, ts)

            rows = sorted(rows, key=_rank, reverse=False)

            out: List[str] = []
            seen_file = set()
            for row in rows:
                if not isinstance(row, dict):
                    continue
                meta = row.get("metadata", {}) or {}
                when = (
                    str(meta.get("timestamp") or meta.get("seen_at") or meta.get("created_at") or "Unknown time")
                )
                filename = str(meta.get("filename", ""))
                basename = os.path.basename(filename) if filename else ""
                status = str(meta.get("analysis_status", "")).lower()
                ts = str(meta.get("timestamp") or meta.get("seen_at") or "")

                if specific_hint.get("basename") and basename != specific_hint["basename"]:
                    continue
                if specific_hint.get("timestamp") and not ts.startswith(specific_hint["timestamp"]):
                    continue

                if basename in seen_file and status != "ready":
                    continue
                hint = (
                    meta.get("timeline_text")
                    or meta.get("content_description")
                    or meta.get("ocr_text")
                    or self._extract_memory_content(row)
                )
                hint = " ".join(str(hint).split())
                if len(hint) > 180:
                    hint = hint[:180] + "..."
                out.append(f"- {when} {basename}：{hint}")
                if basename:
                    seen_file.add(basename)
                if len(out) >= limit:
                    break
            return out
        except Exception as e:
            print(f"[Chat] memory recording evidence failed: {e}")
            return []

    def _build_visual_detail_response(
        self,
        query: str,
        memory_context: str = "",
    ) -> Tuple[str, str]:
        """
        Produce detailed visual-memory answer using richer evidence and larger model.
        Returns: (answer_text, used_model)
        """
        evidence_list, harness_stats = self._collect_visual_harness_evidence(query, max_videos=2)
        if not evidence_list:
            return self._format_visual_detail_fallback(query, []), "visual-harness-fallback"

        evidence_text = self._format_visual_harness_response(
            query=query,
            evidence_list=evidence_list,
            memory_context=memory_context,
        )

        model_name = self._select_large_text_model()
        if self._is_vision_model(model_name):
            return evidence_text, model_name

        compact_evidence = []
        for ev in evidence_list[:2]:
            compact_evidence.append(
                {
                    "timestamp": ev.get("timestamp", ""),
                    "video": ev.get("basename", ""),
                    "text": (ev.get("ocr_snippets", []) or [])[:10],
                    "objects": (ev.get("objects", []) or [])[:8],
                    "target_hits": (ev.get("target_hits", []) or [])[:8],
                    "frame_rows": (ev.get("frame_timeline_text", []) or [])[:6],
                }
            )

        synthesis_prompt = (
            "你是 MemScreen 视觉记忆总结器。\n"
            "只根据给定证据输出 3~5 行中文结论，不得编造。\n"
            "如果用户问“在哪里/什么时候出现”，优先回答命中时间点+位置。\n"
            "如果证据不足，要明确写“未找到足够证据”。\n"
            "输出时不要重复整段时间线。"
        )
        summary_text = self._ollama_generate_once(
            model=model_name,
            prompt=(
                f"{synthesis_prompt}\n\n用户问题：{query}\n"
                f"链路统计：{json.dumps(harness_stats, ensure_ascii=False)}\n"
                f"证据：{json.dumps(compact_evidence, ensure_ascii=False)}"
            ),
            options={
                "num_predict": 260,
                "temperature": 0.2,
                "top_p": 0.85,
                "top_k": 30,
                "num_ctx": 8192,
                "repeat_penalty": 1.1,
            },
            timeout=14.0,
        )
        summary_text = self._sanitize_ai_text(summary_text)
        if summary_text and len(summary_text) >= 20:
            return evidence_text + "\n\n综合结论：\n" + summary_text, model_name
        return evidence_text, model_name

    def _classify_activity_kind(self, text: str) -> str:
        """Classify rough activity type from OCR/timeline text."""
        t = " ".join(str(text).lower().split())
        if any(k in t for k in ["paper", "pdf", "arxiv", "abstract", "论文", "福昕"]):
            return "论文/文档阅读"
        if any(k in t for k in ["terminal", "zsh", "bash", "python", "git", "error", "exception"]):
            return "终端/开发调试"
        if any(k in t for k in ["vscode", "code", ".py", ".ts", "flutter"]):
            return "代码编辑"
        if any(k in t for k in ["chrome", "safari", "firefox", "search", "browser"]):
            return "网页浏览/检索"
        if any(k in t for k in ["wecom", "企业微信", "chat", "message"]):
            return "沟通/消息处理"
        return "通用窗口操作"

    def _collect_activity_timeline_entries(
        self,
        query: str,
        limit: int = 12,
    ) -> List[Dict[str, Any]]:
        """Collect recording timeline entries for retrospective summary."""
        entries: List[Dict[str, Any]] = []
        seen = set()

        # Prefer memory entries because they carry enriched timeline_text/frame_details.
        if self.memory_system:
            try:
                result = self.memory_system.search(
                    query=query or "recent work summary",
                    user_id="default_user",
                    filters={"type": "screen_recording"},
                    limit=max(limit, 16),
                    threshold=0.0,
                )
                rows = result.get("results", []) if isinstance(result, dict) else (result or [])
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    meta = row.get("metadata", {}) or {}
                    ts = str(meta.get("timestamp") or meta.get("seen_at") or meta.get("created_at") or "")
                    filename = str(meta.get("filename", ""))
                    basename = os.path.basename(filename) if filename else ""
                    key = (ts, basename)
                    if key in seen:
                        continue
                    seen.add(key)
                    detail = (
                        meta.get("timeline_text")
                        or meta.get("content_description")
                        or meta.get("ocr_text")
                        or self._extract_memory_content(row)
                    )
                    detail = " ".join(str(detail).split())[:350]
                    entries.append(
                        {
                            "timestamp": ts or "Unknown time",
                            "basename": basename,
                            "detail": detail,
                            "kind": self._classify_activity_kind(detail),
                        }
                    )
                    if len(entries) >= limit:
                        break
            except Exception as e:
                print(f"[Chat] collect activity entries from memory failed: {e}")

        # DB fallback for missing entries.
        if len(entries) < min(4, limit):
            db_rows = self._load_recent_recordings_from_db(limit=limit)
            for row in db_rows:
                ts = str(row.get("timestamp", "Unknown time"))
                basename = str(row.get("basename", ""))
                key = (ts, basename)
                if key in seen:
                    continue
                seen.add(key)
                hint = self._quick_extract_video_text(str(row.get("filename", "")), dense=False)
                hint = " ".join(str(hint).split())[:300]
                if not hint:
                    hint = f"录屏时长 {float(row.get('duration', 0.0)):.1f}s，帧数 {int(row.get('frame_count', 0))}"
                entries.append(
                    {
                        "timestamp": ts,
                        "basename": basename,
                        "detail": hint,
                        "kind": self._classify_activity_kind(hint),
                    }
                )
                if len(entries) >= limit:
                    break

        # Sort by timestamp desc when possible.
        def _ts_key(item: Dict[str, Any]) -> float:
            ts = self._parse_memory_timestamp({"timestamp": item.get("timestamp", "")})
            return ts.timestamp() if ts else 0.0

        entries = sorted(entries, key=_ts_key, reverse=True)
        return entries[:limit]

    def _build_activity_summary_response(
        self,
        query: str,
        memory_context: str = "",
    ) -> Tuple[str, str]:
        """Build evidence-grounded retrospective summary and suggestions."""
        entries = self._collect_activity_timeline_entries(query, limit=10)
        if not entries:
            return (
                "我没有找到可用的录屏时间线来做总结。\n"
                "建议：先录制关键操作后再问“帮我总结今天做了什么”。",
                "activity-fallback",
            )

        kind_counts: Dict[str, int] = {}
        for item in entries:
            kind = item.get("kind", "通用窗口操作")
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
        top_kinds = sorted(kind_counts.items(), key=lambda x: x[1], reverse=True)
        focus = "、".join([f"{k}({v})" for k, v in top_kinds[:3]]) if top_kinds else "通用窗口操作"

        lines = ["我按录屏时间线整理了你最近做过的事情：", "时间线证据："]
        timeline_rows: List[List[str]] = []
        for item in entries[:6]:
            timeline_rows.append([
                str(item.get('timestamp', 'Unknown time')),
                str(item.get('basename', '')),
                str(item.get('kind', '')),
                str(item.get('detail', ''))[:180],
            ])
        lines.append(self._build_markdown_table(["时间", "视频", "活动类型", "证据摘要"], timeline_rows))
        lines.append(f"主要活动类型：{focus}")

        # Deterministic suggestion baseline.
        suggestions = []
        if any("终端/开发调试" in k for k, _ in top_kinds):
            suggestions.append("把报错关键词和修复动作记录成 checklist，避免重复排查。")
        if any("论文/文档阅读" in k for k, _ in top_kinds):
            suggestions.append("为论文阅读建立“标题-结论-待验证点”三栏笔记，方便后续检索。")
        if any("沟通/消息处理" in k for k, _ in top_kinds):
            suggestions.append("把消息中的待办转成明确任务，补上截止时间。")
        if not suggestions:
            suggestions.append("按时间线回顾关键窗口，确认下一步唯一优先动作。")
        if len(suggestions) < 2:
            suggestions.append("把关键录屏片段打上标签（论文/报错/代码），后续追问会更快更准。")
        if len(suggestions) < 3:
            suggestions.append("每天结束前做一次 1 分钟复盘：今天完成、阻塞点、明天第一步。")

        model_name = self._select_large_text_model()
        if not self._is_vision_model(model_name):
            summary_prompt = (
                "你是 MemScreen 复盘助手。只基于证据输出：\n"
                "1) 最近在做什么（2-3行）；\n"
                "2) 具体建议（2-3条）；\n"
                "禁止编造，禁止脱离证据。"
            )
            ai_summary = self._ollama_generate_once(
                model=model_name,
                prompt=(
                    f"{summary_prompt}\n\n用户问题：{query}\n"
                    f"证据：{json.dumps(entries[:8], ensure_ascii=False)}\n"
                    f"已有记忆上下文：{memory_context[:800]}"
                ),
                options={
                    "num_predict": 300,
                    "temperature": 0.25,
                    "top_p": 0.85,
                    "top_k": 30,
                    "num_ctx": 8192,
                    "repeat_penalty": 1.12,
                },
                timeout=14.0,
            )
            ai_summary = self._sanitize_ai_text(ai_summary)
            if ai_summary and len(ai_summary) >= 20:
                lines.append("\n复盘总结：")
                lines.append(ai_summary)

        lines.append("\n建议：")
        for idx, item in enumerate(suggestions[:3], 1):
            lines.append(f"{idx}. {item}")
        return "\n".join(lines), model_name

    def _build_hybrid_visual_evidence(
        self,
        query: str,
        *,
        db_limit: int = 6,
        ocr_limit: int = 2,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Build mixed evidence from recording DB + on-demand OCR.

        Returns:
            (evidence_text, stats)
        """
        stats = {
            "db_rows": 0,
            "ocr_rows": 0,
            "keyword_matches": 0,
            "db_lines": [],
            "ocr_lines": [],
            "ocr_details": [],
        }
        rows = self._load_recent_recordings_from_db(limit=db_limit)
        if not rows:
            return "", stats

        stats["db_rows"] = len(rows)
        window = self._infer_time_window(query)
        target_rows = self._filter_recordings_by_time_window(rows, window)
        time_window_note = ""
        if window and not target_rows:
            time_window_note = (
                f"时间段筛选提示：没有找到 {window[0]:02d}:00-{window[1]:02d}:00 的录屏，"
                "以下为最近可用录屏。"
            )
            target_rows = rows[: min(4, len(rows))]
        elif window:
            target_rows = target_rows[: min(4, len(target_rows))]
        else:
            target_rows = rows[: min(4, len(rows))]

        if not target_rows:
            return "", stats

        evidence_lines = ["[Hybrid Visual Evidence: DB Timeline]"]
        db_rows_md: List[List[str]] = []
        for row in target_rows:
            db_rows_md.append([
                str(row.get('timestamp', 'Unknown time')),
                str(row.get('basename', '')),
                f"{float(row.get('duration', 0.0)):.1f}s",
                str(row.get('frame_count', 0)),
            ])
        evidence_lines.append(self._build_markdown_table(["时间", "视频", "时长", "帧数"], db_rows_md))
        stats["db_lines"] = [f"- {r[0]}：{r[1]}（{r[2]}, {r[3]} 帧）" for r in db_rows_md]

        if time_window_note:
            evidence_lines.append(f"- {time_window_note}")

        query_keywords = self._extract_query_keywords(query)
        paper_like = any(k in query.lower() for k in ["论文", "paper", "pdf", "arxiv"])
        ocr_scan_rows = target_rows
        if paper_like:
            # For paper/doc queries prioritize longer recordings (more likely to contain readable document pages).
            merged_candidates = list(target_rows)
            if len(merged_candidates) < 3:
                merged_candidates.extend(rows)
            ocr_scan_rows = sorted(
                {r.get("filename", ""): r for r in merged_candidates}.values(),
                key=lambda r: float(r.get("duration", 0.0)),
                reverse=True,
            )
            ocr_limit = max(ocr_limit, 2)

        ocr_lines: List[str] = []
        for row in ocr_scan_rows[:ocr_limit]:
            ocr_text = self._quick_extract_video_text(row.get("filename", ""))
            if not ocr_text:
                continue
            stats["ocr_rows"] += 1
            match_count = sum(1 for kw in query_keywords if kw and kw in ocr_text.lower())
            if match_count > 0:
                stats["keyword_matches"] += 1
            snippets = self._extract_ocr_snippets(ocr_text, query_keywords)
            preview = " / ".join(snippets[:2]) if snippets else ocr_text
            if len(preview) > 180:
                preview = preview[:180] + "..."
            ocr_line = f"- {row.get('timestamp', 'Unknown time')}：{preview}"
            ocr_lines.append(ocr_line)
            stats["ocr_lines"].append(ocr_line)
            stats["ocr_details"].append(
                {
                    "timestamp": row.get("timestamp", "Unknown time"),
                    "basename": row.get("basename", ""),
                    "snippets": snippets[:4],
                }
            )

        if ocr_lines:
            evidence_lines.append("\n[Hybrid Visual Evidence: OCR]")
            ocr_rows_md: List[List[str]] = []
            for line in ocr_lines:
                txt = line[2:] if line.startswith("- ") else line
                if "：" in txt:
                    t, pv = txt.split("：", 1)
                    ocr_rows_md.append([t.strip(), pv.strip()])
                else:
                    ocr_rows_md.append(["", txt])
            evidence_lines.append(self._build_markdown_table(["时间", "OCR证据"], ocr_rows_md))

        return "\n".join(evidence_lines), stats

    def _build_tiered_memory_context(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Build a tiered (working/short/long) context string for faster and better grounded answers."""
        stats = {
            "total_memories": 0,
            "working_count": 0,
            "short_term_count": 0,
            "long_term_count": 0,
            "recording_count": 0,
        }

        query_lower = query.lower()
        temporal_keywords = [
            "什么时候", "何时", "今天", "昨天", "最近", "当时", "看到", "看到了",
            "上午", "中午", "下午", "晚上", "夜里", "在看什么", "看了什么",
            "论文", "paper", "pdf", "arxiv",
            "when", "today", "yesterday", "recent", "saw", "seen",
            "morning", "afternoon", "evening", "night",
        ]
        need_recording_fallback = any(k in query_lower for k in temporal_keywords)

        # Memory system might be unavailable; still provide timeline from recordings DB.
        if not self.memory_system:
            if need_recording_fallback:
                db_rows = self._load_recent_recordings_from_db(limit=5)
                if db_rows:
                    context_parts = ["[Screen Timeline: local recording database fallback]"]
                    for row in db_rows:
                        context_parts.append(
                            f"- {row.get('timestamp', 'Unknown time')}: "
                            f"录屏文件 {row.get('basename', '')}"
                            f"（{row.get('duration', 0.0):.1f}s, {row.get('frame_count', 0)} frames）"
                        )
                    stats["recording_count"] = len(db_rows)
                    stats["total_memories"] = len(db_rows)
                    print(
                        "[Chat] Tiered memory context built from DB fallback only: "
                        f"recordings={stats['recording_count']}"
                    )
                    return "\n".join(context_parts), stats
            return "", stats

        memories = []
        try:
            if hasattr(self.memory_system, "smart_search"):
                result = self.memory_system.smart_search(
                    query=query,
                    user_id="default_user",
                    limit=18,
                )
            else:
                result = self.memory_system.search(
                    query=query,
                    user_id="default_user",
                    limit=18,
                    threshold=0.0,
                )

            if isinstance(result, dict):
                memories = result.get("results", []) or []
            elif isinstance(result, list):
                memories = result
        except Exception as mem_err:
            print(f"[Chat] Tiered memory search failed: {mem_err}")
            memories = []

        # If user asks temporal "what did I see" style questions, always pull recent screen recordings.
        if need_recording_fallback:
            try:
                recording_result = self.memory_system.search(
                    query="screen recording timeline what was seen",
                    user_id="default_user",
                    filters={"type": "screen_recording"},
                    limit=8,
                    threshold=0.0,
                )
                extra_memories = []
                if isinstance(recording_result, dict):
                    extra_memories = recording_result.get("results", []) or []
                elif isinstance(recording_result, list):
                    extra_memories = recording_result

                if extra_memories:
                    seen_ids = {str(m.get("id")) for m in memories if isinstance(m, dict)}
                    for mem in extra_memories:
                        mem_id = str(mem.get("id")) if isinstance(mem, dict) else ""
                        if mem_id and mem_id in seen_ids:
                            continue
                        memories.append(mem)
            except Exception as rec_err:
                print(f"[Chat] Recording fallback search failed: {rec_err}")

        now = datetime.now()
        working_cutoff = now - timedelta(hours=self.working_memory_hours)
        short_term_cutoff = now - timedelta(days=self.short_term_days)

        working_items = []
        short_term_items = []
        long_term_items = []
        recording_timeline = []
        db_recording_timeline = []

        for mem in memories:
            if not isinstance(mem, dict):
                continue

            metadata = mem.get("metadata", {}) or {}
            content = self._extract_memory_content(mem)
            if not content:
                continue

            ts = self._parse_memory_timestamp(metadata)
            if ts and ts >= working_cutoff:
                working_items.append((ts, mem, content))
            elif ts and ts >= short_term_cutoff:
                short_term_items.append((ts, mem, content))
            else:
                long_term_items.append((ts, mem, content))

            if metadata.get("type") == "screen_recording":
                stats["recording_count"] += 1
                timeline_hint = (
                    metadata.get("timeline_text")
                    or metadata.get("content_description")
                    or content
                )
                timeline_hint = " ".join(str(timeline_hint).split())
                if len(timeline_hint) > 220:
                    timeline_hint = timeline_hint[:220] + "..."
                when = ts.strftime("%Y-%m-%d %H:%M") if ts else str(metadata.get("timestamp", "Unknown time"))
                recording_timeline.append(f"- {when}: {timeline_hint}")

        # Fallback: if vector memory has no recording entries yet, use recording DB timeline.
        if need_recording_fallback and stats["recording_count"] == 0:
            db_rows = self._load_recent_recordings_from_db(limit=5)
            for row in db_rows:
                when = row.get("timestamp", "Unknown time")
                basename = row.get("basename", "")
                duration = row.get("duration", 0.0)
                frame_count = row.get("frame_count", 0)
                db_recording_timeline.append(
                    f"- {when}: 录屏文件 {basename}（{duration:.1f}s, {frame_count} frames）"
                )

            if db_recording_timeline:
                stats["recording_count"] = len(db_recording_timeline)

        if not memories and not db_recording_timeline:
            return "", stats

        sort_key = lambda item: item[0] or datetime.min
        working_items.sort(key=sort_key, reverse=True)
        short_term_items.sort(key=sort_key, reverse=True)
        long_term_items.sort(key=sort_key, reverse=True)

        stats["working_count"] = len(working_items)
        stats["short_term_count"] = len(short_term_items)
        stats["long_term_count"] = len(long_term_items)
        stats["total_memories"] = len(working_items) + len(short_term_items) + len(long_term_items)
        if db_recording_timeline:
            stats["total_memories"] += len(db_recording_timeline)

        def _fmt_row(ts: Optional[datetime], mem: Dict[str, Any], content: str) -> str:
            metadata = mem.get("metadata", {}) or {}
            mem_type = metadata.get("type", metadata.get("category", "memory"))
            when = ts.strftime("%Y-%m-%d %H:%M") if ts else "Unknown time"
            if len(content) > 220:
                content = content[:220] + "..."
            return f"- [{when}] ({mem_type}) {content}"

        context_parts: List[str] = []
        if working_items:
            context_parts.append(f"[Layer: Working Memory <= {self.working_memory_hours}h]")
            for row in working_items[: self.max_tier_items["working"]]:
                context_parts.append(_fmt_row(*row))

        if short_term_items:
            context_parts.append(
                f"\n[Layer: Short-term Memory <= {self.short_term_days}d]"
                if context_parts
                else f"[Layer: Short-term Memory <= {self.short_term_days}d]"
            )
            for row in short_term_items[: self.max_tier_items["short_term"]]:
                context_parts.append(_fmt_row(*row))

        if long_term_items:
            context_parts.append("\n[Layer: Long-term Memory]" if context_parts else "[Layer: Long-term Memory]")
            for row in long_term_items[: self.max_tier_items["long_term"]]:
                context_parts.append(_fmt_row(*row))

        if recording_timeline:
            context_parts.append(
                "\n[Screen Timeline: when things were seen]"
                if context_parts
                else "[Screen Timeline: when things were seen]"
            )
            context_parts.extend(recording_timeline[:5])
        elif db_recording_timeline:
            context_parts.append(
                "\n[Screen Timeline: local recording database fallback]"
                if context_parts
                else "[Screen Timeline: local recording database fallback]"
            )
            context_parts.extend(db_recording_timeline[:5])

        # Add hybrid evidence (DB + OCR) for temporal/visual queries to improve specificity.
        if need_recording_fallback:
            hybrid_text, hybrid_stats = self._build_hybrid_visual_evidence(query)
            if hybrid_text:
                context_parts.append("\n" + hybrid_text if context_parts else hybrid_text)
                stats["total_memories"] += hybrid_stats.get("db_rows", 0) + hybrid_stats.get("ocr_rows", 0)
                if stats["recording_count"] == 0 and hybrid_stats.get("db_rows", 0) > 0:
                    stats["recording_count"] = hybrid_stats.get("db_rows", 0)

        context_text = "\n".join(context_parts)
        print(
            "[Chat] Tiered memory context built: "
            f"total={stats['total_memories']}, "
            f"working={stats['working_count']}, "
            f"short={stats['short_term_count']}, "
            f"long={stats['long_term_count']}, "
            f"recordings={stats['recording_count']}"
        )
        return context_text, stats

    def _select_sync_model(
        self,
        user_message: str,
        context_stats: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """Auto-select an Ollama model for sync chat path."""
        if not self.available_models:
            self._load_available_models()

        chat_models = [m for m in self.available_models if not self._is_embedding_model(m)]
        if not chat_models:
            chat_models = list(self.available_models)

        default_model = self.current_model
        if default_model not in chat_models and chat_models:
            default_model = sorted(chat_models, key=lambda m: self._parse_model_size_b(m), reverse=True)[0]
        if not default_model:
            default_model = "qwen3:1.7b"

        default_params = {
            "temperature": 0.45,
            "top_p": 0.85,
            "top_k": 25,
            "num_predict": 384,
            "num_ctx": 4096,
            "repeat_penalty": 1.15,
        }

        if not self.auto_model_selection:
            return default_model, default_params

        try:
            from ..llm.model_router import get_router, ModelConfig, ModelTier
        except Exception as import_err:
            print(f"[Chat] Model router import failed, using default model: {import_err}")
            return default_model, default_params

        routing_query = user_message
        if context_stats.get("recording_count", 0) > 0:
            routing_query += " timeline timestamp suggestion"
        if context_stats.get("working_count", 0) > 0:
            routing_query += " recent context"
        if context_stats.get("long_term_count", 0) > 2:
            routing_query += " summarize history"

        try:
            router = get_router(chat_models)
            analysis = router.analyzer.analyze(routing_query)

            temporal_recording_query = (
                context_stats.get("recording_count", 0) > 0
                and self._is_memory_sensitive_query(user_message)
            )
            visual_detail_query = (
                context_stats.get("recording_count", 0) > 0
                and self._is_visual_detail_query(user_message)
            )

            # Temporal recording QA needs better factual compliance; avoid tiny tier.
            if visual_detail_query:
                preferred_tiers = [ModelTier.LARGE, ModelTier.MEDIUM, ModelTier.SMALL]
            elif temporal_recording_query:
                preferred_tiers = [ModelTier.LARGE, ModelTier.MEDIUM, ModelTier.SMALL]
            elif analysis.tier == ModelTier.TINY:
                preferred_tiers = [ModelTier.TINY, ModelTier.SMALL, ModelTier.MEDIUM]
            elif analysis.tier == ModelTier.SMALL:
                preferred_tiers = [ModelTier.SMALL, ModelTier.TINY, ModelTier.MEDIUM]
            elif analysis.tier == ModelTier.MEDIUM:
                preferred_tiers = [ModelTier.MEDIUM, ModelTier.SMALL, ModelTier.LARGE]
            else:
                preferred_tiers = [ModelTier.LARGE, ModelTier.MEDIUM, ModelTier.SMALL]

            candidates = []
            for tier in preferred_tiers:
                candidates.extend(router.tier_models.get(tier, []))
            if not candidates:
                candidates = list(chat_models)

            candidates = [m for m in candidates if not self._is_embedding_model(m)]
            if not candidates:
                candidates = list(chat_models)

            # For detail-heavy visual questions, prefer >=3B models when available.
            if visual_detail_query:
                stronger = [m for m in candidates if self._parse_model_size_b(m) >= 7.0]
                if not stronger:
                    stronger = [m for m in candidates if self._parse_model_size_b(m) >= 3.0]
                if stronger:
                    candidates = stronger
            elif temporal_recording_query:
                stronger = [m for m in candidates if self._parse_model_size_b(m) >= 7.0]
                if not stronger:
                    stronger = [m for m in candidates if self._parse_model_size_b(m) >= 3.0]
                if stronger:
                    candidates = stronger
            else:
                # Avoid ultra-tiny chat models (e.g. 270M) unless absolutely no alternative exists.
                stronger = [m for m in candidates if self._parse_model_size_b(m) >= 1.0]
                if stronger:
                    candidates = stronger

            # Prefer low-latency models while keeping baseline quality.
            def _score(model_name: str) -> float:
                cfg = router.model_configs.get(
                    model_name,
                    ModelConfig(
                        name=model_name,
                        tier=analysis.tier,
                        avg_latency_ms=800,
                        quality_score=0.7,
                    ),
                )
                latency = cfg.avg_latency_ms or 800
                quality = cfg.quality_score or 0.7
                size_b = self._parse_model_size_b(model_name)
                vision_penalty = 80 if ("vl" in model_name.lower() and context_stats.get("recording_count", 0) == 0) else 0
                # For visual details, bias toward quality and slightly larger models.
                if visual_detail_query:
                    return latency - quality * 220 - min(size_b, 14.0) * 10 + vision_penalty
                return latency - quality * 120 + vision_penalty

            selected_model = sorted(set(candidates), key=_score)[0] if candidates else default_model
            model_config = router.model_configs.get(
                selected_model,
                ModelConfig(name=selected_model, tier=analysis.tier),
            )
            params = router.get_optimized_parameters(routing_query, model_config)

            if selected_model not in chat_models:
                selected_model = default_model
        except Exception as route_err:
            print(f"[Chat] Model routing failed, fallback to default model: {route_err}")
            selected_model = default_model
            params = dict(default_params)

        # Timeline/suggestion questions need slightly longer output budget.
        if context_stats.get("recording_count", 0) > 0:
            params["num_predict"] = max(params.get("num_predict", 320), 384)
            params["num_ctx"] = max(params.get("num_ctx", 4096), 6144)
            if self._is_visual_detail_query(user_message):
                params["num_predict"] = max(params.get("num_predict", 384), 640)
                params["temperature"] = min(params.get("temperature", 0.45), 0.25)

        self.current_model = selected_model
        return selected_model, params

    def _persist_chat_memory_async(
        self,
        user_message: str,
        ai_text: str,
        selected_model: str,
        context_stats: Dict[str, Any],
        used_context: bool,
    ) -> None:
        """Persist chat conversation in a background thread to avoid blocking the user response."""
        if not self.memory_system:
            return

        def _save():
            try:
                conversation = [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": ai_text},
                ]
                self.memory_system.add(
                    conversation,
                    user_id="default_user",
                    metadata={
                        "source": "ai_chat",
                        "type": "ai_chat",
                        "timestamp": datetime.now().isoformat(),
                        "model": selected_model,
                        "memory_count": context_stats.get("total_memories", 0),
                        "used_context": used_context,
                        "working_count": context_stats.get("working_count", 0),
                        "short_term_count": context_stats.get("short_term_count", 0),
                        "long_term_count": context_stats.get("long_term_count", 0),
                    },
                    infer=True,
                )
                print("[Chat] Saved conversation to memory")
            except Exception as mem_err:
                print(f"[Chat] Failed to save conversation to memory: {mem_err}")

        threading.Thread(target=_save, daemon=True).start()

    def _sanitize_ai_text(self, text: str) -> str:
        """Remove chain-of-thought style blocks/tags from model output."""
        if not text:
            return text

        cleaned = text
        # Remove XML-style think blocks.
        cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
        # Remove markdown think fences if any.
        cleaned = re.sub(r"```think[\\s\\S]*?```", "", cleaned, flags=re.IGNORECASE)
        # Remove lingering standalone think tags.
        cleaned = cleaned.replace("<think>", "").replace("</think>", "")
        # Normalize whitespace while preserving line breaks.
        cleaned = "\n".join(line.rstrip() for line in cleaned.splitlines()).strip()
        return cleaned

    def send_message_sync(
        self,
        user_message: str,
        on_done: Callable[[str, Optional[str]], None],
    ) -> None:
        """
        Send a message in background and return full response via callback.

        Optimizations:
        - Auto model selection based on query + memory complexity
        - Tiered memory context (working/short-term/long-term)
        - Non-blocking memory persistence (save after sending reply)
        """

        def _run():
            try:
                from ..llm import OllamaLLM

                if not user_message.strip():
                    on_done("", "Error: empty message")
                    return

                if self._is_identity_query(user_message):
                    ai_text = (
                        "我是 MemScreen 助手，主要基于你的录屏与记忆数据回答问题。\n"
                        "我可以：\n"
                        "1. 按时间线回忆你屏幕上出现的文字和内容。\n"
                        "2. 给出对应录屏证据（时间点、视频文件、OCR文本）。\n"
                        "3. 根据最近活动给出下一步建议。\n"
                        "如果你愿意，现在可以直接问我：刚刚屏幕上有哪些字/物体？"
                    )
                    self.conversation_history.append(ChatMessage("user", user_message))
                    self.conversation_history.append(ChatMessage("assistant", ai_text))
                    on_done(ai_text, None)
                    self._persist_chat_memory_async(
                        user_message=user_message,
                        ai_text=ai_text,
                        selected_model="identity-fastpath",
                        context_stats={"total_memories": 0, "working_count": 0, "short_term_count": 0, "long_term_count": 0},
                        used_context=False,
                    )
                    return

                visual_detail_query = (
                    self._is_visual_detail_query(user_message)
                    or self._is_visual_location_query(user_message)
                )
                activity_summary_query = self._is_activity_summary_query(user_message)

                # Fast cache hit path
                skip_cache = (
                    self._is_memory_sensitive_query(user_message)
                    or activity_summary_query
                    or visual_detail_query
                )
                if not skip_cache:
                    cached_response = self._get_cached_response(user_message)
                    if cached_response:
                        self.conversation_history.append(ChatMessage("user", user_message))
                        self.conversation_history.append(ChatMessage("assistant", cached_response))
                        on_done(cached_response, None)
                        return

                # Visual QA path uses dedicated harness retrieval; avoid heavy tiered-context build.
                if visual_detail_query:
                    context = ""
                    context_stats = {
                        "total_memories": 0,
                        "working_count": 0,
                        "short_term_count": 0,
                        "long_term_count": 0,
                        "recording_count": 0,
                    }
                    mem_lines = self._collect_memory_recording_evidence(user_message, limit=6)
                    if mem_lines:
                        context = "\n".join(mem_lines)
                        context_stats["recording_count"] = len(mem_lines)
                        context_stats["total_memories"] = len(mem_lines)
                else:
                    context, context_stats = self._build_tiered_memory_context(user_message)

                # For visual-detail questions, use dedicated richer pipeline first.
                if visual_detail_query:
                    ai_text, visual_model = self._build_visual_detail_response(
                        user_message,
                        memory_context=context,
                    )
                    self.conversation_history.append(ChatMessage("user", user_message))
                    self.conversation_history.append(ChatMessage("assistant", ai_text))
                    on_done(ai_text, None)
                    self._persist_chat_memory_async(
                        user_message=user_message,
                        ai_text=ai_text,
                        selected_model=visual_model,
                        context_stats=context_stats,
                        used_context=bool(context),
                    )
                    return

                # For retrospective summary/suggestion questions, use dedicated timeline summarizer.
                if activity_summary_query:
                    ai_text, summary_model = self._build_activity_summary_response(
                        user_message,
                        memory_context=context,
                    )
                    self.conversation_history.append(ChatMessage("user", user_message))
                    self.conversation_history.append(ChatMessage("assistant", ai_text))
                    on_done(ai_text, None)
                    self._persist_chat_memory_async(
                        user_message=user_message,
                        ai_text=ai_text,
                        selected_model=summary_model,
                        context_stats=context_stats,
                        used_context=bool(context),
                    )
                    return

                # For timeline/screen-memory questions, avoid hallucination when no recording evidence exists.
                if self._is_memory_sensitive_query(user_message) and context_stats.get("recording_count", 0) == 0:
                    recent_recordings = self._load_recent_recordings_from_db(limit=3)
                    if recent_recordings:
                        # For "paper/论文" queries, do a quick OCR pass on matching time-window recordings.
                        q_lower = user_message.lower()
                        paper_like = any(k in q_lower for k in ["论文", "paper", "arxiv", "pdf"])
                        ocr_hint = ""
                        if paper_like:
                            win = self._infer_time_window(user_message)
                            target_rows = self._filter_recordings_by_time_window(recent_recordings, win)
                            if not target_rows:
                                target_rows = recent_recordings
                            for row in target_rows[:2]:
                                hint = self._quick_extract_video_text(row.get("filename", ""))
                                if hint:
                                    ocr_hint = (
                                        f"\n我从最近录屏里识别到的文本线索：\n"
                                        f"- {row.get('timestamp', 'Unknown time')}：{hint}"
                                    )
                                    break
                        else:
                            # For generic visual-memory queries, still attach one OCR content hint when possible.
                            for row in recent_recordings[:2]:
                                hint = self._quick_extract_video_text(row.get("filename", ""))
                                if hint:
                                    ocr_hint = (
                                        f"\n我从最近录屏里识别到的画面内容：\n"
                                        f"- {row.get('timestamp', 'Unknown time')}：{hint}"
                                    )
                                    break

                        lines = []
                        for row in recent_recordings:
                            lines.append(
                                f"- {row.get('timestamp', 'Unknown time')}："
                                f"{row.get('basename', '')}"
                                f"（{row.get('duration', 0.0):.1f}s, {row.get('frame_count', 0)} 帧）"
                            )
                        ai_text = (
                            "我没有检索到可用的录屏向量时间线，但从最近录屏记录看：\n"
                            + "\n".join(lines)
                            + ocr_hint
                            + "\n建议：\n"
                            + "1. 先打开最近一条录屏确认画面内容。\n"
                            + "2. 再用关键词问我（如“终端/浏览器/报错词”），我会给更准确的时间线。"
                        )
                        self.conversation_history.append(ChatMessage("user", user_message))
                        self.conversation_history.append(ChatMessage("assistant", ai_text))
                        on_done(ai_text, None)
                        self._persist_chat_memory_async(
                            user_message=user_message,
                            ai_text=ai_text,
                            selected_model="recording-db-fallback",
                            context_stats=context_stats,
                            used_context=False,
                        )
                        return

                    ai_text = (
                        "我暂时没有在记忆中找到对应的录屏时间线证据。\n"
                        "建议：\n"
                        "1. 先开启录屏后再复现一次关键操作。\n"
                        "2. 用更具体关键词再问一次（例如应用名/报错词）。"
                    )
                    self.conversation_history.append(ChatMessage("user", user_message))
                    self.conversation_history.append(ChatMessage("assistant", ai_text))
                    on_done(ai_text, None)
                    self._persist_chat_memory_async(
                        user_message=user_message,
                        ai_text=ai_text,
                        selected_model="memory-fastpath",
                        context_stats=context_stats,
                        used_context=False,
                    )
                    return

                selected_model, params = self._select_sync_model(user_message, context_stats)
                used_context = bool(context)

                print(
                    f"[Chat] Auto model selected: {selected_model} "
                    f"(context={context_stats.get('total_memories', 0)} memories)"
                )

                llm = OllamaLLM(
                    config={
                        "model": selected_model,
                        "temperature": params.get("temperature", 0.45),
                        "max_tokens": params.get("num_predict", 384),
                        "top_p": params.get("top_p", 0.85),
                        "top_k": params.get("top_k", 25),
                        "num_ctx": params.get("num_ctx", 4096),
                        "repeat_penalty": params.get("repeat_penalty", 1.15),
                    }
                )

                # Use project prompt templates to keep API/Flutter behavior aligned.
                try:
                    from ..prompts.chat_prompts import ChatPromptBuilder

                    query_type = ChatPromptBuilder.detect_query_type(user_message)
                    if used_context:
                        base_prompt = ChatPromptBuilder.build_with_context(context, user_message, query_type)
                    else:
                        base_prompt = ChatPromptBuilder.build_without_context(user_message, query_type)
                except Exception:
                    base_prompt = "你是 MemScreen，一个基于记忆回答的助手。"

                system_prompt = (
                    base_prompt
                    + "\n\n[执行约束]\n"
                    + "1. 仅根据给定记忆上下文作答，禁止编造。\n"
                    + "2. 优先使用具体时间和录屏文件名作为证据。\n"
                    + "3. 若证据不足，明确说明“未找到”并给出下一步建议。\n"
                    + "4. 回答语言使用中文，禁止输出 <think> 或推理过程。"
                )

                messages: List[Dict[str, str]] = []
                messages.append({"role": "system", "content": system_prompt})

                # Keep short conversation continuity without inflating prompt too much
                for msg in self.conversation_history[-6:]:
                    messages.append(msg.to_dict())
                messages.append({"role": "user", "content": user_message})

                response = llm.generate_response(messages)
                ai_text = str(response).strip() if response else ""
                ai_text = self._sanitize_ai_text(ai_text)
                if not ai_text:
                    ai_text = "我暂时没有生成有效回复，请重试一次。"

                # Ensure timeline answers always include concrete recent recording evidence.
                if self._is_memory_sensitive_query(user_message) and context_stats.get("recording_count", 0) > 0:
                    paper_like = any(k in user_message.lower() for k in ["论文", "paper", "pdf", "arxiv"])
                    has_time = bool(re.search(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", ai_text))
                    has_file = ".mp4" in ai_text.lower()
                    need_append = (not (has_time and has_file)) or paper_like
                    if need_append:
                        hybrid_text, hybrid_stats = self._build_hybrid_visual_evidence(
                            user_message,
                            db_limit=6,
                            ocr_limit=3 if paper_like else 2,
                        )
                        if hybrid_text:
                            hybrid_lines = [
                                ln for ln in hybrid_text.splitlines()
                                if ln.strip().startswith("- ")
                            ]
                            if hybrid_lines and "最近录屏证据：" not in ai_text:
                                ai_text = (
                                    ai_text.rstrip()
                                    + "\n\n最近录屏证据：\n"
                                    + "\n".join(hybrid_lines[:6])
                                )
                            ocr_lines = hybrid_stats.get("ocr_lines", []) or []
                            if ocr_lines and "对应视频画面内容：" not in ai_text:
                                ai_text = (
                                    ai_text.rstrip()
                                    + "\n\n对应视频画面内容：\n"
                                    + "\n".join(ocr_lines[:2])
                                )

                    if "对应视频画面内容：" not in ai_text:
                        _, quick_stats = self._build_hybrid_visual_evidence(
                            user_message,
                            db_limit=4,
                            ocr_limit=1,
                        )
                        quick_ocr_lines = quick_stats.get("ocr_lines", []) or []
                        if quick_ocr_lines:
                            ai_text = (
                                ai_text.rstrip()
                                + "\n\n对应视频画面内容：\n"
                                + "\n".join(quick_ocr_lines[:1])
                            )

                # If answer is still vague for visual-memory queries, append hybrid evidence directly.
                if self._is_memory_sensitive_query(user_message):
                    vague_answer = any(k in ai_text for k in ["未找到", "没有找到", "不确定", "无法确定"])
                    if (
                        vague_answer
                        and "可核验的录屏证据：" not in ai_text
                        and "最近录屏证据：" not in ai_text
                    ):
                        hybrid_text, _ = self._build_hybrid_visual_evidence(user_message, db_limit=4, ocr_limit=2)
                        if hybrid_text:
                            hybrid_lines = [
                                ln for ln in hybrid_text.splitlines()
                                if ln.strip().startswith("- ")
                            ]
                            if hybrid_lines:
                                ai_text = (
                                    ai_text.rstrip()
                                    + "\n\n可核验的录屏证据：\n"
                                    + "\n".join(hybrid_lines[:8])
                                )

                # Add concrete content snippets for visual-detail questions.
                if self._is_visual_detail_query(user_message):
                    _, detail_stats = self._build_hybrid_visual_evidence(
                        user_message,
                        db_limit=6,
                        ocr_limit=3,
                    )
                    detail_rows = detail_stats.get("ocr_details", []) or []
                    if detail_rows and "对应视频画面内容：" not in ai_text:
                        detail_lines: List[str] = []
                        for row in detail_rows[:2]:
                            snippets = row.get("snippets", []) or []
                            if not snippets:
                                continue
                            detail_lines.append(
                                f"- {row.get('timestamp', 'Unknown time')} {row.get('basename', '')}："
                                + "；".join(snippets[:3])
                            )
                        if detail_lines:
                            ai_text = (
                                ai_text.rstrip()
                                + "\n\n对应视频画面内容：\n"
                                + "\n".join(detail_lines)
                            )

                if not skip_cache:
                    self._cache_response(user_message, ai_text)
                self.conversation_history.append(ChatMessage("user", user_message))
                self.conversation_history.append(ChatMessage("assistant", ai_text))

                # Return to UI/API first for better perceived latency.
                on_done(ai_text, None)

                # Persist chat memory in background.
                self._persist_chat_memory_async(
                    user_message=user_message,
                    ai_text=ai_text,
                    selected_model=selected_model,
                    context_stats=context_stats,
                    used_context=used_context,
                )

            except Exception as err:
                import traceback

                traceback.print_exc()
                on_done("", f"Error: {str(err)}")

        threading.Thread(target=_run, daemon=True).start()

    def _execute_with_intelligent_agent(self, user_message: str) -> bool:
        """
        Execute using Intelligent Agent with auto-classification (OPTIMIZED).

        The intelligent agent will:
        1. Classify the input (question, task, code, etc.)
        2. Identify query intent (retrieve_fact, find_procedure, etc.)
        3. Dispatch to appropriate handler
        4. Return formatted response

        OPTIMIZATIONS:
        - Reuses event loop instead of creating new one
        - Caches responses for repeated queries
        - Faster pattern-based classification

        Args:
            user_message: The user's message

        Returns:
            True if execution was successful
        """
        import asyncio

        try:
            # OPTIMIZATION: Check cache first
            cached_response = self._get_cached_response(user_message)
            if cached_response:
                print(f"[ChatPresenter] ⚡ Using cached response")

                # Add to history
                assistant_msg = ChatMessage("assistant", cached_response)
                self.conversation_history.append(assistant_msg)

                # Notify view (Kivy + API stream/SSE)
                if self.view:
                    self.view.on_message_added("assistant", cached_response)
                    self.view.on_response_chunk(cached_response)
                    self.view.on_response_completed(cached_response)

                return True

            # OPTIMIZATION: Reuse event loop
            loop = self._get_event_loop()

            # Process input with intelligent agent
            result = loop.run_until_complete(
                self.intelligent_agent.process_input(
                    input_text=user_message,
                    context={
                        "user_id": "chat_user",
                        "session_id": "chat_session"
                    }
                )
            )

            # Format and display response
            response_text = self._format_intelligent_agent_response(result)

            # OPTIMIZATION: Cache the response
            self._cache_response(user_message, response_text)

            # Add assistant message to history
            assistant_msg = ChatMessage("assistant", response_text)
            self.conversation_history.append(assistant_msg)

            # Notify view (both for Kivy and for API stream/SSE)
            if self.view:
                self.view.on_message_added("assistant", response_text)
                self.view.on_response_chunk(response_text)
                self.view.on_response_completed(response_text)

            # Log classification info
            handler = result.get("handler", "unknown")
            print(f"[ChatPresenter] ✅ Intelligent Agent response (handler: {handler})")

            return True

        except Exception as e:
            print(f"[ChatPresenter] Intelligent Agent error: {e}")
            import traceback
            traceback.print_exc()

            # Fall back to standard chat
            print("[ChatPresenter] Falling back to standard chat...")
            return self._execute_standard_chat(user_message)

    def _format_intelligent_agent_response(self, result: Dict[str, Any]) -> str:
        """Format intelligent agent result into chat response"""

        if not result.get("success"):
            return "抱歉，处理您的请求时出错。"

        handler = result.get("handler", "")
        data = result.get("data", {})

        # Format based on handler type
        if handler == "greet":
            return data.get("response", "你好！")

        elif handler == "smart_search":
            # Format search results
            memories = data.get("results", [])
            if memories:
                response = f"🔍 找到 {len(memories)} 条相关信息：\n\n"
                for i, item in enumerate(memories[:5], 1):
                    memory_text = item.get("memory", item.get("text", ""))
                    response += f"{i}. {memory_text}\n"
                return response
            return "未找到相关信息。"

        elif handler == "manage_task":
            return "✅ 任务已添加到列表中。"

        elif handler == "add_task":
            return "✅ 已记住这个任务。"

        elif handler == "code_assistant":
            return data.get("response", "这是我的代码分析。")

        elif handler == "find_procedure":
            procedures = data.get("results", [])
            if procedures:
                return f"📋 找到相关操作步骤：\n\n{procedures[0]}"
            return "未找到相关操作步骤。"

        elif handler == "general_query":
            return data.get("response", "已为您处理。")

        else:
            # Default response
            if isinstance(data, dict) and "response" in data:
                return data["response"]
            return "已处理完成。"

    def _execute_standard_chat(self, user_message: str) -> bool:
        """Execute standard chat flow as fallback (OPTIMIZED)"""
        # Search memory for context
        context = self._search_memory(user_message)

        # Build messages for API
        messages = self._build_messages(user_message, context)

        # Start streaming response
        self._start_streaming(messages)

        return True

    def _execute_with_agent(self, user_message: str) -> bool:
        """
        Execute a complex task using the rule-based Agent Executor.

        This is more reliable than LLM-based planning.

        Args:
            user_message: The user's goal/task

        Returns:
            True if execution was successful
        """
        try:
            # Notify view that we're using Agent mode
            if self.view:
                self.view.on_response_started()

            print(f"[ChatPresenter] 🤖 Agent executing: {user_message}")

            # Execute using AgentExecutor
            result = self.agent_executor.execute_task(user_message)

            if result.get("success"):
                full_response = result.get("response", "")
                print(f"[ChatPresenter] 🤖 Agent completed in {result.get('execution_time', 0):.2f}s")

                # Stream the response
                if self.view:
                    self.view.on_response_chunk(full_response)
                    self.view.on_response_completed(full_response)

                # Add to history
                assistant_msg = ChatMessage("assistant", full_response)
                self.conversation_history.append(assistant_msg)

                return True
            else:
                error_msg = result.get("error", "Agent execution failed")
                print(f"[ChatPresenter] 🤖 Agent error: {error_msg}")

                full_error = f"[!] **Agent execution failed**\n\n{error_msg}\n\n[i] Tip: Try recording some screen content before querying."

                if self.view:
                    self.view.on_response_completed(full_error)

                # Add error to history
                error_msg_obj = ChatMessage("assistant", full_error)
                self.conversation_history.append(error_msg_obj)

                return False

        except Exception as e:
            import traceback
            error_msg = f"Agent execution error: {str(e)}"
            error_trace = traceback.format_exc()

            print(f"[ChatPresenter] 🤖 Agent exception:\n{error_trace}")

            self.handle_error(e, "Failed to execute with agent")

            full_error = f"[!] **Agent execution exception**\n\n{str(e)}\n\n[i] This may be a temporary issue. Please retry or use standard chat mode."

            if self.view:
                self.view.on_response_completed(full_error)

            # Add error to history
            error_msg_obj = ChatMessage("assistant", full_error)
            self.conversation_history.append(error_msg_obj)

            return False

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()

        if self.view:
            self.view.on_history_cleared()

    def refresh_models(self) -> List[str]:
        """
        Refresh the list of available models.

        Returns:
            List of available model names
        """
        self._load_available_models()
        return self.available_models

    # ==================== Private Methods ====================

    def _load_available_models(self):
        """Load available models from Ollama"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                self.available_models = [model["name"] for model in models]

                # Set current model if available
                if self.available_models:
                    if self.current_model not in self.available_models or self._is_embedding_model(self.current_model):
                        self.current_model = self._pick_default_chat_model(self.available_models)

                print(f"[ChatPresenter] Loaded {len(self.available_models)} models")

                # Notify view
                if self.view:
                    self.view.on_models_loaded(self.available_models, self.current_model)

        except Exception as e:
            self.handle_error(e, "Failed to load models")
            # Set default models if API call fails
            self.available_models = [
                "qwen3:1.7b",
                "qwen3:1.7b",
                "llama3.2:3b",
                "gemma2:9b"
            ]

    def _search_memory(self, query: str) -> str:
        """
        Search memory for relevant context (OPTIMIZED).

        Args:
            query: Search query

        Returns:
            Context string with relevant memories
        """
        if not self.memory_system:
            print(f"[ChatPresenter] ⚠️  No memory system available")
            return ""

        try:
            print(f"[ChatPresenter] 🔍 Searching memory for: {query}")

            # OPTIMIZATION: Try smart_search first (faster, category-based)
            if hasattr(self.memory_system, 'smart_search'):
                print(f"[ChatPresenter] ⚡ Using smart_search (category-based)")
                results = self.memory_system.smart_search(
                    query=query,
                    user_id="default_user",
                    limit=self._smart_search_limit  # Only get top 5
                )
            else:
                # Fallback to standard search
                results = self.memory_system.search(query=query, user_id="default_user")

            if not results:
                print(f"[ChatPresenter] ⚠️  No results returned from memory search")
                return ""

            # Handle different result formats
            if isinstance(results, dict):
                if 'results' not in results:
                    print(f"[ChatPresenter] ⚠️  Results missing 'results' key: {list(results.keys())}")
                    return ""
                memories = results['results']
            elif isinstance(results, list):
                memories = results
            else:
                print(f"[ChatPresenter] ⚠️  Unexpected results format: {type(results)}")
                return ""

            if not memories:
                print(f"[ChatPresenter] ⚠️  Empty results list - no memories found for query")
                return ""

            # OPTIMIZATION: Limit results for faster processing
            memories = memories[:self._smart_search_limit]
            print(f"[ChatPresenter] ✅ Found {len(memories)} memories (limited to {self._smart_search_limit})")

            # Prioritize different types of memories
            recording_memories = [
                r for r in memories
                if 'metadata' in r and r['metadata'].get('type') == 'screen_recording'
            ]

            # Prioritize recording memories whose semantic tags match the current query.
            if recording_memories:
                def _recording_rank(row: Dict[str, Any]) -> Tuple[int, str]:
                    meta = row.get("metadata", {}) if isinstance(row, dict) else {}
                    tag_score = self._recording_tag_match_score(meta, query)
                    ts = str(meta.get("timestamp") or meta.get("seen_at") or "")
                    # Higher tag score first, newer first.
                    return (-tag_score, ts)

                recording_memories = sorted(recording_memories, key=_recording_rank, reverse=False)

            ocr_memories = [
                r for r in memories
                if 'metadata' in r and r['metadata'].get('type') == 'ocr_text'
            ]

            chat_memories = [
                r for r in memories
                if 'metadata' in r and r['metadata'].get('type') in {'chat', 'ai_chat'}
            ]

            print(f"[ChatPresenter] - Screen recordings: {len(recording_memories)}")
            print(f"[ChatPresenter] - OCR memories: {len(ocr_memories)}")
            print(f"[ChatPresenter] - Chat memories: {len(chat_memories)}")

            # Build rich context
            context_parts = []

            # Add screen recording context
            if recording_memories:
                context_parts.append("[Video] **Screen Recording Context:**")
                for i, mem in enumerate(recording_memories[:3], 1):  # Top 3 recordings
                    metadata = mem.get('metadata', {})
                    timestamp = metadata.get('timestamp', 'Unknown time')
                    duration = metadata.get('duration', 0)

                    context_parts.append(f"\n{i}. Recording from {timestamp}")
                    context_parts.append(f"   - Duration: {duration:.1f} seconds")
                    context_parts.append(f"   - File: {metadata.get('filename', 'Unknown')}")

                    if 'content_description' in metadata:
                        context_parts.append(f"   - Summary: {metadata['content_description']}")

                    sem_tags = self._extract_recording_tags_from_meta(metadata)
                    if sem_tags:
                        context_parts.append(f"   - Tags: {', '.join(sem_tags[:6])}")

                    if 'ocr_text' in metadata and metadata['ocr_text']:
                        # Include OCR text preview (first 200 chars)
                        ocr_preview = metadata['ocr_text'][:200]
                        if len(metadata['ocr_text']) > 200:
                            ocr_preview += "..."
                        context_parts.append(f"   - Text on screen: \"{ocr_preview}\"")

            # Add OCR context if available
            if ocr_memories:
                context_parts.append("\n[Doc] **Related Text Content:**")
                for i, mem in enumerate(ocr_memories[:2], 1):  # Top 2 OCR results
                    metadata = mem.get('metadata', {})
                    if 'ocr_text' in metadata and metadata['ocr_text']:
                        text = metadata['ocr_text'][:300]  # First 300 chars
                        if len(metadata['ocr_text']) > 300:
                            text += "..."
                        context_parts.append(f"\n{i}. {text}")

            # Add chat context if relevant
            if chat_memories:
                context_parts.append("\n[Chat] **Previous Conversations:**")
                for i, mem in enumerate(chat_memories[:2], 1):  # Top 2 chats
                    metadata = mem.get('metadata', {})
                    timestamp = metadata.get('timestamp', 'Unknown time')
                    content = metadata.get('content', '')[:200]
                    if len(metadata.get('content', '')) > 200:
                        content += "..."
                    context_parts.append(f"\n{i}. From {timestamp}:")
                    context_parts.append(f"   {content}")

            return "\n".join(context_parts)

        except Exception as e:
            print(f"[ChatPresenter] Memory search failed: {e}")
            return ""

    def _build_messages(self, user_message: str, context: str) -> List[Dict[str, str]]:
        """
        Build messages list for Ollama API with humanized prompts.

        Args:
            user_message: User's message
            context: Context from memory search

        Returns:
            List of message dictionaries
        """
        messages = []

        # Import humanized prompt builder
        from ..prompts.chat_prompts import ChatPromptBuilder

        # Detect query type
        query_type = ChatPromptBuilder.detect_query_type(user_message)

        # Build system prompt with appropriate template
        if context:
            system_prompt = ChatPromptBuilder.build_with_context(context, user_message, query_type)
        else:
            system_prompt = ChatPromptBuilder.build_without_context(user_message, query_type)

        messages.append({"role": "system", "content": system_prompt})

        # Add conversation history (last 10 messages for context)
        recent_history = self.conversation_history[-10:]
        for msg in recent_history:
            messages.append(msg.to_dict())

        return messages

    def _start_streaming(self, messages: List[Dict[str, str]]):
        """
        Start streaming AI response.

        Args:
            messages: Messages to send to API
        """
        self.is_streaming = True
        self.stream_queue = queue.Queue()

        # Start streaming in background thread
        self.stream_thread = threading.Thread(
            target=self._stream_response,
            args=(messages,),
            daemon=True
        )
        self.stream_thread.start()

        # Notify view
        if self.view:
            self.view.on_response_started()

        # Start processing stream
        self._process_stream()

    def _stop_streaming(self):
        """Stop streaming response"""
        self.is_streaming = False

        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2)

    def _stream_response(self, messages: List[Dict[str, str]]):
        """
        Stream response from Ollama API with intelligent model routing (runs in background thread).

        Args:
            messages: Messages to send
        """
        try:
            # Import intelligent model router
            from ..llm.model_router import get_router

            # Get last user message for routing decision
            user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break

            # Get router and route to optimal model
            router = get_router(self.available_models)
            selected_model, model_config = router.route(user_message)

            # Get optimized parameters for this query
            optimized_params = router.get_optimized_parameters(user_message, model_config)

            # Build request with intelligent routing
            request_data = {
                "model": selected_model,
                "prompt": messages[-1]["content"],
                "messages": [msg.to_dict() for msg in self.conversation_history[-10:]],
                "stream": True,
                "options": {
                    "temperature": optimized_params["temperature"],
                    "top_p": optimized_params["top_p"],
                    "top_k": optimized_params["top_k"],
                    "num_predict": optimized_params["num_predict"],
                    "num_ctx": optimized_params["num_ctx"],
                    "repeat_penalty": optimized_params.get("repeat_penalty", 1.15),
                }
            }

            print(f"[ChatPresenter] 🧠 Intelligent routing:")
            print(f"  - Model: {selected_model} ({model_config.tier.value} tier)")
            print(f"  - Quality score: {model_config.quality_score:.2f}")
            print(f"  - Est. latency: {model_config.avg_latency_ms}ms")
            print(f"  - Temperature: {optimized_params['temperature']}")

            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=request_data,
                stream=True,
                timeout=120
            )

            if response.status_code == 200:
                for line in response.iter_lines():
                    if not self.is_streaming:
                        break

                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get("response", "")

                            if chunk:
                                self.stream_queue.put(chunk)

                            if data.get("done", False):
                                self.stream_queue.put(None)  # Signal end of stream
                                break

                        except json.JSONDecodeError:
                            continue
            else:
                error_msg = f"API error: {response.status_code}"
                self.stream_queue.put({"error": error_msg})

        except Exception as e:
            self.stream_queue.put({"error": str(e)})

        finally:
            self.is_streaming = False

    def _process_stream(self):
        """Process streaming response (runs in main thread via polling)"""
        full_response = ""

        while self.is_streaming:
            try:
                # Get chunk from queue (with timeout)
                chunk = self.stream_queue.get(timeout=0.1)

                if chunk is None:
                    # End of stream
                    break

                if isinstance(chunk, dict) and "error" in chunk:
                    # Error occurred
                    self.show_error(chunk["error"])
                    break

                # Append to response
                full_response += chunk

                # Notify view of new chunk
                if self.view:
                    self.view.on_response_chunk(chunk)

            except queue.Empty:
                # No chunk available, continue polling
                continue

        # Add assistant message to history
        if full_response:
            assistant_msg = ChatMessage("assistant", full_response)
            self.conversation_history.append(assistant_msg)

        # Notify view of completion
        if self.view:
            self.view.on_response_completed(full_response)

        # Reset streaming state
        self.is_streaming = False

    def export_conversation(self, filepath: str) -> bool:
        """
        Export conversation to file.

        Args:
            filepath: Path to save file

        Returns:
            True if export successful
        """
        try:
            export_data = {
                "model": self.current_model,
                "messages": [msg.to_dict() for msg in self.conversation_history],
                "exported_at": str(__import__("datetime").datetime.now())
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            if self.view:
                self.view.on_conversation_exported(filepath)

            return True

        except Exception as e:
            self.handle_error(e, f"Failed to export conversation to {filepath}")
            return False

    def import_conversation(self, filepath: str) -> bool:
        """
        Import conversation from file.

        Args:
            filepath: Path to load file from

        Returns:
            True if import successful
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load messages
            self.conversation_history.clear()
            for msg_data in data.get("messages", []):
                msg = ChatMessage(msg_data["role"], msg_data["content"])
                self.conversation_history.append(msg)

            # Load model
            model = data.get("model")
            if model and model in self.available_models:
                self.current_model = model

            # Notify view
            if self.view:
                self.view.on_conversation_imported(len(self.conversation_history))

            return True

        except Exception as e:
            self.handle_error(e, f"Failed to import conversation from {filepath}")
            return False
