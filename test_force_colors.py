#!/usr/bin/env python3
"""
Test forcing colors with different methods for macOS compatibility
"""

import tkinter as tk
from tkinter import scrolledtext
from memscreen.ui.components.colors import COLORS, FONTS

print("=" * 70)
print("🔨 Forcing Colors - macOS Compatibility Test")
print("=" * 70)
print()

root = tk.Tk()
root.title("Force Color Test")
root.geometry("700x500")

# IMPORTANT: Use tk_setPalette to force color scheme
root.tk_setPalette(
    background=COLORS["bg"],
    foreground=COLORS["text"],
    activeBackground=COLORS["primary"],
    activeForeground="white"
)

root.configure(bg=COLORS["bg"])

main_frame = tk.Frame(root, bg=COLORS["bg"], padx=20, pady=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# Method 1: Using configure() to set colors AFTER packing
print("🧪 Method 1: Configure after pack")
print("-" * 70)

frame1 = tk.Frame(main_frame, bg=COLORS["surface"], padx=15, pady=15)
frame1.pack(fill=tk.X, pady=(0, 15))

tk.Label(
    frame1,
    text="Method 1: Entry with configure()",
    font=FONTS["heading"],
    bg=COLORS["surface"],
    fg=COLORS["text"]
).pack(anchor=tk.W, pady=(0, 10))

entry1 = tk.Entry(frame1)
entry1.pack(fill=tk.X, ipady=8, pady=5)

# Force configure colors AFTER pack
entry1.configure(
    bg=COLORS["input_bg"],
    fg=COLORS["text"],
    insertbackground=COLORS["text"],
    relief=tk.SOLID,
    bd=2
)
entry1.insert(0, "Method 1: Configured after pack - Can you see this?")

print(f"   Entry bg: {entry1.cget('bg')}")
print(f"   Entry fg: {entry1.cget('fg')}")
print()

# Method 2: Using option_add to set default styles
print("🧪 Method 2: option_add for default Entry styles")
print("-" * 70)

# Set default options for all Entry widgets
root.option_add('*Entry.background', COLORS["input_bg"])
root.option_add('*Entry.foreground', COLORS["text"])
root.option_add('*Entry.insertBackground', COLORS["text"])
root.option_add('*Entry.relief', 'solid')
root.option_add('*Entry.borderWidth', 2)

frame2 = tk.Frame(main_frame, bg=COLORS["surface"], padx=15, pady=15)
frame2.pack(fill=tk.X, pady=(0, 15))

tk.Label(
    frame2,
    text="Method 2: Entry with option_add defaults",
    font=FONTS["heading"],
    bg=COLORS["surface"],
    fg=COLORS["text"]
).pack(anchor=tk.W, pady=(0, 10))

entry2 = tk.Entry(frame2)
entry2.pack(fill=tk.X, ipady=8, pady=5)
entry2.insert(0, "Method 2: Using option_add - Can you see this?")

print(f"   Entry bg: {entry2.cget('bg')}")
print(f"   Entry fg: {entry2.cget('fg')}")
print()

# Method 3: ScrolledText with configure
print("🧪 Method 3: ScrolledText with configure")
print("-" * 70)

frame3 = tk.Frame(main_frame, bg=COLORS["surface"], padx=15, pady=15)
frame3.pack(fill=tk.BOTH, expand=True)

tk.Label(
    frame3,
    text="Method 3: ScrolledText with configure()",
    font=FONTS["heading"],
    bg=COLORS["surface"],
    fg=COLORS["text"]
).pack(anchor=tk.W, pady=(0, 10))

text1 = scrolledtext.ScrolledText(frame3, height=8)
text1.pack(fill=tk.BOTH, expand=True, pady=5)

# Force configure colors AFTER pack
text1.configure(
    bg=COLORS["bg"],
    fg=COLORS["text"],
    insertbackground=COLORS["text"],
    relief=tk.FLAT,
    font=FONTS["body"]
)
text1.insert(tk.END, """Method 3: ScrolledText configured after pack

Can you see this text?

This method uses configure() AFTER packing the widget,
which can help on some systems where colors are not applied correctly.""")
text1.config(state=tk.NORMAL)

print(f"   Text bg: {text1.cget('bg')}")
print(f"   Text fg: {text1.cget('fg')}")
print()

# Method 4: Pure white/black for maximum contrast
print("🧪 Method 4: Maximum contrast (pure white/black)")
print("-" * 70)

frame4 = tk.Frame(main_frame, bg="#000000", padx=15, pady=15)
frame4.pack(fill=tk.X, pady=(15, 0))

entry3 = tk.Entry(frame4, bg="#000000", fg="#FFFFFF", insertbackground="#FFFFFF",
                  relief=tk.SOLID, bd=2, font=FONTS["body"])
entry3.pack(fill=tk.X, ipady=8, pady=5)
entry3.insert(0, "PURE WHITE on BLACK - Can you see this?")

print("=" * 70)
print("✅ All methods configured")
print("=" * 70)
print()
print("Please tell me which methods show visible text:")
print("1. Method 1 (configure after pack)")
print("2. Method 2 (option_add)")
print("3. Method 3 (ScrolledText with configure)")
print("4. Method 4 (pure white/black)")
print()
print("Window will stay open for 30 seconds...")
print()

root.update()
root.after(30000, root.destroy)
root.mainloop()

print("Test complete. Which methods were visible?")
