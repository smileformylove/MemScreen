#!/usr/bin/env python3
"""
MemScreen - Screen Memory Application with AI

A smart screen recording and memory system that uses AI to:
- Record your screen activity
- Extract and index content with OCR
- Enable natural language search through recordings
- Provide AI chat assistance based on your screen history
"""

if __name__ == '__main__':
    # Ensure Ollama service is running before starting the app
    from memscreen.utils import ensure_ollama_running
    import logging

    logging.basicConfig(level=logging.INFO)

    if ensure_ollama_running():
        from memscreen.ui.kivy_app import MemScreenApp
        MemScreenApp().run()
    else:
        print("❌ Failed to start Ollama service")
        print("")
        print("Please install Ollama from https://ollama.com/download")
        print("Then run: ollama serve")
        print("")
        print("Or use the macOS installer:")
        print("  cd macos && ./install_complete.sh")
