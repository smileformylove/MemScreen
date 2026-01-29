#!/usr/bin/env python3
"""
Local Model Optimization Guide for MemScreen

Provides tips and tools for optimizing MemScreen with small local models.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_section(title):
    """Print formatted section"""
    print(f"\n▶ {title}")
    print("-" * 70)


def main():
    print_header("MemScreen v0.4.0 - Local Model Optimization Guide")

    print("""
🎯 This guide helps you get the most out of MemScreen with small local models (3B)

Current Model: qwen2.5vl:3b
- Parameters: 3 Billion
- Context Window: ~4K tokens
- Strengths: Vision understanding, simple tasks
- Limitations: Complex reasoning, long outputs
    """)

    print_section("1. Model Capabilities & Limitations")

    print("""
✅ What it CAN do well:
   • Screen capture and visual analysis
   • Simple Q&A about screenshots
   • Basic text summarization (short texts)
   • Keyword-based search
   • Single-step tasks

⚠️  What it STRUGGLES with:
   • Complex multi-step reasoning
   • Long documents (>1000 words)
   • Precise JSON formatting
   • Nuanced understanding
   • Creative writing
    """)

    print_section("2. Best Practices for Local Models")

    print("""
📝 Keep prompts SIMPLE:
   ❌ "Analyze the screenshot, extract all text, identify UI components,
       categorize them by type, and format the output as JSON with the
       following structure: {...}"

   ✅ "Describe what you see on this screen in 2-3 sentences."

📊 Limit content length:
   • Summarize: Use texts <500 words
   • Search: Focus on specific keywords
   • Analysis: Break complex tasks into smaller steps

🎯 Be specific and direct:
   ❌ "Tell me about the stuff on my screen from earlier"
   ✅ "Search for Python code from today's recordings"

⏱️  Manage expectations:
   • Response time: 10-60 seconds per request
   • Accuracy: 70-85% for simple tasks
   • Errors: May need 1-2 retries
    """)

    print_section("3. Recommended Workflows")

    print("""
🔴 SCREEN ANALYSIS:
   "看看屏幕上有什么"
   "分析当前屏幕内容"
   ✅ Works well with vision model

📊 CONTENT SEARCH:
   "搜索Python相关内容"
   "查找今天录制的代码"
   ✅ Reliable and fast

📝 SIMPLE SUMMARY:
   "总结今天录制的Python教程"
   "概括最近的工作内容"
   ✅ Works well for <10 items

⚠️  AVOID - Complex Reports:
   "生成过去一周所有活动的详细分析报告，包括每个应用的
   使用时间、频率、以及工作模式分析"
   ❌ Too complex for 3B model
    """)

    print_section("4. Token Budget Management")

    print("""
📊 Token limits for qwen2.5vl:3b:
   • Input prompt: ~500 tokens max recommended
   • Output response: ~200-300 tokens max
   • Vision images: ~1000 tokens per image

💡 Optimization tips:
   1. Short prompts = faster responses
   2. Limit search results to top 3-5
   3. Break long tasks into multiple steps
   4. Use specific keywords instead of vague descriptions

📈 Performance estimates:
   • Simple search: 5-15 seconds
   • Screen analysis: 30-60 seconds
   • Summary: 20-40 seconds
   • Complex multi-step: May timeout or fail
    """)

    print_section("5. Troubleshooting Common Issues")

    print("""
❌ "Model gives incomplete/empty responses"
   → Reduce num_predict in model options
   → Simplify your prompt
   → Break into smaller tasks

❌ "JSON parsing errors"
   → Use text-based formats instead
   → Avoid complex structures
   → Accept free-form responses

❌ "Timeout errors"
   → Check if Ollama is running: ollama list
   → Reduce task complexity
   → Increase timeout in agent config

❌ "Poor understanding of screen"
   → Ensure sufficient lighting/contrast
   → Try different screenshots
   → Use specific questions
    """)

    print_section("6. When to Upgrade Models")

    print("""
🚀 Consider upgrading to larger models if:
   • You need complex reasoning
   • Working with long documents
   • Require precise formatting
   • Need higher accuracy (>90%)

💪 Recommended models:
   • qwen2.5vl:7b (Better reasoning, more VRAM needed)
   • llama3.2:11b (Excellent text understanding)
   • mixtral:8x7b (Strong multilingual capabilities)

⚙️  Hardware requirements:
   • 3B models: 8GB RAM + 4GB VRAM
   • 7B models: 16GB RAM + 8GB VRAM
   • 13B+ models: 32GB RAM + 16GB VRAM
    """)

    print_section("7. Quick Reference - Example Queries")

    print("""
✅ GOOD Examples:

Screen Analysis:
  "看看屏幕上有什么"
  "当前显示的是什么应用"
  "描述屏幕上的内容"

Search & Find:
  "搜索Python代码"
  "查找关于asyncio的内容"
  "找到今天录制的错误信息"

Simple Summaries:
  "总结今天的代码工作"
  "概括最近5条录制的内容"

❌ AVOID Examples:

Too Complex:
  "分析过去一周的工作模式，识别效率瓶颈，
   提供详细的改进建议，并生成可视化报告"

Too Vague:
  "告诉我一些有用的东西"

Too Long:
  "搜索从一月一日到现在所有包含以下关键词的内容：
   [100+ keywords]，并总结每个类别的详细信息..."
    """)

    print_section("8. Configuration Tuning")

    print("""
🔧 Adjust these in agent_executor_v2.py:

# For faster responses (less accurate):
self.max_tokens = 200  # Reduce output length
self.temperature = 0.4  # More focused

# For better quality (slower):
self.max_tokens = 400  # More detailed
self.temperature = 0.7  # More creative

# For consistency:
self.temperature = 0.3  # Very deterministic

# Vision model settings:
"num_predict": 200-400  # Balance speed vs detail
"temperature": 0.6-0.8  # Higher for more descriptive
    """)

    print_header("Ready to Optimize?")

    print("""
📝 Key takeaways:

1. Keep it simple - small models do best with clear, direct tasks
2. Be patient - local inference is slower than cloud APIs
3. Manage expectations - 3B models have limitations
4. Use appropriate workflows - match task to model capability
5. Iterate - refine prompts based on results

🚀 For advanced users:
   - Edit agent_executor_v2.py for custom behavior
   - Adjust token budgets for your hardware
   - Experiment with different prompts
   - Consider upgrading to larger models if needed

💬 Need help?
   - Check README.md for basic usage
   - Review test_system_comprehensive.py for diagnostics
   - Report issues at github.com/smileformylove/MemScreen

Happy local AI computing! 🎉
    """)

    print("\n" + "=" * 70)
    print(" Guide Complete")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
