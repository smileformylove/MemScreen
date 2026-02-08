### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                 ###

import hashlib
import re, ast, json, base64
import subprocess
import time
import psutil
import logging
import platform
import shutil

from .prompts import FACT_RETRIEVAL_PROMPT

logger = logging.getLogger(__name__)


def get_fact_retrieval_messages(message):
    return FACT_RETRIEVAL_PROMPT, f"Input:\n{message}"


def parse_messages(messages):
    response = ""
    for msg in messages:
        if msg["role"] == "system":
            response += f"system: {msg['content']}\n"
        if msg["role"] == "user":
            response += f"user: {msg['content']}\n"
        if msg["role"] == "assistant":
            response += f"assistant: {msg['content']}\n"
    return response


def format_entities(entities):
    if not entities:
        return ""

    formatted_lines = []
    for entity in entities:
        simplified = f"{entity['source']} -- {entity['relationship']} -- {entity['destination']}"
        formatted_lines.append(simplified)

    return "\n".join(formatted_lines)


def remove_code_blocks(content: str) -> str:
    """
    Removes enclosing code block markers ```[language] and ``` from a given string.

    Remarks:
    - The function uses a regex pattern to match code blocks that may start with ``` followed by an optional language tag (letters or numbers) and end with ```.
    - If a code block is detected, it returns only the inner content, stripping out the markers.
    - If no code block markers are found, the original content is returned as-is.
    """
    pattern = r"^```[a-zA-Z0-9]*\n([\s\S]*?)\n```$"
    match = re.match(pattern, content.strip())
    return match.group(1).strip() if match else content.strip()


def extract_python_dict(input_str):
    """
    Extracts a Python dictionary from a string.
    Removes enclosing triple backticks and optional language tags if present.
    If no valid dictionary is found, returns None.
    """
    # 移除 markdown 代码块标记（```python、```json、```等）
    cleaned_str = re.sub(r'```[\w]*', '', input_str).strip()

    # Step 1: 如果整个字符串就是合法 JSON
    try:
        parsed = json.loads(cleaned_str)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Step 2: 如果整个字符串是合法 Python dict
    try:
        parsed = ast.literal_eval(cleaned_str)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Step 3: 提取所有 {...} 片段
    candidates = re.findall(r'\{.*?\}', cleaned_str, flags=re.DOTALL)
    
    for candidate in candidates:
        candidate = candidate.strip()
        # 尝试 JSON 解析
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        # 尝试 Python 字面量解析
        try:
            parsed = ast.literal_eval(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    return None


def fix_and_parse_json(json_str: str):
    """
    修复格式错误的JSON字符串，特别优化了包含单引号的多种场景
    """
    original_str = json_str
    
    # Step 1: 移除Markdown代码块包裹
    json_str = re.sub(r"```(?:json)?\s*|\s*```", "", json_str).strip()
    if not json_str:
        raise ValueError("处理后JSON字符串为空")

    # Step 2: 修复单引号问题（核心逻辑）
    # 处理键名的单引号：'key' → "key"
    json_str = re.sub(
        r"'([^']+)'(?=\s*:)",  # 匹配作为键名的单引号
        lambda m: '"' + m.group(1).replace('"', '\\"') + '"',
        json_str
    )
    
    # 处理值的单引号：精确匹配最外层单引号，忽略内部单引号
    # 使用否定前瞻确保只匹配最外层的单引号
    json_str = re.sub(
        r":\s*'((?:[^']|'(?!\s*[,}\]]))*)'",  # 忽略内部单引号
        lambda m: ': "' + m.group(1).replace('"', '\\"') + '"',
        json_str
    )

    s = json_str.strip()

    # Step 3: 修复结构错误
    # 处理数组和对象闭合不匹配的情况
    if re.match(r'^\{.*\}\s*\]\s*\}?$', s, re.DOTALL):
        obj_part = re.sub(r'\}\s*\]\s*\}?$', '}', s)
        s = f'[{obj_part}]'
    elif s.startswith("{") and s.endswith("}"):
        s = f'[{s}]'
    elif s.startswith("[") and s.endswith("}]"):
        s = s[:-1]

    # Step 4: 补全括号
    brace_diff = s.count("{") - s.count("}")
    if brace_diff > 0:
        s += "}" * brace_diff
    elif brace_diff < 0:
        s = "{" * (-brace_diff) + s

    bracket_diff = s.count("[") - s.count("]")
    if bracket_diff > 0:
        s += "]" * bracket_diff
    elif bracket_diff < 0:
        s = "[" * (-bracket_diff) + s

    # Step 5: 提取并解析JSON
    match = re.search(r"(\{.*\}|\[.*\])", s, re.DOTALL)
    if not match:
        raise ValueError(f"未找到有效的JSON片段: {original_str}")
    candidate = match.group(0)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"解析失败: {e}\n"
            f"原始内容: {original_str[:200]}\n"
            f"修复后内容: {candidate[:200]}"
        ) from e


def extract_json_from_response(response_str):
    # Split by the delimiter that indicates the start of the assistant's response
    parts = response_str.split('</think>\n\n')
    if len(parts) < 2:
        # If we don't find the delimiter, try to find the last JSON structure in the string
        # We'll search for the last occurrence of '{' and then try to parse from there to the end
        start_index = response_str.rfind('{')
        if start_index == -1:
            return None
        candidate = response_str[start_index:]

        try:
            candidate = fix_and_parse_json(candidate)
        except:
            return None
    else:
        candidate = parts[-1].strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Try to fix common issues
            # For example, remove any non-JSON content after the JSON
            # We'll try to find the last valid JSON by trying to parse from the beginning until we get a valid JSON
            # We'll try to parse progressively shorter substrings until it works
            for end_index in range(len(candidate), 0, -1):
                try:
                    return json.loads(candidate[:end_index])
                except:
                    continue
            return None


def extract_json(text):
    """
    Extracts JSON content from a string, removing enclosing triple backticks and optional 'json' tag if present.
    If no code block is found, returns the text as-is.
    """
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        json_str = text  # assume it's raw JSON
    return json_str

def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        base64_bytes = base64.b64encode(img_file.read())
        base64_str = base64_bytes.decode("utf-8")
        return base64_str

def get_image_description(image_obj, llm, vision_details):
    """
    Get the description of the image
    """

    if isinstance(image_obj, str):
        images = [image_to_base64(image_obj)]
        messages = [
            {
                "role": "user",
                "content": "A user is providing an image. Provide a high level description of the image and do not include any additional text.",
                # [
                #     {
                #         "type": "text",
                #         "text": "A user is providing an image. Provide a high level description of the image and do not include any additional text.",
                #     },
                #     # {"type": "image_url", "image_url": {"url": image_obj, "detail": vision_details}},
                # ],
                "images": images,
            },
        ]
    else:
        messages = [image_obj]

    response = llm.generate_response(messages=messages)
    return response


def parse_vision_messages(messages, llm=None, vision_details="auto"):
    """
    Parse the vision messages from the messages
    """
    returned_messages = []
    for msg in messages:
        if msg["role"] == "system":
            returned_messages.append(msg)
            continue

        # Handle message content
        if isinstance(msg["content"], list):
            # Multiple image URLs in content
            description = get_image_description(msg, llm, vision_details)
            returned_messages.append({"role": msg["role"], "content": description})
        elif isinstance(msg["content"], dict) and msg["content"].get("type") == "image_url":
            # Single image content
            image_url = msg["content"]["image_url"]["url"]
            try:
                description = get_image_description(image_url, llm, vision_details)
                if "text" in msg["content"]:
                    description = f" {msg['content']['text']}" + description
                returned_messages.append({"role": msg["role"], "content": description})
            except Exception:
                raise Exception(f"Error while downloading {image_url}.")
        else:
            # Regular text content
            returned_messages.append(msg)

    return returned_messages


def process_telemetry_filters(filters):
    """
    Process the telemetry filters
    """
    if filters is None:
        return {}

    encoded_ids = {}
    if "user_id" in filters:
        encoded_ids["user_id"] = hashlib.md5(filters["user_id"].encode()).hexdigest()
    if "agent_id" in filters:
        encoded_ids["agent_id"] = hashlib.md5(filters["agent_id"].encode()).hexdigest()
    if "run_id" in filters:
        encoded_ids["run_id"] = hashlib.md5(filters["run_id"].encode()).hexdigest()

    return list(filters.keys()), encoded_ids


def ensure_ollama_running():
    """
    Check if Ollama service is running, and start it if not.
    Cross-platform implementation supporting macOS, Linux, and Windows.

    Returns:
        bool: True if Ollama is running or was successfully started, False otherwise.
    """
    # Check if ollama command exists (cross-platform)
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        logger.warning("Ollama not found. Please install Ollama from https://ollama.com/download")
        return False

    logger.debug(f"Found Ollama at: {ollama_path}")

    # First, try to verify Ollama is responsive by checking if it can list models
    # This is more reliable than just checking for the process
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            check=True,
            timeout=3
        )
        # If we got here, Ollama is running and responsive
        logger.debug("Ollama service is already running and responsive")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        # Ollama might not be running, check for process
        pass

    # Check if ollama process is already running (fallback)
    try:
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                # Check process name
                if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                    logger.debug("Ollama service is already running (detected by name)")
                    return True

                # Check command line arguments
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'ollama' in cmdline.lower() and 'serve' in cmdline.lower():
                        logger.debug("Ollama service is already running (detected by cmdline)")
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.debug(f"Error checking for Ollama process: {e}")

    # Ollama is not running, start it
    logger.info("Starting Ollama service...")
    try:
        # Platform-specific process startup
        system = platform.system()

        if system == "Windows":
            # Windows: use CREATE_NEW_PROCESS_GROUP
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags
            )
        else:
            # Unix-like (macOS, Linux): use start_new_session
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

        # Wait for Ollama to start
        max_wait = 10  # seconds
        for i in range(max_wait):
            time.sleep(1)
            try:
                # Check if Ollama is responding
                subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    check=True,
                    timeout=2
                )
                logger.info("Ollama service started successfully")
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                if i < max_wait - 1:
                    continue
                else:
                    logger.warning("Ollama service started but not responding yet")
                    return True  # Return True anyway, it might start working

        logger.warning("Ollama service started but could not verify it's responding")
        return True  # Return True anyway, process was started

    except FileNotFoundError:
        logger.warning("Ollama command not found. Please install Ollama from https://ollama.com/download")
        return False
    except Exception as e:
        logger.error(f"Failed to start Ollama service: {e}")
        return False


# ==========================================
# Screen Detection and Selection Utilities
# ==========================================

import sys
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ScreenInfo:
    """Information about a screen/monitor."""
    index: int  # Screen index (0-based)
    name: str  # Human-readable name
    width: int  # Screen width in pixels
    height: int  # Screen height in pixels
    x: int  # Screen X position (for multi-monitor setups)
    y: int  # Screen Y position (for multi-monitor setups)
    is_primary: bool  # Whether this is the primary/main screen

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Get bounding box as (left, top, right, bottom) tuple."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def __str__(self) -> str:
        """String representation of screen info."""
        primary_marker = " (Primary)" if self.is_primary else ""
        return f"{self.name}{primary_marker} - {self.width}x{self.height} at ({self.x}, {self.y})"


def get_screens() -> List[ScreenInfo]:
    """
    Get list of all available screens/monitors.

    Returns:
        List of ScreenInfo objects, one for each screen
    """
    if sys.platform == 'darwin':
        return _get_screens_macos()
    elif sys.platform == 'win32':
        return _get_screens_windows()
    elif sys.platform.startswith('linux'):
        return _get_screens_linux()
    else:
        logger.warning(f"[ScreenUtils] Unsupported platform: {sys.platform}")
        return _get_screens_fallback()


def _get_screens_macos() -> List[ScreenInfo]:
    """Get screens on macOS using Cocoa/NSScreen."""
    try:
        from Cocoa import NSScreen

        screens = []
        all_screens = NSScreen.screens()

        if not all_screens:
            logger.warning("[ScreenUtils] No screens detected via NSScreen")
            return _get_screens_fallback()

        main_screen = NSScreen.mainScreen()

        for idx, screen in enumerate(all_screens):
            frame = screen.frame()
            # Note: Cocoa uses bottom-left origin, PIL uses top-left origin
            # Get Cocoa coordinates (bottom-left origin)
            cocoa_x = int(frame.origin.x)
            cocoa_y = int(frame.origin.y)  # Bottom edge in Cocoa coordinates
            width = int(frame.size.width)
            height = int(frame.size.height)

            # Convert Cocoa coordinates to PIL coordinates
            # In PIL/ImageGrab: (0, 0) is top-left of main screen, y increases downward
            # Cocoa: y=0 at bottom, increases upward
            # PIL: y=0 at top, increases downward

            # For the main screen (or screens above it):
            # PIL_y = main_height - cocoa_y - height
            # This puts the screen's bottom (cocoa_y) at the correct PIL position

            # Get the main screen dimensions
            main_frame = main_screen.frame()
            main_height = int(main_frame.size.height)

            # Calculate PIL coordinates
            x = cocoa_x  # X is the same in both systems

            # Y conversion: PIL_top = main_height - cocoa_bottom
            # where cocoa_bottom is the screen's bottom edge in Cocoa coordinates
            # But cocoa_y is the bottom edge, so:
            y = main_height - cocoa_y - height

            # Debug output
            logger.debug(f"[ScreenUtils] Screen {idx + 1}: Cocoa=({cocoa_x}, {cocoa_y}), "
                        f"PIL=({x}, {y}), size=({width}×{height})")

            is_primary = (screen == main_screen)
            name = f"Screen {idx + 1}"

            screens.append(ScreenInfo(
                index=idx,
                name=name,
                width=width,
                height=height,
                x=x,
                y=y,
                is_primary=is_primary
            ))

        logger.info(f"[ScreenUtils] Detected {len(screens)} screen(s) on macOS")
        for screen in screens:
            logger.info(f"  - {screen}")

        return screens

    except ImportError as e:
        logger.warning(f"[ScreenUtils] Failed to import Cocoa: {e}")
        return _get_screens_fallback()
    except Exception as e:
        logger.error(f"[ScreenUtils] Error getting screens on macOS: {e}")
        return _get_screens_fallback()


def _get_screens_windows() -> List[ScreenInfo]:
    """Get screens on Windows using win32api."""
    try:
        import win32api

        screens = []
        idx = 0

        try:
            # Try to enumerate monitors using win32api
            monitor_handles = win32api.EnumDisplayMonitors()

            # Get primary screen info first
            primary_width = win32api.GetSystemMetrics(0)
            primary_height = win32api.GetSystemMetrics(1)

            # Note: This is a simplified implementation
            # A more complete implementation would use EnumDisplayMonitors
            # with a callback to get each monitor's rect
            screens.append(ScreenInfo(
                index=0,
                name="Screen 1",
                width=primary_width,
                height=primary_height,
                x=0,
                y=0,
                is_primary=True
            ))

            logger.info(f"[ScreenUtils] Detected {len(screens)} screen(s) on Windows")
            for screen in screens:
                logger.info(f"  - {screen}")

            return screens

        except Exception as e:
            logger.error(f"[ScreenUtils] Error enumerating monitors: {e}")
            return _get_screens_fallback()

    except ImportError:
        logger.warning("[ScreenUtils] win32api not available, using fallback")
        return _get_screens_fallback()


def _get_screens_linux() -> List[ScreenInfo]:
    """Get screens on Linux using Xlib or XRandR."""
    try:
        # Try using Xlib
        from Xlib.display import Display

        display = Display()
        screen = display.screen()
        width = screen.width_in_pixels
        height = screen.height_in_pixels

        screens = [ScreenInfo(
            index=0,
            name="Screen 1",
            width=width,
            height=height,
            x=0,
            y=0,
            is_primary=True
        )]

        logger.info(f"[ScreenUtils] Detected {len(screens)} screen(s) on Linux")
        for screen in screens:
            logger.info(f"  - {screen}")

        return screens

    except ImportError:
        logger.warning("[ScreenUtils] Xlib not available, trying XRandR")
        try:
            # Try using XRandR via subprocess
            import subprocess
            import re

            result = subprocess.run(
                ['xrandr'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                screens = []
                idx = 0
                connected_pattern = re.compile(r'^(\S+) connected')

                for line in result.stdout.split('\n'):
                    match = connected_pattern.match(line)
                    if match:
                        name = match.group(1)
                        # Parse resolution from line like "HDMI-1 connected 1920x1080+0+0"
                        res_match = re.search(r'(\d+)x(\d+)\+(\d+)\+(\d+)', line)
                        if res_match:
                            width = int(res_match.group(1))
                            height = int(res_match.group(2))
                            x = int(res_match.group(3))
                            y = int(res_match.group(4))

                            is_primary = 'primary' in line
                            display_name = f"{name}"

                            screens.append(ScreenInfo(
                                index=idx,
                                name=display_name,
                                width=width,
                                height=height,
                                x=x,
                                y=y,
                                is_primary=is_primary
                            ))
                            idx += 1

                if screens:
                    logger.info(f"[ScreenUtils] Detected {len(screens)} screen(s) via XRandR")
                    for screen in screens:
                        logger.info(f"  - {screen}")
                    return screens

        except Exception as e:
            logger.error(f"[ScreenUtils] Error using XRandR: {e}")

        return _get_screens_fallback()


def _get_screens_fallback() -> List[ScreenInfo]:
    """Fallback method to get screen info using PIL."""
    try:
        from PIL import ImageGrab

        # Get screen size by capturing a test image
        test_img = ImageGrab.grab()
        width, height = test_img.size

        screens = [ScreenInfo(
            index=0,
            name="Screen 1",
            width=width,
            height=height,
            x=0,
            y=0,
            is_primary=True
        )]

        logger.info(f"[ScreenUtils] Fallback: Detected {len(screens)} screen(s)")
        for screen in screens:
            logger.info(f"  - {screen}")

        return screens

    except Exception as e:
        logger.error(f"[ScreenUtils] Fallback also failed: {e}")
        # Last resort: return a default screen
        return [ScreenInfo(
            index=0,
            name="Default Screen",
            width=1920,
            height=1080,
            x=0,
            y=0,
            is_primary=True
        )]


def get_screen_by_index(screen_index: int) -> Optional[ScreenInfo]:
    """
    Get screen information by index.

    Args:
        screen_index: The screen index (0-based)

    Returns:
        ScreenInfo object or None if index is invalid
    """
    screens = get_screens()
    if 0 <= screen_index < len(screens):
        return screens[screen_index]
    return None


def get_primary_screen() -> Optional[ScreenInfo]:
    """
    Get the primary/main screen.

    Returns:
        ScreenInfo object for the primary screen or None
    """
    screens = get_screens()
    for screen in screens:
        if screen.is_primary:
            return screen
    # Fallback to first screen
    return screens[0] if screens else None


def get_screen_names() -> List[str]:
    """
    Get list of screen names for UI display.

    Returns:
        List of screen name strings
    """
    screens = get_screens()
    return [screen.name for screen in screens]


def get_all_screen_bboxes() -> List[Tuple[int, int, int, int]]:
    """
    Get bounding boxes for all screens.

    Returns:
        List of (left, top, right, bottom) tuples
    """
    screens = get_screens()
    return [screen.bbox for screen in screens]


def get_combined_screen_bbox() -> Tuple[int, int, int, int]:
    """
    Get bounding box that encompasses all screens.

    Returns:
        (left, top, right, bottom) tuple covering all screens
    """
    screens = get_screens()

    if not screens:
        return (0, 0, 1920, 1080)

    min_x = min(s.x for s in screens)
    min_y = min(s.y for s in screens)
    max_x = max(s.x + s.width for s in screens)
    max_y = max(s.y + s.height for s in screens)

    return (min_x, min_y, max_x, max_y)
