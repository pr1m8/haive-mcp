# buildkite-mcp-server

[![Build status](https://badge.buildkite.com/79fefd75bc7f1898fb35249f7ebd8541a99beef6776e7da1b4.svg?branch=main)](https://buildkite.com/buildkite/buildkite-mcp-server)

This is an [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) server for [Buildkite](https://buildkite.com). The goal is to provide access to information from buildkite about pipelines, builds and jobs to tools such as [Claude Desktop](https://claude.ai/download), [GitHub Copilot](https://github.com/features/copilot) and other tools, or editors.

[![Add to Cursor](https://cursor.com/deeplink/mcp-install-dark.png)](https://cursor.com/install-mcp?name=buildkite&config=eyJjb21tYW5kIjoiZG9ja2VyIHJ1biAtaSAtLXJtIC1lIEJVSUxES0lURV9BUElfVE9LRU4gZ2hjci5pby9idWlsZGtpdGUvYnVpbGRraXRlLW1jcC1zZXJ2ZXIgc3RkaW8iLCJlbnYiOnsiQlVJTERLSVRFX0FQSV9UT0tFTiI6ImJrdWFfeHh4eHh4eHgifX0%3D)

# Tools

- `get_cluster` - Get details of a buildkite cluster in an organization
- `list_clusters` - List all buildkite clusters in an organization
- `get_cluster_queue` - Get details of a buildkite cluster queue in an organization
- `list_cluster_queues` - List all buildkite queues in a cluster
- `get_pipeline` - Get details of a specific pipeline in Buildkite
- `list_pipelines` - List all pipelines in a buildkite organization
- `list_builds` - List all builds in a pipeline in Buildkite
- `get_build` - Get a build in Buildkite
- `current_user` - Get the current user
- `user_token_organization` - Get the organization associated with the user token used for this request
- `get_jobs` - Get a list of jobs for a build
- `get_job_logs` - Get the logs of a job in a Buildkite build
- `access_token` - Get the details for the API access token that was used to authenticate the request
- `list_artifacts` - List the artifacts for a Buildkite build
- `get_artifact` - Get an artifact from a Buildkite build
- `list_annotations` - List the annotations for a Buildkite build
- `list_test_runs` - List all test runs for a test suite in Test Engine
- `get_test_run` - Get a specific test run in Test Engine
- `get_failed_test_executions` - Get a list of the failed test executions for a run in Test Engine
- `get_test` - Get a test in Test Engine

Example of the `get_pipeline` tool in action.

![Get Pipeline Tool](docs/images/get_pipeline.png)

### Production

To ensure the MCP server is run in a secure environment, we recommend running it in a container.

Pull the pre-built image (recommended):

```bash
docker pull ghcr.io/buildkite/buildkite-mcp-server
```

Or build it yourself using GoReleaser and copy the binary into your path:

```bash
goreleaser build --snapshot --clean
```

# configuration

Create a [Buildkite API Access Token with read access to pipelines].

## Claude Desktop Configuration

Use this configuration if you want to run the server `buildkite-mcp-server` Docker (recommended):

```json
{
  "mcpServers": {
    "buildkite": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "BUILDKITE_API_TOKEN",
        "ghcr.io/buildkite/buildkite-mcp-server",
        "stdio"
      ],
      "env": {
        "BUILDKITE_API_TOKEN": "bkua_xxxxxxxx"
      }
    }
  }
}
```

Configuration if you have `buildkite-mcp-server` installed locally.

```json
{
  "mcpServers": {
    "buildkite": {
      "command": "buildkite-mcp-server",
      "args": ["stdio"],
      "env": {
        "BUILDKITE_API_TOKEN": "bkua_xxxxxxxx"
      }
    }
  }
}
```

## Goose Configuration

For Docker with [Goose](https://block.github.io/goose/) (recommended):

```yaml
extensions:
  fetch:
    name: Buildkite
    cmd: docker
    args:
      [
        "run",
        "-i",
        "--rm",
        "-e",
        "BUILDKITE_API_TOKEN",
        "ghcr.io/buildkite/buildkite-mcp-server",
        "stdio",
      ]
    enabled: true
    envs: { "BUILDKITE_API_TOKEN": "bkua_xxxxxxxx" }
    type: stdio
    timeout: 300
```

Local configuration for Goose:

```yaml
extensions:
  fetch:
    name: Buildkite
    cmd: buildkite-mcp-server
    args: [stdio]
    enabled: true
    envs: { "BUILDKITE_API_TOKEN": "bkua_xxxxxxxx" }
    type: stdio
    timeout: 300
```

## VSCode Configuration

[VSCode](https://code.visualstudio.com/) supports interactive inputs for variables. To get the API token interactively on MCP startup, put the following in `.vscode/mcp.json`

```json
{
  "inputs": [
    {
      "id": "BUILDKITE_API_TOKEN",
      "type": "promptString",
      "description": "Enter your BuildKite Access Token (https://buildkite.com/user/api-access-tokens)",
      "password": true
    }
  ],
  "servers": {
    "buildkite": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "BUILDKITE_API_TOKEN",
        "ghcr.io/buildkite/buildkite-mcp-server",
        "stdio"
      ],
      "env": {
        "BUILDKITE_API_TOKEN": "${input:BUILDKITE_API_TOKEN}"
      }
    }
  }
}
```

## Zed

There is a [Zed](https://zed.dev) editor [extension](https://github.com/mcncl/zed-mcp-server-buildkite) available in the [official extension gallery](https://zed.dev/extensions?query=buildkite). During installation it will ask for an API token which will be added to your settings. Or you can manually configure:

```jsonc
// ~/.config/zed/settings.json
{
  "context_servers": {
    "mcp-server-buildkite": {
      "settings": {
        "buildkite_api_token": "your-buildkite-token-here",
      },
    },
  },
}
```

# Security

This container image is built using [cgr.dev/chainguard/static](https://images.chainguard.dev/directory/image/static/versions) base image and is configured to run the MCP server as a non-root user.

# Contributing

Notes on building this project are in the [DEVELOPMENT.md](DEVELOPMENT.md)

## Disclaimer

This project is in the early stages of development and is not yet ready for use.

## License

This project is released under MIT license.

[Buildkite API Access Token with read access to pipelines]: https://buildkite.com/user/api-access-tokens/new?scopes[]=read_pipelines
