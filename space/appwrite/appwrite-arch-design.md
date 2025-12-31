# Appwrite 架构分析

## 概述

Appwrite 是一个开源的后端即服务（BaaS）平台，为 Web、移动和服务器端应用提供完整的后端解决方案。它使用 PHP 8.3+ 和 Swoole 异步运行时构建，采用事件驱动的微服务架构，支持多租户隔离。

## 系统架构总览

```mermaid
graph TB
    subgraph "客户端层"
        WEB[Web 应用]
        MOBILE[移动应用]
        SERVER[服务端应用]
    end

    subgraph "入口层"
        TRAEFIK[Traefik 反向代理]
    end

    subgraph "应用层"
        HTTP[HTTP API Server<br/>Swoole]
        REALTIME[Realtime Server<br/>WebSocket]
        GRAPHQL[GraphQL Endpoint]
    end

    subgraph "消息队列层"
        REDIS[(Redis<br/>消息队列/缓存)]
    end

    subgraph "Worker 层"
        W_FUNC[Functions Worker]
        W_DB[Database Worker]
        W_MAIL[Mails Worker]
        W_MSG[Messaging Worker]
        W_HOOK[Webhooks Worker]
        W_DEL[Deletes Worker]
        W_CERT[Certificates Worker]
        W_AUDIT[Audits Worker]
        W_STATS[Stats Worker]
        W_BUILD[Builds Worker]
        W_MIG[Migrations Worker]
    end

    subgraph "存储层"
        MARIADB[(MariaDB<br/>数据库)]
        STORAGE[对象存储<br/>Local/S3/DO Spaces]
    end

    subgraph "执行器层"
        EXECUTOR[Functions Executor<br/>容器运行时]
    end

    WEB --> TRAEFIK
    MOBILE --> TRAEFIK
    SERVER --> TRAEFIK

    TRAEFIK --> HTTP
    TRAEFIK --> REALTIME
    HTTP --> GRAPHQL

    HTTP --> REDIS
    REALTIME --> REDIS

    REDIS --> W_FUNC
    REDIS --> W_DB
    REDIS --> W_MAIL
    REDIS --> W_MSG
    REDIS --> W_HOOK
    REDIS --> W_DEL
    REDIS --> W_CERT
    REDIS --> W_AUDIT
    REDIS --> W_STATS
    REDIS --> W_BUILD
    REDIS --> W_MIG

    W_FUNC --> EXECUTOR
    W_BUILD --> EXECUTOR

    HTTP --> MARIADB
    HTTP --> STORAGE
    W_DB --> MARIADB
    W_DEL --> MARIADB
    W_DEL --> STORAGE
    W_BUILD --> STORAGE

    style HTTP fill:#4a90d9
    style REALTIME fill:#4a90d9
    style REDIS fill:#dc382d
    style MARIADB fill:#c0765a
```

## 目录结构

```
appwrite/
├── app/                          # 应用入口和控制器
│   ├── http.php                  # HTTP 服务器入口
│   ├── worker.php                # Worker 入口
│   ├── realtime.php              # WebSocket 服务器入口
│   ├── controllers/              # API 控制器
│   │   ├── api/                  # REST API 端点
│   │   │   ├── account.php       # 用户账户管理
│   │   │   ├── databases.php     # 数据库操作
│   │   │   ├── storage.php       # 文件存储
│   │   │   ├── functions.php     # 云函数
│   │   │   ├── messaging.php     # 消息推送
│   │   │   └── ...
│   │   └── console/              # 控制台 API
│   └── init/                     # 初始化配置
│       ├── constants.php         # 常量定义
│       ├── resources.php         # 依赖注入
│       ├── configs.php           # 配置加载
│       └── locales.php           # 国际化
├── src/Appwrite/                 # 核心业务逻辑
│   ├── Platform/                 # 平台模块
│   │   ├── Modules/              # 功能模块
│   │   ├── Workers/              # Worker 实现
│   │   └── Action.php            # 基础 Action 类
│   ├── Auth/                     # 认证授权
│   │   ├── OAuth2/               # OAuth2 提供商
│   │   └── MFA/                  # 多因素认证
│   ├── Event/                    # 事件系统
│   ├── Messaging/                # 消息传递
│   ├── GraphQL/                  # GraphQL 实现
│   └── Databases/                # 数据库层
├── public/                       # 静态资源
├── tests/                        # 测试套件
├── docs/                         # 文档
└── docker-compose.yml            # Docker 编排
```

## 核心组件详解

### 1. HTTP 服务器

HTTP 服务器基于 Swoole 异步运行时，提供高性能的请求处理能力。

```mermaid
graph LR
    subgraph "Swoole HTTP Server"
        MASTER[Master 进程]
        MANAGER[Manager 进程]
        W1[Worker 1]
        W2[Worker 2]
        W3[Worker N]
        TW1[Task Worker 1]
        TW2[Task Worker N]
    end

    REQUEST[HTTP 请求] --> MASTER
    MASTER --> MANAGER
    MANAGER --> W1
    MANAGER --> W2
    MANAGER --> W3
    W1 -.-> TW1
    W2 -.-> TW2
```

**关键配置** (`app/http.php:42-100`):
- Worker 数量 = CPU 核心数 × `_APP_WORKER_PER_CORE` (默认 6)
- 智能调度算法将"高风险"请求路由到专用 Worker
- 支持协程并发处理

### 2. 事件驱动系统

Appwrite 采用事件驱动架构，API 操作触发异步事件，由专门的 Worker 处理。

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant API as HTTP API
    participant Event as Event 系统
    participant Redis as Redis 队列
    participant Worker as Worker

    Client->>API: POST /databases/{db}/documents
    API->>API: 验证权限
    API->>API: 写入数据库
    API->>Event: 创建事件
    Event->>Redis: 入队 (v1-database)
    API-->>Client: 201 Created

    Redis->>Worker: 出队消息
    Worker->>Worker: 处理事件
    Note over Worker: 触发 Webhooks<br/>更新索引<br/>发送通知
```

**事件队列类型** (`src/Appwrite/Event/Event.php:12-46`):

| 队列名称 | Worker | 职责 |
|---------|--------|------|
| v1-database | DatabaseV1 | 数据库变更处理 |
| v1-deletes | DeletesV1 | 级联删除操作 |
| v1-audits | AuditsV1 | 审计日志记录 |
| v1-mails | MailsV1 | 邮件发送 |
| v1-functions | FunctionsV1 | 云函数执行 |
| v1-webhooks | WebhooksV1 | Webhook 回调 |
| v1-messaging | MessagingV1 | 消息推送 |
| v1-certificates | CertificatesV1 | SSL 证书管理 |
| v1-builds | BuildsV1 | 函数构建 |
| v1-stats-usage | StatsUsageV1 | 用量统计 |
| v1-migrations | MigrationsV1 | 数据迁移 |

### 3. 平台模块架构

```mermaid
graph TB
    subgraph "Appwrite Platform"
        PLATFORM[Platform Core]

        subgraph "Modules"
            CORE[Core Module]
            ACCOUNT[Account Module]
            DB[Databases Module]
            FUNC[Functions Module]
            STORE[Storage Module]
            MSG[Messaging Module]
            CONSOLE[Console Module]
            PROXY[Proxy Module]
        end

        subgraph "Actions"
            A1[REST Endpoints]
            A2[GraphQL Resolvers]
            A3[Worker Actions]
        end
    end

    PLATFORM --> CORE
    PLATFORM --> ACCOUNT
    PLATFORM --> DB
    PLATFORM --> FUNC
    PLATFORM --> STORE
    PLATFORM --> MSG
    PLATFORM --> CONSOLE
    PLATFORM --> PROXY

    CORE --> A1
    ACCOUNT --> A1
    DB --> A1
    DB --> A2
    FUNC --> A3
```

**模块职责**:
- **Core Module**: 基础路由和 API 框架
- **Account Module**: 用户认证、会话管理
- **Databases Module**: 数据库 CRUD 操作
- **Functions Module**: 云函数生命周期管理
- **Storage Module**: 文件上传、下载、管理
- **Messaging Module**: 推送通知、邮件、SMS
- **Console Module**: 管理控制台后端
- **Proxy Module**: 请求路由和代理

### 4. 多租户数据库架构

```mermaid
graph TB
    subgraph "Console 数据库"
        PLATFORM_DB[(Platform DB<br/>dbForPlatform)]
        PROJECTS[Projects 表]
        USERS[Users 表]
        TEAMS[Teams 表]
    end

    subgraph "项目数据库池"
        P1_DB[(Project 1 DB<br/>dbForProject)]
        P2_DB[(Project 2 DB<br/>dbForProject)]
        PN_DB[(Project N DB<br/>dbForProject)]
    end

    PLATFORM_DB --> PROJECTS
    PLATFORM_DB --> USERS
    PLATFORM_DB --> TEAMS

    PROJECTS --> P1_DB
    PROJECTS --> P2_DB
    PROJECTS --> PN_DB

    P1_DB --> |文档| DOC1[Collections]
    P1_DB --> |文件| FILE1[Buckets]
    P1_DB --> |函数| FUNC1[Functions]
```

**关键特性**:
- **dbForPlatform**: 系统级数据库，存储项目、用户、团队信息
- **dbForProject**: 每个项目独立的数据库，实现租户隔离
- **连接池**: 使用 `Utopia\Database\Adapter\Pool` 管理连接
- **事务支持**: `TransactionState` 类跟踪事务状态

**事务管理** (`src/Appwrite/Databases/TransactionState.php`):
- 支持 ACID 事务
- 操作类型: `create`, `update`, `upsert`, `delete`, `bulk`
- 限制: 每事务最多 100 操作，TTL 1-3600 秒
- 重放机制确保跨操作的事务可见性

### 5. 认证与授权

```mermaid
graph TB
    subgraph "认证方式"
        SESSION[Session 认证<br/>Cookie-based]
        APIKEY[API Key<br/>Server-to-Server]
        JWT[JWT Token<br/>无状态]
        OAUTH[OAuth2<br/>30+ 提供商]
        MFA[多因素认证<br/>TOTP/SMS]
    end

    subgraph "授权模型"
        RBAC[角色访问控制]
        PERM[文档级权限]
    end

    subgraph "角色类型"
        GUEST[guest]
        MEMBER[member]
        ADMIN[admin]
        OWNER[owner]
    end

    subgraph "权限操作"
        READ[read]
        CREATE[create]
        UPDATE[update]
        DELETE[delete]
    end

    SESSION --> RBAC
    APIKEY --> RBAC
    JWT --> RBAC
    OAUTH --> RBAC
    MFA --> RBAC

    RBAC --> GUEST
    RBAC --> MEMBER
    RBAC --> ADMIN
    RBAC --> OWNER

    PERM --> READ
    PERM --> CREATE
    PERM --> UPDATE
    PERM --> DELETE
```

**OAuth2 提供商** (`src/Appwrite/Auth/OAuth2/`):
- Google, GitHub, Discord, Twitter, Facebook
- LinkedIn, Twitch, Notion, Stripe, PayPal
- Apple, Microsoft, Spotify, Slack 等 30+ 个

**安全机制**:
- 密码哈希: Argon2, SHA
- 会话存储与验证
- CORS 验证: `src/Appwrite/Network/Cors.php`
- 来源验证: `src/Appwrite/Network/Validator/Origin.php`

### 6. 存储系统

```mermaid
graph LR
    subgraph "存储抽象层"
        STORAGE_API[Storage API]
    end

    subgraph "存储后端"
        LOCAL[Local<br/>本地文件系统]
        S3[AWS S3]
        DO[DigitalOcean Spaces]
        B2[Backblaze B2]
        LINODE[Linode Object Storage]
        WASABI[Wasabi]
    end

    subgraph "安全扫描"
        CLAMAV[ClamAV<br/>病毒扫描]
    end

    STORAGE_API --> LOCAL
    STORAGE_API --> S3
    STORAGE_API --> DO
    STORAGE_API --> B2
    STORAGE_API --> LINODE
    STORAGE_API --> WASABI

    STORAGE_API --> CLAMAV
```

**存储路径** (`app/init/constants.php:69-76`):
```
/storage/uploads      - 用户上传文件
/storage/sites        - 静态站点
/storage/functions    - 云函数代码
/storage/builds       - 构建产物
/storage/cache        - 缓存数据
/storage/imports      - 导入数据
/storage/certificates - SSL 证书
```

### 7. 实时系统

```mermaid
sequenceDiagram
    participant Client as WebSocket 客户端
    participant Realtime as Realtime Server
    participant Redis as Redis PubSub
    participant API as HTTP API
    participant Worker as Worker

    Client->>Realtime: 建立 WebSocket 连接
    Realtime->>Redis: 订阅频道

    API->>Worker: 触发事件
    Worker->>Redis: 发布消息
    Redis->>Realtime: 推送更新
    Realtime->>Client: 实时推送

    Note over Client,Realtime: 支持的事件:<br/>documents.*.create<br/>documents.*.update<br/>documents.*.delete<br/>files.*.create<br/>等
```

**组件**:
- Realtime Server: `app/realtime.php`
- Redis PubSub 适配器: `src/Appwrite/PubSub/Adapter/Redis.php`
- 消息适配器: `src/Appwrite/Messaging/Adapter/Realtime.php`

### 8. 云函数执行

```mermaid
graph TB
    subgraph "函数生命周期"
        DEPLOY[部署函数]
        BUILD[构建镜像]
        EXECUTE[执行函数]
    end

    subgraph "执行器"
        EXECUTOR[Functions Executor]
        RUNTIME[运行时容器]
    end

    subgraph "支持的运行时"
        NODE[Node.js]
        PYTHON[Python]
        PHP[PHP]
        RUBY[Ruby]
        DART[Dart]
        DENO[Deno]
        DOTNET[.NET]
        JAVA[Java]
        SWIFT[Swift]
        KOTLIN[Kotlin]
        BUN[Bun]
    end

    DEPLOY --> BUILD
    BUILD --> EXECUTOR
    EXECUTOR --> RUNTIME
    EXECUTE --> EXECUTOR

    RUNTIME --> NODE
    RUNTIME --> PYTHON
    RUNTIME --> PHP
    RUNTIME --> RUBY
    RUNTIME --> DART
    RUNTIME --> DENO
    RUNTIME --> DOTNET
    RUNTIME --> JAVA
    RUNTIME --> SWIFT
    RUNTIME --> KOTLIN
    RUNTIME --> BUN
```

**配置参数**:
- `_APP_EXECUTOR_HOST`: 执行器地址
- `_APP_FUNCTIONS_TIMEOUT`: 执行超时 (默认 900 秒)
- `_APP_COMPUTE_CPUS`: 可用 CPU 核心
- `_APP_COMPUTE_MEMORY`: 可用内存 (MB)

### 9. GraphQL 实现

```mermaid
graph LR
    subgraph "GraphQL 层"
        ENDPOINT[/graphql Endpoint]
        SCHEMA[Schema Generator]
        RESOLVER[Resolvers]
        VALIDATOR[Complexity Validator]
    end

    subgraph "数据源"
        REST[REST API Controllers]
        DB[Database]
    end

    ENDPOINT --> SCHEMA
    SCHEMA --> RESOLVER
    RESOLVER --> VALIDATOR
    RESOLVER --> REST
    REST --> DB
```

**特性** (`src/Appwrite/GraphQL/Schema.php`):
- 动态 Schema 生成
- 查询批处理
- 复杂度限制
- 与 REST API 共享业务逻辑

## 技术栈

### 核心框架

| 组件 | 技术 |
|-----|------|
| 语言 | PHP 8.3+ (严格类型) |
| 运行时 | Swoole 异步扩展 |
| Web 框架 | Utopia Framework |
| 数据库 | MariaDB / MySQL |
| 缓存/队列 | Redis |
| 反向代理 | Traefik |
| DNS | CoreDNS |

### Utopia 库生态

```mermaid
graph TB
    APPWRITE[Appwrite]

    subgraph "Utopia Libraries"
        U_HTTP[utopia-php/http]
        U_DB[utopia-php/database]
        U_QUEUE[utopia-php/queue]
        U_CACHE[utopia-php/cache]
        U_STORAGE[utopia-php/storage]
        U_MSG[utopia-php/messaging]
        U_WS[utopia-php/websocket]
        U_PLATFORM[utopia-php/platform]
    end

    APPWRITE --> U_HTTP
    APPWRITE --> U_DB
    APPWRITE --> U_QUEUE
    APPWRITE --> U_CACHE
    APPWRITE --> U_STORAGE
    APPWRITE --> U_MSG
    APPWRITE --> U_WS
    APPWRITE --> U_PLATFORM
```

### 第三方依赖

- `webonyx/graphql-php` - GraphQL 实现
- `phpmailer/phpmailer` - 邮件发送
- `adhocore/jwt` - JWT 令牌
- `chillerlan/php-qrcode` - 二维码生成

## Docker 部署架构

```mermaid
graph TB
    subgraph "Docker Compose Stack"
        subgraph "入口"
            TRAEFIK[traefik<br/>反向代理]
        end

        subgraph "应用"
            APPWRITE[appwrite<br/>PHP 8.3 + Swoole]
        end

        subgraph "数据存储"
            MARIADB[mariadb<br/>数据库]
            REDIS[redis<br/>缓存/队列]
        end

        subgraph "辅助服务"
            COREDNS[coredns<br/>内部 DNS]
            CLAMAV[clamav<br/>病毒扫描]
        end

        subgraph "数据卷"
            V1[appwrite-uploads]
            V2[appwrite-cache]
            V3[appwrite-functions]
            V4[appwrite-builds]
            V5[appwrite-certificates]
            V6[appwrite-config]
        end
    end

    TRAEFIK --> APPWRITE
    APPWRITE --> MARIADB
    APPWRITE --> REDIS
    APPWRITE --> COREDNS
    APPWRITE --> CLAMAV

    APPWRITE --> V1
    APPWRITE --> V2
    APPWRITE --> V3
    APPWRITE --> V4
    APPWRITE --> V5
    APPWRITE --> V6
```

**Dockerfile 多阶段构建**:
1. **Composer 阶段**: 依赖安装
2. **Base 阶段**: PHP 环境配置
3. **Production 阶段**: 生产优化镜像
4. **Development 阶段**: 开发调试工具

## 环境配置

### 核心配置项

```bash
# 应用配置
_APP_ENV=development
_APP_EDITION=self-hosted
_APP_VERSION=1.8.0
_APP_WORKER_PER_CORE=6

# 数据库
_APP_DB_HOST=mariadb
_APP_DB_PORT=3306
_APP_DB_USER=user
_APP_DB_PASS=password
_APP_DB_SCHEMA=appwrite

# Redis
_APP_REDIS_HOST=redis
_APP_REDIS_PORT=6379

# 存储
_APP_STORAGE_DEVICE=Local
_APP_STORAGE_S3_*=s3-credentials

# 函数执行
_APP_EXECUTOR_HOST=http://exc1/v1
_APP_FUNCTIONS_TIMEOUT=900
_APP_COMPUTE_CPUS=8
_APP_COMPUTE_MEMORY=8192

# 维护
_APP_MAINTENANCE_INTERVAL=86400
_APP_MAINTENANCE_RETENTION_EXECUTION=1209600
```

## 设计模式

### 1. 事件驱动架构
- API 操作触发异步事件
- 事件入队到 Redis
- Worker 异步处理

### 2. 依赖注入 / 服务定位器
- Utopia 框架提供全局资源注册
- 资源注入到控制器和 Worker
- 位置: `app/init/resources.php`

### 3. 模块化组织
- 每个功能区域是独立模块
- 模块通过 Utopia Platform 框架实现
- 位置: `src/Appwrite/Platform/Modules/`

### 4. Action 模式
- Worker 继承 Action 基类
- 单一 `action()` 方法处理队列消息
- 位置: `src/Appwrite/Platform/Action.php`

### 5. 文档模型
- 所有数据表示为 Document 对象
- 支持元数据、属性、权限
- 来自 Utopia Database 库

## 关键文件索引

| 组件 | 文件路径 |
|-----|---------|
| 平台架构 | `src/Appwrite/Platform/Appwrite.php` |
| HTTP 服务器 | `app/http.php` |
| Worker 系统 | `app/worker.php` |
| 实时服务器 | `app/realtime.php` |
| 事件基础系统 | `src/Appwrite/Event/Event.php` |
| 数据库事务 | `src/Appwrite/Databases/TransactionState.php` |
| 用户认证 | `app/controllers/api/account.php` |
| 平台 Action 基类 | `src/Appwrite/Platform/Action.php` |
| 资源注入 | `app/init/resources.php` |
| 常量定义 | `app/init/constants.php` |
| 函数 Worker | `src/Appwrite/Platform/Workers/Functions.php` |
| PubSub 系统 | `src/Appwrite/PubSub/Adapter.php` |
| GraphQL Schema | `src/Appwrite/GraphQL/Schema.php` |

## 总结

Appwrite 是一个设计精良的后端即服务平台，其架构具有以下特点：

1. **高性能**: 基于 Swoole 异步运行时，支持高并发请求处理
2. **可扩展**: 模块化设计，易于添加新功能
3. **多租户**: 每个项目独立数据库，实现完全隔离
4. **事件驱动**: 异步处理提高响应速度和系统吞吐量
5. **安全性**: 完善的认证授权机制，支持多种认证方式
6. **可观测**: 完整的审计日志和统计系统
7. **云原生**: 容器化部署，易于扩展和运维

这种架构使 Appwrite 能够作为一个完整的后端解决方案，支持从小型项目到企业级应用的各种场景。
