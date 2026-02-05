### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""
Rule-based Agent Executor for ChatPresenter

Provides reliable, rule-based task execution without LLM planning dependency.
Includes screen capture and visual understanding capabilities.
"""

import time
from typing import Dict, Any, List
import requests
import os
from datetime import datetime
from PIL import ImageGrab


class AgentExecutor:
    """
    Rule-based agent that executes common task workflows.

    This is simpler and more reliable than LLM-based planning.
    """

    def __init__(self, memory_system, ollama_base_url: str, current_model: str):
        """
        Initialize the agent executor.

        Args:
            memory_system: Memory system for searching
            ollama_base_url: Ollama API URL
            current_model: Current AI model to use
        """
        self.memory_system = memory_system
        self.ollama_base_url = ollama_base_url
        self.current_model = current_model
        self.vision_model = "qwen3:1.7b"  # Vision model for screen understanding

        # Create temp directory for screenshots
        self.temp_dir = "./db/temp"
        os.makedirs(self.temp_dir, exist_ok=True)

    def execute_task(self, user_message: str) -> Dict[str, Any]:
        """
        Execute a task based on user message.

        Args:
            user_message: User's task description

        Returns:
            Execution result with report
        """
        start_time = time.time()

        print(f"[AgentExecutor] 🤖 Executing task: {user_message}")

        # Determine workflow
        workflow = self._analyze_task(user_message)

        # Execute workflow
        results = []
        for step in workflow["steps"]:
            print(f"[AgentExecutor] 📍 Step: {step['description']}")
            result = self._execute_step(step, user_message, results)
            results.append(result)

        # Build response
        response = self._build_response(workflow, results, start_time)

        return {
            "success": True,
            "response": response,
            "execution_time": time.time() - start_time
        }

    def _analyze_task(self, user_message: str) -> Dict[str, Any]:
        """Analyze task and determine workflow."""
        user_msg_lower = user_message.lower()

        # Screen analysis (current screen)
        if any(kw in user_msg_lower for kw in ["屏幕上", "现在屏幕", "当前屏幕", "截屏", "screenshot", "what's on screen", "屏幕有什么", "看看屏幕"]):
            return {
                "type": "screen_analysis",
                "description": "屏幕分析",
                "steps": [
                    {"type": "capture_screen", "description": "捕获并分析当前屏幕"},
                    {"type": "format", "description": "展示结果"}
                ]
            }

        # Report generation
        if any(kw in user_msg_lower for kw in ["报告", "生成报告", "形成报告", "report"]):
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
        elif any(kw in user_msg_lower for kw in ["总结", "汇总", "summary"]):
            return {
                "type": "summary",
                "description": "内容总结",
                "steps": [
                    {"type": "search", "description": "搜索相关内容"},
                    {"type": "summarize", "description": "生成摘要"}
                ]
            }

        # Search and process
        elif any(kw in user_msg_lower for kw in ["搜索", "查找"]) and \
             any(kw in user_msg_lower for kw in ["并", "然后", "and", "then"]):
            return {
                "type": "search_and_process",
                "description": "搜索与处理",
                "steps": [
                    {"type": "search", "description": "执行搜索"},
                    {"type": "summarize", "description": "处理结果"}
                ]
            }

        # Analysis task
        elif any(kw in user_msg_lower for kw in ["分析", "流程", "模式", "analyze", "workflow"]):
            return {
                "type": "analysis",
                "description": "数据分析",
                "steps": [
                    {"type": "search", "description": "收集数据"},
                    {"type": "summarize", "description": "生成分析"}
                ]
            }

        # Default: search only
        return {
            "type": "search",
            "description": "内容搜索",
            "steps": [
                {"type": "search", "description": "搜索记录"},
                {"type": "format", "description": "展示结果"}
            ]
        }

    def _execute_step(self, step: Dict, user_message: str, previous_results: List[Dict]) -> Dict[str, Any]:
        """Execute a single step."""
        step_type = step["type"]

        if step_type == "search":
            return self._execute_search(user_message)
        elif step_type == "capture_screen":
            return self._execute_capture_screen(user_message)
        elif step_type == "summarize":
            return self._execute_summarize(user_message, previous_results)
        elif step_type == "format":
            return {"success": True, "formatted": True}
        else:
            return {"success": False, "error": f"Unknown step type: {step_type}"}

    def _execute_search(self, query: str) -> Dict[str, Any]:
        """Execute search step."""
        try:
            if not self.memory_system:
                return {"success": False, "error": "Memory system not available"}

            print(f"[AgentExecutor] 🔍 Searching: {query}")

            results = self.memory_system.search(
                query=query,
                user_id="screenshot"
            )

            if not results or 'results' not in results:
                return {"success": True, "count": 0, "results": []}

            search_results = results['results']
            print(f"[AgentExecutor] 🔍 Found {len(search_results)} results")

            return {
                "success": True,
                "count": len(search_results),
                "results": search_results
            }

        except Exception as e:
            print(f"[AgentExecutor] ❌ Search error: {e}")
            return {"success": False, "error": str(e)}

    def _execute_capture_screen(self, query: str) -> Dict[str, Any]:
        """Execute screen capture and analysis step."""
        try:
            print(f"[AgentExecutor] 📸 Capturing screen...")

            # Capture screen
            screenshot = ImageGrab.grab()

            # Save to temporary file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = os.path.join(self.temp_dir, f"temp_screenshot_{timestamp}.png")
            screenshot.save(temp_path)

            print(f"[AgentExecutor] 📸 Screenshot saved: {temp_path}")

            # Analyze with vision model
            print(f"[AgentExecutor] 👁️ Analyzing with vision model...")

            # Build prompt for vision understanding
            vision_prompt = f"""请详细描述你在这个截图中看到的内容。包括：
1. 主要应用程序或窗口
2. 界面布局和元素
3. 文本内容（如果有的话）
4. 图表、图片或数据
5. 任何显著的特征或活动

用户的问题：{query}"""

            try:
                # Use Ollama vision API
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
                            "temperature": 0.7,
                            "num_predict": 500,
                            "top_p": 0.9,
                            "top_k": 40
                        }
                    },
                    timeout=90
                )

                if response.status_code == 200:
                    data = response.json()
                    analysis = data.get("response", "").strip()

                    print(f"[AgentExecutor] 👁️ Vision analysis: {len(analysis)} chars")

                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                        print(f"[AgentExecutor] 🧹 Cleaned up temp file")
                    except:
                        pass

                    return {
                        "success": True,
                        "analysis": analysis,
                        "screenshot_path": temp_path,
                        "type": "screen_capture"
                    }
                else:
                    raise Exception(f"Vision API error: {response.status_code}")

            except Exception as e:
                print(f"[AgentExecutor] ⚠️ Vision model error: {e}")

                # Fallback: Try OCR extraction
                try:
                    import pytesseract
                    text = pytesseract.image_to_string(screenshot, lang='chi_sim+eng')

                    print(f"[AgentExecutor] 📄 OCR fallback: {len(text)} chars")

                    return {
                        "success": True,
                        "analysis": f"通过OCR提取的屏幕文本内容：\n\n{text[:1000]}",
                        "screenshot_path": temp_path,
                        "type": "ocr_fallback"
                    }
                except:
                    # Final fallback
                    return {
                        "success": True,
                        "analysis": "已捕获屏幕截图，但视觉分析暂时不可用。截图已保存。",
                        "screenshot_path": temp_path,
                        "type": "capture_only"
                    }

        except Exception as e:
            print(f"[AgentExecutor] ❌ Screen capture error: {e}")
            return {"success": False, "error": str(e)}

    def _execute_summarize(self, query: str, previous_results: List[Dict]) -> Dict[str, Any]:
        """Execute summarization step."""
        try:
            # Collect content from previous searches
            content_items = []

            for result in previous_results:
                if result.get("success") and result.get("results"):
                    for item in result["results"][:3]:  # Top 3
                        if isinstance(item, dict):
                            content = item.get("content", "")
                            metadata = item.get("metadata", {})
                            content_items.append({
                                "content": content[:400],
                                "type": metadata.get("type", "unknown"),
                                "timestamp": metadata.get("timestamp", "")
                            })

            if not content_items:
                return {
                    "success": True,
                    "summary": "没有找到相关内容。建议先录制一些屏幕内容，然后再尝试查询。"
                }

            # Build content for summarization
            combined_content = "\n\n".join([
                f"[{item['type']}] {item['timestamp']}\n{item['content']}"
                for item in content_items
            ])

            print(f"[AgentExecutor] 📝 Summarizing {len(content_items)} items")

            # Generate summary using LLM
            try:
                summary_prompt = f"""请简洁总结以下屏幕记录内容（不超过150字）：

{combined_content}

总结："""

                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.current_model,
                        "prompt": summary_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.6,
                            "num_predict": 250,
                            "top_p": 0.9,
                            "top_k": 30
                        }
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    summary = data.get("response", "").strip()
                    print(f"[AgentExecutor] 📝 Summary: {len(summary)} chars")
                    return {"success": True, "summary": summary}
                else:
                    raise Exception(f"API error: {response.status_code}")

            except Exception as e:
                print(f"[AgentExecutor] ⚠️ LLM error: {e}")
                # Fallback
                summary = f"找到 {len(content_items)} 条记录，包括：{', '.join(set(item['type'] for item in content_items))}。"
                return {"success": True, "summary": summary}

        except Exception as e:
            print(f"[AgentExecutor] ❌ Summarization error: {e}")
            return {"success": False, "error": str(e)}

    def _build_response(self, workflow: Dict, results: List[Dict], start_time: float) -> str:
        """Build formatted response."""
        parts = []

        # Header
        parts.append(f"🤖 **AI Agent {workflow['description']}报告**\n")

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
                                content = item.get("content", "")[:120]
                                score = item.get("score", 0)
                                parts.append(f"   {j}. [{score:.2f}] {content}...")
                        parts.append("")

                elif "analysis" in result:
                    analysis = result["analysis"]
                    result_type = result.get("type", "unknown")

                    if result_type == "screen_capture":
                        parts.append(f"[OK] 完成\n")
                        parts.append(f"[Eye] **屏幕视觉分析**:\n{analysis}\n")
                    elif result_type == "ocr_fallback":
                        parts.append(f"[OK] 完成（OCR模式）\n")
                        parts.append(f"[Doc] **文本提取**:\n{analysis}\n")
                    else:
                        parts.append(f"[OK] 完成\n")
                        parts.append(f"[Chart] **分析结果**:\n{analysis}\n")

                elif "summary" in result:
                    summary = result["summary"]
                    parts.append(f"[OK] 完成\n")
                    parts.append(f"[Note] **摘要**:\n{summary}\n")
                else:
                    parts.append("[OK] 完成\n")
            else:
                error = result.get("error", "Unknown error")
                parts.append(f"✗ 失败: {error}\n")

        # Execution time
        exec_time = time.time() - start_time
        parts.append(f"\n[Time] 执行时间: {exec_time:.2f} 秒")

        return "\n".join(parts)


__all__ = ["AgentExecutor"]
