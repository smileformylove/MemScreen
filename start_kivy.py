#!/usr/bin/env python3
"""
MemScreen Kivy UI Launcher
Launch MemScreen with modern Kivy interface

This is a fully functional Kivy application that integrates
with the existing MVP architecture and memory system.
"""

if __name__ == '__main__':
    from memscreen.ui.kivy_app import MemScreenKivyApp
    MemScreenKivyApp().run()
