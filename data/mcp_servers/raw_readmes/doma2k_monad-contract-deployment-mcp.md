> ⚠️ **Warning:** Noob builder, code could contain bugs and flaws.

_For learning [**monad-sse-mcp**](https://github.com/monad-developers/monad-sse-mcp) and [**evm-mcp-serve**](https://github.com/mcpdotdirect/evm-mcp-server) repos was used as example_

# 🚀 Monad Contracts: Unleash the Power! 🚀

**Build** 🛠️, **Deploy** 📤, **Interact** 🤝 — All in the _Monad Universe_!
**This is MCP server to compile and deploy contracts directly from chat promt or compatible MCP client.**

> Project focus around smart contracts interactions.

### ✨ Features

- **Deploy contracts** single or multiple in one call by `compile-and-deploy`
- **Resolve Address** from private with `resolve-signer-address`
- **Check Balance** of wallet from dialog context with `get-balance`
- .......

### 💡 To implement

- Deployed contracts Abi storage
- Interaction and Event Monitoring logic

## ⚙️ Supported connection types

The server uses the following default configuration:

## How to use SSE server

# Monad Contract Deployment MCP **DEMO**

![Demo Animation](./public/gif.gif)

Paste the following in the `mcp.json` file

```json
{
  "mcpServers": {
    ...
    "monad-mcp-sse": {
      "url": "https://https://monad-contract-deployment-mcp.vercel.app/sse"
    }
  }
}
```

## Sample Client

`script/test-client.mjs` contains a sample client to try invocations.

```sh
node scripts/test-client.mjs http://localhost:3000
```

# 🚧 Project Status: Under Development

> ⚠️ **Warning:** This project is currently under active development and is not yet stable. Features may change, and things may break without notice.
