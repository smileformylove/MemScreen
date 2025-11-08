### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                 ###

import os
import sqlite3
import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from PIL import Image, ImageTk

# 数据库文件名，与录屏脚本保持一致
DB_NAME = "./db/screen_capture.db"

class VideoPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("屏幕录制查看器")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        self.root.resizable(True, True)

        # --- 变量定义 ---
        self.current_video_path = None
        self.current_video_id = None  # 新增：用于存储当前视频的数据库ID
        self.cap = None  # OpenCV VideoCapture 对象
        self.total_frames = 0
        self.fps = 0
        self.total_duration = 0  # 总时长（秒）
        self.is_playing = False
        self.current_frame_pos = 0
        self.video_paths = []  # 存储视频文件路径
        self.video_ids = []    # 新增：存储视频ID

        # --- 创建UI组件 ---
        self.create_widgets()
        
        # --- 加载视频列表 ---
        self.load_video_list()

    def create_widgets(self):
        # --- 顶部：主框架 ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 左侧：视频列表和控制区 ---
        left_frame = ttk.Frame(main_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False) # 防止列表框收缩

        # 列表框
        list_label = ttk.Label(left_frame, text="录制历史:")
        list_label.pack(anchor=tk.W, pady=(0, 5))

        list_control_frame = ttk.Frame(left_frame)
        list_control_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.refresh_btn = ttk.Button(list_control_frame, text="刷新", command=self.refresh_video_list)
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_btn = ttk.Button(list_control_frame, text="删除选中", command=self.delete_selected_video)
        self.delete_btn.pack(side=tk.LEFT)

        self.video_listbox = tk.Listbox(left_frame, selectmode=tk.SINGLE, font=("Helvetica", 10))
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.video_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.video_listbox.config(yscrollcommand=scrollbar.set)
        self.video_listbox.bind('<<ListboxSelect>>', self.on_video_select)

        # --- 右侧：视频播放区和详情区 ---
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 视频播放画布
        video_frame = ttk.LabelFrame(right_frame, text="视频播放", padding="10")
        video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.video_canvas = tk.Canvas(video_frame, bg="black")
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        # 视频详情
        details_frame = ttk.LabelFrame(right_frame, text="视频详情", padding="10")
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.details_text = tk.Text(details_frame, height=4, state=tk.DISABLED, font=("Helvetica", 10))
        self.details_text.pack(fill=tk.X, expand=True)

        # --- 底部：播放控制区 ---
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        # 时间线滑块和时间码
        timeline_frame = ttk.Frame(control_frame)
        timeline_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.timeline_scale = ttk.Scale(timeline_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_scale_change)
        self.timeline_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.timeline_scale.bind("<ButtonRelease-1>", self.on_scale_release)
        
        self.timecode_label = ttk.Label(timeline_frame, text="00:00:00 / 00:00:00", width=20)
        self.timecode_label.pack(side=tk.LEFT, padx=(10, 0))

        # 播放/暂停和停止按钮
        self.play_pause_btn = ttk.Button(control_frame, text="播放", command=self.toggle_play_pause)
        self.play_pause_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="停止", command=self.stop_playback)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

    def load_video_list(self):
        """从数据库加载视频列表到Listbox"""
        self.video_listbox.delete(0, tk.END)
        self.video_paths.clear()
        self.video_ids.clear()
        
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            # 查询更多信息用于详情显示
            cursor.execute("SELECT id, filename, start_time, duration, fps, frame_count FROM videos ORDER BY start_time DESC")
            videos = cursor.fetchall()
            conn.close()

            for video in videos:
                video_id, filename, start_time, duration, fps, frame_count = video
                start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f")
                formatted_time = start_dt.strftime("%Y-%m-%d %H:%M:%S")
                formatted_duration = self.format_duration(duration)
                display_text = f"{formatted_time} ({formatted_duration})"
                
                self.video_listbox.insert(tk.END, display_text)
                self.video_paths.append(filename)
                self.video_ids.append(video_id)

        except sqlite3.Error as e:
            messagebox.showerror("数据库错误", f"加载视频列表失败: {e}")

    def refresh_video_list(self):
        """刷新视频列表"""
        self.stop_playback()
        self.clear_details()
        self.load_video_list()
        messagebox.showinfo("刷新成功", "视频列表已更新。")

    def delete_selected_video(self):
        """删除选中的视频文件和数据库记录"""
        selection = self.video_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先从列表中选择一个视频。")
            return
        
        index = selection[0]
        video_id = self.video_ids[index]
        video_path = self.video_paths[index]
        
        confirm = messagebox.askyesno("确认删除", f"确定要删除以下视频吗？\n\n{os.path.basename(video_path)}\n\n此操作不可恢复！")
        if not confirm:
            return
        
        try:
            # 1. 删除文件
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"文件已删除: {video_path}")
            else:
                print(f"文件不存在，跳过删除: {video_path}")

            # 2. 从数据库删除记录
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
            conn.commit()
            conn.close()
            print(f"数据库记录已删除: ID={video_id}")
            
            # 3. 刷新列表
            self.refresh_video_list()
            messagebox.showinfo("删除成功", "视频文件和记录已成功删除。")

        except Exception as e:
            messagebox.showerror("删除失败", f"删除过程中发生错误: {e}")

    def format_duration(self, seconds):
        """将秒数格式化为 HH:MM:SS"""
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def on_video_select(self, event):
        """当用户在列表中选择一个视频时触发"""
        selection = self.video_listbox.curselection()
        if not selection:
            return
        
        # 停止当前播放的视频
        self.stop_playback()

        index = selection[0]
        self.current_video_path = self.video_paths[index]
        self.current_video_id = self.video_ids[index]
        
        print(f"尝试打开视频: {self.current_video_path}")
        
        # 打开并初始化视频
        if self.open_video(self.current_video_path):
            # 如果视频成功打开，加载其详情
            self.load_video_details(index)

    def open_video(self, video_path):
        """打开视频文件并初始化播放器"""
        if not os.path.exists(video_path):
            messagebox.showerror("文件错误", f"视频文件不存在或路径错误:\n{video_path}")
            print(f"错误：文件不存在 - {video_path}")
            self.clear_details()
            return False

        if self.cap and self.cap.isOpened():
            self.cap.release()
        
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            messagebox.showerror("播放错误", f"无法打开视频文件。可能是解码器问题或文件已损坏:\n{video_path}")
            print(f"错误：无法打开视频 - {video_path}")
            self.clear_details()
            return False

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = 10.0
        
        self.total_duration = self.total_frames / self.fps
        
        self.timeline_scale.config(to=self.total_duration)
        self.current_frame_pos = 0
        
        self.show_frame_at(0)
        self.update_timecode_label(0) # 初始化时间码标签
        return True

    def load_video_details(self, index):
        """加载并显示选中视频的详细信息"""
        video_path = self.video_paths[index]
        try:
            # 从数据库获取信息
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT start_time, end_time, duration, fps, frame_count FROM videos WHERE id = ?", (self.current_video_id,))
            video_info = cursor.fetchone()
            conn.close()

            if video_info:
                start_time, end_time, duration, fps, frame_count = video_info
                
                # 获取视频分辨率
                width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # 获取文件大小
                file_size = os.path.getsize(video_path)
                file_size_str = self.format_file_size(file_size)

                details = f"文件名: {os.path.basename(video_path)}\n"
                details += f"路径: {os.path.dirname(video_path)}\n"
                details += f"分辨率: {width} x {height}\n"
                details += f"文件大小: {file_size_str}\n"
                details += f"开始时间: {start_time}\n"
                details += f"结束时间: {end_time}\n"
                details += f"时长: {self.format_duration(duration)}\n"
                details += f"帧率: {fps:.2f} FPS\n"
                details += f"总帧数: {frame_count}\n"

                self.details_text.config(state=tk.NORMAL)
                self.details_text.delete(1.0, tk.END)
                self.details_text.insert(tk.END, details)
                self.details_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"加载视频详情时出错: {e}")

    def clear_details(self):
        """清空详情面板"""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.config(state=tk.DISABLED)
        self.timecode_label.config(text="00:00:00 / 00:00:00")

    def format_file_size(self, size_bytes):
        """将字节大小格式化为人类可读的字符串 (B, KB, MB, GB)"""
        units = ['B', 'KB', 'MB', 'GB']
        size = size_bytes
        unit_index = 0
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        return f"{size:.2f} {units[unit_index]}"

    def show_frame_at(self, seconds):
        """在指定时间点显示一帧"""
        if not self.cap or not self.cap.isOpened():
            return
        
        frame_pos = int(seconds * self.fps)
        if frame_pos < 0 or frame_pos >= self.total_frames:
            return
            
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        ret, frame = self.cap.read()
        if ret:
            self.display_frame(frame)
            self.current_frame_pos = frame_pos

    def display_frame(self, frame):
        """将OpenCV的帧显示在Tkinter的Canvas上"""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        canvas_width = self.video_canvas.winfo_width()
        canvas_height = self.video_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(100, lambda: self.display_frame(frame))
            return

        img_height, img_width, _ = rgb_image.shape
        ratio = min(canvas_width / img_width, canvas_height / img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        resized_image = cv2.resize(rgb_image, (new_width, new_height))
        
        pil_image = Image.fromarray(resized_image)
        self.tk_image = ImageTk.PhotoImage(image=pil_image)
        
        self.video_canvas.delete("all")
        x_offset = (canvas_width - new_width) // 2
        y_offset = (canvas_height - new_height) // 2
        self.video_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.tk_image)

    def update_timecode_label(self, current_seconds):
        """更新时间码标签"""
        current_time_str = self.format_duration(current_seconds)
        total_time_str = self.format_duration(self.total_duration)
        self.timecode_label.config(text=f"{current_time_str} / {total_time_str}")

    def toggle_play_pause(self):
        """切换播放和暂停状态"""
        if not self.cap or not self.cap.isOpened():
            return
            
        if self.is_playing:
            self.is_playing = False
            self.play_pause_btn.config(text="播放")
        else:
            self.is_playing = True
            self.play_pause_btn.config(text="暂停")
            self.play_video()

    def stop_playback(self):
        """停止播放并重置到开始位置"""
        self.is_playing = False
        self.play_pause_btn.config(text="播放")
        if self.cap and self.cap.isOpened():
            self.show_frame_at(0)
            self.timeline_scale.set(0)
            self.update_timecode_label(0)

    def play_video(self):
        """播放视频的主循环"""
        if not self.is_playing or not self.cap or not self.cap.isOpened():
            return
            
        ret, frame = self.cap.read()
        if ret:
            self.display_frame(frame)
            self.current_frame_pos += 1
            
            current_time = self.current_frame_pos / self.fps
            self.timeline_scale.set(current_time)
            self.update_timecode_label(current_time)
            
            delay = int(1000 / self.fps)
            self.root.after(delay, self.play_video)
        else:
            self.stop_playback()

    def on_scale_change(self, value):
        """当滑块被拖动时调用"""
        pass
        
    def on_scale_release(self, event):
        """当鼠标从滑块上释放时调用"""
        if not self.cap or not self.cap.isOpened():
            return
            
        seek_time = float(self.timeline_scale.get())
        
        was_playing = self.is_playing
        if was_playing:
            self.is_playing = False # 暂停播放循环
            
        self.show_frame_at(seek_time)
        self.update_timecode_label(seek_time)
        
        if was_playing:
            self.is_playing = True # 恢复播放状态
            self.root.after(100, self.play_video)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoPlayerApp(root)
    root.mainloop()