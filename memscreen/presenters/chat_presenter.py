### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Presenter for AI Chat functionality (MVP Pattern)"""

import json
import queue
import threading
import requests
from typing import Optional, List, Dict, Any, Callable

from .base_presenter import BasePresenter


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
        self.ollama_base_url = ollama_base_url

        # Chat state
        self.conversation_history: List[ChatMessage] = []
        self.current_model = "qwen2.5vl:3b"
        self.available_models = []

        # Streaming state
        self.is_streaming = False
        self.stream_queue = None
        self.stream_thread = None

        self._is_initialized = False

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

        self._is_initialized = False

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

    def send_message(self, user_message: str) -> bool:
        """
        Send a user message and get AI response.

        Args:
            user_message: The user's message

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
                "qwen2.5vl:3b",
                "qwen3:1.7b",
                "llama3.2:3b",
                "gemma2:9b"
            ]

    def _search_memory(self, query: str) -> str:
        """
        Search memory for relevant context.

        Args:
            query: Search query

        Returns:
            Context string with relevant memories
        """
        if not self.memory_system:
            return ""

        try:
            print(f"[ChatPresenter] Searching memory for: {query}")

            results = self.memory_system.search(query=query, user_id="screenshot")

            if not results or 'results' not in results or not results['results']:
                return ""

            # Prioritize screen recordings
            recording_memories = [
                r for r in results['results']
                if 'metadata' in r and r['metadata'].get('type') == 'screen_recording'
            ]

            # Build context
            context_parts = []

            if recording_memories:
                metadata = recording_memories[0].get('metadata', {})
                context_parts.append(f"Relevant Screen Recording Found:")
                context_parts.append(f"- Video File: {metadata['filename']}")
                context_parts.append(f"- Duration: {metadata.get('duration', 0):.1f} seconds")

                if 'content_description' in metadata:
                    context_parts.append(f"- Content: {metadata['content_description']}")

            return "\n".join(context_parts)

        except Exception as e:
            print(f"[ChatPresenter] Memory search failed: {e}")
            return ""

    def _build_messages(self, user_message: str, context: str) -> List[Dict[str, str]]:
        """
        Build messages list for Ollama API.

        Args:
            user_message: User's message
            context: Context from memory search

        Returns:
            List of message dictionaries
        """
        messages = []

        # Add system prompt with context if available
        if context:
            system_prompt = f"""You are a helpful AI assistant that answers questions about the user's screen recordings and activity.

Relevant Context:
{context}

When answering:
- Reference the screen recordings and content found
- Be specific about what was on the screen
- If you don't know something, say so
- Keep answers concise and helpful"""
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
        Stream response from Ollama API (runs in background thread).

        Args:
            messages: Messages to send
        """
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": messages[-1]["content"],
                    "messages": [msg.to_dict() for msg in self.conversation_history[-10:]],
                    "stream": True
                },
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
