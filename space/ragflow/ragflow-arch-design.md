# RAGFlow 架构设计深度分析

> 文档版本: v0.23.0
> 分析日期: 2025-12-30
> 项目地址: https://github.com/infiniflow/ragflow

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 系统架构总览](#2-系统架构总览)
- [3. 核心模块详解](#3-核心模块详解)
- [4. 数据流与处理流程](#4-数据流与处理流程)
- [5. Agent 系统架构](#5-agent-系统架构)
- [6. DeepDoc 文档理解引擎](#6-deepdoc-文档理解引擎)
- [7. GraphRAG 知识图谱系统](#7-graphrag-知识图谱系统)
- [8. 部署架构](#8-部署架构)
- [9. 技术栈总结](#9-技术栈总结)
- [10. 架构优势与设计亮点](#10-架构优势与设计亮点)

---

## 1. 项目概述

RAGFlow 是由 InfiniFlow 开发的开源 RAG (Retrieval-Augmented Generation) 引擎，基于深度文档理解技术。它提供了一个适应各种规模企业的流畅 RAG 工作流，结合 LLM 提供基于可靠引用的问答能力。

### 1.1 核心特性

- **深度文档理解**: 从复杂格式的非结构化数据中提取知识
- **模板化分块**: 智能且可解释的文档分块策略
- **引用追溯**: 可视化文本分块，支持人工干预
- **异构数据源兼容**: 支持 Word、PPT、Excel、PDF、图片、网页等多种格式
- **自动化 RAG 工作流**: 可配置的 LLM 和 Embedding 模型

### 1.2 系统要求

- CPU >= 4 核
- RAM >= 16 GB
- Disk >= 50 GB
- Docker >= 24.0.0 & Docker Compose >= v2.26.1
- Python >= 3.12

---

## 2. 系统架构总览

### 2.1 高层架构图

```mermaid
graph TB
    subgraph "Frontend Layer"
        WEB[React/TypeScript Web UI<br/>UmiJS + Ant Design]
    end

    subgraph "API Gateway"
        NGINX[Nginx Reverse Proxy]
    end

    subgraph "Backend Services"
        API[Flask API Server<br/>ragflow_server.py]
        TASK[Task Executor<br/>异步任务处理]
        ADMIN[Admin Server<br/>管理接口]
        MCP[MCP Server<br/>模型上下文协议]
    end

    subgraph "Core Engines"
        RAG[RAG Pipeline<br/>检索增强生成]
        AGENT[Agent System<br/>工作流引擎]
        DEEPDOC[DeepDoc Engine<br/>文档理解]
        GRAPHRAG[GraphRAG<br/>知识图谱]
    end

    subgraph "Data Layer"
        MYSQL[(MySQL<br/>元数据存储)]
        ES[(Elasticsearch/Infinity<br/>向量+全文检索)]
        REDIS[(Redis/Valkey<br/>缓存+会话)]
        MINIO[(MinIO<br/>对象存储)]
    end

    subgraph "External Services"
        LLM[LLM Providers<br/>35+ 支持]
        EMBED[Embedding Models]
        RERANK[Rerank Models]
    end

    WEB --> NGINX
    NGINX --> API
    API --> RAG
    API --> AGENT
    RAG --> DEEPDOC
    RAG --> GRAPHRAG
    RAG --> ES
    RAG --> LLM
    RAG --> EMBED
    RAG --> RERANK
    TASK --> RAG
    API --> MYSQL
    API --> REDIS
    API --> MINIO
```

### 2.2 目录结构

```
ragflow/
├── api/                    # 后端 API 服务
│   ├── apps/              # Flask 蓝图模块
│   ├── db/                # 数据库模型和服务
│   ├── common/            # 通用工具
│   └── utils/             # API 工具函数
├── agent/                  # Agent 工作流系统
│   ├── canvas.py          # 画布执行引擎
│   ├── component/         # 工作流组件
│   ├── tools/             # 外部工具集成
│   └── templates/         # 预置模板
├── rag/                    # RAG 核心管道
│   ├── llm/               # LLM 抽象层
│   ├── flow/              # 处理流程
│   └── nlp/               # NLP 工具
├── deepdoc/                # 文档深度理解
│   ├── parser/            # 文档解析器
│   └── vision/            # 视觉识别
├── graphrag/               # 知识图谱 RAG
│   ├── general/           # 完整实现
│   └── light/             # 轻量实现
├── common/                 # 公共模块
│   ├── data_source/       # 数据源连接器
│   └── doc_store/         # 文档存储抽象
├── web/                    # 前端 React 应用
├── docker/                 # Docker 部署配置
└── sdk/                    # Python SDK
```

---

## 3. 核心模块详解

### 3.1 API 后端架构

#### 3.1.1 Flask 应用入口

**主入口**: `api/ragflow_server.py`

```mermaid
graph LR
    subgraph "Flask Application"
        INIT[应用初始化] --> BLUEPRINTS[注册蓝图]
        BLUEPRINTS --> MIDDLEWARE[中间件配置]
        MIDDLEWARE --> ROUTES[路由分发]
    end

    subgraph "Blueprints"
        USER[user_app<br/>用户认证]
        KB[kb_app<br/>知识库]
        DOC[document_app<br/>文档处理]
        DIALOG[dialog_app<br/>对话管理]
        CANVAS[canvas_app<br/>Agent画布]
        CHUNK[chunk_app<br/>分块管理]
        API_SDK[api_app/sdk<br/>外部API]
    end

    ROUTES --> USER
    ROUTES --> KB
    ROUTES --> DOC
    ROUTES --> DIALOG
    ROUTES --> CANVAS
    ROUTES --> CHUNK
    ROUTES --> API_SDK
```

#### 3.1.2 API 模块功能

| 模块 | 文件 | 功能描述 |
|------|------|----------|
| 用户管理 | `user_app.py` | 认证、授权、OAuth |
| 知识库 | `kb_app.py` | 知识库 CRUD、配置 |
| 文档处理 | `document_app.py` | 文档上传、解析状态 |
| 对话管理 | `dialog_app.py` | 聊天会话、历史记录 |
| Agent 画布 | `canvas_app.py` | 工作流设计与执行 |
| 分块管理 | `chunk_app.py` | 分块查看、编辑 |
| 文件管理 | `file_app.py` | 文件上传下载 |
| LLM 配置 | `llm_app.py` | 模型配置管理 |
| 外部 API | `api_app.py` | SDK 和外部集成 |
| 搜索 | `search_app.py` | 跨知识库搜索 |

#### 3.1.3 服务层架构

```mermaid
graph TB
    subgraph "API Layer"
        ROUTE[Route Handler]
    end

    subgraph "Service Layer"
        COMMON[CommonService<br/>基础 CRUD]
        USER_SVC[UserService]
        KB_SVC[KnowledgebaseService]
        DOC_SVC[DocumentService]
        DIALOG_SVC[DialogService]
    end

    subgraph "Data Access Layer"
        MODEL[Peewee ORM Models]
        DB[MySQL Database]
    end

    ROUTE --> COMMON
    ROUTE --> USER_SVC
    ROUTE --> KB_SVC
    ROUTE --> DOC_SVC
    ROUTE --> DIALOG_SVC

    USER_SVC --> MODEL
    KB_SVC --> MODEL
    DOC_SVC --> MODEL
    DIALOG_SVC --> MODEL

    MODEL --> DB
```

### 3.2 LLM 集成层

#### 3.2.1 支持的 LLM 提供商 (35+)

```python
class SupportedLiteLLMProvider(StrEnum):
    OpenAI = "OpenAI"
    Anthropic = "Anthropic"
    Tongyi_Qianwen = "Tongyi-Qianwen"
    DeepSeek = "DeepSeek"
    ZHIPU_AI = "ZHIPU-AI"
    Groq = "Groq"
    Cohere = "Cohere"
    Gemini = "Gemini"
    Ollama = "Ollama"
    # ... 更多提供商
```

#### 3.2.2 LLM 抽象层架构

```mermaid
classDiagram
    class LLMBundle {
        +tenant_id: str
        +llm_type: LLMType
        +llm_name: str
        +encode(texts): ndarray
        +chat(system, history): str
        +similarity(query, texts): ndarray
    }

    class ChatModel {
        <<abstract>>
        +chat(system, history, gen_conf)
        +async_chat_streamly()
        +async_chat_with_tools()
    }

    class EmbeddingModel {
        <<abstract>>
        +encode(texts): ndarray
        +encode_queries(text): ndarray
    }

    class RerankModel {
        <<abstract>>
        +similarity(query, texts): ndarray
    }

    class OpenAIChat
    class QWenChat
    class ZhipuChat

    LLMBundle --> ChatModel
    LLMBundle --> EmbeddingModel
    LLMBundle --> RerankModel

    ChatModel <|-- OpenAIChat
    ChatModel <|-- QWenChat
    ChatModel <|-- ZhipuChat
```

#### 3.2.3 模型类型

| 类型 | 文件 | 功能 |
|------|------|------|
| ChatModel | `chat_model.py` | 对话生成、工具调用 |
| EmbeddingModel | `embedding_model.py` | 文本向量化 |
| RerankModel | `rerank_model.py` | 结果重排序 |
| CVModel | `cv_model.py` | 图像理解 |
| OCRModel | `ocr_model.py` | 文字识别 |
| Seq2TxtModel | `sequence2txt_model.py` | 语音转文本 |
| TTSModel | `tts_model.py` | 文本转语音 |

### 3.3 文档存储抽象

#### 3.3.1 存储引擎支持

```mermaid
graph TB
    subgraph "DocStore Abstraction"
        BASE[DocStoreConnection<br/>抽象基类]
    end

    subgraph "Implementations"
        ES[Elasticsearch<br/>默认引擎]
        INFINITY[Infinity<br/>高性能替代]
        OCEANBASE[OceanBase<br/>分布式数据库]
    end

    BASE --> ES
    BASE --> INFINITY
    BASE --> OCEANBASE
```

#### 3.3.2 核心接口

```python
class DocStoreConnection(ABC):
    # 数据库操作
    def db_type(self) -> str
    def health(self) -> dict

    # 索引操作
    def create_idx(index_name, dataset_id, vector_size)
    def delete_idx(index_name, dataset_id)
    def index_exist(index_name, dataset_id) -> bool

    # CRUD 操作
    def search(select_fields, highlight_fields, condition,
               match_expressions, order_by, offset, limit, ...)
    def get(data_id, index_name, dataset_ids) -> dict
    def insert(rows, index_name, dataset_id) -> list[str]
    def update(condition, new_value, index_name, dataset_id)
    def delete(condition, index_name, dataset_id) -> int
```

---

## 4. 数据流与处理流程

### 4.1 文档处理管道

```mermaid
flowchart TB
    subgraph "输入层"
        UPLOAD[文件上传]
        SYNC[数据源同步<br/>Confluence/S3/Notion]
    end

    subgraph "解析层"
        DEEPDOC[DeepDoc 解析引擎]
        subgraph "解析器"
            PDF[PDF Parser]
            DOCX[Word Parser]
            EXCEL[Excel Parser]
            HTML[HTML Parser]
            IMG[Image Parser]
        end
    end

    subgraph "分块层"
        SPLITTER[Splitter<br/>文档分块]
        TOKEN[Tokenizer<br/>分词+嵌入]
    end

    subgraph "索引层"
        EMBED[向量嵌入]
        FULLTEXT[全文索引]
        STORE[存储入库]
    end

    UPLOAD --> DEEPDOC
    SYNC --> DEEPDOC

    DEEPDOC --> PDF
    DEEPDOC --> DOCX
    DEEPDOC --> EXCEL
    DEEPDOC --> HTML
    DEEPDOC --> IMG

    PDF --> SPLITTER
    DOCX --> SPLITTER
    EXCEL --> SPLITTER
    HTML --> SPLITTER
    IMG --> SPLITTER

    SPLITTER --> TOKEN
    TOKEN --> EMBED
    TOKEN --> FULLTEXT
    EMBED --> STORE
    FULLTEXT --> STORE
```

### 4.2 RAG 检索流程

```mermaid
sequenceDiagram
    participant U as User
    participant API as API Server
    participant RAG as RAG Pipeline
    participant ES as Elasticsearch
    participant LLM as LLM Provider

    U->>API: 发送查询
    API->>RAG: 处理查询

    RAG->>RAG: 查询分析/重写

    par 并行检索
        RAG->>ES: 全文搜索
        RAG->>ES: 向量搜索
    end

    ES-->>RAG: 候选结果

    RAG->>RAG: 结果融合
    RAG->>RAG: 重排序

    RAG->>LLM: 构建 Prompt + 上下文
    LLM-->>RAG: 生成回答

    RAG-->>API: 返回答案+引用
    API-->>U: 展示结果
```

### 4.3 混合搜索机制

```mermaid
graph LR
    subgraph "Query Processing"
        Q[用户查询] --> REWRITE[查询重写]
        REWRITE --> KEYWORDS[关键词提取]
        REWRITE --> VECTOR[向量编码]
    end

    subgraph "Search Methods"
        KEYWORDS --> FULLTEXT[全文搜索<br/>BM25]
        VECTOR --> DENSE[稠密向量搜索<br/>HNSW]
    end

    subgraph "Fusion & Ranking"
        FULLTEXT --> FUSION[融合排序<br/>加权和]
        DENSE --> FUSION
        FUSION --> RERANK[重排序<br/>Cross-Encoder]
        RERANK --> RESULT[最终结果]
    end
```

### 4.4 分块策略

| 策略 | 参数 | 描述 |
|------|------|------|
| Token Size | `chunk_token_size=512` | 最大分块大小 |
| 重叠 | `overlapped_percent=0.1` | 相邻块重叠比例 |
| 分隔符 | `delimiters=["\n"]` | 主要分隔符 |
| 表格上下文 | `table_context_size` | 表格周围文本 |
| 图像上下文 | `image_context_size` | 图像描述 |

---

## 5. Agent 系统架构

### 5.1 Canvas 执行引擎

```mermaid
graph TB
    subgraph "Canvas 画布"
        BEGIN[Begin<br/>开始节点]
        LLM[LLM<br/>大模型调用]
        RETRIEVAL[Retrieval<br/>知识检索]
        CATEGORIZE[Categorize<br/>分类路由]
        SWITCH[Switch<br/>条件分支]
        MESSAGE[Message<br/>消息输出]
        AGENT_TOOLS[AgentWithTools<br/>工具调用Agent]
    end

    subgraph "控制流"
        LOOP[Loop<br/>循环]
        ITERATION[Iteration<br/>迭代]
        EXIT_LOOP[ExitLoop<br/>退出循环]
    end

    subgraph "数据操作"
        VAR_ASSIGN[VariableAssigner<br/>变量赋值]
        VAR_AGG[VariableAggregator<br/>变量聚合]
        DATA_OPS[DataOperations<br/>数据操作]
        LIST_OPS[ListOperations<br/>列表操作]
    end

    BEGIN --> LLM
    BEGIN --> RETRIEVAL
    LLM --> CATEGORIZE
    CATEGORIZE --> SWITCH
    SWITCH --> MESSAGE
    SWITCH --> AGENT_TOOLS
    LOOP --> ITERATION
    ITERATION --> EXIT_LOOP
```

### 5.2 组件基类设计

```python
class ComponentBase(ABC):
    """所有组件的抽象基类"""

    @abstractmethod
    async def invoke(self, **kwargs) -> dict:
        """执行组件逻辑"""
        pass

    def get_input(self) -> dict:
        """获取上游输入"""
        pass

    def output(self) -> dict:
        """返回下游输出"""
        pass

    def get_downstream(self) -> list[str]:
        """获取下游组件ID"""
        pass
```

### 5.3 组件类型详解

| 组件 | 类型 | 功能 |
|------|------|------|
| Begin | 入口 | 工作流起点，定义输入变量 |
| LLM | 处理 | 调用大语言模型 |
| Retrieval | 检索 | 从知识库检索相关内容 |
| Categorize | 路由 | LLM驱动的分类路由 |
| Switch | 条件 | 条件判断分支 |
| Message | 输出 | 消息格式化输出 |
| AgentWithTools | Agent | 带工具调用的智能体 |
| Loop/Iteration | 控制 | 循环控制 |
| VariableAssigner | 数据 | 变量赋值 |
| DataOperations | 数据 | JSON数据操作 |

### 5.4 工具集成

```mermaid
graph LR
    subgraph "内置工具"
        TAVILY[Tavily Search<br/>网络搜索]
        WIKI[Wikipedia<br/>百科查询]
        SQL[SQL Executor<br/>数据库查询]
        CODE[Code Executor<br/>代码执行]
    end

    subgraph "外部集成"
        MCP_TOOLS[MCP Tools<br/>模型上下文协议]
        API_TOOLS[HTTP API<br/>自定义接口]
    end

    AGENT[AgentWithTools] --> TAVILY
    AGENT --> WIKI
    AGENT --> SQL
    AGENT --> CODE
    AGENT --> MCP_TOOLS
    AGENT --> API_TOOLS
```

### 5.5 预置模板

| 模板 | 用途 |
|------|------|
| customer_service | 客户服务 |
| choose_your_knowledge_base | 多知识库选择 |
| chunk_summary | 分块摘要生成 |
| customer_review_analysis | 客户评论分析 |
| advanced_ingestion_pipeline | 高级数据入库 |

---

## 6. DeepDoc 文档理解引擎

### 6.1 架构概览

```mermaid
graph TB
    subgraph "DeepDoc Engine"
        INPUT[文档输入]

        subgraph "Vision Module"
            OCR[OCR<br/>文字识别]
            LAYOUT[Layout Recognition<br/>版面分析]
            TABLE[Table Structure<br/>表格识别]
        end

        subgraph "Parser Module"
            PDF_P[PDF Parser]
            DOCX_P[DOCX Parser]
            EXCEL_P[Excel Parser]
            PPT_P[PPT Parser]
            HTML_P[HTML Parser]
        end

        OUTPUT[结构化输出]
    end

    INPUT --> PDF_P
    INPUT --> DOCX_P
    INPUT --> EXCEL_P
    INPUT --> PPT_P
    INPUT --> HTML_P

    PDF_P --> OCR
    PDF_P --> LAYOUT
    PDF_P --> TABLE

    OCR --> OUTPUT
    LAYOUT --> OUTPUT
    TABLE --> OUTPUT
    DOCX_P --> OUTPUT
    EXCEL_P --> OUTPUT
    PPT_P --> OUTPUT
    HTML_P --> OUTPUT
```

### 6.2 Vision 模块

#### 6.2.1 OCR 识别

- **双引擎设计**: TextDetector + TextRecognizer
- **算法**: DB边界检测 + CTC解码
- **批处理**: batch_size=16
- **多GPU支持**: 可配置GPU内存限制

#### 6.2.2 版面识别

**10种布局类型**:
- Text (正文)
- Title (标题)
- Figure (图片)
- Figure caption (图片标题)
- Table (表格)
- Table caption (表格标题)
- Header (页眉)
- Footer (页脚)
- Reference (参考文献)
- Equation (公式)

#### 6.2.3 表格结构识别

```mermaid
flowchart LR
    IMG[表格图像] --> DETECT[元素检测<br/>ONNX模型]
    DETECT --> ALIGN[行列对齐<br/>K-Means]
    ALIGN --> BUILD[2D表格构建]
    BUILD --> OUTPUT[HTML/Markdown<br/>输出]
```

### 6.3 PDF 解析核心算法

```mermaid
flowchart TB
    PDF[PDF文件] --> IMG_EXTRACT[图像提取<br/>pdfplumber 3x缩放]

    IMG_EXTRACT --> OCR_PROCESS[OCR处理<br/>~40%时间]
    OCR_PROCESS --> LAYOUT_REC[版面识别<br/>~23%时间]
    LAYOUT_REC --> TABLE_ANAL[表格分析<br/>~20%时间]
    TABLE_ANAL --> TEXT_MERGE[文本合并<br/>~9%时间]
    TEXT_MERGE --> STRUCTURE[结构化输出<br/>~8%时间]

    subgraph "文本合并策略"
        H_MERGE[水平合并<br/>相邻框]
        V_MERGE[垂直合并<br/>同列框]
        ML_MERGE[ML驱动合并<br/>XGBoost]
    end

    TEXT_MERGE --> H_MERGE
    H_MERGE --> V_MERGE
    V_MERGE --> ML_MERGE
```

### 6.4 支持的文档格式

| 格式 | 解析器 | 特性 |
|------|--------|------|
| PDF | RAGFlowPdfParser | OCR+版面+表格完整解析 |
| DOCX | RAGFlowDocxParser | 原生提取，保留表格 |
| Excel | RAGFlowExcelParser | 多Sheet，ODS/CSV支持 |
| PPT | RAGFlowPptParser | 形状提取，表格识别 |
| HTML | RAGFlowHtmlParser | BeautifulSoup解析 |
| Markdown | RAGFlowMarkdownParser | 元素级提取 |
| 图像 | FigureParser | OCR识别 |

---

## 7. GraphRAG 知识图谱系统

### 7.1 整体架构

```mermaid
graph TB
    subgraph "构建流程"
        CHUNK[文档分块] --> EXTRACT[实体关系抽取<br/>LLM驱动]
        EXTRACT --> MERGE[子图合并]
        MERGE --> RESOLVE[实体解析<br/>去重合并]
        RESOLVE --> COMMUNITY[社区检测<br/>Leiden算法]
        COMMUNITY --> REPORT[社区报告生成]
    end

    subgraph "存储层"
        GRAPH[(NetworkX Graph)]
        ES_IDX[(ES/Infinity<br/>实体+关系索引)]
    end

    subgraph "查询流程"
        QUERY[用户查询] --> REWRITE[查询重写]
        REWRITE --> MULTI_RETRIEVE[多路检索]
        MULTI_RETRIEVE --> FUSE[结果融合]
        FUSE --> RESPONSE[生成响应]
    end

    REPORT --> GRAPH
    REPORT --> ES_IDX
    ES_IDX --> MULTI_RETRIEVE
```

### 7.2 实体关系抽取

```mermaid
sequenceDiagram
    participant DOC as 文档分块
    participant LLM as LLM
    participant GRAPH as 图构建器

    loop 每个分块
        DOC->>LLM: 初始提示词
        LLM-->>GRAPH: 实体+关系

        loop Gleaning (最多N轮)
            GRAPH->>LLM: 还有遗漏吗?
            LLM-->>GRAPH: 补充实体+关系
            GRAPH->>LLM: 继续? (Y/N)
            alt 继续
                LLM-->>GRAPH: Y
            else 停止
                LLM-->>GRAPH: N
            end
        end
    end

    GRAPH->>GRAPH: 合并子图到全局图
```

### 7.3 实体类型

- person (人物)
- organization (组织)
- geo (地理位置)
- event (事件)
- category (类别)

### 7.4 社区检测与报告

```mermaid
graph LR
    GRAPH[全局图] --> LEIDEN[Leiden算法<br/>层级聚类]
    LEIDEN --> COMMUNITY[社区划分]
    COMMUNITY --> LLM_ANALYZE[LLM分析<br/>生成报告]

    LLM_ANALYZE --> REPORT[社区报告]

    subgraph "报告结构"
        TITLE[标题]
        SUMMARY[摘要]
        FINDINGS[发现列表]
        RATING[重要性评分]
    end

    REPORT --> TITLE
    REPORT --> SUMMARY
    REPORT --> FINDINGS
    REPORT --> RATING
```

### 7.5 多路检索融合

| 检索路径 | 方法 | 描述 |
|---------|------|------|
| 关键词实体 | 向量相似度 | 查询关键词匹配实体 |
| 类型实体 | PageRank排序 | 按实体类型检索 |
| 关系检索 | 向量相似度 | 查询相关关系 |
| N-hop路径 | 图遍历 | 多步邻域扩展 |
| 社区报告 | 关联实体 | 相关社区摘要 |

---

## 8. 部署架构

### 8.1 Docker Compose 服务编排

```mermaid
graph TB
    subgraph "应用层"
        RAGFLOW_CPU[ragflow-cpu<br/>主服务CPU版]
        RAGFLOW_GPU[ragflow-gpu<br/>主服务GPU版]
    end

    subgraph "数据层"
        MYSQL[MySQL 8.0<br/>元数据存储]
        ES[Elasticsearch 8.x<br/>向量+全文]
        REDIS[Valkey/Redis<br/>缓存]
        MINIO[MinIO<br/>对象存储]
    end

    subgraph "可选服务"
        INFINITY[Infinity<br/>替代ES]
        SANDBOX[Sandbox<br/>代码执行]
        TEI[TEI<br/>嵌入服务]
        KIBANA[Kibana<br/>ES管理]
    end

    RAGFLOW_CPU --> MYSQL
    RAGFLOW_CPU --> ES
    RAGFLOW_CPU --> REDIS
    RAGFLOW_CPU --> MINIO

    RAGFLOW_GPU --> MYSQL
    RAGFLOW_GPU --> ES
    RAGFLOW_GPU --> REDIS
    RAGFLOW_GPU --> MINIO
```

### 8.2 端口配置

| 服务 | 端口 | 用途 |
|------|------|------|
| Web UI | 80/443 | 前端界面 |
| API Server | 9380 | 后端API |
| Admin Server | 9381 | 管理接口 |
| MCP Server | 9382 | MCP协议 |
| MySQL | 3306 | 数据库 |
| Elasticsearch | 9200 | 搜索引擎 |
| MinIO | 9000/9001 | 对象存储 |
| Redis | 6379 | 缓存 |

### 8.3 配置文件

| 文件 | 用途 |
|------|------|
| `docker/.env` | 环境变量 |
| `docker/service_conf.yaml.template` | 服务配置 |
| `docker/docker-compose.yml` | 服务编排 |
| `docker/docker-compose-base.yml` | 基础服务 |

---

## 9. 技术栈总结

### 9.1 后端技术

| 类别 | 技术 |
|------|------|
| Web框架 | Flask + Quart (异步) |
| ORM | Peewee |
| 任务队列 | Redis + 自定义执行器 |
| 缓存 | Redis/Valkey |
| 对象存储 | MinIO / S3 / OSS |
| 向量数据库 | Elasticsearch / Infinity |

### 9.2 AI/ML技术

| 类别 | 技术 |
|------|------|
| LLM集成 | 35+ 提供商 (OpenAI, Anthropic, 通义千问等) |
| 嵌入模型 | OpenAI, BGE, Jina, QWen等 |
| 重排模型 | Cohere, Jina, 本地模型 |
| OCR | 自研ONNX模型 |
| 版面识别 | YOLOv10 |
| 图算法 | NetworkX, graspologic |

### 9.3 前端技术

| 类别 | 技术 |
|------|------|
| 框架 | React + TypeScript |
| 构建 | UmiJS |
| UI组件 | Ant Design + shadcn/ui |
| 状态管理 | Zustand |
| 样式 | Tailwind CSS + Less |

### 9.4 DevOps

| 类别 | 技术 |
|------|------|
| 容器化 | Docker + Docker Compose |
| 包管理 | uv (Python) |
| 测试 | pytest |
| 代码质量 | ruff, pre-commit |
| Kubernetes | Helm Charts |

---

## 10. 架构优势与设计亮点

### 10.1 核心优势

```mermaid
mindmap
  root((RAGFlow 架构优势))
    深度文档理解
      10种版面类型识别
      复杂表格解析
      中英文双语支持
    多模型支持
      35+ LLM 提供商
      统一 LLMBundle 接口
      零适配成本切换
    混合检索
      全文 + 向量融合
      多维度重排序
      GraphRAG 增强
    可扩展性
      模块化组件设计
      插件化架构
      易于定制
    企业级
      多租户支持
      权限控制
      审计日志
```

### 10.2 设计亮点

1. **深度文档理解**
   - 不仅仅是文本提取，而是理解文档结构
   - 表格、图像、公式的智能处理
   - 位置信息保留，支持精确引用

2. **工厂模式 LLM 抽象**
   - 统一的 `LLMBundle` 接口
   - 支持热切换模型提供商
   - 自动错误分类和重试

3. **混合检索架构**
   - 全文搜索 + 稠密向量 + 稀疏向量
   - 可配置的融合权重
   - 多层重排序机制

4. **低代码 Agent 系统**
   - 可视化工作流设计
   - 丰富的内置组件
   - MCP 协议支持

5. **GraphRAG 增强**
   - 知识图谱构建和查询
   - 社区检测和报告生成
   - 实体解析和去重

### 10.3 性能优化策略

| 策略 | 实现 | 效果 |
|------|------|------|
| 批处理 | EMBEDDING_BATCH_SIZE=16 | 减少API调用 |
| 异步执行 | asyncio + Semaphore | 并行处理 |
| 缓存 | Redis (LLM响应、向量) | 避免重复计算 |
| 连接池 | ES/MySQL连接复用 | 减少连接开销 |
| 分布式锁 | Redis分布式锁 | 并发控制 |

### 10.4 适用场景

- **知识库问答**: 企业文档智能问答
- **客户服务**: 智能客服机器人
- **数据分析**: 结构化数据智能查询
- **内容生成**: 基于知识的内容创作
- **合规审查**: 文档合规性检查

---

## 参考资料

- [RAGFlow 官方文档](https://ragflow.io/docs/dev/)
- [RAGFlow GitHub 仓库](https://github.com/infiniflow/ragflow)
- [RAGFlow Roadmap 2025](https://github.com/infiniflow/ragflow/issues/4214)
- [DeepDoc README](https://github.com/infiniflow/ragflow/blob/main/deepdoc/README.md)
