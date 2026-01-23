# 🧪 MemScreen 完整功能测试流程

## 测试目标

验证从录制到查看、搜索的完整工作流程。

## 前置条件检查

### 1. 依赖项 ✅
```bash
python3 test_all_features.py
```

**预期输出：**
- ✅ Dependencies
- ✅ Database
- ✅ Ollama
- ✅ Output Directory
- ✅ Memory System

### 2. Ollama 服务 ✅
```bash
ollama list
```

**预期输出：**
```
NAME                                ID              SIZE
mxbai-embed-large:latest            468836162de7    669 MB
qwen2.5vl:3b                        fb90415cde1e    3.2 GB
qwen3:1.7b                          8f68893c685c    1.4 GB
```

## 完整测试流程

### 步骤 1: 启动界面 ✅

```bash
memscreen-ui
```

**验证点：**
- ✅ 界面正常打开
- ✅ 默认显示 Record 标签页
- ✅ 屏幕预览实时更新（每秒）
- ✅ 录制设置显示正常

**界面元素：**
```
┌────────────────────────────────────────┐
│  MemScreen - Ask Screen Anything       │
├────────────────────────────────────────┤
│ 🔴 Record  💬 Chat  🎬 Videos  🔍  ⚙️  │ ← 导航标签
├────────────────────────────────────────┤
│  Recording Settings                    │
│  Duration: [60]                        │
│  Interval: [2.0]                       │
│  Output: [./db/videos]                 │
│  [🔴 Start Recording]                  │
│  [Screen Preview]                      │
└────────────────────────────────────────┘
```

### 步骤 2: 录制屏幕 ✅

**操作：**
1. 保持默认设置：Duration=60, Interval=2.0
2. 点击 "🔴 Start Recording"
3. 观察状态变化

**验证点：**
- ✅ 按钮文本变为 "⏹️ Stop Recording"
- ✅ 状态显示 "● Recording..." (红色)
- ✅ 实时状态更新：`Recording: 5s | Remaining: 55s | Frames: 2`
- ✅ 帧数持续增长

**录制中状态：**
```
Button: ⏹️ Stop Recording (橙色)
Status: ● Recording... (红色)
Info: Recording: 15s | Remaining: 45s | Frames: 7
```

**等待 10 秒后手动停止**

### 步骤 3: 停止录制 ✅

**操作：**
点击 "⏹️ Stop Recording"

**验证点：**
- ✅ 按钮变回 "🔴 Start Recording"
- ✅ 状态显示 "● Saving video..." (橙色)
- ✅ 弹出成功对话框：显示保存路径

**保存消息：**
```
Success
Recording saved:
./db/videos/recording_20250123_235900.mp4
```

### 步骤 4: 查看录制 ✅

**操作：**
1. 点击 "🎬 Videos" 标签
2. 检查视频列表

**验证点：**
- ✅ 视频出现在列表中
- ✅ 显示时间戳和时长
- ✅ 点击视频可以播放

**预期列表项：**
```
2025-01-23 23:59 - 00:10  (刚录制的视频)
```

**视频详情：**
```
📁 recording_20250123_235900.mp4
⏱️ 10s | 📊 0.5 MB
```

### 步骤 5: 播放录制 ✅

**操作：**
1. 从列表中选择刚录制的视频
2. 点击 "▶️ Play"

**验证点：**
- ✅ 视频在画布中播放
- ✅ 时间轴更新
- ✅ 时间码显示正确
- ✅ 可以暂停和继续

### 步骤 6: 搜索功能 ✅

**操作：**
1. 切换到 "🔍 Search" 标签
2. 输入搜索词（如："screen", "recording"）
3. 点击 "Search"

**验证点：**
- ✅ 显示搜索进度
- ✅ 返回相关结果
- ✅ 结果来自向量搜索

**预期输出：**
```
🔍 Searching for: recording

1. [搜索结果1 - 相关内容]

2. [搜索结果2 - 相关内容]
```

### 步骤 7: AI 对话 ✅

**操作：**
1. 切换到 "💬 Chat" 标签
2. 输入问题："我刚才录制了什么？"
3. 点击 "Send"

**验证点：**
- ✅ 消息出现在聊天历史
- ✅ AI 响应流式显示
- ✅ 响应包含录制相关信息
- ✅ "AI is thinking..." 指示器正确显示/隐藏

**示例对话：**
```
You: 我刚才录制了什么？

AI: 根据您的屏幕录制记录，您刚才录制了一段约10秒的视频，
保存在 ./db/videos/recording_20250123_235900.mp4

您可以切换到 Videos 标签查看这个录制。
```

## 数据流验证

### 录制流程

```
1. 用户点击 "Start Recording"
   ↓
2. 后台线程开始捕获屏幕
   - ImageGrab.grab() 每2秒
   - 转换为 OpenCV BGR 格式
   - 存入帧列表
   ↓
3. 实时状态更新
   - 已录制时长
   - 剩余时间
   - 帧数统计
   ↓
4. 用户点击 "Stop Recording"
   ↓
5. 保存视频
   - 创建 MP4 文件
   - 写入所有帧
   - 生成文件名 (时间戳)
   ↓
6. 存入数据库
   - INSERT INTO videos
   - 保存元数据
   ↓
7. 刷新视频列表
   - load_video_list()
   - Videos 标签自动更新
```

### 搜索流程

```
1. 用户输入搜索词
   ↓
2. 调用 mem.search()
   ↓
3. 向量数据库查询
   - ChromaDB 语义搜索
   - 返回最相关的结果
   ↓
4. 显示结果
```

### AI 对话流程

```
1. 用户输入问题
   ↓
2. 增强提示词
   - 添加 MEMORY_ANSWER_PROMPT
   - 搜索相关记忆
   - 添加上下文
   ↓
3. 发送到 Ollama
   - POST /api/chat
   - 流式响应
   ↓
4. 更新 UI
   - 逐字显示
   - 添加到对话历史
```

## 文件系统验证

### 预期文件结构

```
./db/
├── screen_capture.db          # SQLite 数据库
├── chroma.sqlite3             # 向量数据库
├── videos/
│   └── recording_20250123_235900.mp4
└── logs/
    └── memscreen_20250123.log
```

### 验证命令

```bash
# 检查数据库
sqlite3 ./db/screen_capture.db "SELECT * FROM videos"

# 检查视频文件
ls -lh ./db/videos/

# 检查向量数据库
ls -lh ./db/chroma.sqlite3
```

## 常见问题排查

### 问题 1: 录制后视频不显示在列表

**检查：**
```bash
sqlite3 ./db/screen_capture.db "SELECT * FROM videos"
```

**解决：**
- 确认录制成功保存
- 切换到 Videos 标签
- 点击 "Refresh" 按钮

### 问题 2: 搜索无结果

**检查：**
```bash
ls -lh ./db/chroma.sqlite3
```

**解决：**
- 首次使用需要建立向量索引
- 录制后等待几秒再搜索
- 尝试更通用的关键词

### 问题 3: AI 对话无响应

**检查：**
```bash
curl http://127.0.0.1:11434/api/tags
```

**解决：**
- 确保 Ollama 正在运行
- 检查模型是否已下载
- 查看 Chat 标签的模型选择器

## 性能指标

### 录制性能

| 间隔设置 | FPS | 10分钟视频大小 |
|---------|-----|---------------|
| 0.5秒   | 2   | ~30 MB        |
| 1.0秒   | 1   | ~15 MB        |
| 2.0秒   | 0.5 | ~8 MB         |
| 5.0秒   | 0.2 | ~3 MB         |

### 搜索速度

- 首次搜索：~2-3秒（初始化）
- 后续搜索：~0.5-1秒

### AI 响应速度

- 模型加载：~3-5秒
- 首次响应：~2-3秒
- 流式生成：实时

## 测试完成标准

### 必须通过的测试

- [ ] ✅ 界面正常启动
- [ ] ✅ 录制功能正常
- [ ] ✅ 视频成功保存
- [ ] ✅ 视频出现在列表中
- [ ] ✅ 视频可以播放
- [ ] ✅ 搜索功能正常
- [ ] ✅ AI 对话正常

### 可选测试

- [ ] 长时间录制（5分钟+）
- [ ] 多个录制连续创建
- [ ] 复杂搜索查询
- [ ] 多轮对话

## 测试脚本

运行完整测试：
```bash
# 1. 启动 UI
memscreen-ui &

# 2. 等待启动
sleep 3

# 3. 运行测试
python3 test_all_features.py

# 4. 手动测试
# - 录制 10 秒视频
# - 在 Videos 中查看
# - 在 Search 中搜索
# - 在 Chat 中对话
```

## 预期结果

所有测试通过后，您应该能够：
1. ✅ 在一个界面中完成所有操作
2. ✅ 录制并立即查看视频
3. ✅ 搜索到录制内容
4. ✅ 与 AI 讨论录制内容
5. ✅ 享受流畅的用户体验

---

**测试完成后，您将拥有一个功能完整的屏幕记忆系统！** 🎉
