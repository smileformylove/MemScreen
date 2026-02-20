# 

## 

,

- **macOS**:  NSPanel ,
- ****: ,

## 

### 1. 
- "Start Recording"
- 
- ()

### 2.  (macOS )

#### 
- 
- ,

#### 
- ****: 
- (/)

#### 
- 
- :
  - **⏹ Stop Recording**: 
  - **⏸ Pause / ▶ Resume**: /
  - **🏠 Main Window**: 
  - ****: 

### 3. 
- 1:  → Stop Recording
- 2:  →  → Stop Recording
- 3:  Dock  → Stop Recording

## 

:

|  |  |  |  |
|------|------|------|------|
|  |  | ○ |  |
|  |  | ● |  |
|  |  | II |  |

## 

### 
```
memscreen/ui/
├── floating_ball.py        # K ()
├── floating_ball_native.py # macOS  (NSPanel)
├── floating_ball_simple.py # 
└── kivy_app.py             # 
```

### macOS 

#### FloatingBallWindow  ([memscreen/ui/floating_ball_native.py](memscreen/ui/floating_ball_native.py))

****:
1. ****:  NSPanel,
2. ****:  NSFloatingWindowLevel 
3. ****: 
4. ****: ,

****:

```python
# 
self.setLevel_(NSWindowLevelFloating)

# 
self.setFloatingPanel_(True)  # 
self.setBecomesKeyOnlyIfNeeded_(True)  # 
self.setHidesOnDeactivate_(False)  # 

# 
self.setCollectionBehavior_(
    (1 << 6) |  # NSWindowCollectionBehaviorCanJoinAllSpaces
    (1 << 8) |  # NSWindowCollectionBehaviorFullScreenAuxiliary
    (1 << 10)   # NSWindowCollectionBehaviorIgnoresCycle
)
```

****:
- ****:  5 
- ****: ,
- ****: 

### 

,:

1. **FloatingBallWindow** ([memscreen/ui/floating_ball.py](memscreen/ui/floating_ball.py))
   - KivyWidget
   - 
   - 
   - ()

2. **RecordingScreen**
   - `_show_floating_ball()`: 120×120px
   - `_hide_floating_ball()`: 

### 
- ****: 80px
- ****: 
- ****: 60fps (Kivy)
- ****: 
- ****: 

## 

### macOS 
1. ****: ,
2. ****: 
3. ****: "Main Window"
4. ****: 

### 
1. ****: ,
2. ****: 
3. ****: 
4. ****: "Main Window"

## 

### macOS 
- ✅ 
- ✅ 
- ✅ 
- ✅ 
- ✅ 

### 
Kivy, macOS ****:
- : 
- : ,

## 

- [ ] /
- [ ] 
- [ ] ()
- [ ] 
- [ ] ()
- [x] ~~API~~ (macOS )
- [ ] Windows  ( Layered Window)
- [ ] Linux  ( X11/Wayland)
