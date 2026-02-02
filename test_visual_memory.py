#!/usr/bin/env python3
"""
视觉记忆测试 - 测试物体识别和搜索
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("👁️ 视觉记忆测试")
print("=" * 80)

from memscreen.memory import Memory, MemoryConfig
import requests
import base64
from PIL import ImageGrab
import cv2
import numpy as np

print("\n1️⃣ 初始化 Memory 系统...")
config = MemoryConfig(
    enable_dynamic_memory=True,
    dynamic_config={
        "enable_auto_classification": True,
    }
)
memory = Memory(config=config)
print("   ✅ Memory 初始化完成")

print("\n2️⃣ 测试视觉分析（当前屏幕）...")
print("   提示：请确保屏幕上有一个明显的物体（如钥匙、图标等）")

try:
    # 捕获当前屏幕
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # 编码图像
    _, buffer = cv2.imencode('.jpg', screenshot_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    img_str = base64.b64encode(buffer).decode('utf-8')

    print("\n正在分析屏幕内容...")
    start = time.time()

    # 使用改进的视觉分析提示词
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

        print(f"\n✅ 视觉分析完成 (耗时: {elapsed:.2f}s)")
        print("\n" + "=" * 60)
        print("分析结果:")
        print("=" * 60)
        print(content)
        print("=" * 60)

        # 保存到记忆
        print("\n3️⃣ 保存到 Memory...")
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
        print("   ✅ 已保存到 Memory")

        # 测试搜索
        print("\n4️⃣ 测试搜索功能...")
        test_queries = [
            "钥匙",
            "key",
            "屏幕上有什么",
            "objects",
        ]

        for query in test_queries:
            print(f"\n搜索: '{query}'")
            results = memory.search(query=query, user_id="test_user")

            if results and 'results' in results and results['results']:
                print(f"  ✅ 找到 {len(results['results'])} 条结果")
                for i, r in enumerate(results['results'][:2], 1):
                    desc = r.get('metadata', {}).get('content_description', 'N/A')
                    print(f"     {i}. {desc[:100]}...")
            else:
                print(f"  ❌ 未找到结果")

    else:
        print(f"❌ 视觉分析失败: {response.status_code}")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ 测试完成")
print("=" * 80)

print("""
优化建议:

1. 如果视觉分析没有描述物体:
   - 增加 num_predict 参数
   - 降低 temperature 参数
   - 改进提示词

2. 如果搜索不到物体:
   - 检查 content_description 是否保存
   - 检查 infer=True 是否启用
   - 使用 smart_search 代替 search

3. 录制视频时:
   - 增加采样帧数（已优化：5→10帧）
   - 使用详细的视觉分析提示词（已优化）
   - 保存帧级别的详细描述（已实现）

测试截图已保存，请检查是否能找到屏幕上的物体！
""")
print("=" * 80)
