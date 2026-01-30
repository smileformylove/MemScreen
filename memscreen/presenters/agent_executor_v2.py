### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-01-29             ###
### license: MIT                ###

"""
Improved Agent Executor with Local Model Limitations Handling

This version is optimized for small local models (3B parameters):
- Simpler prompts
- Text-based formats instead of JSON
- Robust error handling
- Token budget management
- Fallback mechanisms
"""

import time
from typing import Dict, Any, List
import requests
import os
from datetime import datetime
from PIL import ImageGrab


class LocalModelExecutor:
    """
    Optimized agent executor for local models with limited capabilities.

    Key optimizations:
    1. Use simple text prompts instead of complex JSON
    2. Limit response length to avoid truncation
    3. Implement multiple fallback strategies
    4. Handle errors gracefully
    5. Work within token budget constraints
    """

    def __init__(self, memory_system, ollama_base_url: str, current_model: str):
        """
        Initialize the optimized executor.

        Args:
            memory_system: Memory system for searching
            ollama_base_url: Ollama API URL
            current_model: Current AI model to use
        """
        self.memory_system = memory_system
        self.ollama_base_url = ollama_base_url
        self.current_model = current_model
        self.vision_model = "qwen2.5vl:3b"

        # Model-specific constraints (optimized for speed and quality)
        self.max_tokens = 384  # Optimized for faster responses
        self.context_window = 4096  # Conservative context window
        self.temperature = 0.4  # Lower temperature for faster, focused responses

        # Create temp directory
        self.temp_dir = "./db/temp"
        os.makedirs(self.temp_dir, exist_ok=True)

    def execute_task(self, user_message: str) -> Dict[str, Any]:
        """
        Execute a task with robust error handling.

        Args:
            user_message: User's task description

        Returns:
            Execution result with comprehensive error handling
        """
        start_time = time.time()

        print(f"[LocalModelExecutor] 🤖 Executing: {user_message[:50]}...")

        try:
            # Determine workflow
            workflow = self._analyze_task(user_message)

            # Execute workflow with error handling
            results = []
            for i, step in enumerate(workflow["steps"]):
                print(f"[LocalModelExecutor] 📍 Step {i+1}/{len(workflow['steps'])}: {step['description']}")

                try:
                    result = self._execute_step(step, user_message, results)
                    results.append(result)

                    # Check for critical failures
                    if not result.get("success") and result.get("critical", False):
                        print(f"[LocalModelExecutor] ⚠️ Critical failure in step {i+1}, stopping")
                        break

                except Exception as e:
                    print(f"[LocalModelExecutor] ❌ Error in step {i+1}: {e}")
                    # Add error result and continue
                    results.append({
                        "success": False,
                        "error": str(e),
                        "step": step['description']
                    })

            # Build response
            response = self._build_response(workflow, results, start_time)

            return {
                "success": True,
                "response": response,
                "execution_time": time.time() - start_time,
                "workflow_type": workflow["type"]
            }

        except Exception as e:
            print(f"[LocalModelExecutor] ❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()

            # Return fallback response
            return {
                "success": False,
                "response": f"I encountered an error while processing your request: {str(e)}",
                "execution_time": time.time() - start_time,
                "error": str(e)
            }

    def _analyze_task(self, user_message: str) -> Dict[str, Any]:
        """Analyze task using simple keyword matching (no LLM needed)."""
        user_msg_lower = user_message.lower()

        # Screen analysis (highest priority)
        screen_keywords = ["屏幕上", "现在屏幕", "当前屏幕", "截屏", "screenshot", "what's on screen", "屏幕有什么", "看看屏幕"]
        if any(kw in user_msg_lower for kw in screen_keywords):
            return {
                "type": "screen_analysis",
                "description": "屏幕分析",
                "steps": [
                    {"type": "capture_screen", "description": "捕获并分析当前屏幕"},
                    {"type": "format", "description": "展示结果"}
                ]
            }

        # Report generation (requires search + summary)
        report_keywords = ["报告", "生成报告", "形成报告", "report", "总结报告", "分析报告"]
        if any(kw in user_msg_lower for kw in report_keywords):
            return {
                "type": "report",
                "description": "报告生成",
                "steps": [
                    {"type": "search", "description": "搜索相关屏幕记录"},
                    {"type": "summarize", "description": "生成内容摘要"},
                    {"type": "format", "description": "格式化报告"}
                ]
            }

        # Summary task
        summary_keywords = ["总结", "汇总", "summary", "概括"]
        if any(kw in user_msg_lower for kw in summary_keywords):
            return {
                "type": "summary",
                "description": "内容总结",
                "steps": [
                    {"type": "search", "description": "搜索相关内容"},
                    {"type": "summarize", "description": "生成摘要"}
                ]
            }

        # Search and analyze
        if any(kw in user_msg_lower for kw in ["搜索", "查找", "search"]):
            return {
                "type": "search_and_analyze",
                "description": "搜索与分析",
                "steps": [
                    {"type": "search", "description": "执行搜索"},
                    {"type": "summarize", "description": "分析结果"}
                ]
            }

        # Default: simple search
        return {
            "type": "search",
            "description": "内容搜索",
            "steps": [
                {"type": "search", "description": "搜索记录"},
                {"type": "format", "description": "展示结果"}
            ]
        }

    def _execute_step(self, step: Dict, user_message: str, previous_results: List[Dict]) -> Dict[str, Any]:
        """Execute a single step with error handling."""
        step_type = step["type"]

        try:
            if step_type == "search":
                return self._execute_search(user_message)
            elif step_type == "capture_screen":
                return self._execute_capture_screen(user_message)
            elif step_type == "summarize":
                return self._execute_summarize_simple(user_message, previous_results)
            elif step_type == "format":
                return {"success": True, "formatted": True}
            else:
                return {"success": False, "error": f"Unknown step type: {step_type}"}

        except Exception as e:
            print(f"[LocalModelExecutor] ⚠️ Step error: {e}")
            return {"success": False, "error": str(e)}

    def _execute_search(self, query: str) -> Dict[str, Any]:
        """Execute search with error handling."""
        try:
            if not self.memory_system:
                return {"success": False, "error": "Memory system not available", "critical": True}

            print(f"[LocalModelExecutor] 🔍 Searching: {query[:50]}...")

            results = self.memory_system.search(
                query=query,
                user_id="screenshot"
            )

            if not results or 'results' not in results:
                return {"success": True, "count": 0, "results": []}

            search_results = results['results']
            print(f"[LocalModelExecutor] 🔍 Found {len(search_results)} results")

            return {
                "success": True,
                "count": len(search_results),
                "results": search_results[:5]  # Limit to top 5 for token budget
            }

        except Exception as e:
            print(f"[LocalModelExecutor] ❌ Search error: {e}")
            return {"success": False, "error": str(e)}

    def _execute_capture_screen(self, query: str) -> Dict[str, Any]:
        """Execute screen capture with optimized vision prompt."""
        try:
            print(f"[LocalModelExecutor] 📸 Capturing screen...")

            # Capture screen
            screenshot = ImageGrab.grab()

            # Save to temporary file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = os.path.join(self.temp_dir, f"temp_screenshot_{timestamp}.png")
            screenshot.save(temp_path)

            print(f"[LocalModelExecutor] 📸 Screenshot saved")

            # Use simpler, more focused prompt for small models
            vision_prompt = f"""请简洁描述屏幕内容（不超过200字）：
1. 主要应用
2. 界面元素
3. 文本内容

用户问题：{query}"""

            try:
                # Use Ollama vision API with conservative settings
                with open(temp_path, "rb") as image_file:
                    import base64
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')

                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.vision_model,
                        "prompt": vision_prompt,
                        "images": [image_data],
                        "stream": False,
                        "options": {
                            "temperature": 0.6,
                            "num_predict": 300,  # Conservative limit
                            "top_p": 0.9,
                            "top_k": 30
                        }
                    },
                    timeout=90
                )

                if response.status_code == 200:
                    data = response.json()
                    analysis = data.get("response", "").strip()

                    print(f"[LocalModelExecutor] 👁️ Analysis: {len(analysis)} chars")

                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                    except:
                        pass

                    return {
                        "success": True,
                        "analysis": analysis[:500],  # Limit length
                        "type": "screen_capture"
                    }
                else:
                    raise Exception(f"Vision API error: {response.status_code}")

            except Exception as e:
                print(f"[LocalModelExecutor] ⚠️ Vision error: {e}")

                # Fallback
                return {
                    "success": True,
                    "analysis": "屏幕已捕获，但视觉分析暂时不可用。",
                    "type": "capture_fallback"
                }

        except Exception as e:
            print(f"[LocalModelExecutor] ❌ Capture error: {e}")
            return {"success": False, "error": str(e)}

    def _execute_summarize_simple(self, query: str, previous_results: List[Dict]) -> Dict[str, Any]:
        """Execute summarization with simple text-based approach."""
        try:
            # Collect content from previous searches
            content_items = []

            for result in previous_results:
                if result.get("success") and result.get("results"):
                    for item in result["results"][:3]:  # Top 3 only
                        if isinstance(item, dict):
                            content = item.get("content", "")[:300]  # Truncate long content
                            content_items.append(content)

            if not content_items:
                return {
                    "success": True,
                    "summary": "没有找到相关内容。建议先录制一些屏幕内容，然后再尝试查询。"
                }

            # Build simple summary prompt (text-based, no JSON)
            combined_content = "\n".join([f"- {item}" for item in content_items])

            summary_prompt = f"""请简洁总结以下内容（不超过150字）：

{combined_content}

总结："""

            print(f"[LocalModelExecutor] 📝 Summarizing {len(content_items)} items")

            try:
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.current_model,
                        "prompt": summary_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.6,
                            "num_predict": 200,  # Conservative
                            "top_p": 0.9,
                            "top_k": 30
                        }
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    summary = data.get("response", "").strip()

                    print(f"[LocalModelExecutor] 📝 Summary: {len(summary)} chars")
                    return {"success": True, "summary": summary[:300]}
                else:
                    raise Exception(f"API error: {response.status_code}")

            except Exception as e:
                print(f"[LocalModelExecutor] ⚠️ LLM error: {e}")

                # Simple fallback summary
                count = len(content_items)
                fallback_summary = f"找到 {count} 条相关记录。内容包括：{combined_content[:100]}..."
                return {"success": True, "summary": fallback_summary}

        except Exception as e:
            print(f"[LocalModelExecutor] ❌ Summarization error: {e}")
            return {"success": False, "error": str(e)}

    def _build_response(self, workflow: Dict, results: List[Dict], start_time: float) -> str:
        """Build clear, user-friendly response."""
        parts = []

        # Header
        parts.append(f"🤖 **AI 助手 - {workflow['description']}**\n")

        # Steps and results
        for i, (step, result) in enumerate(zip(workflow["steps"], results), 1):
            parts.append(f"⏳ 步骤 {i}: {step['description']}")

            if result.get("success"):
                if "count" in result:
                    count = result["count"]
                    parts.append(f"✅ 完成：找到 {count} 条记录")

                    # Show top results
                    if result.get("results") and len(result["results"]) > 0:
                        parts.append(f"\n📌 **最相关结果**:")
                        for j, item in enumerate(result["results"][:3], 1):
                            if isinstance(item, dict):
                                content = item.get("content", "")[:100]
                                score = item.get("score", 0)
                                parts.append(f"   {j}. [{score:.2f}] {content}...")
                        parts.append("")

                elif "analysis" in result:
                    analysis = result["analysis"]
                    parts.append(f"✅ 完成\n")
                    parts.append(f"👁️ **分析结果**:\n{analysis}\n")

                elif "summary" in result:
                    summary = result["summary"]
                    parts.append(f"✅ 完成\n")
                    parts.append(f"📝 **摘要**:\n{summary}\n")
                else:
                    parts.append("✅ 完成\n")
            else:
                error = result.get("error", "Unknown error")
                parts.append(f"⚠️ 该步骤遇到问题: {error}\n")

        # Execution time
        exec_time = time.time() - start_time
        parts.append(f"\n⏱️ 执行时间: {exec_time:.1f} 秒")

        return "\n".join(parts)


__all__ = ["LocalModelExecutor"]
