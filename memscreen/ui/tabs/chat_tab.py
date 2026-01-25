### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Chat tab for AI conversation functionality"""

import json
import queue
import threading
import tkinter as tk
import requests
from tkinter import ttk, scrolledtext

from .base_tab import BaseTab
from ..components.colors import COLORS, FONTS, ANIMATION_COLORS, STATUS_COLORS
from ..components.animations import TypingIndicator, ScrollAnimator
from ...prompts import MEMORY_ANSWER_PROMPT
from ...memory import Memory


class ChatTab(BaseTab):
    """Chat with AI tab"""

    def __init__(self, parent, app, mem):
        super().__init__(parent, app)
        self.mem = mem
        self.model_var = None
        self.model_combo = None
        self.chat_history = None
        self.chat_input = None
        self.thinking_label = None
        self.typing_indicator_canvas = None
        self.typing_dots = None
        self.current_model = "qwen3:1.7b"
        self.conversation_history = []
        self.message_count = 0

    def create_ui(self):
        """Create chat tab UI"""
        self.frame = tk.Frame(self.parent, bg=COLORS["bg"])

        # Model selector
        model_bar = tk.Frame(self.frame, bg=COLORS["surface"], height=50)
        model_bar.pack(fill=tk.X, pady=(0, 10))
        model_bar.pack_propagate(False)

        tk.Label(
            model_bar,
            text="Model:",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text_light"]
        ).pack(side=tk.LEFT, padx=15)

        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            model_bar,
            textvariable=self.model_var,
            state="readonly",
            font=FONTS["body"],
            width=20
        )
        self.model_combo.pack(side=tk.LEFT, padx=10)
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_change)

        refresh_btn = tk.Button(
            model_bar,
            text="🔄 Refresh",
            font=("Helvetica", 12, "bold"),
            bg="#C7D2FE",
            fg="#000000",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2",
            command=self.load_models
        )
        refresh_btn.pack(side=tk.LEFT, padx=10)

        # Chat history
        chat_container = tk.Frame(self.frame, bg=COLORS["surface"])
        chat_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.chat_history = scrolledtext.ScrolledText(
            chat_container,
            wrap=tk.WORD,
            font=FONTS["body"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
            relief=tk.FLAT,
            padx=20,
            pady=20
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True)

        # Configure tags for enhanced chat UI
        self.chat_history.tag_configure("user", foreground=COLORS["primary"],
                                        font=(FONTS["body"][0], FONTS["body"][1], "bold"))
        self.chat_history.tag_configure("ai", foreground=COLORS["secondary"],
                                       font=(FONTS["body"][0], FONTS["body"][1], "bold"))
        self.chat_history.tag_configure("user_msg", background=COLORS["chat_user_bg"],
                                       lmargin1=10, lmargin2=10, rmargin=10, spacing1=5, spacing3=5)
        self.chat_history.tag_configure("ai_msg", background=COLORS["chat_ai_bg"],
                                       lmargin1=10, lmargin2=10, rmargin=10, spacing1=5, spacing3=5)
        self.chat_history.tag_configure("timestamp", foreground=COLORS["text_muted"],
                                       font=FONTS["small"])
        self.chat_history.tag_configure("avatar", font=("Segoe UI", 14))

        # Add typing indicator canvas (hidden initially)
        self.typing_indicator_canvas = tk.Canvas(
            chat_container,
            width=60,
            height=20,
            bg=COLORS["chat_ai_bg"],
            highlightthickness=0
        )

        # Input area
        input_frame = tk.Frame(self.frame, bg=COLORS["surface"], height=100)
        input_frame.pack(fill=tk.X)
        input_frame.pack_propagate(False)

        self.chat_input = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=FONTS["body"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief=tk.FLAT,
            padx=15,
            pady=10,
            height=3
        )
        self.chat_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.chat_input.bind("<Return>", self.on_chat_enter)

        # Send button
        send_btn = tk.Button(
            input_frame,
            text="Send ➤",
            font=("Helvetica", 12, "bold"),
            bg="#C7D2FE",
            fg="#000000",
            relief=tk.RAISED,
            bd=3,
            cursor="hand2",
            padx=20,
            pady=10,
            command=self.send_chat_message
        )
        send_btn.place(relx=0.95, rely=0.5, anchor=tk.E)

        self.thinking_label = tk.Label(
            input_frame,
            text="AI is thinking...",
            font=FONTS["small"],
            bg=COLORS["surface"],
            fg=STATUS_COLORS["processing"]["text"]
        )

    def load_models(self):
        """Load available Ollama models"""
        try:
            response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
            response.raise_for_status()
            models_data = response.json()

            models = [model['name'] for model in models_data.get('models', [])]
            self.model_combo['values'] = models

            if models:
                self.model_combo.current(0)
                self.current_model = models[0]
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to load models: {e}")

    def on_model_change(self, event):
        """Handle model selection change"""
        self.current_model = self.model_var.get()

    def on_chat_enter(self, event):
        """Handle Enter key in chat input"""
        if event.state & 0x4:  # Ctrl+Enter for new line
            return "continue"
        self.send_chat_message()
        return "break"

    def send_chat_message(self):
        """Send chat message to AI with animations"""
        user_input = self.chat_input.get("1.0", tk.END).strip()
        if not user_input:
            return

        # Add screen memory context
        enhanced_input = MEMORY_ANSWER_PROMPT + "\n\n" + user_input
        related_memories = self.mem.search(query=enhanced_input, user_id="screenshot")
        if related_memories and 'results' in related_memories and len(related_memories['results']) > 0:
            enhanced_input = related_memories['results'][0]['memory'] + '\n\n' + enhanced_input

        self.chat_input.delete("1.0", tk.END)

        # Add user message to chat with timestamp and avatar
        self._add_user_message(user_input)

        # Show typing indicator
        self._show_typing_indicator()

        # Send to AI in background thread
        message_queue = queue.Queue()
        thread = threading.Thread(
            target=self.send_to_ollama,
            args=(enhanced_input, self.current_model, message_queue),
            daemon=True
        )
        thread.start()

        # Update UI with response
        self.process_ai_response(message_queue, thread)

    def _add_user_message(self, message: str):
        """Add user message with enhanced formatting"""
        from datetime import datetime

        self.chat_history.config(state=tk.NORMAL)

        # Add avatar
        self.chat_history.insert(tk.END, "👤 ", "avatar")

        # Add sender label
        self.chat_history.insert(tk.END, "You", "user")

        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_history.insert(tk.END, f" • {timestamp}\n", "timestamp")

        # Add message with animation effect
        self.chat_history.insert(tk.END, f"{message}\n\n", "user_msg")

        self.chat_history.config(state=tk.DISABLED)

        # Smooth scroll to bottom
        ScrollAnimator.scroll_to_bottom(self.chat_history, duration=150)

    def _add_ai_message(self, message: str):
        """Add AI message with enhanced formatting"""
        from datetime import datetime

        self.chat_history.config(state=tk.NORMAL)

        # Add avatar
        self.chat_history.insert(tk.END, "🤖 ", "avatar")

        # Add sender label
        self.chat_history.insert(tk.END, "AI", "ai")

        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_history.insert(tk.END, f" • {timestamp}\n", "timestamp")

        # Add message
        self.chat_history.insert(tk.END, f"{message}\n\n", "ai_msg")

        self.chat_history.config(state=tk.DISABLED)

        # Smooth scroll to bottom
        ScrollAnimator.scroll_to_bottom(self.chat_history, duration=150)

    def _show_typing_indicator(self):
        """Show animated typing indicator"""
        # Add typing indicator to chat
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, "🤖 AI is typing", "ai")

        # Create typing indicator canvas with bouncing dots
        self.typing_dots = TypingIndicator.create(
            self.typing_indicator_canvas,
            x=30, y=10,
            color=ANIMATION_COLORS["typing"][0],
            dot_radius=2
        )

        self.chat_history.window_create(tk.END, window=self.typing_indicator_canvas)
        self.chat_history.insert(tk.END, "\n\n")
        self.chat_history.config(state=tk.DISABLED)
        self.chat_history.see(tk.END)

    def _hide_typing_indicator(self):
        """Hide typing indicator"""
        if self.typing_indicator_canvas:
            try:
                self.typing_indicator_canvas.destroy()
                self.typing_indicator_canvas = None
            except:
                pass

    def send_to_ollama(self, prompt, model_name, message_queue):
        """Send request to Ollama"""
        url = "http://127.0.0.1:11434/api/chat"
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True
        }

        try:
            response = requests.post(url, json=payload, stream=True, timeout=60)
            response.raise_for_status()

            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data_str = line.decode('utf-8').replace("data: ", "", 1)
                        if data_str == "[DONE]":
                            break

                        data = json.loads(data_str)
                        if "message" in data and "content" in data["message"]:
                            chunk = data["message"]["content"]
                            full_response += chunk
                            message_queue.put(("chunk", chunk))
                    except (json.JSONDecodeError, KeyError):
                        pass

            message_queue.put(("done", full_response))

        except Exception as e:
            message_queue.put(("error", str(e)))

    def process_ai_response(self, message_queue, thread):
        """Process AI response and update UI with smooth animations"""
        # Remove typing indicator
        self._hide_typing_indicator()

        # Start AI message header
        from datetime import datetime
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, "🤖 ", "avatar")
        self.chat_history.insert(tk.END, "AI", "ai")
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_history.insert(tk.END, f" • {timestamp}\n", "timestamp")

        response_buffer = ""

        def update():
            nonlocal response_buffer
            try:
                item = message_queue.get_nowait()
                if item[0] == "chunk":
                    # Accumulate response chunks
                    chunk = item[1]
                    response_buffer += chunk

                    # Insert chunk with streaming effect
                    self.chat_history.insert(tk.END, chunk)
                    self.chat_history.see(tk.END)

                    # Continue updating
                    self.root.after(10, update)

                elif item[0] == "done":
                    # Complete the message
                    self.chat_history.insert(tk.END, "\n\n", "ai_msg")
                    self.chat_history.config(state=tk.DISABLED)

                    # Hide thinking label
                    self.thinking_label.place_forget()

                    # Save to conversation history
                    self.conversation_history.append({"role": "assistant", "content": response_buffer})

                    # Smooth scroll to bottom
                    ScrollAnimator.scroll_to_bottom(self.chat_history, duration=150)

                elif item[0] == "error":
                    # Show error
                    self.chat_history.insert(tk.END, f"\nError: {item[1]}\n\n", "ai_msg")
                    self.chat_history.config(state=tk.DISABLED)
                    self.thinking_label.place_forget()
                    ScrollAnimator.scroll_to_bottom(self.chat_history, duration=150)

            except queue.Empty:
                if thread.is_alive():
                    self.root.after(10, update)
                else:
                    # Thread ended but no final message received
                    if response_buffer:
                        self.chat_history.insert(tk.END, "\n\n", "ai_msg")
                    self.chat_history.config(state=tk.DISABLED)
                    self.thinking_label.place_forget()
                    ScrollAnimator.scroll_to_bottom(self.chat_history, duration=150)

        update()


__all__ = ["ChatTab"]
