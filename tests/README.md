# MemScreen 测试

本目录包含 MemScreen 的核心测试与验证脚本（基于 Flutter 主界面结构）。

## 📁 当前测试结构

```text
tests/
├── run_tests.py                 # 统一测试入口
├── test_performance.py          # 性能测试
├── test_visual_memory.py        # 视觉记忆测试
├── test_dynamic_memory.py       # 动态 Memory 测试
├── test_memory_integration.py   # Memory 集成测试
├── test_app_integration.py      # 应用集成测试
├── test_audio_recording.py      # 音频录制测试
├── test_recording_flow.py       # 录屏流程测试
├── test_hybrid_vision.py        # 混合视觉检索测试
└── verify_dynamic_memory.py     # 动态 Memory 验证脚本
```

## 🚀 快速开始

```bash
# 从项目根目录运行全部基础测试
python tests/run_tests.py

# 仅运行指定测试组
python tests/run_tests.py --performance
python tests/run_tests.py --visual
python tests/run_tests.py --dynamic
python tests/run_tests.py --integration
python tests/run_tests.py --audio
```

## 📝 说明

- 已移除对旧 Kivy UI 模块的测试引用。
- 与 Flutter/macOS 悬浮球相关能力，优先通过 `frontend/flutter` 的集成流程验证。
- 需要人工交互的演示脚本不再作为默认测试集。

## 🐳 Docker 测试

详细说明见 `tests/DOCKER_TEST.md`。

## 📚 相关文档

- `docs/TESTING_GUIDE.md`
- `docs/DYNAMIC_MEMORY.md`
- `docs/FLUTTER.md`
