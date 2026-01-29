### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-01-29             ###
### license: MIT                 ###

import hashlib
import re, ast, json, base64

from .prompts import FACT_RETRIEVAL_PROMPT


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
            # return json.loads(candidate)
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
