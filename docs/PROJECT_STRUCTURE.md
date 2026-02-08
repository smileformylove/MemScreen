# MemScreen 项目结构

## 目录结构

```
MemScreen/
├── start.py                 # 应用启动入口
├── config_example.yaml      # 配置文件示例
├── README.md               # 项目说明
├── LICENSE                 # MIT 许可证
│
├── memscreen/              # 主代码包
│   ├── ui/                # UI 组件
│   ├── presenters/        # 业务逻辑 (MVP架构)
│   ├── memory/            # 记忆系统
│   ├── llm/               # LLM集成
│   ├── audio/             # 音频录制
│   ├── prompts/           # Prompt模板
│   ├── embeddings/        # 向量嵌入
│   ├── vector_store/      # 向量数据库
│   ├── config/            # 配置管理
│   └── utils/             # 工具函数
│
├── tests/                 # 测试文件
│   ├── test_hybrid_vision.py
│   ├── test_integration.py
│   ├── test_recording_flow.py
│   ├── test_*.py
│   └── README.md
│
├── examples/              # 示例代码
│   ├── demo_optimization.py       # 优化功能演示
│   ├── demo_chat_integration.py
│   ├── demo_dynamic_memory.py
│   ├── demo_intelligent_agent.py
│   └── demo_visual_agent.py
│
├── docs/                  # 文档
│   ├── integration_guide.py        # 集成指南
│   ├── IMPLEMENTATION_SUMMARY.md   # 实施总结
│   └── *.md
│
├── setup/                 # 安装和打包脚本
├── assets/                # 资源文件
└── .github/               # GitHub Actions
```

## 数据目录

用户数据存储在 `~/.memscreen/`：

```
~/.memscreen/
├── db/                    # 数据库文件
│   ├── screen_capture.db  # 录制元数据
│   ├── memories.db        # 记忆数据
│   └── chroma.sqlite3     # 向量数据库
│
├── videos/                # 录制的视频
├── audio/                 # 音频文件
└── logs/                  # 日志文件
```

## 启动方式

```bash
# 方式1：直接运行
python start.py

# 方式2：使用脚本
./run.sh

# 方式3：打包的 .app (macOS)
open dist/MemScreen.app
```

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python tests/test_hybrid_vision.py

# 运行集成测试
python tests/test_integration.py

# 运行演示
python examples/demo_optimization.py
```

## 配置文件

复制 `config_example.yaml` 到 `~/.memscreen/config.yaml` 并根据需要修改：

```bash
mkdir -p ~/.memscreen
cp config_example.yaml ~/.memscreen/config.yaml
```

## 主要模块说明

### UI 层 (memscreen/ui/)
- `kivy_app.py`: 主应用程序，包含所有屏幕
- `components.py`: 可复用UI组件

### 业务逻辑层 (memscreen/presenters/)
- `recording_presenter.py`: 录制功能
- `video_presenter.py`: 视频管理
- `chat_presenter.py`: 聊天功能
- `process_mining_presenter.py`: 流程挖掘

### 记忆系统 (memscreen/memory/)
- `memory.py`: 基础记忆系统
- `enhanced_memory.py`: 增强记忆（包含6阶段优化）
- `tiered_memory_manager.py`: 分层记忆管理
- `conflict_resolver.py`: 冲突检测和解决

### LLM集成 (memscreen/llm/)
- `ollama_llm.py`: Ollama LLM
- `model_router.py`: 模型路由

### 向量存储 (memscreen/vector_store/)
- `chroma_store.py`: ChromaDB 集成
- `multimodal_chroma.py`: 多模态向量存储

## 优化功能（6个阶段）

1. **视觉编码器** (memscreen/embeddings/vision_encoder.py)
   - SigLIP/CLIP 模型支持
   - 视觉哈希计算
   - 特征提取

2. **多模态搜索** (memscreen/memory/hybrid_retriever.py)
   - 文本+视觉双路检索
   - RRF 融合排序

3. **分层记忆管理** (memscreen/memory/tiered_memory_manager.py)
   - Working Memory (1小时)
   - Short-term Memory (1-7天)
   - Long-term Memory (7天+)

4. **冲突检测** (memscreen/memory/conflict_resolver.py)
   - 三级冲突检测
   - 智能冲突解决

5. **多粒度视觉记忆** (memscreen/memory/multigranular_vision_memory.py)
   - Scene/Object/Text 三级表示
   - 时序事件检测

6. **视觉问答优化** (memscreen/prompts/vision_qa_prompts.py)
   - 查询类型分类
   - 视觉推理链
   - 7b 模型优化

## 开发指南

### 添加新功能
1. 在对应模块创建文件
2. 编写单元测试到 `tests/`
3. 更新文档
4. 提交 PR

### 代码风格
- 遵循 PEP 8
- 使用类型注解
- 添加文档字符串
- 编写测试

## 许可证

MIT License - 详见 LICENSE 文件
