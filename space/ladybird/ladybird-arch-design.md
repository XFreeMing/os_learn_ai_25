# Ladybird 浏览器架构分析

## 概述

Ladybird 是一个全新的独立 Web 浏览器，最初从 SerenityOS 项目中分离出来。它采用现代化的多进程架构设计，拥有自研的渲染引擎、JavaScript 引擎以及完整的网络协议栈。

## 目录结构

```
ladybird/
├── AK/                    # AsterKernel 基础库（数据结构、工具类）
├── Libraries/             # 32 个核心库
│   ├── LibWeb/           # HTML/CSS 渲染引擎
│   ├── LibJS/            # JavaScript 引擎
│   ├── LibGfx/           # 2D 图形和图像编解码
│   ├── LibCore/          # 操作系统抽象层
│   ├── LibIPC/           # 进程间通信
│   ├── LibWebView/       # UI 与 WebContent 桥接层
│   ├── LibHTTP/          # HTTP 协议实现
│   ├── LibTLS/           # TLS/SSL 安全层
│   └── ...               # 其他支持库
├── Services/              # 独立进程服务
│   ├── WebContent/       # Web 内容渲染服务
│   ├── RequestServer/    # 网络请求服务
│   ├── ImageDecoder/     # 图像解码服务
│   └── WebWorker/        # Web Worker 服务
├── UI/                    # 用户界面层
│   ├── Qt/               # Qt 跨平台实现
│   ├── AppKit/           # macOS 原生实现
│   └── Android/          # Android 实现
├── Meta/                  # 构建系统和代码生成
└── Tests/                 # 测试套件
```

## 多进程架构

Ladybird 采用现代浏览器的多进程架构，通过进程隔离提供安全性和稳定性。

```mermaid
flowchart TB
    subgraph Browser["Browser Process (UI)"]
        UI[用户界面]
        TabManager[标签管理器]
        WebView[WebContentView]
    end

    subgraph WebContent1["WebContent Process (Tab 1)"]
        DOM1[DOM 树]
        CSS1[样式计算]
        Layout1[布局引擎]
        Paint1[渲染管线]
        JS1[JavaScript VM]
    end

    subgraph WebContent2["WebContent Process (Tab 2)"]
        DOM2[DOM 树]
        CSS2[样式计算]
        Layout2[布局引擎]
        Paint2[渲染管线]
        JS2[JavaScript VM]
    end

    subgraph RequestServer["RequestServer Process"]
        HTTP[HTTP/HTTPS 客户端]
        Cache[磁盘缓存]
        Cookie[Cookie 管理]
    end

    subgraph ImageDecoder["ImageDecoder Process"]
        Decoder[图像解码器]
        PNG[PNG]
        JPEG[JPEG]
        WebP[WebP]
    end

    UI --> TabManager
    TabManager --> WebView
    WebView <-->|IPC Socket| WebContent1
    WebView <-->|IPC Socket| WebContent2
    WebContent1 <-->|IPC| RequestServer
    WebContent2 <-->|IPC| RequestServer
    WebContent1 <-->|IPC| ImageDecoder
    WebContent2 <-->|IPC| ImageDecoder
    RequestServer --> HTTP
    HTTP --> Cache
    HTTP --> Cookie
```

### 进程职责

| 进程类型 | 入口点 | 职责 |
|---------|--------|------|
| **Browser Process** | `UI/Qt/main.cpp` | GUI 管理、标签控制、用户交互 |
| **WebContent Process** | `Services/WebContent/main.cpp` | HTML 解析、CSS 渲染、JS 执行 |
| **RequestServer** | `Services/RequestServer/main.cpp` | HTTP/HTTPS 请求、缓存、Cookie |
| **ImageDecoder** | `Services/ImageDecoder/main.cpp` | 图像解码（PNG、JPEG、WebP 等） |
| **WebWorker** | `Services/WebWorker/main.cpp` | Web Worker 执行环境 |

## 核心库依赖层次

```mermaid
flowchart BT
    subgraph Tier1["Tier 1: 基础层"]
        AK[AK 基础库]
        LibCore[LibCore]
        LibIPC[LibIPC]
    end

    subgraph Tier2["Tier 2: 图形层"]
        LibGfx[LibGfx]
        LibGC[LibGC]
    end

    subgraph Tier3["Tier 3: 工具层"]
        LibUnicode[LibUnicode]
        LibTextCodec[LibTextCodec]
        LibRegex[LibRegex]
        LibCompress[LibCompress]
    end

    subgraph Tier4["Tier 4: 网络层"]
        LibURL[LibURL]
        LibHTTP[LibHTTP]
        LibTLS[LibTLS]
        LibCrypto[LibCrypto]
        LibDNS[LibDNS]
    end

    subgraph Tier5["Tier 5: 脚本层"]
        LibJS[LibJS]
        LibWasm[LibWasm]
    end

    subgraph Tier6["Tier 6: 渲染层"]
        LibWeb[LibWeb]
    end

    subgraph Tier7["Tier 7: 桥接层"]
        LibWebView[LibWebView]
    end

    subgraph Tier8["Tier 8: 服务层"]
        Services[Services]
    end

    subgraph Tier9["Tier 9: UI 层"]
        UILayer[UI]
    end

    Tier2 --> Tier1
    Tier3 --> Tier1
    Tier4 --> Tier1
    Tier5 --> Tier1
    Tier5 --> Tier2
    Tier5 --> Tier3
    Tier6 --> Tier5
    Tier6 --> Tier4
    Tier6 --> Tier3
    Tier6 --> Tier2
    Tier7 --> Tier6
    Tier8 --> Tier7
    Tier9 --> Tier8
```

## LibWeb 渲染引擎

LibWeb 是 Ladybird 的核心渲染引擎，包含 90+ 子目录和 2800+ 源文件。

### 主要组件

```mermaid
flowchart LR
    subgraph LibWeb["LibWeb 渲染引擎"]
        subgraph Parsing["解析层"]
            HTMLTokenizer[HTML Tokenizer]
            HTMLParser[HTML Parser]
            CSSParser[CSS Parser]
        end

        subgraph DOM["DOM 层"]
            Document[Document]
            Element[Element]
            Node[Node]
        end

        subgraph Style["样式层"]
            StyleComputer[StyleComputer]
            Cascade[级联计算]
            ComputedValues[计算值]
        end

        subgraph Layout["布局层"]
            BFC[块格式化上下文]
            IFC[内联格式化上下文]
            FFC[弹性盒上下文]
            TFC[表格格式化上下文]
        end

        subgraph Paint["绘制层"]
            DisplayList[DisplayList]
            Paintable[Paintable Tree]
            Skia[Skia 后端]
        end
    end

    HTMLTokenizer --> HTMLParser
    HTMLParser --> DOM
    CSSParser --> Style
    DOM --> Style
    Style --> Layout
    Layout --> Paint
```

### 渲染管线详解

```mermaid
sequenceDiagram
    participant HTML as HTML 文档
    participant Tokenizer as HTMLTokenizer
    participant Parser as HTMLParser
    participant DOM as DOM 树
    participant Style as StyleComputer
    participant Layout as FormattingContext
    participant DL as DisplayListRecorder
    participant Skia as Skia 渲染器

    HTML->>Tokenizer: 原始字节流
    Tokenizer->>Parser: Token 流
    Parser->>DOM: 构建 DOM 树
    DOM->>Style: 遍历节点
    Style->>Style: CSS 级联计算
    Style->>Layout: 带样式的节点
    Layout->>Layout: 盒模型计算
    Layout->>DL: 生成绘制指令
    DL->>Skia: DisplayList 回放
    Skia-->>HTML: 位图输出
```

## LibJS JavaScript 引擎

LibJS 是完整的 ECMAScript 引擎实现，包含 1500+ 源文件。

```mermaid
flowchart TB
    subgraph LibJS["LibJS JavaScript 引擎"]
        Lexer[词法分析器]
        Parser[语法分析器]
        AST[抽象语法树]
        Bytecode[字节码编译器]
        Interpreter[字节码解释器]

        subgraph Runtime["运行时"]
            Heap[堆内存]
            GC[垃圾回收器]
            VM[虚拟机]
            Realm[Realm 域]
        end

        subgraph Builtins["内置对象"]
            Object[Object]
            Array[Array]
            Promise[Promise]
            Map[Map/Set]
        end
    end

    Lexer --> Parser
    Parser --> AST
    AST --> Bytecode
    Bytecode --> Interpreter
    Interpreter --> Runtime
    Runtime --> Builtins
```

### 执行模型

```mermaid
flowchart LR
    subgraph Context["执行上下文栈"]
        Global[全局上下文]
        Func1[函数上下文 1]
        Func2[函数上下文 2]
    end

    subgraph Agent["代理 (Agent)"]
        MainThread[主线程 VM]
        WorkerAgent[Worker 代理]
    end

    subgraph Realm["Realm 域"]
        GlobalObject[全局对象]
        Bindings[WebIDL 绑定]
    end

    Context --> Agent
    Agent --> Realm
```

## IPC 通信机制

Ladybird 使用自定义的 IPC 协议进行进程间通信。

```mermaid
sequenceDiagram
    participant Browser as Browser Process
    participant WC as WebContent Process
    participant RS as RequestServer
    participant ID as ImageDecoder

    Browser->>WC: load_url("https://example.com")
    WC->>RS: start_request(url)
    RS->>RS: HTTP GET
    RS-->>WC: response_data
    WC->>WC: 解析 HTML
    WC->>ID: decode_image(png_data)
    ID->>ID: 解码 PNG
    ID-->>WC: Bitmap
    WC->>WC: 布局和绘制
    WC-->>Browser: did_paint(backing_store)
```

### IPC 协议文件

关键的 `.ipc` 定义文件：

| 文件 | 用途 |
|------|------|
| `WebContentServer.ipc` | Browser → WebContent 命令 |
| `WebContentClient.ipc` | WebContent → Browser 回调 |
| `RequestClient.ipc` | WebContent → RequestServer 请求 |
| `ImageDecoderClient.ipc` | WebContent → ImageDecoder 解码请求 |

## 平台抽象层

```mermaid
flowchart TB
    subgraph Platform["平台抽象"]
        EventLoop[EventLoopPlugin]
        Font[FontPlugin]
        Image[ImageCodecPlugin]
        Timer[TimerPlugin]
    end

    subgraph Unix["Unix 实现"]
        UnixLoop[EventLoopImplementationUnix]
        UnixFont[系统字体加载]
    end

    subgraph Windows["Windows 实现"]
        WinLoop[EventLoopImplementationWindows]
        WinFont[DirectWrite]
    end

    subgraph Qt["Qt 集成"]
        QtLoop[EventLoopImplementationQt]
        QtIntegration[Qt6 Framework]
    end

    Platform --> Unix
    Platform --> Windows
    Platform --> Qt
```

## 安全模型

Ladybird 采用多层次安全架构：

```mermaid
flowchart TB
    subgraph Security["安全层次"]
        subgraph L1["层 1: 进程隔离"]
            Tab1[Tab 1 进程]
            Tab2[Tab 2 进程]
        end

        subgraph L2["层 2: 网络隔离"]
            RS[RequestServer 网关]
        end

        subgraph L3["层 3: 媒体隔离"]
            ID[ImageDecoder 沙箱]
        end

        subgraph L4["层 4: 权限分离"]
            Priv[特权 Browser 进程]
            Unpriv[非特权 WebContent]
        end
    end
```

### 安全特性

1. **进程隔离**: 每个标签页运行在独立进程中
2. **网络网关**: 所有网络请求通过 RequestServer 代理
3. **图像解码沙箱**: 不受信任的图像在隔离进程中解码
4. **权限分离**: 辅助进程以低权限用户运行
5. **站点隔离**: 支持按站点隔离渲染进程

## 内存管理

### 垃圾回收器 (LibGC)

```mermaid
flowchart LR
    subgraph GC["LibGC 垃圾回收"]
        Heap[GC 堆]
        Roots[根集合]
        Mark[标记阶段]
        Sweep[清扫阶段]
    end

    subgraph Pointers["智能指针"]
        GCRef["GC::Ref<T>"]
        GCPtr["GC::Ptr<T>"]
        RefPtr["RefPtr<T>"]
        OwnPtr["OwnPtr<T>"]
    end

    Roots --> Mark
    Mark --> Sweep
    Sweep --> Heap
```

### 指针类型

| 类型 | 用途 |
|------|------|
| `GC::Ref<T>` | GC 管理的引用（非空） |
| `GC::Ptr<T>` | GC 管理的指针（可空） |
| `RefPtr<T>` | 引用计数智能指针 |
| `NonnullRefPtr<T>` | 非空引用计数指针 |
| `OwnPtr<T>` | 独占所有权指针 |
| `WeakPtr<T>` | 弱引用指针 |

## 错误处理模式

Ladybird 使用类似 Rust 的错误处理模式：

```cpp
// ErrorOr<T> 返回类型
ErrorOr<NonnullRefPtr<Document>> Document::create(...)
{
    auto document = TRY(adopt_ref(...));
    return document;
}

// TRY 宏自动传播错误
auto result = TRY(some_fallible_operation());

// MUST 宏断言成功
auto value = MUST(operation_that_must_succeed());
```

## 构建系统

```mermaid
flowchart LR
    subgraph Build["构建系统"]
        CMake[CMake 3.25+]
        Presets[CMakePresets.json]
        vcpkg[vcpkg 包管理]
    end

    subgraph CodeGen["代码生成"]
        IDL[WebIDL 编译器]
        CSS[CSS 属性生成器]
        IPC[IPC 协议编译器]
    end

    subgraph Platform["目标平台"]
        Linux[Linux]
        macOS[macOS]
        Windows[Windows/WSL2]
        Android[Android]
    end

    CMake --> CodeGen
    vcpkg --> CMake
    CMake --> Platform
```

## 关键文件索引

### 入口点

| 文件 | 描述 |
|------|------|
| `UI/Qt/main.cpp` | Browser 进程入口 |
| `Services/WebContent/main.cpp` | WebContent 进程入口 |
| `Services/RequestServer/main.cpp` | RequestServer 进程入口 |
| `Services/ImageDecoder/main.cpp` | ImageDecoder 进程入口 |

### 核心接口

| 文件 | 描述 |
|------|------|
| `Libraries/LibWebView/ViewImplementation.h` | 视图抽象接口 |
| `Libraries/LibWebView/WebContentClient.h` | IPC 客户端 |
| `Libraries/LibWeb/Page/Page.h` | 网页表示 |
| `Libraries/LibWeb/DOM/Node.h` | DOM 节点基类 |
| `Libraries/LibWeb/CSS/StyleComputer.h` | 样式级联计算 |
| `Libraries/LibWeb/Layout/FormattingContext.h` | 布局算法 |
| `Libraries/LibJS/Runtime/VM.h` | JavaScript 虚拟机 |

## 与其他浏览器架构对比

```mermaid
flowchart TB
    subgraph Ladybird["Ladybird"]
        LWeb[LibWeb]
        LJS[LibJS]
        LGfx[Skia]
    end

    subgraph Chromium["Chromium"]
        Blink[Blink]
        V8[V8]
        Skia1[Skia]
    end

    subgraph Firefox["Firefox"]
        Gecko[Gecko]
        Spider[SpiderMonkey]
        WebRender[WebRender]
    end

    subgraph WebKit["WebKit"]
        WCore[WebCore]
        JSC[JavaScriptCore]
        CoreGraphics[CoreGraphics]
    end
```

| 特性 | Ladybird | Chromium | Firefox | Safari |
|------|----------|----------|---------|--------|
| 渲染引擎 | LibWeb | Blink | Gecko | WebCore |
| JS 引擎 | LibJS | V8 | SpiderMonkey | JavaScriptCore |
| 图形后端 | Skia | Skia | WebRender | CoreGraphics |
| 进程模型 | 多进程 | 多进程 | 多进程 | 多进程 |
| 代码库 | 全新独立 | WebKit 分支 | 自研 | KHTML 演进 |

## 总结

Ladybird 是一个现代化的、完全独立的 Web 浏览器实现，具有以下特点：

1. **规范驱动**: 严格遵循 W3C/WHATWG 规范
2. **安全优先**: 多进程沙箱架构
3. **模块化设计**: 32 个独立库，职责清晰
4. **跨平台**: 支持 Linux、macOS、Windows、Android
5. **现代 C++**: 使用 C++23，自研基础库
6. **性能导向**: Display List 渲染、增量布局

该项目展示了从零构建现代 Web 浏览器的可行性，是学习浏览器内核的优秀资源。
