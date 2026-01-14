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

from PIL import ImageGrab
from argparse import ArgumentParser
from memory import Memory
# 新增：用于线程池
from concurrent.futures import ThreadPoolExecutor

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

# --- 辅助函数保持不变 ---
def init_db():
    """初始化数据库，创建视频信息表"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS frames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        frame_count DATETIME NOT NULL,
        caption TEXT, 
        box TEXT, 
        prob float           
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
    """
    接收一个数据列表，使用 executemany() 一次性将所有数据插入数据库。
    """
    if not data_list:
        return # 如果列表为空，则不执行任何操作

    conn = None # 初始化连接变量
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # SQL 插入语句，使用 ? 作为占位符
        sql = '''
        INSERT INTO frames (filename, frame_count, caption, box, prob)
        VALUES (?, ?, ?, ?, ?)
        '''
        # 使用 executemany() 执行批量插入
        cursor.executemany(sql, data_list)
        # 一次性提交所有更改
        conn.commit()

    except sqlite3.Error as e:
        print(f"[ERROR] 批量插入数据库时发生错误: {e}")
        if conn:
            conn.rollback() # 如果发生错误，则回滚事务
            print("[INFO] 事务已回滚。")

    finally:
        # 确保在任何情况下数据库连接都被关闭
        if conn:
            conn.close()

def capture_screen():
    """
    截取屏幕并返回OpenCV格式的图像 (BGR)。
    - 在Linux上，优先使用`mss`库（无闪烁，高性能）。
    - 如果`mss`失败，降级使用`gnome-screenshot`命令行工具。
    - 如果`gnome-screenshot`也失败，最后使用Pillow的ImageGrab。
    - 在Windows/macOS上，直接使用Pillow的ImageGrab。
    """
    if os.name == 'posix' and 'linux' in os.uname().sysname.lower():
        try:
            with mss.mss() as sct:
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

def screen_memory(frame_path, m):
    """
    处理单帧图像并将其存入记忆。
    """
    messages = [
        {"role": "user", "content": {"image_url": {"url": os.path.dirname(__file__)+'/'+frame_path}, "type": "image_url"}},
    ]
    m.add(messages=messages, user_id="screenshot")

def ocr_memory(frame, i, start_time):
    """
    处理单帧图像OCR，收集所有结果，并调用函数进行一次性批量插入。
    """
    # 1. 生成唯一的文件名（基于视频开始时间）
    frame_path = start_time.strftime("%Y%m%d_%H%M%S")

    # 2. 对当前帧执行OCR
    results = ocr_reader.readtext(frame)

    # 3. 检查是否有识别结果
    if not results:
        print(f"[INFO] 第 {i} 帧没有识别到任何文字。")
        return

    # 4. 创建一个列表来收集所有待插入的数据
    data_to_insert = []
    for (bbox, text, prob) in results:
        # 将每条记录的参数打包成一个元组，添加到列表中
        # 注意：bbox是一个列表，SQLite可以直接存储
        data_to_insert.append( (frame_path, i, text, str(bbox), prob) )

    # 5. 调用函数，一次性插入所有数据
    save_frame_info_batch(data_to_insert)

def resize_to_480p(frame):
    """
    将图像的垂直分辨率调整为 480 像素，同时保持原始宽高比。

    参数:
    frame (numpy.ndarray): 输入的 OpenCV 图像 (BGR 格式)。

    返回:
    numpy.ndarray: 调整大小后的图像。
    """
    # 获取原始图像的高度和宽度
    height, width = frame.shape[:2]

    # 定义目标垂直分辨率 (480p)
    target_height = 480

    # 计算缩放比例
    # 新高度 / 原始高度 = 缩放比例
    scale = target_height / height

    # 根据缩放比例计算新的宽度，确保它是整数
    target_width = int(width * scale)

    # 使用 cv2.resize 进行缩放
    # interpolation=cv2.INTER_AREA 非常适合用于缩小图像，可以产生较好的效果
    resized_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
    
    return resized_frame


def capture_and_save(duration, interval, output_dir, mem=None):
    """定期截图并保存为视频，同时并行处理记忆存储"""
    start_time = datetime.datetime.now()
    frames = []
    total_frames = int(duration / interval)
    print(f"开始录制视频，持续时间: {duration}秒，间隔: {interval}秒，总帧数: {total_frames}")
    
    temp_dir = os.path.join(db_path, 'tmp')
    os.makedirs(temp_dir, exist_ok=True)
    prev_frame = None

    # 创建一个线程池，用于并行处理 screen_memory
    # max_workers 可以根据你的CPU核心数和任务负载调整
    with ThreadPoolExecutor(max_workers=4) as executor:
        # 用于存储所有提交的任务，以便后续检查
        future_to_frame = {}

        for i in range(total_frames):
            progress = (i + 1) / total_frames * 100
            print(f"录制进度: {progress:.2f}%", end="\r")

            frame = capture_screen()        
            if prev_frame is not None and np.array_equal(frame, prev_frame):
                time.sleep(interval)
                continue
            prev_frame = frame
            frames.append(frame)
            
            frame_filename = os.path.join(temp_dir, f"frame_{i}.png")
            cv2.imwrite(frame_filename, resize_to_480p(frame))

            # 立即将处理任务提交给线程池，而不是等待
            # executor.submit 会在后台线程中调用 screen_memory
            # future = executor.submit(screen_memory, frame_filename, mem)
            # future = executor.submit(ocr_memory, frame_filename, i, start_time)
            # future_to_frame[future] = frame_filename

            ocr_memory(frame_filename, i, start_time)
            screen_memory(frame_filename, mem)

            time.sleep(interval)
        
        # 等待所有后台的 screen_memory 任务全部完成
        # 这很重要，确保在删除临时文件和退出函数前，所有记忆都已处理完毕
        print("\n录制循环结束，等待所有记忆处理任务完成...")
        for future in future_to_frame:
            try:
                future.result()  # 如果任务抛出异常，这里会重新抛出
            except Exception as exc:
                frame_path = future_to_frame[future]
                print(f"处理帧 {frame_path} 时发生错误: {exc}")

    print("所有记忆处理任务已完成。")

    # 所有帧捕获和记忆处理完成后，再生成视频
    end_time = datetime.datetime.now()
    duration_actual = (end_time - start_time).total_seconds()
    fps_actual = len(frames) / duration_actual if duration_actual > 0 else 0
    
    print("正在生成视频文件...")
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = start_time.strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"screen_{timestamp}.mp4")
    
    frame_count = create_video(frames, output_file, fps=10.0)
    
    print(f"视频已保存: {output_file}")
    
    save_video_info(
        filename=output_file,
        start_time=start_time,
        end_time=end_time,
        duration=duration_actual,
        frame_count=frame_count,
        fps=fps_actual
    )
    
    # 最后删除临时文件夹
    shutil.rmtree(temp_dir)

# --- 其他函数保持不变 ---
def scheduled_capture(interval_minutes, video_duration, screenshot_interval, output_dir, mem=None):
    """定时执行屏幕录制任务"""
    while True:
        capture_and_save(video_duration, screenshot_interval, output_dir, mem)
        print(f"等待 {interval_minutes} 分钟后开始下一次录制...")
        time.sleep(interval_minutes * 60)

def main():
    """主函数"""
    parser = ArgumentParser(description="定期屏幕录制工具 (并行处理优化版)")
    parser.add_argument("--interval", type=int, default=10, 
                       help="录制间隔（分钟），默认为10分钟")
    parser.add_argument("--duration", type=int, default=60, 
                       help="每次录制持续时间（秒），默认为60秒")
    parser.add_argument("--screenshot-interval", type=float, default=1.0, 
                       help="截图间隔（秒），默认为1秒")
    parser.add_argument("--output", type=str, default=os.path.join(db_path, "videos"), 
                       help="视频保存目录，默认为db/videos")
    
    args = parser.parse_args()
    
    init_db()
    print("数据库初始化完成")    
    m = Memory.from_config(config)

    try:
        scheduled_capture(args.interval, args.duration, args.screenshot_interval, args.output, m)
    except KeyboardInterrupt:
        print("\n程序已停止")


if __name__ == "__main__":
    main()


