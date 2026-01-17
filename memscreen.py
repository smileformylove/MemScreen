### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                 ###

import os
import time
import datetime
import sqlite3
import threading
import cv2
import numpy as np
import subprocess
import shutil
import mss 
import easyocr
import queue

from PIL import ImageGrab
from argparse import ArgumentParser
from memory import Memory
# 新增：用于线程池
from concurrent.futures import ThreadPoolExecutor
# ===================== 新增键鼠监听依赖 START =====================
from pynput import keyboard, mouse
# ===================== 新增键鼠监听依赖 END =====================
# ===================== 新增：流程挖掘分析模块 START =====================
from process_mining import ProcessMiningAnalyzer
# ===================== 新增：流程挖掘分析模块 END =====================

# --- 数据库和配置部分保持不变 ---
db_path = "./db"
if not os.path.exists(db_path):
    os.mkdir(db_path)
DB_NAME = db_path + "/screen_capture.db"
ocr_reader = easyocr.Reader(['ch_sim', 'en']) 

config = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "qwen3:1.7b",
            "temperature": 0.8,
            "max_tokens": 2000,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "mllm": {
        "provider": "ollama",
        "config": {
            "model": "qwen2.5vl:3b",
            "enable_vision": True,
            "temperature": 0.8,
            "max_tokens": 2000,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "test",
            "path": "db",
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "mxbai-embed-large",
            "ollama_base_url": "http://localhost:11434",
        },
    },
}

# ===================== 新增：键鼠监听全局变量 START =====================
# 键鼠日志批量插入缓存，提升入库性能
KM_LOG_BATCH_LIST = []
# 批量插入阈值，达到阈值自动入库
KM_BATCH_THRESHOLD = 20
# 键鼠监听线程对象
keyboard_listener = None
mouse_listener = None
# ===================== 新增：键鼠监听全局变量 END =====================

# --- 辅助函数保持不变 + 新增数据库初始化/键鼠入库方法 ---
def init_db():
    """初始化数据库，创建视频信息表+帧表+新增【键鼠操作日志表】"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 原有视频表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        start_time DATETIME NOT NULL,
        end_time DATETIME NOT NULL,
        duration REAL NOT NULL,
        frame_count INTEGER NOT NULL,
        fps REAL NOT NULL,
        caption TEXT
    )
    ''')
    # 原有帧数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS frames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        frame_count INTEGER NOT NULL,
        caption TEXT, 
        box TEXT, 
        prob float           
    )
    ''')
    # ===================== 新增：创建键盘鼠标操作日志表 =====================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keyboard_mouse_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operate_time DATETIME NOT NULL,
        operate_type TEXT NOT NULL,  -- keyboard / mouse
        action TEXT NOT NULL,        -- press/release/move/click/scroll
        content TEXT NOT NULL,       -- 按键内容/坐标信息
        details TEXT                 -- 扩展详情
    )
    ''')
    conn.commit()
    conn.close()

def save_video_info(filename, start_time, end_time, duration, frame_count, fps, caption=None):
    """保存视频信息到数据库"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO videos (filename, start_time, end_time, duration, frame_count, fps, caption)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (filename, start_time, end_time, duration, frame_count, fps, caption))
    conn.commit()
    conn.close()

def save_frame_info_batch(data_list):
    """批量插入帧数据"""
    if not data_list:
        return
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        sql = '''
        INSERT INTO frames (filename, frame_count, caption, box, prob)
        VALUES (?, ?, ?, ?, ?)
        '''
        cursor.executemany(sql, data_list)
        conn.commit()
    except sqlite3.Error as e:
        print(f"[ERROR] 批量插入帧数据时发生错误: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# ===================== 新增：键鼠日志批量入库核心方法 =====================
def save_km_log_batch(data_list):
    """批量插入键盘鼠标操作日志，和帧数据入库逻辑保持一致"""
    if not data_list:
        return
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        sql = '''
        INSERT INTO keyboard_mouse_logs (operate_time, operate_type, action, content, details)
        VALUES (?, ?, ?, ?, ?)
        '''
        cursor.executemany(sql, data_list)
        conn.commit()
    except sqlite3.Error as e:
        print(f"[ERROR] 批量插入键鼠日志时发生错误: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# ===================== 新增：键鼠日志添加到缓存/自动入库 =====================
def add_km_log(operate_type, action, content, details=None):
    """添加键鼠日志到缓存，达到阈值自动批量入库，轻量化无阻塞"""
    global KM_LOG_BATCH_LIST, KM_BATCH_THRESHOLD
    curr_time = datetime.datetime.now()
    KM_LOG_BATCH_LIST.append( (curr_time, operate_type, action, content, details) )
    # 达到阈值自动入库，清空缓存
    if len(KM_LOG_BATCH_LIST) >= KM_BATCH_THRESHOLD:
        save_km_log_batch(KM_LOG_BATCH_LIST)
        KM_LOG_BATCH_LIST = []

# ===================== 新增：程序退出时，强制入库剩余键鼠日志 =====================
def flush_km_log_remain():
    """强制将缓存中剩余的键鼠日志入库，防止数据丢失"""
    global KM_LOG_BATCH_LIST
    if KM_LOG_BATCH_LIST:
        save_km_log_batch(KM_LOG_BATCH_LIST)
        KM_LOG_BATCH_LIST = []
        print("[INFO] 剩余键鼠日志已全部入库完成")

# ===================== 新增：完整键盘监听回调函数 =====================
def on_key_press(key):
    """监听键盘按键按下事件"""
    try:
        # 普通字符按键：字母、数字、符号
        add_km_log(
            operate_type="keyboard",
            action="press",
            content=f"char:{key.char}",
            details=f"Normal key: {key.char}"
        )
    except AttributeError:
        # 特殊功能按键：ESC/回车/空格/Shift/Ctrl/Alt/退格等
        key_name = str(key).replace("Key.", "")
        add_km_log(
            operate_type="keyboard",
            action="press",
            content=f"func:{key_name}",
            details=f"Special key: [{key_name}]"
        )

def on_key_release(key):
    """监听键盘按键松开事件"""
    try:
        key_name = key.char if hasattr(key, 'char') else str(key).replace("Key.", "")
        add_km_log(
            operate_type="keyboard",
            action="release",
            content=f"char:{key_name}",
            details=f"Key released: {key_name}"
        )
    except:
        key_name = str(key).replace("Key.", "")
        add_km_log(
            operate_type="keyboard",
            action="release",
            content=f"func:{key_name}",
            details=f"Special key released: [{key_name}]"
        )

# ===================== 新增：完整鼠标监听回调函数 =====================
def on_mouse_move(x, y):
    """监听鼠标移动事件"""
    add_km_log(
        operate_type="mouse",
        action="move",
        content=f"X:{x},Y:{y}",
        details=f"Mouse move to coordinate ({x},{y})"
    )

def on_mouse_click(x, y, button, pressed):
    """监听鼠标点击/松开事件"""
    click_status = "press" if pressed else "release"
    btn_name = str(button).replace("Button.", "")
    add_km_log(
        operate_type="mouse",
        action=click_status,
        content=f"{btn_name}@X:{x},Y:{y}",
        details=f"Mouse {click_status} {btn_name} button at ({x},{y})"
    )

def on_mouse_scroll(x, y, dx, dy):
    """监听鼠标滚轮滑动事件"""
    scroll_dir = "up" if dy > 0 else "down"
    add_km_log(
        operate_type="mouse",
        action="scroll",
        content=f"{scroll_dir}@X:{x},Y:{y}",
        details=f"Mouse wheel {scroll_dir} at ({x},{y}) | dx:{dx}, dy:{dy}"
    )

# ===================== 新增：启动键鼠监听的核心方法 =====================
def start_km_listener():
    """启动键盘+鼠标监听，后台守护线程运行"""
    global keyboard_listener, mouse_listener
    # 启动键盘监听
    keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
    keyboard_listener.daemon = True  # 守护线程，主程序退出自动关闭
    keyboard_listener.start()
    # 启动鼠标监听
    mouse_listener = mouse.Listener(on_move=on_mouse_move, on_click=on_mouse_click, on_scroll=on_mouse_scroll)
    mouse_listener.daemon = True  # 守护线程，主程序退出自动关闭
    mouse_listener.start()
    print("[INFO] 键盘鼠标监听服务已启动，后台运行中...")

# ===================== 优化：复用mss连接提升性能 START =====================
_mss_instance = None
_mss_lock = threading.Lock()

def get_mss_instance():
    """获取或创建mss实例，复用连接提升性能"""
    global _mss_instance
    if _mss_instance is None:
        with _mss_lock:
            if _mss_instance is None:
                _mss_instance = mss.mss()
    return _mss_instance
# ===================== 优化：复用mss连接提升性能 END =====================

def capture_screen():
    """截取屏幕并返回OpenCV格式的图像 (BGR) - 优化版本，复用mss连接"""
    if os.name == 'posix' and 'linux' in os.uname().sysname.lower():
        try:
            # 复用mss实例，避免每次创建连接的开销
            sct = get_mss_instance()
            monitor = sct.monitors[1]
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame
        except Exception as e:
            print(f"警告: 使用 mss 库失败: {e}")
            print("  将降级使用 gnome-screenshot。")

        try:
            result = subprocess.run(
                ['gnome-screenshot', '-f', '-'],
                check=True,
                capture_output=True,
                text=False
            )
            if not result.stdout:
                print("错误: gnome-screenshot 输出为空。")
                raise ValueError("Empty output from gnome-screenshot")
            frame = cv2.imdecode(np.frombuffer(result.stdout, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                print("错误: OpenCV未能从gnome-screenshot输出解码图像。")
                raise ValueError("Failed to decode image from gnome-screenshot output")
            return frame
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
            print(f"警告: 使用 gnome-screenshot 也失败: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"  Gnome-screenshot 错误详情: {e.stderr.decode('utf-8', 'ignore')}")
            print("  将最终降级使用可能导致闪烁的 ImageGrab。")
            
        img = ImageGrab.grab()
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    else:
        img = ImageGrab.grab()
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def create_video(frames, output_file, fps=10.0):
    """将图像序列创建为视频文件"""
    if not frames:
        return 0
    height, width, layers = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    for frame in frames:
        video.write(frame)
    video.release()
    return len(frames)

def screen_memory(frame_path, m, frame_idx=None):
    """处理单帧图像并将其存入记忆 - 优化版本：添加异常处理、重试机制和性能优化"""
    try:
        # 检查文件是否存在
        if not os.path.exists(frame_path):
            print(f"[WARNING] Memory任务 (帧 {frame_idx}): 帧文件不存在: {frame_path}")
            return False
        
        messages = [
            {"role": "user", "content": {"image_url": {"url": os.path.abspath(frame_path)}, "type": "image_url"}},
        ]
        
        # 优化：对于screenshot场景，使用infer=False跳过LLM推理，直接存储图像描述，大幅提升速度
        # 添加重试机制
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # 使用infer=False跳过LLM推理，直接存储，速度更快
                m.add(messages=messages, user_id="screenshot", infer=False)
                if frame_idx is not None and frame_idx % 10 == 0:
                    print(f"[MEMORY] 已处理 {frame_idx} 帧记忆存储")
                return True
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                if attempt < max_retries - 1:
                    print(f"[WARNING] Memory任务 (帧 {frame_idx}): 失败，重试中 ({attempt+1}/{max_retries})")
                    print(f"  - 异常类型: {error_type}")
                    print(f"  - 错误信息: {error_msg}")
                    time.sleep(0.5)
                else:
                    print(f"[ERROR] Memory任务 (帧 {frame_idx}): 最终失败")
                    print(f"  - 异常类型: {error_type}")
                    print(f"  - 错误信息: {error_msg}")
                    return False
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"[ERROR] Memory任务 (帧 {frame_idx}): 异常")
        print(f"  - 异常类型: {error_type}")
        print(f"  - 错误信息: {error_msg}")
        return False

def ocr_memory(frame_path, i, start_time):
    """处理单帧图像OCR，收集所有结果，并调用函数进行一次性批量插入 - 优化版本：添加异常处理和性能优化"""
    try:
        # 检查文件是否存在
        if not os.path.exists(frame_path):
            print(f"[WARNING] OCR: 帧文件不存在: {frame_path}")
            return False
        
        # 读取图像（如果传入的是路径）
        if isinstance(frame_path, str):
            frame = cv2.imread(frame_path)
            if frame is None:
                print(f"[WARNING] OCR: 无法读取图像: {frame_path}")
                return False
        else:
            frame = frame_path
        
        # 优化：如果图像太大，先缩小再OCR（加快处理速度）
        height, width = frame.shape[:2]
        if height > 600 or width > 1000:
            scale = min(600 / height, 1000 / width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # OCR处理，添加超时保护和优化参数
        try:
            # 使用优化参数加快处理：paragraph=False 不合并段落，detail=1 返回详细信息但更快
            results = ocr_reader.readtext(frame, paragraph=False)
        except Exception as e:
            print(f"[ERROR] OCR读取失败 (帧 {i}): {e}")
            return False
        
        if not results:
            # 不打印无文字信息，减少输出
            return True
        
        # 批量插入数据
        frame_path_str = start_time.strftime("%Y%m%d_%H%M%S")
        data_to_insert = []
        for (bbox, text, prob) in results:
            # 过滤低置信度的结果
            if prob > 0.3:  # 只保存置信度>0.3的结果
                data_to_insert.append((frame_path_str, i, text, str(bbox), prob))
        
        if data_to_insert:
            try:
                save_frame_info_batch(data_to_insert)
                if i % 10 == 0:
                    print(f"[OCR] 已处理 {i} 帧，本帧识别到 {len(data_to_insert)} 条文字")
            except Exception as e:
                print(f"[ERROR] OCR数据保存失败 (帧 {i}): {e}")
                return False
        
        return True
    except Exception as e:
        print(f"[ERROR] OCR处理异常 (帧 {i}): {e}")
        return False

def resize_to_480p(frame):
    """将图像的垂直分辨率调整为 480 像素，同时保持原始宽高比。"""
    height, width = frame.shape[:2]
    target_height = 480
    scale = target_height / height
    target_width = int(width * scale)
    resized_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
    return resized_frame

# ===================== 优化：实时录制函数 - 使用队列和后台处理 START =====================
def process_frame_async(frame_queue, mem, start_time, temp_dir, ocr_executor, memory_executor, stats_lock, stats_dict):
    """后台线程：异步处理帧的OCR和记忆存储 - 优化版本：改进任务显示和异常处理"""
    frame_count = 0
    ocr_success = 0
    ocr_failed = 0
    memory_success = 0
    memory_failed = 0
    pending_tasks = []
    last_update_time = time.time()
    
    while True:
        try:
            item = frame_queue.get(timeout=1)
            if item is None:  # 结束信号
                # 等待所有任务完成
                active_tasks = [t for t in pending_tasks if not t.done()]
                if active_tasks:
                    print(f"\n[INFO] 等待 {len(active_tasks)} 个后台任务完成...")
                    for task in active_tasks:
                        try:
                            task.result(timeout=60)  # 增加超时时间
                        except Exception as e:
                            # 显示详细的任务失败信息
                            task_type = getattr(task, 'task_type', 'unknown').upper()
                            task_idx = getattr(task, 'frame_idx', '?')
                            error_type = type(e).__name__
                            error_msg = str(e)
                            print(f"\n[ERROR] 等待中的{task_type}任务失败:")
                            print(f"  - 帧号: {task_idx}")
                            print(f"  - 异常类型: {error_type}")
                            print(f"  - 错误信息: {error_msg}")
                break
            
            frame_idx, frame_data, frame_resized = item
            
            # 异步处理OCR和记忆存储
            frame_filename = os.path.join(temp_dir, f"frame_{frame_idx}.png")
            try:
                cv2.imwrite(frame_filename, frame_resized)
            except Exception as e:
                print(f"[ERROR] 保存帧文件失败 (帧 {frame_idx}): {e}")
                frame_queue.task_done()
                continue
            
            # 提交到线程池异步处理，不阻塞，并保存future以便后续等待
            ocr_task = ocr_executor.submit(ocr_memory, frame_filename, frame_idx, start_time)
            memory_task = memory_executor.submit(screen_memory, frame_filename, mem, frame_idx)
            
            # 使用字典标记任务类型，便于统计
            ocr_task.task_type = 'ocr'
            ocr_task.frame_idx = frame_idx
            memory_task.task_type = 'memory'
            memory_task.frame_idx = frame_idx
            
            pending_tasks.extend([ocr_task, memory_task])
            
            # 清理已完成的任务并统计结果
            new_pending = []
            for task in pending_tasks:
                if task.done():
                    try:
                        result = task.result()  # 获取结果，触发异常如果有的话
                        # 根据任务类型统计
                        if hasattr(task, 'task_type'):
                            if task.task_type == 'ocr':
                                if result:
                                    ocr_success += 1
                                else:
                                    ocr_failed += 1
                            else:  # memory
                                if result:
                                    memory_success += 1
                                else:
                                    memory_failed += 1
                    except Exception as e:
                        # 根据任务类型统计失败，显示详细错误信息
                        if hasattr(task, 'task_type'):
                            task_idx = getattr(task, 'frame_idx', '?')
                            task_type = task.task_type.upper()
                            error_type = type(e).__name__
                            error_msg = str(e)
                            
                            # 显示详细的错误信息
                            print(f"\n[ERROR] {task_type}任务失败详情:")
                            print(f"  - 帧号: {task_idx}")
                            print(f"  - 异常类型: {error_type}")
                            print(f"  - 错误信息: {error_msg}")
                            
                            # 如果是关键错误，显示更多信息
                            if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                                print(f"  - 提示: 可能是网络或服务超时问题")
                            
                            if task.task_type == 'ocr':
                                ocr_failed += 1
                            else:  # memory
                                memory_failed += 1
                else:
                    new_pending.append(task)
            pending_tasks = new_pending
            
            # 定期更新统计信息（每5秒或每10帧）
            current_time = time.time()
            if current_time - last_update_time >= 5 or frame_count % 10 == 0:
                with stats_lock:
                    stats_dict['ocr_success'] = ocr_success
                    stats_dict['ocr_failed'] = ocr_failed
                    stats_dict['memory_success'] = memory_success
                    stats_dict['memory_failed'] = memory_failed
                    stats_dict['total_processed'] = frame_count
                last_update_time = current_time
            
            frame_count += 1
            frame_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[ERROR] 处理帧时发生错误: {e}")
    
    # 最终统计
    with stats_lock:
        stats_dict['ocr_success'] = ocr_success
        stats_dict['ocr_failed'] = ocr_failed
        stats_dict['memory_success'] = memory_success
        stats_dict['memory_failed'] = memory_failed
        stats_dict['total_processed'] = frame_count
    
    print(f"\n[INFO] 后台处理完成:")
    print(f"  - 总处理帧数: {frame_count}")
    print(f"  - OCR成功: {ocr_success}, 失败: {ocr_failed}")
    print(f"  - Memory成功: {memory_success}, 失败: {memory_failed}")

def capture_and_save(duration, interval, output_dir, mem=None):
    """实时录制视频 - 优化版本：实时写入视频，异步处理OCR和记忆"""
    start_time = datetime.datetime.now()
    print(f"开始实时录制，持续时间: {duration}秒，目标FPS: {1.0/interval:.1f}")
    
    # 创建输出目录和视频文件
    os.makedirs(output_dir, exist_ok=True)
    timestamp = start_time.strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"screen_{timestamp}.mp4")
    
    # 获取第一帧以确定视频尺寸
    first_frame = capture_screen()
    if first_frame is None:
        print("[ERROR] 无法捕获屏幕，录制终止")
        return
    
    height, width = first_frame.shape[:2]
    target_fps = 1.0 / interval if interval > 0 else 10.0
    
    # 使用更高效的视频编码（H.264）
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_file, fourcc, target_fps, (width, height))
    
    if not video_writer.isOpened():
        print(f"[ERROR] 无法创建视频文件: {output_file}")
        return
    
    temp_dir = os.path.join(db_path, 'tmp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建队列用于异步处理
    frame_queue = queue.Queue(maxsize=50)  # 限制队列大小，避免内存溢出
    
    # 创建统计信息字典和锁
    stats_lock = threading.Lock()
    stats_dict = {
        'ocr_success': 0,
        'ocr_failed': 0,
        'memory_success': 0,
        'memory_failed': 0,
        'total_processed': 0
    }
    
    # 使用独立的线程池处理OCR和记忆存储（增加工作线程数以加快处理）
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="ocr") as ocr_executor, \
         ThreadPoolExecutor(max_workers=3, thread_name_prefix="memory") as memory_executor:
        
        # 启动后台处理线程
        processing_thread = threading.Thread(
            target=process_frame_async,
            args=(frame_queue, mem, start_time, temp_dir, ocr_executor, memory_executor, stats_lock, stats_dict),
            daemon=True
        )
        processing_thread.start()
        
        frame_count = 0
        prev_frame = None
        end_time = start_time + datetime.timedelta(seconds=duration)
        
        print(f"[INFO] 开始实时录制，视频将保存到: {output_file}")
        
        try:
            while datetime.datetime.now() < end_time:
                frame_start_time = time.time()
                
                # 捕获屏幕
                frame = capture_screen()
                
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # 跳过重复帧（可选优化）
                if prev_frame is not None:
                    if np.array_equal(frame, prev_frame):
                        time.sleep(interval)
                        continue
                
                prev_frame = frame.copy()
                
                # 实时写入视频（不等待）
                video_writer.write(frame)
                frame_count += 1
                
                # 准备异步处理的帧（缩放到480p用于OCR和记忆）
                frame_resized = resize_to_480p(frame)
                
                # 将帧放入队列异步处理（非阻塞）
                try:
                    frame_queue.put_nowait((frame_count - 1, frame, frame_resized))
                except queue.Full:
                    # 队列满时跳过，避免阻塞录制
                    print(f"[WARNING] 处理队列已满，跳过帧 {frame_count - 1} 的OCR处理")
                
                # 计算实际FPS并调整等待时间
                frame_elapsed = time.time() - frame_start_time
                sleep_time = max(0, interval - frame_elapsed)
                
                # 优化显示：每5帧或每5秒更新一次，显示更详细的后台任务信息
                if frame_count % 5 == 0 or frame_count == 1:
                    actual_fps = 1.0 / (frame_elapsed + sleep_time) if (frame_elapsed + sleep_time) > 0 else 0
                    progress = (datetime.datetime.now() - start_time).total_seconds() / duration * 100
                    
                    # 获取后台任务统计
                    with stats_lock:
                        ocr_s = stats_dict.get('ocr_success', 0)
                        ocr_f = stats_dict.get('ocr_failed', 0)
                        mem_s = stats_dict.get('memory_success', 0)
                        mem_f = stats_dict.get('memory_failed', 0)
                        processed = stats_dict.get('total_processed', 0)
                    
                    # 显示优化后的信息
                    queue_size = frame_queue.qsize()
                    status = f"录制: {progress:.1f}% | 帧: {frame_count} | FPS: {actual_fps:.2f} | "
                    status += f"后台: OCR({ocr_s}/{ocr_f}) MEM({mem_s}/{mem_f}) | 队列: {queue_size}"
                    print(status, end="\r")
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            print("\n[INFO] 录制被用户中断")
        finally:
            # 发送结束信号
            frame_queue.put(None)
            
            # 等待后台处理完成
            print("\n[INFO] 等待后台处理任务完成...")
            frame_queue.join()
            processing_thread.join(timeout=5)
            
            # 关闭视频写入器
            video_writer.release()
            
            end_time_actual = datetime.datetime.now()
            duration_actual = (end_time_actual - start_time).total_seconds()
            fps_actual = frame_count / duration_actual if duration_actual > 0 else 0
            
            print(f"[INFO] 录制完成！")
            print(f"  - 总帧数: {frame_count}")
            print(f"  - 实际FPS: {fps_actual:.2f}")
            print(f"  - 视频文件: {output_file}")
            
            # 保存视频信息到数据库
            save_video_info(
                filename=output_file,
                start_time=start_time,
                end_time=end_time_actual,
                duration=duration_actual,
                frame_count=frame_count,
                fps=fps_actual
            )
            
            # 清理临时文件（可选，保留用于调试）
            # shutil.rmtree(temp_dir)
# ===================== 优化：实时录制函数 - 使用队列和后台处理 END =====================

def scheduled_capture(interval_minutes, video_duration, screenshot_interval, output_dir, mem=None):
    """定时执行屏幕录制任务"""
    while True:
        capture_and_save(video_duration, screenshot_interval, output_dir, mem)
        print(f"等待 {interval_minutes} 分钟后开始下一次录制...")
        time.sleep(interval_minutes * 60)

def analyze_process_mining(start_time=None, end_time=None, output_json=None):
    """执行流程挖掘分析"""
    print("[INFO] 开始执行流程挖掘分析...")
    analyzer = ProcessMiningAnalyzer(db_path=DB_NAME)
    
    # 解析时间参数
    start_dt = None
    end_dt = None
    if start_time:
        try:
            start_dt = datetime.datetime.fromisoformat(start_time)
        except:
            start_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    if end_time:
        try:
            end_dt = datetime.datetime.fromisoformat(end_time)
        except:
            end_dt = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    
    # 生成报告
    report = analyzer.generate_full_report(start_time=start_dt, end_time=end_dt)
    
    # 打印摘要
    analyzer.print_summary(report)
    
    # 导出JSON（如果指定）
    if output_json:
        analyzer.export_report_json(report, output_json)
    
    return report

def main():
    """主函数 - 新增启动键鼠监听+流程挖掘分析"""
    parser = ArgumentParser(description="定期屏幕录制工具 (并行处理优化版+键鼠监听+流程挖掘)")
    parser.add_argument("--interval", type=int, default=10, 
                       help="录制间隔（分钟），默认为10分钟")
    parser.add_argument("--duration", type=int, default=60, 
                       help="每次录制持续时间（秒），默认为60秒")
    parser.add_argument("--screenshot-interval", type=float, default=2.0, 
                       help="截图间隔（秒），默认为2秒（0.5 FPS）")
    parser.add_argument("--output", type=str, default=os.path.join(db_path, "videos"), 
                       help="视频保存目录，默认为db/videos")
    # ===================== 新增：流程挖掘分析参数 START =====================
    parser.add_argument("--analyze", action="store_true",
                       help="执行流程挖掘分析（不启动录制）")
    parser.add_argument("--start-time", type=str, default=None,
                       help="分析开始时间 (格式: YYYY-MM-DDTHH:MM:SS 或 YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--end-time", type=str, default=None,
                       help="分析结束时间 (格式: YYYY-MM-DDTHH:MM:SS 或 YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--export-json", type=str, default=None,
                       help="导出分析报告为JSON文件（指定文件路径）")
    # ===================== 新增：流程挖掘分析参数 END =====================
    
    args = parser.parse_args()
    
    # ===================== 新增：流程挖掘分析模式 START =====================
    if args.analyze:
        init_db()
        analyze_process_mining(
            start_time=args.start_time,
            end_time=args.end_time,
            output_json=args.export_json
        )
        return
    # ===================== 新增：流程挖掘分析模式 END =====================
    
    init_db()
    print("数据库初始化完成")    
    m = Memory.from_config(config)

    # ===================== 新增：启动键盘鼠标监听 =====================
    start_km_listener()

    try:
        scheduled_capture(args.interval, args.duration, args.screenshot_interval, args.output, m)
    except KeyboardInterrupt:
        # ===================== 新增：程序中断时，强制入库剩余键鼠日志 =====================
        flush_km_log_remain()
        print("\n程序已停止，所有数据已安全入库！")


if __name__ == "__main__":
    main()