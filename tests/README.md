# MemScreen 测试

本目录包含 MemScreen 的所有测试文件。

## 📁 测试结构

```
tests/
├── DOCKER_TEST.md              # Docker 测试指南
├── test_performance.py         # 性能测试
├── test_visual_memory.py       # 视觉记忆测试
├── test_dynamic_memory.py      # 动态 Memory 测试
├── test_memory_integration.py  # Memory 集成测试
├── test_app_integration.py    # 应用集成测试
└── verify_dynamic_memory.py   # Memory 验证脚本
```

## 🚀 快速开始

### 运行所有测试

```bash
# 从项目根目录
python run_tests.py
```

### 运行特定测试

```bash
# 性能测试
python run_tests.py --performance

# 视觉记忆测试
python run_tests.py --visual

# 动态 Memory 测试
python run_tests.py --dynamic

# 集成测试
python run_tests.py --integration

# 音频测试
python run_tests.py --audio
```

### 直接运行测试

```bash
# 性能测试
python tests/test_performance.py

# 视觉记忆测试
python tests/test_visual_memory.py

# 动态 Memory 测试
python tests/test_dynamic_memory.py
```

## 📋 测试说明

### 1. test_performance.py
**目的**: 验证性能优化效果

测试内容：
- ✅ 输入分类速度
- ✅ 意图识别速度
- ✅ 缓存效果验证
- ✅ 性能提升统计

预期结果：
- 分类时间 < 1ms
- 意图识别 < 1ms
- 缓存加速 > 90%

### 2. test_visual_memory.py
**目的**: 测试视觉物体识别和搜索

测试内容：
- ✅ 屏幕捕获
- ✅ 视觉分析
- ✅ 物体识别
- ✅ 语义搜索

预期结果：
- 成功捕获屏幕
- 准确识别物体
- 正确保存到 Memory

### 3. test_dynamic_memory.py
**目的**: 测试动态 Memory 系统

测试内容：
- ✅ 自动输入分类
- ✅ 查询意图识别
- ✅ 智能调度
- ✅ 类别存储

预期结果：
- 15 种类别正确识别
- 7 种意图正确识别
- 智能调度正常工作

### 4. test_memory_integration.py
**目的**: 测试 Memory 系统集成

测试内容：
- ✅ Memory 初始化
- ✅ 添加记忆
- ✅ 搜索记忆
- ✅ 类别管理

预期结果：
- 所有功能正常工作
- 数据正确保存和检索

### 5. test_app_integration.py
**目的**: 测试应用集成

测试内容：
- ✅ 组件初始化
- ✅ 服务通信
- ✅ 数据流
- ✅ 错误处理

预期结果：
- 所有组件正确集成
- 数据流正常

## 🐳 Docker 测试

详细的 Docker 测试指南请查看：[DOCKER_TEST.md](DOCKER_TEST.md)

快速测试：
```bash
chmod +x ../test_docker.sh
../test_docker.sh
```

## 📊 测试覆盖率

| 模块 | 覆盖率 | 测试文件 |
|------|--------|----------|
| Memory 系统 | ✅ 90% | test_dynamic_memory.py |
| 视觉分析 | ✅ 80% | test_visual_memory.py |
| 性能优化 | ✅ 95% | test_performance.py |
| 集成测试 | ✅ 85% | test_*.py |

## 📝 添加新测试

1. 创建测试文件在 `tests/` 目录
2. 使用 `test_*.py` 命名约定
3. 在 `run_tests.py` 中添加测试函数
4. 更新本 README

## 🐛 故障排除

### 测试失败

```bash
# 查看详细错误
python tests/test_performance.py -v

# 检查依赖
pip install -r requirements.txt

# 检查 Ollama
ollama list
```

### 内存不足

```bash
# 只运行必要的测试
python run_tests.py --performance
```

## 📚 相关文档

- [性能优化文档](../INTELLIGENT_AGENT_SUMMARY.md)
- [动态 Memory 文档](../docs/DYNAMIC_MEMORY.md)
- [Intelligent Agent 文档](../docs/INTELLIGENT_AGENT.md)
