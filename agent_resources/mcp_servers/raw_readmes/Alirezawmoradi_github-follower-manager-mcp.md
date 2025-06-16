# GitHub Follow Manager

## Description

GitHub Follow Manager is a tool designed to help you manage your GitHub followers using the Model Context Protocol (MCP) pattern. It allows you to check who follows you on GitHub, unfollow users who don't follow you back, and analyze follow relationships.

## Features

- ✅ Authenticates with GitHub using a personal access token
- 👤 Retrieves the current authenticated user
- 🔄 Lists users you follow who don't follow you back
- 🔻 Allows bulk unfollowing
- 📊 Generates a detailed report of all follow relationships

## ✨ Why This Project?

This repo is perfect for:

- Developers who want to clean up their GitHub following list
- LLM enthusiasts exploring Claude Desktop + MCP
- Automation fans who want **natural language control** of their tools

## Prerequisites

- Node.js (version 18 or higher)
- npm (Node Package Manager)
- A GitHub personal access token with appropriate scopes

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone <repository-url>
cd follower-manager-mcp
```

### 2. Install the dependencies:

```bash
npm install
```

### 3. Create a `.env` file in the root directory and add your GitHub personal access token:

```
GITHUB_TOKEN= your_github_token_here
```

### 4. Build the project:

```bash
npm run build
```

### 5. Configure mcpServers

```bash
{
  "mcpServers": {
    "github-follow-manager": {
      "command": "node",
      "args": [
        "C:\\Path\\To\\github-follow-manager-mcp\\dist\\mcp-server.js"
      ],
      "env": {
        "GITHUB_TOKEN": "your_personal_access_token_here"
      }
    }
  }
}
```

##### Make sure your GitHub token has appropriate scopes such as: read:user, user:follow.

## 🧪 Demo Prompt for Claude

Once everything is configured and Claude Desktop is running, try prompts like:

- "Initialize the GitHub follower manager."

- "Who am I following that doesn’t follow me back?"

- "Unfollow all users who don’t follow me back."

Claude will automatically use the MCP server to perform these actions!

### 📜 License

This project is open-source and available under the [MIT license](https://opensource.org/licenses/MIT).

### 📣 Help this repo grow

If you found this useful, please consider starring ⭐ the repo to help more people discover it.

### 📬 Contact

Developed by [Alireza Moradi]()

Reach out via [GitHub Issues](https://github.com/Alirezawmoradi/Github-RepoSweep/issues) for questions or suggestions.

## 🙏 Credits

- [Claude Desktop](https://claude.ai/)
- [Model Context Protocol](https://github.com/modelcontextprotocol)
- [GitHub REST API](https://docs.github.com/en/rest?apiVersion=2022-11-28)

### 🔗 Keywords:

**GitHub CLI** · **AI Assistant** · **Claude Desktop** · **MCP** · **GitHub API** · **TypeScript** · **Productivity** · **Automation** · **GitHub Bot**
