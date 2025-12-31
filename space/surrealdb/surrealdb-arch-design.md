# SurrealDB 架构分析

## 项目概述

**SurrealDB** 是一个用 Rust 编写的多模型云原生数据库，支持文档、图、关系、时间序列和地理空间等多种数据模型。

| 属性 | 值 |
|------|-----|
| **版本** | 3.0.0-beta |
| **语言** | Rust (Edition 2024) |
| **核心代码量** | ~169,000 行 |
| **许可证** | Business Source License 1.1 |

### 核心特性

- 多模型数据库（文档、图、关系、时序、向量）
- 实时订阅和 Live Queries
- 内置身份认证和授权系统
- 支持 SQL 风格查询语言（SurrealQL）
- 多存储后端（内存、RocksDB、TiKV、SurrealKV）
- WebAssembly 支持（浏览器端运行）
- GraphQL API 支持

---

## 整体架构

### 高层架构图

```mermaid
flowchart TB
    subgraph Clients["客户端层"]
        JS[JavaScript SDK]
        PY[Python SDK]
        RS[Rust SDK]
        REST[REST API]
        GQL[GraphQL]
    end

    subgraph Server["服务层 (surrealdb-server)"]
        HTTP[HTTP Server<br/>Axum]
        WS[WebSocket Server]
        RPC[RPC Handler]
        AUTH[Authentication]
    end

    subgraph SDK["SDK 层 (surrealdb)"]
        LOCAL[Local Engine]
        REMOTE[Remote Engine]
        METHODS[API Methods]
    end

    subgraph Core["核心引擎 (surrealdb-core)"]
        PARSER[SQL Parser<br/>syn/]
        EXECUTOR[Query Executor<br/>dbs/]
        PLANNER[Query Planner<br/>idx/planner]
        KVS[KVS Layer<br/>kvs/]
        IDX[Index System<br/>idx/]
        VAL[Value System<br/>val/]
    end

    subgraph Storage["存储引擎层"]
        MEM[(Memory)]
        ROCKS[(RocksDB)]
        TIKV[(TiKV)]
        SKV[(SurrealKV)]
        INDX[(IndexedDB)]
    end

    Clients --> Server
    Clients --> SDK
    SDK --> Server
    SDK --> Core
    Server --> Core
    Core --> Storage
```

### Crates 依赖关系

```mermaid
graph TD
    BIN[surreal<br/>二进制入口] --> SERVER[surrealdb-server<br/>服务层]
    SERVER --> SDK[surrealdb<br/>SDK层]
    SDK --> CORE[surrealdb-core<br/>核心引擎]
    CORE --> EXT[External KVS<br/>RocksDB/TiKV/SurrealKV]

    style BIN fill:#e1f5fe
    style SERVER fill:#fff3e0
    style SDK fill:#f3e5f5
    style CORE fill:#e8f5e9
    style EXT fill:#fce4ec
```

---

## 目录结构

```
surrealdb/
├── crates/
│   ├── core/              # 核心数据库引擎 (6.5 MB)
│   │   └── src/
│   │       ├── kvs/       # 键值存储层
│   │       ├── dbs/       # 查询执行层
│   │       ├── sql/       # SQL 解析和 AST
│   │       ├── idx/       # 索引系统
│   │       ├── val/       # 值类型系统
│   │       ├── ctx/       # 执行上下文
│   │       ├── iam/       # 身份认证授权
│   │       ├── api/       # API 请求处理
│   │       ├── syn/       # 语法分析器
│   │       └── ...
│   ├── sdk/               # Rust SDK (604 KB)
│   │   └── src/
│   │       ├── engine/    # 引擎抽象
│   │       ├── method/    # API 方法
│   │       └── conn/      # 连接管理
│   ├── server/            # HTTP/WS 服务器 (480 KB)
│   │   └── src/
│   │       ├── ntw/       # 网络层
│   │       ├── rpc/       # RPC 处理
│   │       ├── cli/       # 命令行
│   │       └── telemetry/ # 可观测性
│   ├── language-tests/    # 语言测试
│   └── fuzz/              # 模糊测试
├── src/                   # CLI 入口点
├── tests/                 # 集成测试
└── doc/                   # 文档
```

---

## 核心组件分析

### 1. 存储引擎层 (kvs/)

存储引擎层提供统一的键值存储抽象，支持多种后端实现。

```mermaid
classDiagram
    class Datastore {
        +transaction_factory: TransactionFactory
        +id: Uuid
        +auth_enabled: bool
        +cache: Arc~DatastoreCache~
        +capabilities: Arc~Capabilities~
        +notification_channel: Option
        +transaction() Transaction
        +execute() QueryResult
    }

    class Transaction {
        +local: bool
        +tr: Transactor
        +cache: TransactionCache
        +sequences: Sequences
        +cf: ChangefeedWriter
        +get() Value
        +set() Result
        +commit() Result
        +cancel() Result
    }

    class TransactionBuilder {
        <<trait>>
        +begin() Transaction
        +transaction_type() TransactionType
        +transaction_lock() LockType
    }

    class Transactor {
        <<trait>>
        +get() Result
        +set() Result
        +del() Result
        +scan() Result
    }

    Datastore --> Transaction : creates
    Transaction --> Transactor : uses
    TransactionBuilder --> Transaction : builds

    class MemTransactor
    class RocksDBTransactor
    class TiKVTransactor
    class SurrealKVTransactor

    Transactor <|.. MemTransactor
    Transactor <|.. RocksDBTransactor
    Transactor <|.. TiKVTransactor
    Transactor <|.. SurrealKVTransactor
```

**关键模块：**

| 模块 | 职责 |
|------|------|
| `ds.rs` | Datastore 实例管理，核心聚合器 |
| `tx.rs` | Transaction 事务管理 |
| `tr.rs` | Transactor 底层事务处理接口 |
| `cache/` | 多层缓存系统 |
| `scanner.rs` | 键值范围扫描 |
| `clock.rs` | 混合逻辑时钟 (HLC) |

### 2. 查询执行层 (dbs/)

查询执行层负责解析、规划和执行 SurrealQL 查询。

```mermaid
sequenceDiagram
    participant C as Client
    participant P as Parser (syn/)
    participant PL as Planner
    participant E as Executor
    participant T as Transaction
    participant S as Storage

    C->>P: SQL Query String
    P->>P: Tokenize & Parse
    P->>PL: AST
    PL->>PL: Optimize
    PL->>E: LogicalPlan
    E->>T: Begin Transaction
    T->>S: Get/Set/Scan
    S-->>T: Results
    T-->>E: Data
    E->>T: Commit
    E-->>C: QueryResult
```

**执行器核心结构：**

```rust
pub struct Executor {
    stack: TreeStack,        // 递归深度控制
    results: Vec<QueryResult>,
    opt: Options,            // 执行选项
    ctx: FrozenContext,      // 冻结的执行上下文
}
```

### 3. SQL/查询语言层 (sql/)

SQL 层定义了 SurrealQL 的完整语法和语义。

```mermaid
graph LR
    subgraph AST["抽象语法树"]
        STMT[Statement]
        EXPR[Expression]
        VAL[Value]
        IDX[Index]
    end

    subgraph Statements["语句类型"]
        SEL[SELECT]
        INS[INSERT]
        UPD[UPDATE]
        DEL[DELETE]
        DEF[DEFINE]
        REL[RELATE]
    end

    subgraph Expressions["表达式"]
        FIELD[Field]
        FUNC[Function]
        OP[Operator]
        SUB[Subquery]
    end

    STMT --> SEL
    STMT --> INS
    STMT --> UPD
    STMT --> DEL
    STMT --> DEF
    STMT --> REL

    EXPR --> FIELD
    EXPR --> FUNC
    EXPR --> OP
    EXPR --> SUB
```

**支持的 47 个子模块包括：**
- `statements/` - 各类 SQL 语句定义
- `expression/` - 表达式处理
- `parser/` - 词法和语法分析
- `index/` - 索引定义
- `kind.rs` - 数据类型
- `function.rs` - 内置函数
- `permissions/` - 权限定义

### 4. 索引系统 (idx/)

索引系统支持多种索引类型，包括 B-Tree、全文索引和向量索引。

```mermaid
graph TB
    subgraph IndexTypes["索引类型"]
        BT[B-Tree Index]
        FT[Full-Text Index<br/>FST]
        VEC[Vector Index<br/>HNSW]
        UNIQ[Unique Index]
    end

    subgraph Components["核心组件"]
        PLANNER[Query Planner]
        SEQDOC[SeqDocIds]
        TREES[Tree Structures]
    end

    PLANNER --> BT
    PLANNER --> FT
    PLANNER --> VEC
    PLANNER --> UNIQ

    BT --> TREES
    FT --> TREES
    VEC --> TREES
```

**向量索引 (HNSW) 特性：**
- 层次化可导航小世界图
- 支持余弦相似度、欧氏距离等度量
- 高效的近似最近邻搜索

### 5. 值类型系统 (val/)

SurrealDB 支持丰富的数据类型。

```mermaid
graph TB
    VALUE[Value Enum]

    VALUE --> PRIM[基础类型]
    VALUE --> COMP[复合类型]
    VALUE --> SPECIAL[特殊类型]

    PRIM --> NONE[None]
    PRIM --> NULL[Null]
    PRIM --> BOOL[Bool]
    PRIM --> NUMBER[Number]
    PRIM --> STRING[String]
    PRIM --> BYTES[Bytes]

    COMP --> ARRAY[Array]
    COMP --> SET[Set]
    COMP --> OBJECT[Object]
    COMP --> RANGE[Range]

    SPECIAL --> DATETIME[Datetime]
    SPECIAL --> DURATION[Duration]
    SPECIAL --> UUID[Uuid]
    SPECIAL --> GEOMETRY[Geometry]
    SPECIAL --> RECORDID[RecordId]
    SPECIAL --> FILE[File]
    SPECIAL --> REGEX[Regex]
    SPECIAL --> CLOSURE[Closure]
```

---

## 服务器架构

### HTTP/WebSocket 服务器

```mermaid
flowchart LR
    subgraph Routes["HTTP 路由"]
        ROOT["/"]
        STATUS["/status"]
        HEALTH["/health"]
        RPC_E["/rpc"]
        SQL_E["/sql"]
        EXPORT["/export"]
        IMPORT["/import"]
        SIGNIN["/signin"]
        SIGNUP["/signup"]
        GQL_E["/gql"]
    end

    subgraph Handlers["处理器"]
        direction TB
        RPC_H[RPC Handler]
        SQL_H[SQL Handler]
        AUTH_H[Auth Handler]
        GQL_H[GraphQL Handler]
    end

    ROOT --> RPC_H
    STATUS --> RPC_H
    RPC_E --> RPC_H
    SQL_E --> SQL_H
    SIGNIN --> AUTH_H
    SIGNUP --> AUTH_H
    GQL_E --> GQL_H
```

### RPC 状态管理

```rust
pub struct RpcState {
    pub web_sockets: RwLock<HashMap<Uuid, Arc<Websocket>>>,
    pub live_queries: RwLock<HashMap<Uuid, (Uuid, Option<Uuid>)>>,
    pub http: Arc<Http>,
}
```

---

## 数据流架构

### 完整查询执行流程

```mermaid
flowchart TB
    subgraph Client["1. 客户端请求"]
        REQ[HTTP/WebSocket Request]
    end

    subgraph Router["2. 路由层"]
        AXUM[Axum Router]
    end

    subgraph RPC["3. RPC 处理"]
        DESER[反序列化<br/>JSON/CBOR]
        AUTH[认证授权检查]
    end

    subgraph Session["4. 会话管理"]
        SESS[Session Setup]
        CTX[FrozenContext]
    end

    subgraph Parser["5. SQL 解析"]
        LEX[Lexer]
        PARSE[Parser]
        AST[AST]
    end

    subgraph Planner["6. 查询规划"]
        PLAN[LogicalPlan]
        OPT[优化器]
    end

    subgraph TX["7. 事务"]
        BEGIN[Begin]
        EXEC[Execute]
        COMMIT[Commit/Rollback]
    end

    subgraph KVS["8. 存储层"]
        CACHE[Cache Lookup]
        STORAGE[Storage Engine]
    end

    subgraph Response["9. 响应"]
        RESULT[QueryResult]
        SER[序列化]
        SEND[发送响应]
    end

    REQ --> AXUM
    AXUM --> DESER
    DESER --> AUTH
    AUTH --> SESS
    SESS --> CTX
    CTX --> LEX
    LEX --> PARSE
    PARSE --> AST
    AST --> PLAN
    PLAN --> OPT
    OPT --> BEGIN
    BEGIN --> EXEC
    EXEC --> CACHE
    CACHE --> STORAGE
    STORAGE --> EXEC
    EXEC --> COMMIT
    COMMIT --> RESULT
    RESULT --> SER
    SER --> SEND
```

### 模块依赖关系

```mermaid
graph TB
    subgraph External["外部存储库"]
        ROCKSDB[facebook/rocksdb]
        TIKV_C[tikv/client]
        SKV_C[surrealdb/surrealkv]
        INDXDB_C[IndexedDB]
    end

    subgraph Core["surrealdb-core"]
        KVS[kvs/]
        DBS[dbs/]
        SQL[sql/]
        IDX[idx/]
        VAL[val/]
        CTX[ctx/]
        IAM[iam/]
    end

    subgraph SDK["surrealdb SDK"]
        ENGINE[engine/]
        METHOD[method/]
        CONN[conn/]
    end

    subgraph Server["surrealdb-server"]
        NTW[ntw/]
        RPC_S[rpc/]
        CLI[cli/]
    end

    NTW --> RPC_S
    RPC_S --> DBS
    CLI --> NTW

    ENGINE --> KVS
    METHOD --> DBS
    CONN --> NTW

    DBS --> SQL
    DBS --> KVS
    DBS --> CTX
    SQL --> VAL
    KVS --> IDX
    KVS --> IAM

    KVS --> ROCKSDB
    KVS --> TIKV_C
    KVS --> SKV_C
    KVS --> INDXDB_C
```

---

## 实时功能架构

### Live Query 系统

```mermaid
sequenceDiagram
    participant C as Client
    participant WS as WebSocket
    participant LQ as Live Query Manager
    participant TX as Transaction
    participant CF as Changefeed

    C->>WS: LIVE SELECT * FROM user
    WS->>LQ: Register Live Query
    LQ-->>C: Live Query ID

    Note over TX,CF: 数据变更发生

    TX->>CF: Write Change
    TX->>TX: Commit
    CF->>LQ: Notify Change
    LQ->>WS: Find Subscribers
    WS-->>C: Push Notification
```

### 通知系统流程

```mermaid
flowchart LR
    subgraph Transaction["事务层"]
        CHANGE[数据变更]
        CAPTURE[ChangeCapture]
        COMMIT[Commit]
    end

    subgraph Notification["通知层"]
        CHANNEL[Notification Channel]
        HANDLER[RPC Handler]
        MATCH[匹配 Live Query]
    end

    subgraph Delivery["分发层"]
        WS[WebSocket]
        CLIENT[客户端]
    end

    CHANGE --> CAPTURE
    CAPTURE --> COMMIT
    COMMIT --> CHANNEL
    CHANNEL --> HANDLER
    HANDLER --> MATCH
    MATCH --> WS
    WS --> CLIENT
```

---

## 身份认证与授权

### IAM 架构

```mermaid
graph TB
    subgraph Actor["Actor (谁)"]
        OWNER[Owner]
        EDITOR[Editor]
        VIEWER[Viewer]
    end

    subgraph Level["Level (层级)"]
        ROOT[Root]
        NS[Namespace]
        DB[Database]
        TB[Table]
        REC[Record]
    end

    subgraph Resource["Resource (什么)"]
        NS_R[Namespace]
        DB_R[Database]
        TB_R[Table]
        REC_R[Record]
        FN_R[Function]
    end

    subgraph Action["Action (做什么)"]
        VIEW[View]
        EDIT[Edit]
    end

    Actor --> Level
    Level --> Resource
    Resource --> Action
```

### 认证流程

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    participant IAM as IAM System
    participant DB as Database

    C->>S: Signin Request
    S->>IAM: Validate Credentials
    IAM->>DB: Check User
    DB-->>IAM: User Data
    IAM->>IAM: Generate JWT
    IAM-->>S: Token
    S-->>C: Auth Response

    C->>S: Query (with Token)
    S->>IAM: Verify Token
    IAM->>IAM: Check Permissions
    IAM-->>S: Authorized
    S->>DB: Execute Query
    DB-->>S: Results
    S-->>C: Response
```

---

## 技术栈

### 核心依赖

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **Web 框架** | Axum | 0.8.5 | HTTP 路由和处理 |
| **WebSocket** | tokio-tungstenite | 0.28 | 实时连接 |
| **异步运行时** | Tokio | 1.44.2 | 异步执行 |
| **序列化** | serde, ciborium, flatbuffers | - | JSON/CBOR/FlatBuffers |
| **存储** | RocksDB, TiKV, SurrealKV | - | 持久化 |
| **向量索引** | HNSW | - | 向量搜索 |
| **全文索引** | FST | - | 全文搜索 |
| **脚本** | rquickjs | - | JavaScript 执行 |
| **密码学** | argon2, bcrypt, blake3 | - | 密码哈希 |
| **地理空间** | geo, geo-types | 0.28 | 地理计算 |
| **并发** | DashMap, parking_lot | - | 并发数据结构 |
| **可观测性** | tracing, OpenTelemetry | - | 日志和追踪 |

### Feature Flags

```mermaid
graph LR
    subgraph Storage["存储引擎"]
        MEM[storage-mem<br/>默认]
        ROCKS[storage-rocksdb<br/>默认]
        TIKV[storage-tikv<br/>默认]
        SKV[storage-surrealkv<br/>默认]
        INDX[storage-indxdb]
    end

    subgraph Optional["可选功能"]
        SCRIPT[scripting]
        HTTP[http]
        NATIVE[native-tls]
        RUSTLS[rustls]
    end

    subgraph Runtime["运行时"]
        TOKIO[runtime-tokio]
        WASM[wasm]
    end
```

---

## 设计模式

### 1. Composer 模式 (依赖注入)

```mermaid
classDiagram
    class TransactionBuilderFactory {
        <<trait>>
        +create_builder() TransactionBuilder
    }

    class RouterFactory {
        <<trait>>
        +create_router() Router
    }

    class ConfigCheck {
        <<trait>>
        +check_config() Result
    }

    class CommunityComposer {
        +create_builder()
        +create_router()
        +check_config()
    }

    TransactionBuilderFactory <|.. CommunityComposer
    RouterFactory <|.. CommunityComposer
    ConfigCheck <|.. CommunityComposer
```

### 2. Builder 模式

```rust
pub struct Connect<C: Connection, Response> { ... }

impl<C, R> Connect<C, R> {
    pub const fn with_capacity(mut self, capacity: usize) -> Self { ... }
    pub fn with_auth(mut self, auth: Auth) -> Self { ... }
}
```

### 3. Provider 模式

```mermaid
classDiagram
    class NodeProvider {
        <<trait>>
        +get_node() Node
    }

    class RootProvider {
        <<trait>>
        +get_root() Root
    }

    class NamespaceProvider {
        <<trait>>
        +get_namespace() Namespace
    }

    class DatabaseProvider {
        <<trait>>
        +get_database() Database
    }

    NodeProvider <|-- RootProvider
    RootProvider <|-- NamespaceProvider
    NamespaceProvider <|-- DatabaseProvider
```

### 4. 多层缓存模式

```mermaid
graph TB
    subgraph Caching["缓存层次"]
        DS[DatastoreCache<br/>全局缓存]
        TX[TransactionCache<br/>事务缓存]
        QC[QueryCache<br/>查询缓存]
    end

    DS --> TX
    TX --> QC
    QC --> STORAGE[(Storage)]
```

---

## 性能优化

### 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `MEMORY_THRESHOLD` | 0 | 内存限制 |
| `MAX_CONCURRENT_TASKS` | 64 | 最大并发任务数 |
| `MAX_COMPUTATION_DEPTH` | 120 | 最大计算深度 |
| `TRANSACTION_CACHE_SIZE` | 10,000 | 事务缓存大小 |
| `DATASTORE_CACHE_SIZE` | 1,000 | 全局缓存大小 |
| `NORMAL_FETCH_SIZE` | 500 | 普通查询批量大小 |
| `EXPORT_BATCH_SIZE` | 1,000 | 导出批量大小 |
| `SCRIPTING_MAX_TIME_LIMIT` | 5s | JavaScript 执行超时 |
| `REGEX_CACHE_SIZE` | 1,000 | 正则表达式缓存 |

### 优化技术

```mermaid
graph LR
    subgraph Memory["内存优化"]
        ALLOC[分配追踪]
        LRU[LRU 缓存]
        POOL[对象池]
    end

    subgraph Execution["执行优化"]
        BATCH[自适应批处理]
        PARALLEL[并行执行]
        PLAN_OPT[查询计划优化]
    end

    subgraph Safety["安全措施"]
        STACK[栈溢出防护<br/>TreeStack]
        DEPTH[递归深度限制]
        TIMEOUT[执行超时]
    end
```

---

## 存储引擎对比

| 引擎 | 类型 | 分布式 | 持久化 | 适用场景 |
|------|------|--------|--------|----------|
| **Memory** | 内存 | 否 | 否 | 开发测试 |
| **RocksDB** | 嵌入式 | 否 | 是 | 单节点生产 |
| **TiKV** | 分布式 | 是 | 是 | 分布式生产 |
| **SurrealKV** | 嵌入式 | 否 | 是 | 优化的单节点 |
| **IndexedDB** | 浏览器 | 否 | 是 | WASM 环境 |

### 存储层抽象

```mermaid
graph TB
    API[Transaction API]

    API --> BUILDER[TransactionBuilder Trait]

    BUILDER --> MEM_B[MemBuilder]
    BUILDER --> ROCKS_B[RocksDBBuilder]
    BUILDER --> TIKV_B[TiKVBuilder]
    BUILDER --> SKV_B[SurrealKVBuilder]
    BUILDER --> INDX_B[IndexedDBBuilder]

    MEM_B --> MEM_S[(Memory)]
    ROCKS_B --> ROCKS_S[(RocksDB)]
    TIKV_B --> TIKV_S[(TiKV)]
    SKV_B --> SKV_S[(SurrealKV)]
    INDX_B --> INDX_S[(IndexedDB)]
```

---

## SDK API 方法

### 可用方法

```mermaid
graph LR
    subgraph CRUD["CRUD 操作"]
        SELECT[select]
        CREATE[create]
        INSERT[insert]
        UPDATE[update]
        UPSERT[upsert]
        DELETE[delete]
        MERGE[merge]
        PATCH[patch]
    end

    subgraph Query["查询"]
        QUERY[query]
        RUN[run]
    end

    subgraph Auth["认证"]
        SIGNIN[signin]
        SIGNUP[signup]
        AUTH[authenticate]
    end

    subgraph TX["事务"]
        BEGIN[begin]
        COMMIT[commit]
        CANCEL[cancel]
    end

    subgraph Util["工具"]
        VERSION[version]
        HEALTH[health]
        IMPORT[import]
        EXPORT[export]
    end
```

### 连接生命周期

```mermaid
stateDiagram-v2
    [*] --> Disconnected
    Disconnected --> Connecting: connect()
    Connecting --> Connected: success
    Connecting --> Disconnected: failure
    Connected --> Querying: query()
    Querying --> Connected: result
    Connected --> Disconnected: disconnect()
    Disconnected --> [*]
```

---

## 总结

### 架构亮点

1. **分层清晰** - SDK → Server → Core → Storage 各层职责明确
2. **高度可扩展** - Composer 模式、Trait 对象、Feature Flags
3. **性能优化** - 多层缓存、自适应批处理、向量索引
4. **实时能力** - WebSocket、Live Queries、事件驱动
5. **多存储支持** - 可插拔存储后端架构
6. **企业特性** - ACID 事务、RBAC、审计日志
7. **开发友好** - 多语言 SDK、GraphQL API、WebAssembly 支持

### 核心设计决策

```mermaid
mindmap
    root((SurrealDB))
        多模型
            文档
            图
            关系
            时序
            向量
        存储抽象
            可插拔后端
            MVCC 事务
            多层缓存
        实时
            Live Queries
            WebSocket
            Change Feed
        安全
            RBAC
            行级权限
            JWT 认证
        可扩展
            分布式 TiKV
            水平扩展
            多区域
```

---

## 参考资源

- [SurrealDB 官方文档](https://surrealdb.com/docs)
- [GitHub 仓库](https://github.com/surrealdb/surrealdb)
- [SurrealQL 语言参考](https://surrealdb.com/docs/surrealql)
