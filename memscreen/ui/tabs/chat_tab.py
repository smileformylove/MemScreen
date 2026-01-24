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
from ..components.colors import COLORS, FONTS
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
        self.current_model = "qwen3:1.7b"
        self.conversation_history = []

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
            font=FONTS["small"],
            bg=COLORS["bg"],
            relief=tk.FLAT,
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

        # Configure tags
        self.chat_history.tag_configure("user", foreground=COLORS["primary"],
                                        font=(FONTS["body"][0], FONTS["body"][1], "bold"))
        self.chat_history.tag_configure("ai", foreground=COLORS["secondary"],
                                       font=(FONTS["body"][0], FONTS["body"][1], "bold"))
        self.chat_history.tag_configure("user_msg", background=COLORS["chat_user_bg"],
                                       lmargin1=10, lmargin2=10, rmargin=10, spacing1=5, spacing3=5)
        self.chat_history.tag_configure("ai_msg", background=COLORS["chat_ai_bg"],
                                       lmargin1=10, lmargin2=10, rmargin=10, spacing1=5, spacing3=5)

        # Input area
        input_frame = tk.Frame(self.frame, bg=COLORS["surface"], height=100)
        input_frame.pack(fill=tk.X)
        input_frame.pack_propagate(False)

        self.chat_input = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=FONTS["body"],
            bg=COLORS["bg"],
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
            font=FONTS["body"],
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.send_chat_message
        )
        send_btn.place(relx=0.95, rely=0.5, anchor=tk.E)

        self.thinking_label = tk.Label(
            input_frame,
            text="AI is thinking...",
            font=FONTS["small"],
            bg=COLORS["surface"],
            fg=COLORS["text_light"]
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
        """Send chat message to AI"""
        user_input = self.chat_input.get("1.0", tk.END).strip()
        if not user_input:
            return

        # Add screen memory context
        enhanced_input = MEMORY_ANSWER_PROMPT + "\n\n" + user_input
        related_memories = self.mem.search(query=enhanced_input, user_id="screenshot")
        if related_memories and 'results' in related_memories and len(related_memories['results']) > 0:
            enhanced_input = related_memories['results'][0]['memory'] + '\n\n' + enhanced_input

        self.chat_input.delete("1.0", tk.END)

        # Add user message to chat
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, "You:\n", "user")
        self.chat_history.insert(tk.END, f"{user_input}\n\n", "user_msg")
        self.chat_history.config(state=tk.DISABLED)
        self.chat_history.see(tk.END)

        # Add thinking indicator
        self.thinking_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

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
        """Process AI response and update UI"""
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, "AI:\n", "ai")

        def update():
            try:
                item = message_queue.get_nowait()
                if item[0] == "chunk":
                    self.chat_history.insert(tk.END, item[1])
                    self.chat_history.see(tk.END)
                    self.root.after(10, update)
                elif item[0] == "done":
                    self.chat_history.insert(tk.END, "\n\n", "ai_msg")
                    self.chat_history.config(state=tk.DISABLED)
                    self.thinking_label.place_forget()

                    # Save to conversation history
                    self.conversation_history.append({"role": "assistant", "content": item[1]})
                elif item[0] == "error":
                    self.chat_history.insert(tk.END, f"\nError: {item[1]}\n\n", "ai_msg")
                    self.chat_history.config(state=tk.DISABLED)
                    self.thinking_label.place_forget()
            except queue.Empty:
                if thread.is_alive():
                    self.root.after(10, update)
                else:
                    self.chat_history.config(state=tk.DISABLED)
                    self.thinking_label.place_forget()

        update()


__all__ = ["ChatTab"]
