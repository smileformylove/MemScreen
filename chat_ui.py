import os
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from ttkthemes import ThemedTk
import requests
import json
import threading
import queue

from memory import Memory
from prompts import MEMORY_ANSWER_PROMPT

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

mem = Memory.from_config(config)

# --- 全局配置 ---
APP_TITLE = "Ollama 本地聊天助手"
APP_SIZE = "950x700"  # 稍微增大窗口
APP_MIN_SIZE = "700x500" # 稍微增大最小窗口

# 字体配置
BASE_FONT_SIZE = 20
FONT_FAMILY = "Segoe UI" # 保持现代字体

# 颜色方案 (保持不变)
COLORS = {
    "bg": "#f0f0f0",            # 背景色
    "text": "#333333",          # 文本色
    "user_bg": "#e3f2fd",       # 用户消息背景
    "assistant_bg": "#f5f5f5",  # 助手消息背景
    "user_border": "#bbdefb",   # 用户消息边框
    "assistant_border": "#e0e0e0", # 助手消息边框
    "input_bg": "#ffffff",      # 输入框背景
    "button_bg": "#2196f3",     # 按钮背景
    "button_hover": "#1976d2",  # 按钮悬停背景
    "button_text": "#ffffff",   # 按钮文本
}

# --- Ollama 交互函数 (保持不变) ---
def send_to_ollama(prompt, model_name, message_queue, conversation_history):
    url = "http://127.0.0.1:11434/api/chat"
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    messages.extend(conversation_history)
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
                    
                except json.JSONDecodeError:
                    message_queue.put(("error", "解析模型响应时出错"))
                except KeyError:
                    message_queue.put(("error", "模型响应格式不正确"))
        
        message_queue.put(("done", full_response))
        
    except requests.exceptions.RequestException as e:
        message_queue.put(("error", f"无法连接到 Ollama: {e}\n请确保 Ollama 服务正在运行。"))
    except Exception as e:
        message_queue.put(("error", f"发生未知错误: {e}"))

# --- UI 更新函数 (保持不变) ---
def update_ui(root, message_queue, chat_history_widget, thinking_label):
    while not message_queue.empty():
        item = message_queue.get()
        if item[0] == "chunk":
            chat_history_widget.config(state=tk.NORMAL)
            chat_history_widget.insert(tk.END, item[1])
            chat_history_widget.config(state=tk.DISABLED)
            chat_history_widget.see(tk.END)
        elif item[0] == "error":
            messagebox.showerror("错误", item[1])
            thinking_label.pack_forget()
        elif item[0] == "done":
            thinking_label.pack_forget()
            chat_history_widget.config(state=tk.NORMAL)
            chat_history_widget.insert(tk.END, "\n\n")
            chat_history_widget.config(state=tk.DISABLED)
    
    root.after(100, update_ui, root, message_queue, chat_history_widget, thinking_label)

# --- 发送消息函数 (保持不变) ---
def send_message():
    user_input = input_field.get("1.0", tk.END).strip()
    if not user_input:
        return
    user_input = MEMORY_ANSWER_PROMPT + "\n\n" + user_input
    ### screen memory
    related_memories = mem.search(query=user_input, user_id="screenshot")
    if related_memories and 'results' in related_memories and len(related_memories['results']) > 0:
        user_input = related_memories['results'][0]['memory'] + '\n\n' + user_input

    print(user_input)
        
    model_name = model_combobox.get()
    input_field.delete("1.0", tk.END)
    
    conversation_history.append({"role": "user", "content": user_input})
    
    chat_history.config(state=tk.NORMAL)
    chat_history.insert(tk.END, f"你: ", "user_tag")
    chat_history.insert(tk.END, f"{user_input}\n\n", "user_text")
    chat_history.config(state=tk.DISABLED)
    chat_history.see(tk.END)
    
    chat_history.config(state=tk.NORMAL)
    chat_history.insert(tk.END, f"模型 ({model_name}): ", "assistant_tag")
    chat_history.config(state=tk.DISABLED)
    
    thinking_label.pack(side=tk.LEFT, padx=10)
    
    message_queue = queue.Queue()
    
    thread = threading.Thread(
        target=send_to_ollama,
        args=(user_input, model_name, message_queue, conversation_history),
        daemon=True
    )
    thread.start()
    
    root.after(100, update_ui, root, message_queue, chat_history, thinking_label)
    
    def save_assistant_response():
        if thread.is_alive():
            root.after(100, save_assistant_response)
        else:
            if message_queue.empty():
                return
            full_response = None
            while not message_queue.empty():
                item = message_queue.get()
                if item[0] == "done":
                    full_response = item[1]
            if full_response:
                conversation_history.append({"role": "assistant", "content": full_response})
    
    root.after(100, save_assistant_response)

# --- 刷新模型列表 (保持不变) ---
def refresh_models():
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags")
        response.raise_for_status()
        models_data = response.json()
        
        model_combobox['values'] = [model['name'] for model in models_data.get('models', [])]
        
        if models_data.get('models'):
            model_combobox.current(0)
            
    except requests.exceptions.RequestException as e:
        messagebox.showerror("错误", f"无法连接到 Ollama: {e}\n请确保 Ollama 服务正在运行。")
    except Exception as e:
        messagebox.showerror("错误", f"获取模型列表时出错: {e}")

# --- 主程序 ---
if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    root.title(APP_TITLE)
    root.geometry(APP_SIZE)
    root.minsize(*APP_MIN_SIZE.split('x'))
    
    conversation_history = []

    # --- 顶部控制区 ---
    control_frame = ttk.Frame(root, padding="10 5")
    control_frame.pack(fill=tk.X, side=tk.TOP)
    
    # 放大标签字体
    ttk.Label(control_frame, text="选择模型:", font=(FONT_FAMILY, BASE_FONT_SIZE)).pack(side=tk.LEFT, padx=(0, 5))
    
    # 放大下拉框字体
    model_combobox = ttk.Combobox(control_frame, state="readonly", width=30, font=(FONT_FAMILY, BASE_FONT_SIZE))
    model_combobox.pack(side=tk.LEFT, padx=(0, 10))
    
    # 放大按钮字体
    refresh_button = ttk.Button(control_frame, text="刷新模型", command=refresh_models)
    refresh_button.pack(side=tk.LEFT)
    
    # --- 主要内容区 ---
    main_pane = ttk.PanedWindow(root, orient=tk.VERTICAL)
    main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
    
    # --- 聊天历史区域 ---
    chat_frame = ttk.Frame(main_pane)
    main_pane.add(chat_frame, weight=1)
    
    # 放大聊天记录字体
    chat_history = scrolledtext.ScrolledText(
        chat_frame,
        wrap=tk.WORD,
        state=tk.DISABLED,
        font=(FONT_FAMILY, BASE_FONT_SIZE),
        bg=COLORS["bg"],
        relief=tk.FLAT
    )
    chat_history.pack(fill=tk.BOTH, expand=True)
    
    # --- 配置文本标签样式 (使用放大后的字体) ---
    chat_history.tag_configure("user_tag", foreground="#0d47a1", font=(FONT_FAMILY, BASE_FONT_SIZE, "bold"))
    chat_history.tag_configure("user_text", foreground=COLORS["text"], background=COLORS["user_bg"], 
                               wrap=tk.WORD, lmargin1=10, lmargin2=10, rmargin=10, spacing1=5, spacing3=5)
    chat_history.tag_configure("assistant_tag", foreground="#3e2723", font=(FONT_FAMILY, BASE_FONT_SIZE, "bold"))
    chat_history.tag_configure("assistant_text", foreground=COLORS["text"], background=COLORS["assistant_bg"],
                               wrap=tk.WORD, lmargin1=10, lmargin2=10, rmargin=10, spacing1=5, spacing3=5)

    # --- 输入区域 ---
    input_frame = ttk.Frame(main_pane, padding="5")
    main_pane.add(input_frame, weight=0)
    
    input_and_button_frame = ttk.Frame(input_frame)
    input_and_button_frame.pack(fill=tk.X, expand=True)
    
    # 放大输入框字体，并增加高度以容纳更大的字体
    input_field = scrolledtext.ScrolledText(
        input_and_button_frame,
        wrap=tk.WORD,
        height=4,  # 从 3 增加到 4
        font=(FONT_FAMILY, BASE_FONT_SIZE),
        relief=tk.SUNKEN,
        bd=1
    )
    input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    input_field.focus_set()
    
    # 放大"正在思考"标签的字体
    thinking_label = ttk.Label(input_and_button_frame, text="模型正在思考...", foreground="#666666", font=(FONT_FAMILY, BASE_FONT_SIZE))

    # 放大发送按钮的字体
    send_button = ttk.Button(input_and_button_frame, text="发送", command=send_message)
    send_button.pack(side=tk.LEFT)
    
    def on_return(event):
        if event.state & 4:
            return "break"
        send_message()
        return "break"
    
    input_field.bind("<Return>", on_return)
    
    refresh_models()
    root.mainloop()