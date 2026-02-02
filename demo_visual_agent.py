#!/usr/bin/env python3
"""
Visual Agent 演示 - 屏幕捕获与视觉理解
"""

import sys
import os
import asyncio
from datetime import datetime
from PIL import ImageGrab
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("👁️ Visual Agent 演示 - 屏幕捕获与视觉理解")
print("=" * 80)

from memscreen.presenters.recording_presenter import RecordingPresenter
from memscreen.presenters.video_presenter import VideoPresenter
from memscreen.memory import Memory, MemoryConfig


class MockView:
    """模拟 View 界面"""
    def __init__(self):
        self.messages = []

    def update_chat_preview(self, sender, message):
        self.messages.append((sender, message))
        print(f"[{sender}] {message[:100]}...")

    def show_status(self, status):
        print(f"[Status] {status}")


class MockLLMClient:
    """模拟 LLM 客户端"""
    def generate_response(self, messages, **kwargs):
        return "这是模拟的视觉分析响应"

    def generate_chat_response(self, messages, **kwargs):
        return "基于截图内容，我识别到了相关信息"


def demo_screen_capture():
    """演示屏幕捕获功能"""
    print("\n" + "=" * 80)
    print("📸 屏幕捕获演示")
    print("=" * 80)

    print("\n🎯 Visual Agent 支持多种捕获模式:")
    print("-" * 60)

    features = [
        ("全屏捕获", "捕获整个屏幕内容"),
        ("自定义区域", "拖拽选择特定区域"),
        ("视觉十字线", "辅助精确定位"),
        ("实时预览", "即时查看捕获效果"),
        ("定时捕获", "0.5-5秒间隔自动截图"),
    ]

    for feature, description in features:
        print(f"  ✅ {feature:12s} — {description}")

    print("\n🔍 屏幕捕获应用场景:")
    print("-" * 60)

    scenarios = [
        "记录重要文档和网页内容",
        "捕获软件操作步骤",
        "保存聊天记录和对话",
        "截取代码片段和错误信息",
        "收集灵感和设计参考",
    ]

    for scenario in scenarios:
        print(f"  📌 {scenario}")

    # 演示捕获
    print("\n📸 执行屏幕捕获...")
    try:
        screenshot = ImageGrab.grab()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"demo_screenshot_{timestamp}.png"
        screenshot.save(filename)
        print(f"  ✅ 截图已保存: {filename}")
        print(f"  📐 分辨率: {screenshot.size[0]}x{screenshot.size[1]}")
    except Exception as e:
        print(f"  ⚠️ 演示模式跳过实际捕获: {e}")


def demo_ocr_text_extraction():
    """演示 OCR 文本提取功能"""
    print("\n" + "=" * 80)
    print("📝 OCR 文本提取演示")
    print("=" * 80)

    print("\n🤖 Visual Agent 的 OCR 能力:")
    print("-" * 60)

    ocr_features = [
        ("多语言识别", "支持中文、英文等多种语言"),
        ("高准确率", "基于先进 OCR 引擎"),
        ("布局保留", "保持原始文本格式"),
        ("批量处理", "一次处理多个截图"),
        ("语义理解", "提取文本并进行语义分析"),
    ]

    for feature, description in ocr_features:
        print(f"  ✅ {feature:12s} — {description}")

    print("\n💡 OCR 应用场景:")
    print("-" * 60)

    scenarios = [
        "从截图中提取关键信息",
        "数字化图片中的文字",
        "提取代码片段和命令",
        "保存重要通知和提醒",
        "创建可搜索的文本存档",
    ]

    for scenario in scenarios:
        print(f"  📌 {scenario}")


def demo_video_analysis():
    """演示视频分析功能"""
    print("\n" + "=" * 80)
    print("🎬 视频分析演示")
    print("=" * 80)

    print("\n🎥 Visual Agent 的视频处理能力:")
    print("-" * 60)

    video_features = [
        ("智能录制", "按需录制屏幕活动"),
        ("帧级别分析", "逐帧理解视频内容"),
        ("场景识别", "自动识别应用和活动"),
        ("语义搜索", "基于内容搜索视频"),
        ("时间轴导航", "快速定位关键帧"),
    ]

    for feature, description in video_features:
        print(f"  ✅ {feature:12s} — {description}")

    print("\n🎯 视频分析应用:")
    print("-" * 60)

    applications = [
        "回溯操作历史",
        "查找特定活动记录",
        "分析工作流程",
        "提取关键信息",
        "创建操作教程",
    ]

    for app in applications:
        print(f"  📌 {app}")


def demo_integrated_workflow():
    """演示集成工作流"""
    print("\n" + "=" * 80)
    print("🔄 集成工作流演示")
    print("=" * 80)

    print("\n🚀 Visual Agent 完整工作流:")
    print("-" * 60)

    workflow = [
        ("1. 捕获", "自动截取屏幕内容"),
        ("2. 理解", "使用视觉模型分析截图"),
        ("3. 提取", "OCR 提取文本信息"),
        ("4. 存储", "保存到 Memory 系统"),
        ("5. 索引", "创建语义索引"),
        ("6. 搜索", "支持自然语言查询"),
        ("7. 回答", "基于视觉记忆回答问题"),
    ]

    for step, description in workflow:
        print(f"  {step:8s} → {description}")

    print("\n💬 使用示例:")
    print("-" * 60)

    examples = [
        ("查找昨天的文档", "搜索历史截图中的文档内容"),
        ("蓝色按钮的界面", "查找特定UI设计的截图"),
        ("Python装饰器的代码", "搜索代码片段截图"),
        ("会议记录的内容", "查找会议相关的屏幕记录"),
    ]

    for query, explanation in examples:
        print(f"\n  用户: {query}")
        print(f"  Agent: {explanation}")


def demo_visual_presenter_integration():
    """演示与 Presenter 的集成"""
    print("\n" + "=" * 80)
    print("🔌 Visual Agent 集成演示")
    print("=" * 80)

    print("\n📦 MemScreen 的视觉组件:")
    print("-" * 60)

    components = [
        ("RecordingPresenter", "处理屏幕录制和捕获"),
        ("VideoPresenter", "管理视频播放和分析"),
        ("ChatPresenter", "集成视觉记忆到对话"),
        ("Memory", "存储和索引视觉内容"),
    ]

    for component, description in components:
        print(f"  📦 {component:20s} — {description}")

    print("\n🔗 数据流:")
    print("-" * 60)
    print("  屏幕 → ImageGrab → PIL Image → OCR/视觉模型 → Memory → Chat")
    print("                                                    ↓")
    print("                                               语义索引")

    print("\n💡 关键优势:")
    print("-" * 60)

    advantages = [
        ("100% 本地", "所有处理在本地完成"),
        ("隐私保护", "不上传任何数据"),
        ("实时处理", "即时分析截图"),
        ("智能搜索", "基于语义理解"),
        ("多模态", "文本+视觉联合分析"),
    ]

    for advantage, description in advantages:
        print(f"  ✅ {advantage:12s} — {description}")


def demo_memory_integration():
    """演示与 Memory 系统的集成"""
    print("\n" + "=" * 80)
    print("🧠 Memory 集成演示")
    print("=" * 80)

    print("\n📊 Visual Agent 使用 Dynamic Memory:")
    print("-" * 60)

    categories = [
        ("screenshot", "屏幕截图"),
        ("ocr_text", "OCR提取的文本"),
        ("video_frame", "视频帧"),
        ("scene", "识别的场景"),
        ("document", "提取的文档"),
    ]

    for category, description in categories:
        print(f"  📂 {category:15s} — {description}")

    print("\n🎯 查询意图:")
    print("-" * 60)

    intents = [
        ("find_screenshot", "查找特定截图"),
        ("search_text", "搜索截图中的文本"),
        ("locate_video", "定位相关视频"),
        ("extract_info", "提取视觉信息"),
    ]

    for intent, description in intents:
        print(f"  🔍 {intent:15s} — {description}")

    print("\n💡 性能优化:")
    print("-" * 60)
    print("  ✅ 只搜索相关类别（3-5x 更快）")
    print("  ✅ 定向上下文获取（70% 更少 tokens）")
    print("  ✅ 智能缓存机制（减少重复处理）")


if __name__ == "__main__":
    # 演示屏幕捕获
    demo_screen_capture()

    # 演示 OCR 文本提取
    demo_ocr_text_extraction()

    # 演示视频分析
    demo_video_analysis()

    # 演示集成工作流
    demo_integrated_workflow()

    # 演示 Presenter 集成
    demo_visual_presenter_integration()

    # 演示 Memory 集成
    demo_memory_integration()

    print("\n" + "=" * 80)
    print("✅ Visual Agent 演示完成")
    print("=" * 80)

    print("""
👁️ Visual Agent 核心特性:

1. 📸 屏幕捕获
   - 全屏和自定义区域捕获
   - 实时预览和视觉引导
   - 灵活的定时捕获

2. 📝 OCR 文本提取
   - 多语言文字识别
   - 高准确率文本提取
   - 布局和格式保留

3. 🎬 视频分析
   - 智能屏幕录制
   - 帧级别内容理解
   - 语义搜索和导航

4. 🧠 智能集成
   - 与 Dynamic Memory 深度集成
   - 自动分类和索引
   - 自然语言查询

5. 🔒 隐私保护
   - 100% 本地处理
   - 零数据上传
   - 完全可控

实际使用:
    from memscreen.presenters import RecordingPresenter, ChatPresenter

    # 录制屏幕
    recorder = RecordingPresenter(view=view, memory=memory)
    recorder.start_recording()  # 自动捕获和分析

    # 查询视觉记忆
    chat = ChatPresenter(view=view, memory_system=memory)
    chat.send_message("显示昨天的代码截图")
    # → 自动搜索截图记忆并返回结果
""")

    print("=" * 80)
