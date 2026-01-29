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
    from memscreen.ui.kivy_app import MemScreenApp
    MemScreenApp().run()
