#!/usr/bin/env python3
"""
 - 
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("👁️ ")
print("=" * 80)

from memscreen.memory import Memory, MemoryConfig
import requests
import base64
from PIL import ImageGrab
import cv2
import numpy as np

print("\n1️⃣  Memory ...")
config = MemoryConfig(
    enable_dynamic_memory=True,
    dynamic_config={
        "enable_auto_classification": True,
    }
)
memory = Memory(config=config)
print("   ✅ Memory ")

print("\n2️⃣ ...")
print("   ")

try:
    # 
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # 
    _, buffer = cv2.imencode('.jpg', screenshot_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    img_str = base64.b64encode(buffer).decode('utf-8')

    print("\n...")
    start = time.time()

    # 
    enhanced_prompt = """You are analyzing a screen capture for memory storage. Describe in detail:

1. **Visible Objects**: List ALL objects you see (icons, buttons, images, symbols, etc.)
   - Examples: keys, locks, icons, logos, buttons, menus, toolbars
   - Be specific about position and appearance

2. **Text Content**: Extract all text visible on screen

3. **Application & Activity**: What app is running and what's happening

4. **Visual Elements**: Colors, layouts, UI components

Format your response as:
Objects: [detailed list of visible objects]
Text: [all extracted text]
Scene: [application] - [activity description]
Visual: [visual elements description]

Be thorough - this information will be used for semantic search."""

    response = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={
            "model": "qwen2.5vl:3b",
            "prompt": enhanced_prompt,
            "images": [img_str],
            "stream": False,
            "options": {
                "num_predict": 512,
                "temperature": 0.3,
                "top_p": 0.9,
            }
        },
        timeout=30
    )

    elapsed = time.time() - start

    if response.status_code == 200:
        result = response.json()
        content = result.get("response", "").strip()

        print(f"\n✅  (: {elapsed:.2f}s)")
        print("\n" + "=" * 60)
        print(":")
        print("=" * 60)
        print(content)
        print("=" * 60)

        # 
        print("\n3️⃣  Memory...")
        memory.add(
            messages=[{"role": "user", "content": f"Screen capture analysis:\n{content}"}],
            user_id="test_user",
            metadata={
                "type": "screen_capture",
                "content_description": content,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            infer=True
        )
        print("   ✅  Memory")

        # 
        print("\n4️⃣ ...")
        test_queries = [
            "",
            "key",
            "",
            "objects",
        ]

        for query in test_queries:
            print(f"\n: '{query}'")
            results = memory.search(query=query, user_id="test_user")

            if results and 'results' in results and results['results']:
                print(f"  ✅  {len(results['results'])} ")
                for i, r in enumerate(results['results'][:2], 1):
                    desc = r.get('metadata', {}).get('content_description', 'N/A')
                    print(f"     {i}. {desc[:100]}...")
            else:
                print(f"  ❌ ")

    else:
        print(f"❌ : {response.status_code}")

except Exception as e:
    print(f"❌ : {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ ")
print("=" * 80)

print("""
:

1. :
   -  num_predict 
   -  temperature 
   - 

2. :
   -  content_description 
   -  infer=True 
   -  smart_search  search

3. :
   - 5→10
   - 
   - 


""")
print("=" * 80)
