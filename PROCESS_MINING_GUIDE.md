# Process Mining Tab - 使用说明

## v0.4.0 新功能

Process Mining标签页已增强，现在支持点击会话记录查看详情和Pattern Analysis。

## 主要改进

### 1. **实时会话统计**
- 显示当前会话的事件数量
- 键盘按键计数
- 鼠标点击计数
- 实时更新

### 2. **当前会话时间轴**
- 显示实时事件流
- 时间戳（HH:MM:SS格式）
- 事件类型分类
- 自动滚动显示最新事件

### 3. **会话历史记录**
- 所有会话自动保存到SQLite数据库
- 显示会话列表（最近20个）
- 每个会话显示：
  - 会话编号
  - 开始/结束时间
  - 事件统计
  - 持续时间
- **点击会话可查看详情**（新增）

### 4. **UI布局**
```
┌─────────────────────────────────────┐
│ Process Mining                        │
├─────────────────────────────────────┤
│ [Start/Stop Tracking]                │
│ Events: 0 | Keystrokes: 0 | Clicks: 0 │
├─────────────────────────────────────┤
│ Current Session                      │
│ ┌───────────────────────────────┐   │
│ │ 09:42:15  🔴 Tracking started │   │
│ │ 09:42:20  ⌨️  Key press: 'a'    │   │
│ │ 09:42:25  🖱️  Mouse click        │   │
│ └───────────────────────────────┘   │
├─────────────────────────────────────┤
│ Session History                       │
│ ┌───────────────────────────────┐   │
│ Session #1 • 09:30:15             │   │
│ 45 events | 120 keys | 30 clicks     │
│ ⏱️ 09:30:15 → 09:45:30            │
│ ────────────────────────────────   │
│ Session #2 • 08:15:10             │   │
│ ...                                 │
│ └───────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 5. **会话详情弹窗**
```
┌─────────────────────────────┐
│ Session #1 Details           │
│ ⏱️ 09:30:15 → 09:45:30       │
├─────────────────────────────┤
│ 📈 Pattern Analysis          │
│ • Most Active Keys: a, s, d  │
│ • Event Frequency: 3.2/min   │
│ • Click Intensity: 25.5%     │
│ • Session Duration: 15.3min  │
├─────────────────────────────┤
│ 📝 Event Timeline            │
│ 09:30:15  🔴 Tracking started│
│ 09:30:20  ⌨️ Key press: 'a'   │
│ ...                            │
├─────────────────────────────┤
│        [Close]               │
└─────────────────────────────┘
```

## 数据存储

### 数据库位置
```
./db/process_mining.db
```

### 数据表结构
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT,      -- HH:MM:SS
    end_time TEXT,        -- HH:MM:SS
    event_count INTEGER,   -- 总事件数
    keystrokes INTEGER,   -- 按键次数
    clicks INTEGER,       -- 点击次数
    events_json TEXT     -- 事件详情(JSON格式)
)
```

### 事件类型
- **info**: 一般信息（开始/停止跟踪）
- **keypress**: 键盘按键
- **click**: 鼠标点击
- **success**: 成功操作（保存会话等）

## 使用方法

### 1. 开始跟踪
点击 "Start Tracking" 按钮
- 按钮变为红色，显示 "Stop Tracking"
- 下方显示实时事件流

### 2. 停止跟踪
点击 "Stop Tracking" 按钮
- 按钮变回紫色，显示 "Start Tracking"
- 当前会话自动保存到数据库
- 历史记录列表自动刷新

### 3. 查看历史
滚动到 "Session History" 区域
- 显示最近20个会话
- 每个会话显示完整统计信息

### 4. 查看会话详情和Pattern Analysis（新功能）
点击任意历史会话记录
- 弹出会话详情窗口
- **Pattern Analysis** 分析内容：
  - 📊 **Most Active Keys**: 最常使用的按键（Top 5）
  - ⚡ **Event Frequency**: 平均每分钟事件数
  - 🖱️ **Click Intensity**: 点击事件占总事件的比例
  - ⏱️ **Session Duration**: 会话持续时长（分钟）
- **Event Timeline**: 显示该会话的所有事件流（最多显示100个）
- 点击"Close"按钮关闭详情窗口

## 与Videos标签的对比

| 特性 | Videos标签 | Process Mining标签 |
|------|-----------|-------------------|
| 时间轴 | 视频录制的时间点 | 键鼠事件的时间流 |
| 标记 | 视频文件标记点 | 会话记录 |
| 媒体类型 | 视频文件 | 事件数据 |
| 数据库 | SQLite (视频元数据) | SQLite (会话数据) |
| 视觉展示 | 视频截图 | 事件文本 |

## 未来计划

### 已实现 ✅
- [x] 会话详情查看（点击会话记录）
- [x] Pattern Analysis（按键统计、事件频率、点击强度）

### 可能的改进
- [ ] 添加键盘热键统计
- [ ] 鼠标移动轨迹可视化
- [ ] 应用使用时长分析
- [ ] 工作流模式识别（更高级的AI分析）
- [ ] 导出会话数据为CSV/JSON
- [ ] 按应用类型过滤事件
- [ ] 搜索历史事件

## 技术实现

### 核心文件
- `memscreen/ui/kivy_app.py` - ProcessScreen类（第1544行开始）
- SQLite数据库 - `./db/process_mining.db`

### 关键方法
```python
def start(self)              # 开始跟踪
def stop(self)               # 停止跟踪
def _add_session_event(...)   # 添加事件到当前会话
def _update_session_stats()  # 更新统计显示
def _save_session()          # 保存会话到数据库
def _load_history()          # 加载历史记录
def _create_session_item()   # 创建历史会话UI项（带点击事件）
def _show_session_detail()   # 显示会话详情弹窗（新）
def _analyze_patterns()      # Pattern Analysis分析（新）
def _create_detail_event_item()  # 创建详情页事件项（新）
```

## 注意事项

1. **性能**: 事件很多时可能影响UI响应
2. **存储**: 长期使用会话数据库会变大
3. **隐私**: 所有键鼠事件都被记录
4. **兼容性**: 与videos标签共享数据库目录

---

*更新时间: 2026-01-29*
*版本: v0.4.0*
