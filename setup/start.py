#!/usr/bin/env python3
"""
MemScreen - Screen Memory Application with AI

A smart screen recording and memory system that uses AI to:
- Record your screen activity
- Extract and index content with OCR
- Enable natural language search through recordings
- Provide AI chat assistance based on your screen history

Usage:
    python setup/start.py          # Start API backend (for Flutter)
    ./scripts/start_flutter.sh      # Start Flutter UI + API backend

Note: Kivy UI has been archived. Use Flutter frontend instead.
"""

if __name__ == '__main__':
    import logging
    import sys
    import uvicorn

    logging.basicConfig(level=logging.INFO)

    try:
        from memscreen.config import get_config

        cfg = get_config()
        host = cfg.api_host
        port = cfg.api_port

        print("\n" + "="*70)
        print("🦉 MemScreen API Server")
        print("="*70)
        print(f"\n🚀 Starting API server on http://{host}:{port}")
        print("\n📱 Flutter UI:")
        print("   Option 1: Use the quick launcher (recommended):")
        print("      ./scripts/start_flutter.sh")
        print("\n   Option 2: Manually start Flutter in another terminal:")
        print("      cd frontend/flutter")
        print("      flutter run")
        print("\n" + "="*70 + "\n")

        uvicorn.run(
            "memscreen.api.app:app",
            host=host,
            port=port,
            reload=False,
        )

    except ImportError as e:
        print(f"❌ Failed to import MemScreen: {e}")
        print("\nPlease install MemScreen first:")
        print("   pip install -e .")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start MemScreen API: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
