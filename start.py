#!/usr/bin/env python3
"""
MemScreen Quick Launcher
Simple script to launch MemScreen UI with mock memory
"""

from memscreen.ui import MemScreenApp
import tkinter as tk

# Create mock memory for quick start (no Ollama required)
class MockMemory:
    """Mock memory class for quick UI testing without full backend"""
    def search(self, query, user_id='user1'):
        return []

    def add(self, *args, **kwargs):
        return 'test_id'

def main():
    """Launch MemScreen UI"""
    print("🚀 Starting MemScreen UI...")
    print("📱 Using mock memory (full features require Ollama)")
    print("")

    # Create main window
    root = tk.Tk()
    root.title("MemScreen v0.1")

    # Create app with mock memory
    app = MemScreenApp(root, mem=MockMemory())

    print("✅ MemScreen UI launched!")
    print("   - 5 tabs available: Recording, Chat, Video, Search, Settings")
    print("   - Close the window to exit")
    print("")

    # Start the UI
    root.mainloop()

    print("👋 MemScreen UI closed. Goodbye!")

if __name__ == "__main__":
    main()
