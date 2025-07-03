# :rainbow: Taskade MCP

All things related to [Taskade](https://taskade.com/)'s MCP (Model Context Protocol) initiatives.

- [Official MCP server](https://github.com/taskade/mcp/tree/main/packages/server) - Connect Taskade’s API to any MCP-compatible client like Claude or Cursor.
- [OpenAPI Codegen](https://github.com/taskade/mcp/tree/main/packages/openapi-codegen) - Generate MCP tools from any OpenAPI schema in minutes.

## ⚡ Taskade MCP Demo

MCP-powered Taskade agent running inside Claude Desktop by Anthropic:

![Image](https://github.com/user-attachments/assets/0cee987b-b0d4-4d10-bb7f-da49a080d731)

## 🛠 Codegen for OpenAPI

Use our generator to build MCP tools from any OpenAPI spec.

```bash
npm install --dev @taskade/mcp-openapi-codegen @readme/openapi-parser
```

Script example:

```ts
import { dereference } from "@readme/openapi-parser";
import { codegen } from "@taskade/mcp-openapi-codegen";

const document = await dereference("taskade-public.yaml");

await codegen({
  path: "src/tools.generated.ts",
  document,
});
```

---

## 🐑 What is Taskade?

Taskade ([YC S19](https://www.ycombinator.com/companies/taskade)) is building the execution layer for AI — a unified workspace to deploy agents, automate workflows, and get work done.

- Deploy autonomous agents with memory and tools

- Automate tasks and workflows (no-code)

- Chat, plan, and collaborate in real-time

- Integrate via API, OpenAPI, or MCP

Developer docs: <https://developers.taskade.com>

Try: <https://www.taskade.com/create>

More at <https://www.taskade.com>

---

## 🚀 Roadmap

- `agent.js` → Open-source autonomous agent toolkit: Coming soon.
- `TaskOS` → Agent platform at [https://developers.taskade.com](https://developers.taskade.com)
- `TechnologyFramework` → Future [home](https://technologyframework.com/) for open agentic standards and extensions

---

## 🤝 Contribute

Help us improve MCP tools, OpenAPI workflows, and agent capabilities.

Community: [https://www.taskade.com/community](https://www.taskade.com/community)

GitHub: [https://github.com/taskade](https://github.com/taskade)

Contact: [hello@taskade.com](mailto:hello@taskade.com)
