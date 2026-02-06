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
    import logging
    logging.basicConfig(level=logging.INFO)

    # Always try to start the app, even if Ollama check fails
    # The app will show a warning in the UI if Ollama is not available
    try:
        from memscreen.ui.kivy_app import MemScreenApp
        MemScreenApp().run()
    except Exception as e:
        print(f"❌ Failed to start MemScreen: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")  # Keep console open for debugging
