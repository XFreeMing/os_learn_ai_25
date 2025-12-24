# 2025 年开源项目学习清单

## 📋 项目清单

### 1. 编辑器与开发工具

#### **Zed** - 高性能代码编辑器

- **项目地址**: https://github.com/zed-industries/zed

```shell
git submodule add git@github.com:zed-industries/zed.git venders/zed

```

- **研究文档**:
  - [GPUI 开发文档](https://docsmith.aigne.io/docs/zed/en/core-development-developing-with-gpui-ae8f50)
  - [GPU 渲染 UI 技术博客](https://zed.dev/blog/videogame)
  - [CRDT 协作算法详解](https://zed.dev/blog/crdts)
- **核心技术**: Rust, GPUI 渲染引擎, CRDTs, 异步 Rust
- **学习要点**:
  - GPU 直接渲染 UI，绕过 DOM 层，实现 120fps 流畅度
  - 即时模式与保留模式混合渲染策略
  - CRDT 算法实现文本并发编辑，理解逻辑时钟和操作日志
  - 异步 Rust 在 UI 主线程与后台任务池之间的消息传递

---

### 2. 浏览器引擎

#### **Ladybird** - 独立浏览器引擎

- **项目地址**: https://github.com/LadybirdBrowser/ladybird
- **官网**: https://ladybird.org/
- **核心技术**: C++, Swift, LibWeb, LibJS, 多进程架构
- **学习要点**:
  - 从零构建浏览器引擎，理解 HTML 解析、CSS 布局算法
  - Swift 逐步替换 C++，学习内存安全语言的迁移策略
  - 多进程架构：WebContent 渲染进程、ImageDecoder 进程、RequestServer 网络进程
  - Flexbox/Grid 等复杂布局算法的边缘情况处理

---

### 3. AI 智能体基础设施

#### **AGENTS.md** - AI 智能体上下文协议

- **规范地址**: https://agents.md/
- **研究文档**:
  - [OpenAI 开发者指南](https://developers.openai.com/codex/guides/agents-md/)
  - [GitHub 最佳实践](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)
  - [Agent Skills 文档](https://developers.openai.com/codex/skills/)
- **核心技术**: Markdown 标准, 分层作用域, 指令集标准化
- **学习要点**:
  - 机器可读的上下文协议设计
  - 分层作用域：根目录全局规则，子目录可覆盖
  - 声明式约束机制：Always do / Never do 指令
  - Skill 封装：自然语言函数接口

#### **Model Context Protocol (MCP)**

- **基金会**: Agentic AI Foundation (AAIF)
- **官网**: https://openai.com/index/agentic-ai-foundation/
- **核心技术**: JSON-RPC, Client-Host-Server 架构, 上下文传输优化
- **学习要点**:
  - 标准化数据管道，类似 LSP 架构
  - 资源（Resources）、提示词（Prompts）和工具（Tools）的暴露机制
  - 基于 stdio 或 HTTP/SSE 的传输层
  - 实时资源更新推送机制

#### **CrewAI** - 多智能体编排框架

- **项目地址**: https://github.com/joaomdmoura/crewAI
- **研究文档**:
  - [框架对比分析](https://www.3pillarglobal.com/insights/blog/comparison-crewai-langgraph-n8n/)
  - [选择指南](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)
- **核心技术**: Python, 组织架构隐喻, 角色扮演, 记忆存储
- **学习要点**:
  - Agent, Task, Crew, Process 抽象
  - 任务委托与结果汇总机制
  - 共享记忆存储实现多智能体信息同步
  - 团队协作的涌现效应

#### **LangGraph** - 图导向智能体编排

- **项目地址**: https://github.com/langchain-ai/langgraph
- **研究文档**:
  - [框架对比](https://www.zenml.io/blog/langgraph-vs-crewai)
  - [差异分析](https://www.truefoundry.com/blog/crewai-vs-langgraph)
- **核心技术**: Python, 图论, 状态机, 持久化状态
- **学习要点**:
  - State, Node, Edge, Conditional Edge 抽象
  - 循环（Cycles）支持，打破 DAG 限制
  - 持久化状态和人在回路（Human-in-the-loop）机制
  - 自我修正和迭代优化智能体的实现

---

### 4. AI 模型与应用

#### **Moondream** - 端侧视觉语言模型

- **项目地址**: https://github.com/vikhyat/moondream
- **研究文档**:
  - [Moondream 3 预览](https://moondream.ai/blog/moondream-3-preview)
  - [官方文档](https://docs.moondream.ai/)
- **核心技术**: VLM, MoE 架构, SigLIP 损失函数, 原生技能支持
- **学习要点**:
  - 混合专家（MoE）架构：9B 总参数，2B 激活参数
  - SigLIP 损失函数：将匹配问题转化为二分类
  - 稀疏激活实现性能与计算成本平衡
  - 内置指向、计数、物体检测等结构化输出技能

#### **RAGFlow** - 深度文档理解 RAG 引擎

- **项目地址**: https://github.com/infiniflow/ragflow
- **研究文档**:
  - [深度文档理解](https://github.com/infiniflow/ragflow/blob/main/deepdoc/README.md)
  - [技术详解](https://medium.com/@infiniflowai/a-deep-dive-into-ragflow-v0-15-0-9f1dbca21347)
  - [RAG 演进](https://ragflow.io/blog/the-rise-and-evolution-of-rag-in-2024-a-year-in-review)
- **核心技术**: OCR, 文档布局分析, YOLOv8, 混合检索
- **学习要点**:
  - 文档布局分析：识别标题、段落、表格、双栏排版
  - 基于模板的分块策略：问答对、简历、论文等
  - 混合检索：向量相似度 + 关键词权重 + 短语查询
  - 解决 RAG 幻觉问题的工程思路

---

### 5. Web 服务器与运行时

#### **Granian** - Rust HTTP 服务器（Python 应用）

- **项目地址**: https://github.com/emmett-framework/granian
- **研究文档**:
  - [PyPI 文档](https://pypi.org/project/granian/2.2.3/)
  - [播客访谈](https://talkpython.fm/episodes/show/463/running-on-rust-granian-web-server)
- **核心技术**: Rust, RSGI, ASGI/WSGI 兼容, Tokio, 背压机制
- **学习要点**:
  - 绕过 Python GIL：Rust 处理 I/O，Python 执行业务逻辑
  - RSGI（Rust Server Gateway Interface）设计
  - 背压控制：防止系统过载的经典范例
  - 精细线程模型配置：workers, blocking threads, runtime threads

#### **Bun** - JavaScript 全能工具箱

- **项目地址**: https://github.com/oven-sh/bun
- **核心技术**: Zig, JavaScriptCore, 一体化架构
- **学习要点**:
  - 基于 JavaScriptCore 而非 V8，更快启动和更低内存
  - 模块解析、转译和执行紧密集成
  - Runtime, Bundler, Test Runner, Package Manager 一体化
  - 生产环境稳定性考量

---

### 6. 机器学习框架

#### **Candle** - Rust 极简 ML 框架

- **项目地址**: https://github.com/huggingface/candle
- **研究文档**:
  - [框架对比](https://medium.com/@athan.seal/candle-vs-burn-comparing-rust-machine-learning-frameworks-4dbd59c332a1)
- **核心技术**: Rust, Tensor 操作, CUDA, Metal, Serverless 优化
- **学习要点**:
  - 零开销设计：无计算图构建，直接操作 Tensor
  - 极小二进制文件，适合 Serverless 和边缘设备
  - 支持 CPU、CUDA、Metal，无需庞大 CUDA 库
  - 类似 PyTorch API 但去除 Python 运行时依赖

#### **Burn** - Rust 深度学习框架

- **项目地址**: https://github.com/tracel-ai/burn
- **核心技术**: Rust, 动态图, 后端 Trait 系统, Autodiff
- **学习要点**:
  - 多后端支持：WGPU, Torch, Candle, NdArray
  - 后端 Trait 系统：利用 Rust 泛型实现后端切换
  - Autodiff 结构体作为后端装饰器
  - 自动微分与计算后端解耦的设计模式

---

### 7. 数据库

#### **Qdrant** - 向量数据库

- **项目地址**: https://github.com/qdrant/qdrant
- **研究文档**:
  - [性能基准](https://qdrant.tech/benchmarks/)
  - [对比指南](https://www.firecrawl.dev/blog/best-vector-databases-2025)
- **核心技术**: Rust, HNSW 算法, 内存映射, SIMD
- **学习要点**:
  - HNSW（分层导航小世界）算法实现
  - 内存映射（mmap）技术处理超内存限制索引
  - SIMD 指令集优化大规模向量检索
  - 亿级向量下的性能优势

#### **SurrealDB** - 多模态数据库

- **项目地址**: https://github.com/surrealdb/surrealdb
- **研究文档**:
  - [2.0 发布](https://surrealdb.com/blog/challenge-accepted-announcing-surrealdb-2-0)
  - [安全特性](https://www.hpcwire.com/bigdatawire/this-just-in/surrealdb-2-0-introduces-advanced-security-and-data-management-features/)
- **核心技术**: 多模态, HNSW 索引, SurrealML, 计算下推
- **学习要点**:
  - 统一文档、图、关系和向量数据库
  - 原生 HNSW 算法用于向量检索
  - 数据库层执行 ML 模型推理（SurrealML）
  - SQL 过滤、图遍历和向量相似度搜索混合查询

---

### 8. WebAssembly 与边缘计算

#### **Spin** - Wasm Serverless 框架

- **项目地址**: https://github.com/fermyon/spin
- **研究文档**:
  - [Spin 2.0 介绍](https://www.fermyon.com/blog/introducing-spin-v2)
  - [组件组合](https://www.fermyon.com/blog/composing-components-with-spin-2)
  - [微服务构建](https://www.fermyon.com/blog/rust-linz-spin-component-model)
- **核心技术**: Wasm Component Model, WASI 0.3, 多语言互操作
- **学习要点**:
  - 组件模型：Rust/Go/Python 组件编译为.wasm 并链接
  - 进程内通信替代网络 API，高效内存拷贝
  - Spin Manifest (spin.toml)：声明式触发器与能力
  - wit-bindgen 自动生成多语言绑定代码

#### **WasmEdge** - AI 推理边缘运行时

- **项目地址**: https://github.com/WasmEdge/WasmEdge
- **核心技术**: Wasm, PyTorch/TensorFlow 插件, GPU 调用, Kubernetes 集成
- **学习要点**:
  - Wasm 沙箱内高效调用宿主机 GPU 资源
  - 插件系统支持 PyTorch、TensorFlow 和 LLM 推理
  - 与 Kubernetes 集成（Runwasi）混合调度容器和 Wasm

---

### 9. 本地优先应用

#### **AppFlowy** - Notion 开源替代

- **项目地址**: https://github.com/AppFlowy-IO/AppFlowy
- **研究文档**:
  - [架构实践](https://skywork.ai/skypage/en/AppFlowy-Docker-My-Journey-to-a-Self-Hosted%2C-AI-Powered-Workspace/1975226298207891456)
- **核心技术**: Flutter, Rust, Dart FFI, Local-First, SQLite
- **学习要点**:
  - Flutter + Rust 架构：UI 跨平台，核心逻辑 Rust
  - Dart FFI 高效调用 Rust 代码
  - 离线优先与数据同步机制
  - 去中心化数据一致性算法

#### **NocoDB** - 数据库转智能表格

- **项目地址**: https://github.com/nocodb/nocodb
- **研究文档**:
  - [架构概览](https://nocodb.com/docs/product-docs/engineering/architecture)
- **核心技术**: MySQL/PostgreSQL, 动态 Schema 解析, API 生成
- **学习要点**:
  - 动态解析数据库 Schema 并生成 API
  - 大规模并发查询处理
  - 企业内部工具快速构建平台

#### **Appwrite** - 开源 Firebase 替代

- **项目地址**: https://github.com/appwrite/appwrite
- **核心技术**: Docker 微服务, Auth, Database, Storage, Functions
- **学习要点**:
  - Backend-as-a-Service 平台架构
  - 高可用、可扩展的微服务设计
  - 多数据库和存储后端支持

---

## 🎯 学习路线图

### 阶段一：基础设施理解

1. **Rust 架构深入**：阅读 Zed 和 Granian 源码，理解高性能并发系统
2. **异步运行时**：学习 Tokio 与 GUI/Web 服务器的结合

### 阶段二：AI 智能体标准

1. **AGENTS.md 实践**：为自己的项目添加智能体描述文件
2. **MCP 协议**：学习如何让工具被 AI 智能体无缝调用

### 阶段三：组件化架构

1. **Wasm Component Model**：通过 Spin 实践下一代微服务
2. **跨语言组件组合**：理解组件模型的语言互操作性

### 阶段四：独立引擎研究

1. **Ladybird 跟踪**：观察浏览器引擎从零构建的过程
2. **Swift 迁移**：学习在大型 C++项目中引入现代语言

### 阶段五：端侧 AI 实践

1. **Moondream 应用**：探索资源受限环境下的视觉理解
2. **RAGFlow 部署**：实践深度文档理解与布局分析

---

## 📚 核心知识点总结

### 架构范式

- **智能体互操作性**：AGENTS.md、MCP 协议标准化
- **Rust 原生基础设施**：内存安全与零成本抽象统一
- **主权化计算**：Local-First 架构，数据主权

### 技术突破

- **GPU 渲染 UI**：绕过 DOM，直接 GPU 指令，120fps 流畅度
- **CRDT 算法**：无冲突复制数据类型，分布式协作
- **MoE 架构**：稀疏激活，性能与成本平衡
- **文档布局分析**：OCR + 视觉模型，解决 RAG 幻觉

### 设计模式

- **分层作用域**：全局规则与局部覆盖
- **后端 Trait 系统**：泛型实现多后端切换
- **背压机制**：防止系统过载的经典范例
- **组件模型**：进程内通信替代网络 API

---

## 🔗 相关资源

- [Agentic AI Foundation](https://openai.com/index/agentic-ai-foundation/)
- [AGENTS.md 规范](https://agents.md/)
- [GitHub 2025 年度项目](https://github.blog/open-source/maintainers/this-years-most-influential-open-source-projects/)
- [WebAssembly 状态报告](https://platform.uno/blog/state-of-webassembly-2024-2025/)

---

## 更新记录

最后更新：2025 年 12 月
