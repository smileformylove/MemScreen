### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""Presenter for AI Chat functionality (MVP Pattern)"""

import json
import queue
import threading
import requests
from typing import Optional, List, Dict, Any, Callable
import asyncio

from .base_presenter import BasePresenter
from .agent_executor import AgentExecutor

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

        self._is_initialized = False

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

    def send_message_sync(
        self,
        user_message: str,
        on_done: Callable[[str, Optional[str]], None],
    ) -> None:
        """
        Send a user message and get full AI response in background; call on_done(ai_text, error_text) when done.
        Replicates original Kivy chat logic 1:1 (memory search, model selection, LLM call, save to memory).
        Call from UI: start a thread that calls this, or call this and let it start the thread; on_done runs
        in worker thread so UI should use Clock.schedule_once inside on_done to update on main thread.

        Args:
            user_message: The user's message
            on_done: Callback(ai_text, error_text). error_text is None on success; str on error.
        """
        def _run():
            ai_text = ""
            error_msg_text = None
            try:
                from ..llm import OllamaLLM

                context = ""
                has_relevant_memory = False
                memory_count = 0

                if self.memory_system:
                    try:
                        search_result = self.memory_system.search(
                            query=user_message,
                            user_id="default_user",
                            limit=5,
                            threshold=0.0,
                        )
                        if search_result and "results" in search_result:
                            memories = search_result["results"]
                            memory_count = len(memories) if memories else 0
                            if memories and len(memories) > 0:
                                has_relevant_memory = True
                                context_parts = []
                                for mem in memories[:3]:
                                    if isinstance(mem, dict):
                                        if "memory" in mem:
                                            content = mem["memory"]
                                        elif "content" in mem:
                                            content = mem["content"]
                                        else:
                                            content = str(mem)
                                        context_parts.append(f"- {content}")
                                if context_parts:
                                    context = "Relevant context from memory:\n" + "\n".join(context_parts)
                                    print(f"[Chat] Found {len(memories)} relevant memories")
                    except Exception as mem_err:
                        print(f"[Chat] Memory search failed: {mem_err}")

                if has_relevant_memory and memory_count >= 2:
                    selected_model = "gemma3:270m"
                    print(f"[Chat] Using small model (gemma3:270m) - {memory_count} memories found")
                else:
                    selected_model = "qwen3:1.7b"
                    print(f"[Chat] Using large model (qwen3:1.7b) - {memory_count} memories found")

                llm = OllamaLLM(config={"model": selected_model})

                system_prompt = """You are MemScreen, a helpful AI assistant. You help users with:
- Answering questions about their screen recordings and activities
- Providing information from their memory
- Assisting with general knowledge
- Being friendly and concise

Respond naturally without mentioning your model provider or technical details."""

                messages = []
                if context:
                    messages.append({"role": "system", "content": f"{system_prompt}\n\nHere is some relevant context from the user's memory:\n\n{context}"})
                else:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": user_message})

                response = llm.generate_response(messages)

                if response:
                    ai_text = str(response)
                    if self.memory_system:
                        try:
                            from datetime import datetime
                            conversation = [
                                {"role": "user", "content": user_message},
                                {"role": "assistant", "content": ai_text},
                            ]
                            self.memory_system.add(
                                conversation,
                                user_id="default_user",
                                metadata={
                                    "source": "ai_chat",
                                    "timestamp": datetime.now().isoformat(),
                                    "model": selected_model,
                                    "memory_count": memory_count,
                                    "used_context": has_relevant_memory,
                                },
                                infer=True,
                            )
                            print(f"[Chat] Saved conversation to memory")
                        except Exception as mem_err:
                            print(f"[Chat] Failed to save conversation to memory: {mem_err}")
                else:
                    ai_text = "I apologize, but I couldn't generate a response."

            except Exception as err:
                error_msg_text = f"Error: {str(err)}"
                import traceback
                traceback.print_exc()

            try:
                on_done(ai_text, error_msg_text)
            except Exception:
                pass

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

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
                if self.current_model not in self.available_models and self.available_models:
                    self.current_model = self.available_models[0]

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
                    user_id="screenshot",
                    limit=self._smart_search_limit  # Only get top 5
                )
            else:
                # Fallback to standard search
                results = self.memory_system.search(query=query, user_id="screenshot")

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
                r for r in results['results']
                if 'metadata' in r and r['metadata'].get('type') == 'screen_recording'
            ]

            ocr_memories = [
                r for r in results['results']
                if 'metadata' in r and r['metadata'].get('type') == 'ocr_text'
            ]

            chat_memories = [
                r for r in results['results']
                if 'metadata' in r and r['metadata'].get('type') == 'chat'
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
