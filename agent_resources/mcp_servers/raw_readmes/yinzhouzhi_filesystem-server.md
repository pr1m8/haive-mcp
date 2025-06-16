# MCP文件系统服务器

[![版本](https://img.shields.io/npm/v/@yinzhouzhi/mcp-filesystem-server.svg)](https://www.npmjs.com/package/@yinzhouzhi/mcp-filesystem-server)
[![许可证](https://img.shields.io/npm/l/@yinzhouzhi/mcp-filesystem-server.svg)](https://github.com/yinzhouzhi/mcp-filesystem-server/blob/main/LICENSE)
[![node版本](https://img.shields.io/node/v/@yinzhouzhi/mcp-filesystem-server.svg)](https://www.npmjs.com/package/@yinzhouzhi/mcp-filesystem-server)

基于Model Context Protocol（MCP）的文件系统操作服务器，提供对本地文件系统的访问和操作能力。

## 目录

- [功能特性](#功能特性)
- [安装](#安装)
- [命令行使用](#命令行使用)
- [编程方式使用](#编程方式使用)
- [可用工具](#可用工具)
  - [文件操作](#文件操作)
  - [Office文件操作](#office文件操作)
  - [目录操作](#目录操作)
  - [行操作](#行操作)
  - [监控工具](#监控工具)
  - [系统工具](#系统工具)
- [用法示例](#用法示例)
- [性能优化](#性能优化)
- [监控器管理池](#监控器管理池)
- [许可证](#许可证)

## 功能特性

- ✅ 基于MCP SDK实现，符合MCP规范
- 📂 提供完整的文件操作能力：读写、复制、移动、删除等
- 📁 支持目录操作：创建、删除、列表等
- 📝 支持文件内容行级操作：读写特定行、搜索内容等
- 👀 支持文件监控：监听文件和目录变更
- 🔄 通过标准输入/输出（stdio）通信，易于集成
- 🛠️ 包含命令行工具，方便直接使用
- 📊 高性能设计：缓存机制、流处理、异步操作

## Cursor

```bash
{
    "mcpServers": {
        "filesystem": {
          "command": "npx",
          "args": [
            "-y",
            "@yinzhouzhi/mcp-filesystem-server",
            "start"
          ],
          "autoConnect": true
        },
    }
}
```

## 安装

```bash
# 全局安装
npm install -g @yinzhouzhi/mcp-filesystem-server

# 或者局部安装到项目
npm install --save @yinzhouzhi/mcp-filesystem-server

# 无需安装，直接通过npx使用
npx @yinzhouzhi/mcp-filesystem-server <命令>
```

## 命令行使用

### 基本命令

```bash
# 启动服务器
mcp-filesystem-server start

# 查看帮助
mcp-filesystem-server --help

# 列出所有可用工具
mcp-filesystem-server list-tools

# 查看连接示例
mcp-filesystem-server example
```

### 使用npx（无需安装）

```bash
# 启动服务器
npx @yinzhouzhi/mcp-filesystem-server start

# 查看帮助
npx @yinzhouzhi/mcp-filesystem-server --help

# 列出所有可用工具
npx @yinzhouzhi/mcp-filesystem-server list-tools
```

### 启动选项

```
Options:
  -d, --debug              启用调试模式
  -l, --log-level <level>  设置日志级别 (debug, info, warn, error) (默认: "info")
  -p, --log-path <path>    设置日志文件路径 (默认: 当前目录下的logs文件夹)
  -r, --rotation-type <type> 设置日志轮转类型 (size, daily, weekly, monthly) (默认: "size")
  -s, --max-size <size>    设置日志文件最大大小 (如 10MB) (默认: 10MB)
  -f, --max-files <num>    设置保留的轮转日志文件数量 (默认: 5)
  --no-rotate              禁用日志轮转
  --no-compress            禁用轮转日志压缩
  -h, --help               显示帮助信息
```

## 编程方式使用

### 作为服务器启动

```javascript
const { startServer } = require("@yinzhouzhi/mcp-filesystem-server");

// 启动服务器
startServer({
  debug: true,
  logLevel: "debug",
  logPath: "./logs/server.log",
  // 日志轮转配置
  rotateLogFiles: true, // 是否启用日志轮转
  rotationType: "daily", // 轮转类型: 'size', 'daily', 'weekly', 'monthly'
  maxLogFileSize: 20 * 1024 * 1024, // 按大小轮转时的最大文件大小 (20MB)
  maxLogFiles: 10, // 保留的轮转日志文件数量
  compressRotatedLogs: true, // 是否压缩轮转后的日志文件
})
  .then((result) => {
    console.log("服务器启动成功:", result);
  })
  .catch((err) => {
    console.error("服务器启动失败:", err);
  });
```

### 连接到MCP服务器

```javascript
const { McpClient } = require("@modelcontextprotocol/sdk/client/mcp.js");
const {
  StdioClientTransport,
} = require("@modelcontextprotocol/sdk/client/stdio.js");
const { spawn } = require("child_process");

async function connectToMcpServer() {
  // 启动MCP服务器进程
  const serverProcess = spawn("mcp-filesystem-server", ["start"], {
    stdio: ["pipe", "pipe", "pipe"],
  });

  // 创建STDIO传输
  const transport = new StdioClientTransport({
    input: serverProcess.stdout,
    output: serverProcess.stdin,
    error: serverProcess.stderr,
  });

  // 创建客户端
  const client = new McpClient();
  await client.connect(transport);

  // 调用工具示例
  const result = await client.invokeTool("read_file", {
    path: "./example.txt",
    encoding: "utf8",
  });

  console.log("文件内容:", result);

  // 关闭连接
  await client.disconnect();
  serverProcess.kill();
}

connectToMcpServer().catch(console.error);
```

### 通过npx连接到MCP服务器

```javascript
const { spawn } = require("child_process");
const { McpClient } = require("@modelcontextprotocol/sdk/client/mcp.js");
const {
  StdioClientTransport,
} = require("@modelcontextprotocol/sdk/client/stdio.js");

async function connectWithNpx() {
  // 使用npx启动MCP服务器
  const serverProcess = spawn(
    "npx",
    ["@yinzhouzhi/mcp-filesystem-server", "start"],
    {
      stdio: ["pipe", "pipe", "pipe"],
    },
  );

  // 创建STDIO传输
  const transport = new StdioClientTransport({
    input: serverProcess.stdout,
    output: serverProcess.stdin,
    error: serverProcess.stderr,
  });

  // 创建客户端并连接
  const client = new McpClient();
  await client.connect(transport);

  // 调用MCP工具
  const result = await client.invokeTool("read_file", {
    path: "./example.txt",
    encoding: "utf8",
  });

  console.log("文件内容:", result);

  // 关闭连接
  await client.disconnect();
  serverProcess.kill();
}

connectWithNpx().catch(console.error);
```

## 可用工具

服务器提供以下MCP工具：

### 文件操作

| 工具名称        | 描述             | 主要参数                               |
| --------------- | ---------------- | -------------------------------------- |
| `read_file`     | 读取文件内容     | path, encoding                         |
| `write_file`    | 写入文件内容     | path, content, encoding                |
| `append_file`   | 追加文件内容     | path, content, encoding                |
| `delete_file`   | 删除文件         | path                                   |
| `copy_file`     | 复制文件         | sourcePath, destinationPath, overwrite |
| `move_file`     | 移动文件         | sourcePath, destinationPath, overwrite |
| `get_file_info` | 获取文件信息     | path                                   |
| `file_exists`   | 检查文件是否存在 | path                                   |

### Office文件操作

#### `read_word_document`

读取Word文档内容并转换为文本（支持.doc和.docx格式）

**参数：**

- `path`: Word文件路径(.doc或.docx格式)【必需】
- `outputFormat`: 输出格式，支持'text'和'html'，默认'text'
- `extractImages`: 是否提取图片信息，默认false
- `includeStyles`: 是否包含样式信息，默认false
- `pagination`: 分页参数，用于大文档分页读取，格式如：`{pageSize: 1000, pageNum: 1}`
- `range`: 读取范围，指定起始行和结束行，格式如：`{startLine: 1, endLine: 100}`
- `splitByParagraphs`: 是否按段落拆分返回，默认false

#### `read_excel_file`

读取Excel文件内容（支持.xlsx、.xls和.csv格式）

**参数：**

- `path`: Excel文件路径(.xlsx、.xls或.csv格式)【必需】
- `sheet`: 工作表名称或索引(从0开始)，默认读取第一个工作表
- `outputFormat`: 输出格式，支持'json'、'csv'和'array'，默认'array'
- `range`: 读取范围，例如`{startRow:1, endRow:10, startCol:1, endCol:5}`
- `includeFormulas`: 是否包含公式，默认false
- `headerRow`: 是否将第一行作为表头，默认false

### 目录操作

| 工具名称           | 描述             | 主要参数                 |
| ------------------ | ---------------- | ------------------------ |
| `list_directory`   | 列出目录内容     | path, recursive, pattern |
| `create_directory` | 创建目录         | path, recursive          |
| `remove_directory` | 删除目录         | path, recursive, force   |
| `directory_exists` | 检查目录是否存在 | path                     |

### 行操作

| 工具名称              | 描述           | 主要参数                               |
| --------------------- | -------------- | -------------------------------------- |
| `read_lines`          | 读取文件指定行 | path, startLine, endLine, encoding     |
| `write_lines`         | 写入文件指定行 | path, lineNumber, content, encoding    |
| `insert_line`         | 插入行         | path, lineNumber, content, encoding    |
| `delete_lines`        | 删除行         | path, startLine, endLine, encoding     |
| `search_file_content` | 搜索文件内容   | path, searchTerm, regex, caseSensitive |

### 监控工具

| 工具名称        | 描述               | 主要参数                |
| --------------- | ------------------ | ----------------------- |
| `watch_path`    | 监控文件或目录变更 | path, recursive, events |
| `stop_watch`    | 停止监控           | watcherId               |
| `list_watchers` | 列出所有监控       | -                       |

### 系统工具

| 工具名称            | 描述           | 主要参数     |
| ------------------- | -------------- | ------------ |
| `get_server_status` | 获取服务器状态 | includeStats |

## 用法示例

### 文件读写

```javascript
// 读取文件
const content = await client.invokeTool("read_file", {
  path: "./example.txt",
  encoding: "utf8",
});

// 写入文件
await client.invokeTool("write_file", {
  path: "./output.txt",
  content: "这是文件内容",
  encoding: "utf8",
});

// 追加内容
await client.invokeTool("append_file", {
  path: "./log.txt",
  content: "新的日志条目\n",
  encoding: "utf8",
});
```

### 按行操作

```javascript
// 读取特定行
const lines = await client.invokeTool("read_lines", {
  path: "./data.txt",
  startLine: 10,
  endLine: 20,
});

// 插入一行
await client.invokeTool("insert_line", {
  path: "./config.txt",
  lineNumber: 5,
  content: "new_setting=value",
});

// 删除多行
await client.invokeTool("delete_lines", {
  path: "./log.txt",
  startLine: 100,
  endLine: 200,
});
```

### 文件与目录管理

```javascript
// 复制文件
await client.invokeTool("copy_file", {
  sourcePath: "./original.txt",
  destinationPath: "./backup/copy.txt",
  overwrite: true,
});

// 创建目录
await client.invokeTool("create_directory", {
  path: "./data/reports/2023",
  recursive: true,
});

// 列出目录内容
const files = await client.invokeTool("list_directory", {
  path: "./documents",
  recursive: true,
  pattern: "*.pdf",
});
```

### 监控文件变化

```javascript
// 开始监控
const watcherId = await client.invokeTool("watch_path", {
  path: "./config",
  recursive: true,
  events: "change,add,unlink",
});

// 列出所有监控
const watchers = await client.invokeTool("list_watchers");

// 停止监控
await client.invokeTool("stop_watch", {
  watcherId: watcherId,
});
```

## 性能优化

文件系统服务器实现了多项性能优化，确保高吞吐量和低延迟：

### 文件操作性能优化

1. **文件缓存**

   - 小型文件内容缓存，减少频繁IO操作
   - 可配置缓存大小和过期时间
   - 智能LRU（最近最少使用）清理策略

2. **流式处理**

   - 大文件自动使用流处理，降低内存占用
   - 可配置流处理的文件大小阈值
   - 支持读取、写入、追加和复制操作

3. **异步操作**
   - 文件压缩/解压采用异步流式处理
   - 日志轮转采用异步压缩
   - 大型目录操作采用优化的算法

### 目录操作性能优化

1. **目录内容缓存**

   - 缓存目录列表结果，减少频繁读取
   - 智能缓存失效机制，确保数据一致性
   - 可配置缓存大小和生命周期

2. **递归操作优化**
   - 优化递归列表和删除操作
   - 减少文件系统调用次数
   - 平衡内存使用和性能

### 日志系统优化

1. **日志缓冲区**

   - 使用内存缓冲区合并写入操作
   - 减少磁盘IO次数，提高性能
   - 可配置缓冲区大小和刷新间隔

2. **日志轮转优化**
   - 异步压缩轮转日志文件
   - 智能检查间隔，减少不必要的文件检查
   - 压缩队列处理，防止IO阻塞

### 性能配置示例

在`defaults.js`中可以自定义以下性能相关配置：

```javascript
// 文件操作配置
const fileOperations = {
  // 文件缓存配置
  fileCache: {
    enabled: true, // 是否启用文件缓存
    maxSize: 100, // 最大缓存文件数
    maxAge: 60000, // 缓存有效期 (ms)
  },
  // 流处理阈值（字节）
  streamThresholds: {
    read: 10 * 1024 * 1024, // 10MB以上使用流读取
    write: 5 * 1024 * 1024, // 5MB以上使用流写入
    append: 1 * 1024 * 1024, // 1MB以上使用流追加
    copy: 10 * 1024 * 1024, // 10MB以上使用流复制
  },
  // 压缩选项
  compression: {
    defaultLevel: 6, // 默认压缩级别 (1-9)
    useForLogs: true, // 是否为日志启用压缩
  },
};

// 日志配置
const loggerConfig = {
  // ...基本配置...

  // 性能优化相关
  useBuffer: true, // 使用缓冲区
  bufferSize: 64 * 1024, // 缓冲区大小 (64KB)
  flushInterval: 1000, // 缓冲区刷新间隔 (ms)
  asyncCompression: true, // 异步压缩
  checkRotationInterval: 60000, // 日志轮转检查间隔 (ms)
};
```

## 监控器管理池

文件系统服务器使用监控器管理池来控制和管理系统中的文件和目录监控器数量，防止资源泄漏。

### 主要功能

- **资源限制控制**：限制系统中监控器的总数量、每个路径的监控器数量和每个进程的监控器数量
- **自动资源回收**：定期清理长时间未使用的监控器，确保系统资源不被浪费
- **智能资源管理**：当达到系统限制时，移除最旧的监控器腾出空间
- **统计和监控**：提供完整的监控器使用统计信息

### 配置选项

```javascript
// 在 src/config/defaults.js 中配置
const watchPool = {
  maxWatchers: 200, // 最大监控器数量
  maxPerPath: 5, // 每个路径的最大监控器数量
  maxPerProcess: 50, // 每个进程的最大监控器数量
  cleanupInterval: 3600000, // 清理间隔 (1小时)
  maxIdleTime: 7200000, // 最大闲置时间 (2小时)
};
```

### 监控池API示例

```javascript
// 导入监控工具模块
const watchTools = require("./src/tools/watch-tools");

// 设置文件变更监控
const watcher = watchTools.setFileChangeCallback(
  "/path/to/file.txt",
  (event, path) => {
    console.log(`文件 ${path} 发生事件: ${event}`);
  },
);

// 设置目录变更监控
const dirWatcher = watchTools.setDirChangeCallback(
  "/path/to/directory",
  (event, path) => {
    console.log(`目录内文件 ${path} 发生事件: ${event}`);
  },
  { recursive: true },
);

// 关闭监控器
watchTools.closeWatcher(watcher);

// 获取监控池状态
const status = watchTools.getMonitorPoolStatus();
console.log(status);
```

### 测试监控池功能

```bash
npm run test:monitor
```

测试脚本将验证监控池的关键功能，包括资源限制、自动清理和资源回收。

## 许可证

MIT License
