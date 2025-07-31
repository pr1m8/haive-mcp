# VueSage 🧙‍♂️

Vue 组件智能分析与优化引擎 - 基于 MCP (Model-Code-Prompt) 的 Vue 代码质量分析工具

## 功能特性 ✨

- 🔍 **智能分析**:
  - 自动检测 Vue 组件中的潜在问题
  - 基于 AST 的代码结构分析
  - 组件复杂度评估
  - 性能隐患识别
- 🛠 **自动修复**:
  - 一键修复常见代码问题
  - 自动应用最佳实践
  - 代码规范自动化
  - 安全模式下的代码重构
- 📊 **性能优化**:
  - 组件渲染性能分析
  - 响应式依赖优化
  - 内存泄漏检测
  - 打包体积优化建议
- 🎯 **最佳实践**:
  - Vue.js 官方推荐规范
  - 组件设计模式指导
  - TypeScript 类型优化
  - 代码可维护性建议

## 安装使用 📦

### 全局安装（推荐）

```bash
npm install -g vuesage
```

### 项目中安装

```bash
npm install vuesage
```

### 1. 作为 MCP 服务使用

#### 安装

```bash
npm install -g vuesage-mcp
```

#### 配置 MCP

在编辑器的 MCP 配置文件中添加：

```json
{
  "mcpServers": {
    "vuesage": {
      "command": "vuesage-mcp",
      "enabled": true,
      "capabilities": {
        "tools": [
          {
            "name": "analyze",
            "description": "分析Vue组件代码质量",
            "parameters": {
              "type": "object",
              "properties": {
                "component": {
                  "type": "string",
                  "description": "Vue组件代码"
                }
              },
              "required": ["component"]
            }
          }
        ]
      },
      "version": "1.1.44"
    }
  }
}
```

支持的编辑器：

- Cursor (推荐)
- VSCode (需要安装 MCP 插件)

#### 使用方法

1. 在编辑器中打开 Vue 组件文件
2. 使用以下方式之一：
   - 命令面板（Command Palette）调用：
     - `VueSage: Analyze Component` - 分析当前组件
   - 对话形式（仅 Cursor）：
     - 直接输入 "分析当前组件" 或类似的自然语言指令
     - AI 助手会调用 vuesage 服务分析代码

#### 返回结果说明

分析结果包含以下信息：

```json
{
  "score": 95, // 代码质量得分
  "issues": 0, // 严重问题数量
  "warnings": 1, // 警告数量
  "details": [
    // 详细问题列表
    {
      "type": "warning",
      "message": "具体的问题描述",
      "line": 16 // 问题所在行号
    }
  ]
}
```

#### 调试模式

如果需要查看详细日志，可以设置环境变量：

```bash
export VUESAGE_DEBUG=true
```

日志文件位置：`~/.vuesage/logs/vuesage.log`

### 2. 作为 Node.js 模块使用

```javascript
import { VueSage } from "vuesage";

// 创建实例
const vueSage = new VueSage();

// 分析组件
const analysis = await vueSage.analyze(componentCode);

// 修复问题
const fixed = await vueSage.fix(componentCode, analysis.issues);
```

### 3. 作为独立服务使用

```bash
# 启动服务
vuesage serve
```

服务将在 http://localhost:6188 启动

## API 使用说明 📚

### analyze(code: string): Promise<Analysis>

分析 Vue 组件代码，返回分析结果。

#### 参数

- `code` (string): Vue 组件代码

#### 返回值

```typescript
interface Analysis {
  summary: {
    totalIssues: number;
    categories: string[];
    hasAutoFixableIssues: boolean;
  };
  issues: Array<{
    category: string;
    issues: Array<{
      id: string;
      message: string;
      severity: "error" | "warning";
      autofix: boolean;
      line?: number;
      column?: number;
    }>;
  }>;
}
```

### fix(code: string, issues: Issue[]): Promise<FixResult>

根据分析结果修复组件代码。

#### 参数

- `code` (string): Vue 组件代码
- `issues` (Issue[]): 需要修复的问题列表

#### 返回值

```typescript
interface FixResult {
  success: boolean;
  fixedComponent: string;
  appliedFixes: Array<{
    id: string;
    message: string;
    type: string;
  }>;
}
```

## HTTP API

### POST /analyze

分析组件代码。

#### 请求体

```json
{
  "component": "Vue组件代码"
}
```

#### 响应

```json
{
  "summary": {
    "totalIssues": 5,
    "categories": ["naming", "props", "performance"],
    "hasAutoFixableIssues": true
  },
  "issues": [
    {
      "category": "naming",
      "issues": [
        {
          "id": "naming-001",
          "message": "组件名称应使用 PascalCase",
          "severity": "warning",
          "autofix": true
        }
      ]
    }
  ]
}
```

### POST /fix

修复组件代码中的问题。

#### 请求体

```json
{
  "component": "组件代码",
  "issues": ["issue_id_1", "issue_id_2"]
}
```

## 配置说明 ⚙️

### 1. 基础配置

在项目根目录创建 `.vuesagerc.json`：

```json
{
  "rules": {
    "naming": {
      "enabled": true,
      "severity": "warning",
      "options": {
        "componentPrefix": "App",
        "propsCasing": "camelCase"
      }
    },
    "props": {
      "enabled": true,
      "severity": "warning",
      "options": {
        "requireType": true,
        "requireDefault": true
      }
    },
    "template": {
      "enabled": true,
      "severity": "error",
      "options": {
        "maxLength": 80,
        "requireKey": true
      }
    }
  },
  "autofix": {
    "safeMode": true,
    "backup": true,
    "ignoreFiles": ["dist/**/*", "node_modules/**/*"]
  },
  "formatting": {
    "indentSize": 2,
    "maxLineLength": 100,
    "singleQuote": true
  }
}
```

### 2. 规则说明

# VueSage MCP

Vue 组件智能分析工具，基于 Model Context Protocol (MCP)。

## 特性

- 🔍 **智能分析**

  - Vue 组件代码质量检查
  - UI/UX 最佳实践验证
  - 可访问性(A11Y)检查
  - 响应式设计分析

- 🛠 **自动修复**

  - 一键修复常见代码问题
  - 自动应用最佳实践
  - 代码规范自动化
  - 安全模式下的代码重构

- 📊 **详细报告**
  - 组件健康评分
  - 问题分类统计
  - 可视化分析结果
  - 优化建议清单

## 快速开始

使用 npx 运行（推荐）:

```bash
# 分析单个组件
npx vuesage-mcp@latest analyze <file>

# 批量分析
npx vuesage-mcp@latest analyzeBatch "src/**/*.vue"

# 自动修复
npx vuesage-mcp@latest autoFix <file>
```

## Cursor 编辑器配置

在 `~/.cursor/mcp.json` 中添加:

```json
{
  "mcpServers": {
    "vuesage": {
      "command": "npx",
      "args": ["vuesage-mcp@latest"],
      "version": "1.1.43"
    }
  }
}
```

## 分析规则

### UI 分析

- ✨ 可访问性 (ARIA属性、alt文本等)
- 📱 响应式设计
- 🏗 语义化结构
- 🎨 样式最佳实践

### 代码质量

- 🔄 v-for 指令规范
- ⚡️ Props 类型验证
- 📢 事件声明检查
- 🎯 样式隔离验证

## 自动修复功能

支持自动修复的问题类型：

- ARIA 属性补充
- 响应式样式优化
- 语义化标签转换
- Props 类型添加
- 事件声明补充
- 样式作用域添加

## API

### analyze

分析单个 Vue 组件文件：

```typescript
interface AnalyzeResult {
  score: number; // 总分 (0-100)
  issues: string[]; // 严重问题
  warnings: string[]; // 警告
  fixes: Fix[]; // 可用的修复方案
  details: {
    ui: {
      accessibility: string;
      responsiveness: string;
      semantics: string;
    };
    code: {
      props: string;
      emits: string;
      style: string;
    };
  };
}
```

### analyzeBatch

批量分析多个组件：

```typescript
interface BatchResult {
  summary: {
    totalFiles: number;
    averageScore: number;
    totalIssues: number;
    totalWarnings: number;
    passRate: string;
  };
  details: AnalyzeResult[];
}
```

### autoFix

自动修复检测到的问题：

```typescript
interface Fix {
  type: string;
  element?: string;
  attribute?: string;
  value?: string;
  content?: string;
  from?: string;
  to?: string;
}
```

## 版本历史

### 1.1.43

- ✨ 新增 UI 分析功能
- 🔧 添加自动修复能力
- 📊 增强分析报告
- 🚀 支持 npx 运行方式
- 📦 优化依赖管理

## 许可证

MIT
