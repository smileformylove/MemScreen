### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT               ###

"""
Chat Screen for AI conversation functionality - Kivy Version
"""

import queue
import threading
import requests
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.lang import Builder

from .base_screen import BaseScreen
from ..components.colors_kivy import *


class ChatScreen(BaseScreen):
    """AI Chat screen with Kivy UI"""

    # UI Components
    chat_input = ObjectProperty(None)
    chat_history = ObjectProperty(None)
    model_spinner = ObjectProperty(None)
    typing_indicator = ObjectProperty(None)

    # State
    current_model = StringProperty("qwen2.5vl:3b")
    is_typing = BooleanProperty(False)
    conversation_history = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typing_message_ref = None

    def on_enter(self):
        """Called when screen is displayed"""
        # Load models when screen is shown
        Clock.schedule_once(self._load_models, 0.5)

    def _load_models(self, dt):
        """Load available Ollama models"""
        try:
            response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
            response.raise_for_status()
            models_data = response.json()

            models = [model['name'] for model in models_data.get('models', [])]

            if self.model_spinner:
                self.model_spinner.values = models

                # Set default model
                if self.current_model in models:
                    self.model_spinner.text = self.current_model

            print(f"[ChatScreen] Loaded {len(models)} models")

        except Exception as e:
            print(f"[ChatScreen] Failed to load models: {e}")
            if self.presenter:
                self.presenter.show_error(f"Failed to load models: {e}")

    def on_model_change(self, spinner_text):
        """Handle model selection change"""
        self.current_model = spinner_text
        print(f"[ChatScreen] Model changed to: {self.current_model}")

    def send_message(self):
        """Send chat message to AI"""
        user_input = self.chat_input.text.strip() if self.chat_input else ""
        if not user_input:
            return

        print(f"[ChatScreen] Sending message: {user_input[:50]}...")

        # Clear input
        if self.chat_input:
            self.chat_input.text = ""

        # Add user message to UI
        self._add_user_message(user_input)

        # Show typing indicator
        self._show_typing_indicator()

        # Delegate to presenter
        if self.presenter:
            # Search memory first
            related_memories = self.presenter.memory_system.search(
                query=user_input,
                user_id="screenshot"
            )

            # Build context
            context = self._build_context(related_memories)

            # Send message via presenter
            self.presenter.send_message(user_input, context)
        else:
            # Fallback: send directly
            self._send_direct_message(user_input)

    def _send_direct_message(self, user_input):
        """Send message directly without presenter (fallback)"""
        # Build messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Provide concise answers."}
        ]
        messages.extend(self.conversation_history[-4:])  # Last 4 messages
        messages.append({"role": "user", "content": user_input})

        # Send in background thread
        message_queue = queue.Queue()
        thread = threading.Thread(
            target=self._send_to_ollama,
            args=(messages, self.current_model, message_queue),
            daemon=True
        )
        thread.start()

        # Process response
        self._process_response(message_queue, thread)

    def _send_to_ollama(self, messages, model_name, message_queue):
        """Send request to Ollama API"""
        url = "http://127.0.0.1:11434/api/chat"

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": 500,
                "temperature": 0.7
            }
        }

        try:
            print(f"[ChatScreen] Sending to Ollama: model={model_name}")
            response = requests.post(url, json=payload, stream=False, timeout=120)
            response.raise_for_status()

            result = response.json()
            full_response = result.get("message", {}).get("content", "")

            print(f"[ChatScreen] Response received: {len(full_response)} chars")
            message_queue.put(("done", full_response))

        except Exception as e:
            print(f"[ChatScreen] Ollama request failed: {e}")
            message_queue.put(("error", str(e)))

    def _process_response(self, message_queue, thread):
        """Process AI response and update UI"""
        import time
        start_time = time.time()

        def check_queue(dt):
            if time.time() - start_time > 60:
                # Timeout
                self._hide_typing_indicator()
                self._add_ai_message("⚠️ Response timeout. Please try again.")
                return False

            try:
                item = message_queue.get(timeout=0.1)

                if item[0] == "done":
                    self._hide_typing_indicator()
                    response_text = item[1]
                    self._add_ai_message(response_text)

                    # Save to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response_text
                    })
                    return False

                elif item[0] == "error":
                    self._hide_typing_indicator()
                    self._add_ai_message(f"❌ Error: {item[1]}")
                    return False

            except queue.Empty:
                if not thread.is_alive():
                    self._hide_typing_indicator()
                    self._add_ai_message("⚠️ No response from AI. Check if Ollama is running.")
                    return False

                # Continue checking
                return True

        # Check queue every 0.1 seconds
        Clock.schedule_interval(check_queue, 0.1)

    def _build_context(self, related_memories):
        """Build context from related memories"""
        if not related_memories or 'results' not in related_memories:
            return ""

        if len(related_memories['results']) == 0:
            return ""

        # Prioritize screen recording memories
        recording_memories = [
            r for r in related_memories['results']
            if 'metadata' in r and r['metadata'].get('type') == 'screen_recording'
        ]

        if recording_memories:
            # Use most relevant recording
            top_memory = recording_memories[0]
            metadata = top_memory.get('metadata', {})

            context = f"Relevant Screen Recording Found:\n"
            context += f"- Video File: {metadata.get('filename', 'N/A')}\n"
            context += f"- Duration: {metadata.get('duration', 0):.1f} seconds\n"
            context += f"- Recorded at: {metadata.get('timestamp', 'unknown')}\n"
            if 'content_description' in metadata:
                context += f"- Content: {metadata['content_description']}\n"
            context += "\nThe user can view this video in the Video tab.\n"
            return context
        else:
            # Use general memory
            top_memory = related_memories['results'][0]['memory']
            if len(top_memory) > 500:
                top_memory = top_memory[:500] + "..."
            return f"Context: {top_memory}\n"

    def _add_user_message(self, message):
        """Add user message to chat history"""
        if not self.chat_history:
            return

        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")

        # Format: 👤 You • HH:MM\nmessage\n\n
        formatted = f"👤 You • {timestamp}\n{message}\n\n"

        self.chat_history.text += formatted

        # Scroll to bottom
        Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)

    def _add_ai_message(self, message):
        """Add AI message to chat history"""
        if not self.chat_history:
            return

        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")

        # Format: 🤖 AI • HH:MM\nmessage\n\n
        formatted = f"🤖 AI • {timestamp}\n{message}\n\n"

        self.chat_history.text += formatted

        # Scroll to bottom
        Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)

    def _show_typing_indicator(self):
        """Show typing indicator"""
        self.is_typing = True

        if self.chat_history:
            self._typing_message_ref = "🤖 AI is typing...\n\n"
            self.chat_history.text += self._typing_message_ref
            self._scroll_to_bottom()

    def _hide_typing_indicator(self):
        """Hide typing indicator"""
        self.is_typing = False

        if self.chat_history and self._typing_message_ref:
            # Remove typing indicator
            current_text = self.chat_history.text
            if self._typing_message_ref in current_text:
                self.chat_history.text = current_text.replace(self._typing_message_ref, "")
            self._typing_message_ref = None

    def _scroll_to_bottom(self):
        """Scroll chat history to bottom"""
        if self.chat_history:
            self.chat_history.scroll_y = 0

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        if self.chat_history:
            self.chat_history.text = ""
        print("[ChatScreen] Conversation history cleared")

    def export_history(self):
        """Export conversation history"""
        if not self.chat_history:
            return

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{timestamp}.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.chat_history.text)
            print(f"[ChatScreen] Chat history exported to {filename}")
        except Exception as e:
            print(f"[ChatScreen] Failed to export: {e}")

    # Presenter callbacks
    def on_models_loaded(self, models, current_model):
        """Called when models are loaded"""
        if self.model_spinner:
            self.model_spinner.values = models
            if current_model in models:
                self.model_spinner.text = current_model

    def on_message_added(self, role, message):
        """Called when a message is added"""
        if role == "user":
            self._add_user_message(message)
        else:
            self._add_ai_message(message)

    def on_response_started(self):
        """Called when AI starts responding"""
        self._show_typing_indicator()

    def on_response_chunk(self, chunk):
        """Called for each chunk of streaming response"""
        # For streaming support (future)
        pass

    def on_response_completed(self, full_response):
        """Called when AI response is complete"""
        self._hide_typing_indicator()
        self._add_ai_message(full_response)

    def on_history_cleared(self):
        """Called when history is cleared"""
        self.clear_history()

    def on_conversation_exported(self, filename):
        """Called when conversation is exported"""
        print(f"[ChatScreen] Conversation exported to {filename}")


# Register KV language
Builder.load_string('''
<ChatScreen>:
    FloatLayout:
        # Header
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.12
            pos_hint: {'top': 1.0}

            # Title bar
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: 0.5
                padding: [20, 10, 20, 5]

                Label:
                    text: "🤖 AI Chat"
                    font_size: 28
                    bold: True
                    color: PRIMARY_COLOR
                    size_hint_x: 0.7

                # Model selector
                Label:
                    text: "Model:"
                    font_size: 16
                    color: TEXT_LIGHT
                    size_hint_x: 0.1
                    halign: 'right'
                    text_size: self.size

                Spinner:
                    id: model_spinner
                    text: 'qwen2.5vl:3b'
                    values: []
                    size_hint_x: 0.2
                    font_size: 14
                    background_color: SURFACE_COLOR
                    color: TEXT_COLOR
                    on_text: root.on_model_change(self.text)

        # Helper text
        Label:
            text: "💡 Ask anything about your screen recordings!"
            font_size: 14
            color: TEXT_LIGHT
            size_hint_y: None
            height: 30
            halign: 'center'
            text_size: self.size

        # Chat history
        BoxLayout:
            orientation: 'vertical'
            pos_hint: {'top': 0.88}
            size_hint_y: 0.65
            padding: [15, 10, 15, 10]

            ScrollView:
                id: chat_scroll
                size_hint_y: 0.9
                bar_width: 10
                bar_color: PRIMARY_COLOR
                bar_margin: -5

                TextInput:
                    id: chat_history
                    text: ""
                    readonly: True
                    font_size: 16
                    foreground_color: TEXT_COLOR
                    background_color: BG_COLOR
                    padding: [20, 20, 20, 20]
                    size_hint_y: None
                    height: self.minimum_height
                    text_size: None, None

        # Input area
        BoxLayout:
            orientation: 'vertical'
            pos_hint: {'y': 0}
            size_hint_y: 0.23
            padding: [15, 5, 15, 15]
            spacing: 10

            # Input box with send button
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: 0.7
                spacing: 10

                TextInput:
                    id: chat_input
                    text: ""
                    hint_text: "Type your message here..."
                    font_size: 16
                    foreground_color: TEXT_COLOR
                    background_color: INPUT_BG_COLOR
                    multiline: False
                    padding: [15, 15, 15, 15]
                    size_hint_x: 0.85
                    on_text_validate: root.send_message()

                Button:
                    text: "Send ➤"
                    font_size: 18
                    bold: True
                    size_hint_x: 0.15
                    background_color: BUTTON_PRIMARY
                    color: BUTTON_TEXT_COLOR
                    on_release: root.send_message()

            # Typing indicator (shown when AI is responding)
            Label:
                id: typing_indicator
                text: "AI is thinking..."
                font_size: 14
                color: PROCESSING_TEXT
                size_hint_y: 0.3
                opacity: 1 if root.is_typing else 0
                halign: 'center'
                text_size: self.size
''')


__all__ = ["ChatScreen"]
