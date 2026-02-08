#!/usr/bin/env python3
"""
Simple test script to check if native_region_selector works
"""
import sys
import os

# Add project to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

try:
    from memscreen.ui.native_region_selector import select_region

    def callback(bbox):
        print(f"Selected: {bbox}")

    print("Starting selector...")
    selector = select_region(callback)
    print("Done!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
