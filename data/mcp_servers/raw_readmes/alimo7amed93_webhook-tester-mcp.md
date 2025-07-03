# 🚀 Webhook Tester MCP Server

A powerful and modular FastMCP server for interacting with webhook-test.com, designed to automate and manage Webhook tokens (URLs), inspect incoming requests, and perform analytics — all without writing custom API integrations.

Built with the FastMCP framework to expose modular tools and resources, this project enables webhook observability and management.

## 🛎️ Webhooks 101

Webhooks let your app send and receive real-time updates between services. When sending, your app can POST data to a URL whenever something important happens — like a new user signup or a status change. When receiving, your app listens for incoming POST requests from other services and reacts to the events they send. This setup is way more efficient than constant polling and is perfect for triggering actions, syncing data, or keeping systems in sync.

## 📦 Features & Use Cases

✅ Create new webhooks\
✅ List all available webhooks\
✅ Fetch webhook's details\
✅ Fetch webhook payloads\
✅ Delete webhooks

## ⚙️ Setup

1. Clone the repo
2. Install dependencies `pip install -r requirements.txt`
3. Configure `.env`

## 🔍 Testing Using Claude

- Configure Claude Desktop to use the local server by editing your claude_desktop_config.json file:

```
{
    "mcpServers": {
      "webhook-tester-mcp": {
        "command": "fastmcp",
        "args": ["run", "{{fullPath}}\\Webhook-test_mcp\\server.py"]
      }
    }
  }
```

## 🧪 Demo testing the Server

[![Watch the video](https://img.youtube.com/vi/nGRlQtRlDA4/hqdefault.jpg)](https://www.youtube.com/watch?v=nGRlQtRlDA4)

## 📄 License

This project is licensed under the [MIT License](https://mit-license.org/).
