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
        self.current_model = "qwen2.5vl:3b"  # Better quality model with vision support
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

        # Input area - increased height
        input_frame = tk.Frame(self.frame, bg=COLORS["surface"], height=150)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        input_frame.pack_propagate(False)

        # Add helper text
        helper_label = tk.Label(
            input_frame,
            text="💡 Ask anything about your screen recordings! AI will search and answer intelligently.",
            font=("Helvetica", 11, "normal"),
            bg=COLORS["surface"],
            fg=COLORS["text_light"]
        )
        helper_label.pack(pady=(5, 5))

        self.chat_input = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=("Helvetica", 12, "normal"),
            bg=COLORS["input_bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief=tk.SOLID,
            bd=3,
            padx=15,
            pady=10,
            height=4
        )
        self.chat_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
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
                # Try to find and set qwen2.5vl:3b as default
                if self.current_model in models:
                    idx = models.index(self.current_model)
                    self.model_combo.current(idx)
                else:
                    # Fallback to first model
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

        print(f"\n[CHAT] ========== Processing user message ==========")
        print(f"[CHAT] User input: {user_input}")
        print(f"[CHAT] Memory object: {type(self.mem)}")
        print(f"[CHAT] Memory has search: {hasattr(self.mem, 'search')}")

        # Search memories for relevant context
        related_memories = self.mem.search(query=user_input, user_id="screenshot")
        print(f"[CHAT] Search completed. Results type: {type(related_memories)}")

        # Build context from memories
        context = ""
        if related_memories and 'results' in related_memories and len(related_memories['results']) > 0:
            print(f"[CHAT] Found {len(related_memories['results'])} related memories")

            # Prioritize screen recording memories
            recording_memories = [
                r for r in related_memories['results']
                if 'metadata' in r and r['metadata'].get('type') == 'screen_recording'
            ]

            print(f"[CHAT] Recording memories found: {len(recording_memories)}")

            if recording_memories:
                # Use the most relevant recording
                top_memory = recording_memories[0]['memory']
                metadata = recording_memories[0].get('metadata', {})

                print(f"[CHAT] Using recording memory:")
                print(f"[CHAT] - Filename: {metadata.get('filename', 'N/A')}")
                print(f"[CHAT] - Duration: {metadata.get('duration', 0):.1f}s")
                print(f"[CHAT] - Content preview: {str(metadata.get('content_description', 'N/A'))[:100]}...")

                # Build informative context about recordings
                if 'filename' in metadata:
                    context = f"Relevant Screen Recording Found:\n"
                    context += f"- Video File: {metadata['filename']}\n"
                    context += f"- Duration: {metadata.get('duration', 0):.1f} seconds\n"
                    context += f"- Recorded at: {metadata.get('timestamp', 'unknown')}\n"
                    if 'content_description' in metadata:
                        context += f"- Content: {metadata['content_description']}\n"
                    context += f"\nThis is a video file that captured screen activity. "
                    context += f"The user can view this video in the Video tab to see the actual screen content.\n\n"
            else:
                # Use general memories if no recordings found
                top_memory = related_memories['results'][0]['memory']
                if len(top_memory) > 500:
                    top_memory = top_memory[:500] + "..."
                context = f"Context from previous activities:\n{top_memory}\n\n"
                print(f"[CHAT] Using general memory: {top_memory[:100]}...")
        else:
            print(f"[CHAT] No related memories found")

        # Build enhanced prompt
        if context:
            enhanced_input = context + f"User question: {user_input}\n\nBased on the context above, provide a helpful answer. If referring to a screen recording, mention that the user can view it in the Video tab."
            print(f"[CHAT] Using enhanced prompt with context ({len(enhanced_input)} chars)")
        else:
            enhanced_input = f"User question: {user_input}\n\nPlease provide a helpful and concise answer."
            print(f"[CHAT] Using basic prompt (no context)")

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
        """Show simple typing indicator"""
        # Add simple text indicator to chat
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, "🤖 AI is typing...\n\n", "ai")
        self.chat_history.config(state=tk.DISABLED)
        self.chat_history.see(tk.END)

    def _hide_typing_indicator(self):
        """Hide typing indicator by removing the text"""
        try:
            self.chat_history.config(state=tk.NORMAL)
            content = self.chat_history.get("1.0", tk.END)
            if "AI is typing..." in content:
                # Find and remove the typing indicator
                lines = content.split('\n')
                new_lines = []
                skip_next = False
                for i, line in enumerate(lines):
                    if "AI is typing..." in line:
                        skip_next = True  # Skip next empty line too
                        continue
                    if skip_next and line.strip() == "":
                        skip_next = False
                        continue
                    new_lines.append(line)

                # Update content
                self.chat_history.delete("1.0", tk.END)
                self.chat_history.insert(tk.END, '\n'.join(new_lines))
            self.chat_history.config(state=tk.DISABLED)
        except:
            pass

    def send_to_ollama(self, prompt, model_name, message_queue):
        """Send request to Ollama (non-streaming for stability)"""
        url = "http://127.0.0.1:11434/api/chat"

        # Limit conversation history to last 2 exchanges (4 messages) to avoid token limit
        # This is especially important for small models like gemma3:270m
        limited_history = self.conversation_history[-4:] if len(self.conversation_history) > 4 else self.conversation_history

        # Build messages - keep system prompt simple for small models
        messages = [{"role": "system", "content": "You are a helpful assistant. Provide concise answers."}]
        messages.extend(limited_history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,  # Use non-streaming for stability
            "options": {
                "num_predict": 500,  # Limit response length to avoid hanging
                "temperature": 0.7
            }
        }

        try:
            # Log the request size
            total_chars = sum(len(m.get("content", "")) for m in messages)
            print(f"[DEBUG] Sending to Ollama: model={model_name}, messages={len(messages)}, total_chars={total_chars}")

            response = requests.post(url, json=payload, stream=False, timeout=120)
            response.raise_for_status()

            result = response.json()
            full_response = result.get("message", {}).get("content", "")

            print(f"[DEBUG] Response complete: {len(full_response)} chars")
            message_queue.put(("done", full_response))

        except Exception as e:
            print(f"[ERROR] Ollama request failed: {e}")
            import traceback
            traceback.print_exc()
            message_queue.put(("error", str(e)))

    def process_ai_response(self, message_queue, thread):
        """Process AI response and update UI"""
        # Wait for response with timeout
        import time
        start_time = time.time()

        while True:
            try:
                # Check timeout (60 seconds)
                if time.time() - start_time > 60:
                    self._hide_typing_indicator()
                    self.chat_history.config(state=tk.NORMAL)
                    self.chat_history.insert(tk.END, "\n⚠️ Response timeout. Please try again.\n\n", "ai_msg")
                    self.chat_history.config(state=tk.DISABLED)
                    self.thinking_label.place_forget()
                    return

                # Try to get message (with small timeout)
                item = message_queue.get(timeout=0.1)

                if item[0] == "done":
                    # Remove typing indicator
                    self._hide_typing_indicator()

                    # Add AI message
                    response_text = item[1]
                    self._add_ai_message(response_text)

                    # Save to conversation history
                    self.conversation_history.append({"role": "assistant", "content": response_text})

                    # Hide thinking label
                    self.thinking_label.place_forget()
                    break

                elif item[0] == "error":
                    # Remove typing indicator
                    self._hide_typing_indicator()

                    # Show error
                    self.chat_history.config(state=tk.NORMAL)
                    self.chat_history.insert(tk.END, f"\n❌ Error: {item[1]}\n\n", "ai_msg")
                    self.chat_history.config(state=tk.DISABLED)
                    self.thinking_label.place_forget()
                    break

            except queue.Empty:
                # Check if thread is still alive
                if not thread.is_alive():
                    self._hide_typing_indicator()
                    self.chat_history.config(state=tk.NORMAL)
                    self.chat_history.insert(tk.END, "\n⚠️ No response from AI. Check if Ollama is running.\n\n", "ai_msg")
                    self.chat_history.config(state=tk.DISABLED)
                    self.thinking_label.place_forget()
                    break
                # Continue waiting
                continue


__all__ = ["ChatTab"]
