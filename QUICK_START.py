#!/usr/bin/env python3
"""
Quick GitHub Optimization for MemScreen
Run this to quickly optimize your repo for more stars!
"""

import os
import subprocess
from pathlib import Path

def check_github_topics():
    """Check and suggest GitHub topics"""
    print("📌 GitHub Topics to Add:")
    print("=" * 50)
    topics = [
        "ai",
        "screen-recording",
        "ollama",
        "local-llm",
        "privacy",
        "kivy",
        "python",
        "productivity-tools",
        "process-mining",
        "vector-search",
        "chromadb",
        "mllm",
        "visual-memory",
        "screen-capture",
        "semantic-search"
    ]

    print("\nGo to: https://github.com/smileformylove/MemScreen/settings")
    print("Add these topics in the 'Topics' section:\n")
    for topic in topics:
        print(f"  - {topic}")

    print(f"\nTotal: {len(topics)} topics")
    return topics

def create_github_social_preview():
    """Create social preview image suggestion"""
    print("\n🖼️  GitHub Social Preview:")
    print("=" * 50)
    print("""
    Create an image for social preview (1280x640px):

    Content:
    ┌────────────────────────────────────────┐
    │  [MemScreen Logo]                      │
    │                                        │
    │  Your AI-Powered Visual Memory System  │
    │  📸 Record • 🧠 Understand • 💬 Ask  │
    │                                        │
    │  100% Local • Privacy-Focused • Free  │
    │                                        │
    │  Built with Ollama + Kivy + Python    │
    └────────────────────────────────────────┘

    Tools:
    - Canva: https://www.canva.com/
    - Figma: https://www.figma.com/
    - Photopea: https://www.photopea.com/ (free)

    Save as: social-preview.png
    Upload to: https://github.com/smileformylove/MemScreen/settings
    (Look for "Social preview" section)
    """)

def optimize_repo_description():
    """Optimize GitHub repo description"""
    print("\n📝 GitHub Repo Description:")
    print("=" * 50)
    print("""
    Update your repo description to this:

    "AI-powered visual memory system that records, understands,
    and searches your screen using local LLMs. 100% privacy-focused."

    Add to About section:
    - 📸 Automatic screen recording
    - 🧠 AI content understanding (Ollama)
    - 💬 Natural language search
    - 🎯 Timeline navigation
    - 📊 Process mining
    - 🔒 100% local & privacy-focused

    Website URL: https://smileformylove.github.io/MemScreen/
    (or your documentation site)
    """)

def create_first_reddit_post():
    """Create first Reddit post"""
    print("\n📝 First Reddit Post Template:")
    print("=" * 50)

    post = """
Title: "I built an AI-powered screen memory system with local LLMs (Ollama + ChromaDB)"

Post content:

Hi everyone,

I've been working on a project called MemScreen – an AI-powered visual memory system that helps you never lose anything on your screen again.

**The Problem:**
Ever struggled to find:
- That article you skimmed yesterday?
- That code snippet from last week?
- That design inspiration from months ago?

**The Solution:**
MemScreen automatically records your screen, understands it with local AI, and lets you search with natural language.

**Key Features:**
- 📸 Screen recording with configurable intervals
- 🧠 AI understanding (uses qwen2.5vl:3b via Ollama)
- 💬 Natural language search (ChromaDB vector search)
- 🎯 Visual timeline navigation (click any moment to replay)
- 📊 Process mining (track keyboard/mouse patterns)
- 🔒 100% local – your data never leaves your machine

**Tech Stack:**
- Kivy (GUI)
- Ollama (local LLM)
- ChromaDB (vector DB)
- OpenCV (video processing)
- Pure Python

**What makes it different:**
Unlike Loom or OBS, MemScreen doesn't just record – it understands. You can ask "What did I work on yesterday?" and it'll show you.

Also, everything runs locally with Ollama – no cloud, no subscriptions, privacy by design.

**Demo:**
[Add a GIF or screenshot of the timeline feature here]

**GitHub:** https://github.com/smileformylove/MemScreen

Would love to get feedback from the community! Especially interested in:
- Privacy concerns with local AI
- Additional features you'd want
- Code review (it's my first Kivy project)

Thanks!

---

**Subreddits to post:**
1. r/Python - https://reddit.com/r/Python
2. r/MachineLearning - https://reddit.com/r/MachineLearning
3. r/opensource - https://reddit.com/r/opensource
4. r/Privacy - https://reddit.com/r/Privacy
5. r/Productivity - https://reddit.com/r/Productivity

**Best time to post:**
Tuesday-Thursday, 9-11pm Beijing Time
(= 6-8am PST = 9-11am EST)

**Important:**
- Customize the post for each subreddit
- Reply to ALL comments within first hour
- Have demo images/GIFs ready
- Be prepared for criticism
- Update based on feedback
"""
    print(post)

def show_priority_actions():
    """Show priority actions"""
    print("\n🎯 Priority Actions (Do Today!):")
    print("=" * 50)

    actions = [
        ("1. Add GitHub Topics", "5 min", "High"),
        ("2. Create social preview image", "15 min", "High"),
        ("3. Optimize repo description", "5 min", "High"),
        ("4. Create demo GIF/screenshot", "30 min", "Critical"),
        ("5. Post to r/Python", "20 min", "Critical"),
    ]

    for i, (action, time, priority) in enumerate(actions, 1):
        priority_icon = "🔴" if priority == "Critical" else "⚠️" if priority == "High" else "✅"
        print(f"\n{priority_icon} {action} ({time})")

    print(f"\n⏱️  Total time: ~75 minutes")
    print("🚀 Do these TODAY for maximum impact!")

if __name__ == "__main__":
    print("🚀 MemScreen Quick GitHub Optimization")
    print("=" * 50)
    print()

    check_github_topics()
    create_github_social_preview()
    optimize_repo_description()
    create_first_reddit_post()
    show_priority_actions()

    print("\n" + "=" * 50)
    print("✅ Optimization plan ready!")
    print("📝 Save this output and follow the steps")
    print("🎯 Focus on demo images FIRST!")
    print("\nGood luck! 🍀")
