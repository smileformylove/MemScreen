#!/usr/bin/env python3
"""
Diagnose text visibility issues in all text boxes
"""

import tkinter as tk
from tkinter import scrolledtext
from memscreen.ui.components.colors import COLORS, FONTS

print("=" * 70)
print("🔍 Text Visibility Diagnosis")
print("=" * 70)
print()

# Show current colors
print("📋 Current Color Configuration:")
print("-" * 70)
print(f"Background (bg):        {COLORS['bg']} - Dark gray")
print(f"Surface:                {COLORS['surface']} - Medium gray")
print(f"Input Background:       {COLORS['input_bg']} - Very dark gray")
print(f"Text Color:             {COLORS['text']} - Off-white")
print()

# Create test window
root = tk.Tk()
root.title("Text Visibility Diagnosis")
root.geometry("800x600")
root.configure(bg=COLORS["bg"])

main_frame = tk.Frame(root, bg=COLORS["bg"], padx=20, pady=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# Test 1: Entry widget (like search input)
print("🧪 Test 1: Entry Widget")
print("-" * 70)

test1_frame = tk.Frame(main_frame, bg=COLORS["surface"], padx=15, pady=15)
test1_frame.pack(fill=tk.X, pady=(0, 15))

tk.Label(
    test1_frame,
    text="Test 1: Entry Widget (Current Configuration)",
    font=FONTS["heading"],
    bg=COLORS["surface"],
    fg=COLORS["text"]
).pack(anchor=tk.W, pady=(0, 10))

entry1 = tk.Entry(
    test1_frame,
    font=FONTS["body"],
    bg=COLORS["input_bg"],
    fg=COLORS["text"],
    insertbackground=COLORS["text"],
    relief=tk.SOLID,
    bd=2,
    highlightthickness=2,
    highlightbackground=COLORS["primary"],
    highlightcolor=COLORS["primary"]
)
entry1.pack(fill=tk.X, ipady=8)
entry1.insert(0, "Can you see this text clearly? Type something...")
entry1.focus_set()

print(f"   Background: {entry1['bg']}")
print(f"   Foreground: {entry1['fg']}")
print(f"   Insert background: {entry1['insertbackground']}")
print()

# Test 2: Text widget (like chat/results)
print("🧪 Test 2: ScrolledText Widget")
print("-" * 70)

test2_frame = tk.Frame(main_frame, bg=COLORS["surface"], padx=15, pady=15)
test2_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

tk.Label(
    test2_frame,
    text="Test 2: ScrolledText Widget (Current Configuration)",
    font=FONTS["heading"],
    bg=COLORS["surface"],
    fg=COLORS["text"]
).pack(anchor=tk.W, pady=(0, 10))

text1 = scrolledtext.ScrolledText(
    test2_frame,
    wrap=tk.WORD,
    font=FONTS["body"],
    bg=COLORS["bg"],
    fg=COLORS["text"],
    insertbackground=COLORS["text"],
    relief=tk.FLAT,
    height=8
)
text1.pack(fill=tk.BOTH, expand=True)
text1.insert(tk.END, """Can you see this text clearly?

This is a ScrolledText widget with:
- Background: #1F2937 (dark gray)
- Foreground: #F9FAFB (off-white)

If you cannot see the text, please describe:
1. Is the text completely invisible?
2. Is the text too faint/low contrast?
3. Is the text the wrong color?

Type your response here...""")
text1.config(state=tk.NORMAL)

print(f"   Background: {text1['bg']}")
print(f"   Foreground: {text1['fg']}")
print(f"   Insert background: {text1['insertbackground']}")
print()

# Test 3: Alternative high-contrast configuration
print("🧪 Test 3: Alternative Configuration (Pure White Text)")
print("-" * 70)

test3_frame = tk.Frame(main_frame, bg=COLORS["surface"], padx=15, pady=15)
test3_frame.pack(fill=tk.BOTH, expand=True)

tk.Label(
    test3_frame,
    text="Test 3: Pure White Text (#FFFFFF) - Maximum Contrast",
    font=FONTS["heading"],
    bg=COLORS["surface"],
    fg="#FFFFFF"
).pack(anchor=tk.W, pady=(0, 10))

text2 = scrolledtext.ScrolledText(
    test3_frame,
    wrap=tk.WORD,
    font=FONTS["body"],
    bg="#000000",  # Pure black
    fg="#FFFFFF",  # Pure white
    insertbackground="#FFFFFF",
    relief=tk.FLAT,
    height=6
)
text2.pack(fill=tk.BOTH, expand=True)
text2.insert(tk.END, """This text is PURE WHITE (#FFFFFF) on PURE BLACK (#000000).

This is the maximum possible contrast.

Can you see THIS text clearly?""")
text2.config(state=tk.NORMAL)

print(f"   Background: #000000 (pure black)")
print(f"   Foreground: #FFFFFF (pure white)")
print()

print("=" * 70)
print("📝 Diagnosis Questions:")
print("-" * 70)
print("Please look at the test window and tell me:")
print()
print("1. Test 1 (Entry widget):")
print("   - Can you see 'Can you see this text clearly?'")
print("   - If not, what does it look like?")
print()
print("2. Test 2 (ScrolledText with current colors):")
print("   - Can you see the long text block?")
print("   - If not, what does it look like?")
print()
print("3. Test 3 (Pure white on black):")
print("   - Can you see 'This text is PURE WHITE'?")
print("   - Is THIS one visible?")
print()
print("The test window will stay open for 30 seconds.")
print("=" * 70)
print()

root.update()
root.after(30000, root.destroy)
root.mainloop()

print("Diagnosis complete. Please report which tests were visible.")
