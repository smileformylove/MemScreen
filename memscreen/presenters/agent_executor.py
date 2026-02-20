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

        # Create temp directory for screenshots - use user home directory
        import tempfile
        self.temp_dir = os.path.join(os.path.expanduser("~"), ".memscreen", "temp")
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
        if any(kw in user_msg_lower for kw in ["", "", "", "", "screenshot", "what's on screen", "", ""]):
            return {
                "type": "screen_analysis",
                "description": "",
                "steps": [
                    {"type": "capture_screen", "description": ""},
                    {"type": "format", "description": ""}
                ]
            }

        # Report generation
        if any(kw in user_msg_lower for kw in ["", "", "", "report"]):
            return {
                "type": "report",
                "description": "",
                "steps": [
                    {"type": "search", "description": ""},
                    {"type": "summarize", "description": ""},
                    {"type": "format", "description": ""}
                ]
            }

        # Summary task
        elif any(kw in user_msg_lower for kw in ["", "", "summary"]):
            return {
                "type": "summary",
                "description": "",
                "steps": [
                    {"type": "search", "description": ""},
                    {"type": "summarize", "description": ""}
                ]
            }

        # Search and process
        elif any(kw in user_msg_lower for kw in ["", ""]) and \
             any(kw in user_msg_lower for kw in ["", "", "and", "then"]):
            return {
                "type": "search_and_process",
                "description": "",
                "steps": [
                    {"type": "search", "description": ""},
                    {"type": "summarize", "description": ""}
                ]
            }

        # Analysis task
        elif any(kw in user_msg_lower for kw in ["", "", "", "analyze", "workflow"]):
            return {
                "type": "analysis",
                "description": "",
                "steps": [
                    {"type": "search", "description": ""},
                    {"type": "summarize", "description": ""}
                ]
            }

        # Default: search only
        return {
            "type": "search",
            "description": "",
            "steps": [
                {"type": "search", "description": ""},
                {"type": "format", "description": ""}
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
            vision_prompt = f"""
1. 
2. 
3. 
4. 
5. 

{query}"""

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
                        "analysis": f"OCR\n\n{text[:1000]}",
                        "screenshot_path": temp_path,
                        "type": "ocr_fallback"
                    }
                except:
                    # Final fallback
                    return {
                        "success": True,
                        "analysis": "",
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
                    "summary": ""
                }

            # Build content for summarization
            combined_content = "\n\n".join([
                f"[{item['type']}] {item['timestamp']}\n{item['content']}"
                for item in content_items
            ])

            print(f"[AgentExecutor] 📝 Summarizing {len(content_items)} items")

            # Generate summary using LLM
            try:
                summary_prompt = f"""150

{combined_content}

"""

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
                summary = f" {len(content_items)} {', '.join(set(item['type'] for item in content_items))}"
                return {"success": True, "summary": summary}

        except Exception as e:
            print(f"[AgentExecutor] ❌ Summarization error: {e}")
            return {"success": False, "error": str(e)}

    def _build_response(self, workflow: Dict, results: List[Dict], start_time: float) -> str:
        """Build formatted response."""
        parts = []

        # Header
        parts.append(f"🤖 **AI Agent {workflow['description']}**\n")

        # Steps and results
        for i, (step, result) in enumerate(zip(workflow["steps"], results), 1):
            parts.append(f"⏳  {i}: {step['description']}")

            if result.get("success"):
                if "count" in result:
                    count = result["count"]
                    parts.append(f"✅  {count} ")

                    # Show top results
                    if result.get("results") and len(result["results"]) > 0:
                        parts.append(f"\n📌 ****:")
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
                        parts.append(f"[OK] \n")
                        parts.append(f"[Eye] ****:\n{analysis}\n")
                    elif result_type == "ocr_fallback":
                        parts.append(f"[OK] OCR\n")
                        parts.append(f"[Doc] ****:\n{analysis}\n")
                    else:
                        parts.append(f"[OK] \n")
                        parts.append(f"[Chart] ****:\n{analysis}\n")

                elif "summary" in result:
                    summary = result["summary"]
                    parts.append(f"[OK] \n")
                    parts.append(f"[Note] ****:\n{summary}\n")
                else:
                    parts.append("[OK] \n")
            else:
                error = result.get("error", "Unknown error")
                parts.append(f"✗ : {error}\n")

        # Execution time
        exec_time = time.time() - start_time
        parts.append(f"\n[Time] : {exec_time:.2f} ")

        return "\n".join(parts)


__all__ = ["AgentExecutor"]
