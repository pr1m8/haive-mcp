# MCP Configuration Guide

## Configuration Structure

The MCP system uses a hierarchical configuration structure with support for templates, server definitions, and discovery patterns.

## Configuration Files

### Default Locations

The system searches for configuration files in the following order:

1. `./mcp_config.yaml` - Current directory
2. `~/.mcp/config.yaml` - User home directory
3. `/etc/mcp/config.yaml` - System-wide configuration
4. Environment variable: `MCP_CONFIG_PATH`

### Configuration Schema

```yaml
# Templates define reusable installation patterns
templates:
  - name: npm_official
    installation_method: npm
    command_pattern: "@modelcontextprotocol/server-{service}"
    capabilities: [tools]
    category: official

  - name: npm_community
    installation_method: npm
    command_pattern: "{package}"
    capabilities: [tools]
    category: community

  - name: pypi_package
    installation_method: pip
    command_pattern: "{package}"
    capabilities: [tools]
    category: python

  - name: git_repo
    installation_method: git
    command_pattern: "python {repo}/server.py"
    post_install: ["pip install -r {repo}/requirements.txt"]
    capabilities: [tools]
    category: development

  - name: docker_image
    installation_method: docker
    command_pattern: "{image}"
    capabilities: [tools]
    category: containerized

# Server definitions using templates
servers:
  - name: filesystem
    template: npm_official
    source: npm
    variables:
      service: filesystem
    enabled: true
    tags: [file, official]

  - name: github
    template: npm_official
    source: npm
    variables:
      service: github
    env:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
    enabled: true
    tags: [git, official]

  - name: custom-python
    template: pypi_package
    source: pypi
    variables:
      package: my-mcp-server
    enabled: true

  - name: private-repo
    template: git_repo
    source: https://github.com/myorg/private-mcp.git
    variables:
      owner: myorg
      repo: private-mcp
    env:
      API_KEY: ${PRIVATE_API_KEY}

# Discovery patterns for finding new servers
patterns:
  discovery_sources:
    - https://github.com/modelcontextprotocol/servers
    - https://registry.npmjs.org/-/v1/search?text=mcp-server
    - https://api.github.com/search/repositories?q=mcp+server

  package_patterns:
    npm:
      - "@modelcontextprotocol/server-*"
      - "mcp-server-*"
      - "*-mcp-server"
    pypi:
      - "mcp-*"
      - "*-mcp"
      - "mcp-server-*"
    docker:
      - "mcp/*"
      - "*/mcp-*"

  exclude_patterns:
    - "*-test"
    - "*-demo"
    - "*-example"

# Global settings
settings:
  install_dir: ~/.mcp/servers
  log_level: INFO
  max_concurrent_downloads: 5
  connection_timeout: 30
  retry_attempts: 3
  health_check_interval: 3600
  auto_update: false
```

## Environment Variables

### Substitution

Environment variables can be referenced using `${VAR_NAME}` syntax:

```yaml
servers:
  - name: api-server
    env:
      API_KEY: ${MY_API_KEY}
      API_URL: ${API_URL:-https://default.api.com}
```

### Global Environment

Set global environment variables for all servers:

```yaml
settings:
  global_env:
    HTTP_PROXY: ${HTTP_PROXY}
    HTTPS_PROXY: ${HTTPS_PROXY}
    NO_PROXY: localhost,127.0.0.1
```

## Server Configuration Options

### Basic Configuration

```yaml
servers:
  - name: server-name
    template: template-name
    source: source-url-or-name
    enabled: true
    priority: 0
    tags: [tag1, tag2]
```

### Advanced Options

```yaml
servers:
  - name: advanced-server
    template: custom

    # Installation details
    installation_method: npm
    command: npx
    args: ["-y", "package-name"]

    # Runtime configuration
    transport: stdio # stdio, sse, http
    url: null # For HTTP transports

    # Environment
    env:
      KEY1: value1
      KEY2: ${ENV_VAR}

    # Capabilities
    capabilities: [tools, resources, prompts]
    required_capabilities: [tools]

    # Categories and tags
    category: development
    tags: [experimental, beta]

    # Connection settings
    timeout: 30
    retry_attempts: 3
    retry_delay: 5

    # Health monitoring
    health_check_interval: 3600
    health_check_command: ["npm", "test"]

    # Updates
    auto_update: true
    update_schedule: "0 2 * * *" # Cron format

    # Dependencies
    prerequisites: ["node>=14", "python>=3.8"]
    depends_on: ["other-server"]

    # Post-installation
    post_install:
      - "npm install"
      - "python setup.py install"

    # Validation
    validate_command: ["npm", "run", "validate"]
    expected_files: ["server.js", "package.json"]
```

## Template System

### Creating Templates

Templates allow you to define reusable patterns:

```yaml
templates:
  - name: my-template
    installation_method: npm
    command_pattern: "npx {package}"
    args_pattern: ["{arg1}", "{arg2}"]
    env_vars:
      DEFAULT_KEY: default_value
    capabilities: [tools]
    category: custom
    health_check: "npm test"
    prerequisites: ["node>=14"]
    post_install: ["npm install"]
```

### Using Templates

Reference templates in server definitions:

```yaml
servers:
  - name: my-server
    template: my-template
    variables:
      package: my-package-name
      arg1: value1
      arg2: value2
    env:
      DEFAULT_KEY: override_value # Override template default
```

## Discovery Configuration

### Automatic Discovery

Enable automatic server discovery:

```yaml
settings:
  auto_discover: true
  discovery_interval: 86400 # Daily
  discovery_limit: 100

patterns:
  discovery_sources:
    - type: npm
      url: https://registry.npmjs.org/-/v1/search
      params:
        text: mcp-server
        size: 250

    - type: github
      url: https://api.github.com/search/repositories
      params:
        q: mcp+server+in:name
        sort: stars
        order: desc

    - type: pypi
      url: https://pypi.org/pypi
      pattern: mcp-*
```

### Manual Discovery

```bash
# Discover from specific source
python scripts/download_servers.py discover --source npm

# Discover and filter
python scripts/download_servers.py discover --limit 50 --output discovered.json
```

## Profile Management

### Multiple Profiles

Create different profiles for different environments:

```yaml
profiles:
  development:
    settings:
      log_level: DEBUG
      install_dir: ./dev-servers
    servers:
      - name: debug-server
        enabled: true

  production:
    settings:
      log_level: WARNING
      install_dir: /opt/mcp/servers
    servers:
      - name: debug-server
        enabled: false
```

### Profile Selection

```bash
# Use specific profile
python scripts/download_servers.py --profile production download --all

# Set default profile
export MCP_PROFILE=production
```

## Best Practices

1. **Use Templates**: Define templates for common patterns
2. **Environment Variables**: Never hardcode sensitive values
3. **Tags and Categories**: Organize servers logically
4. **Health Checks**: Configure health checks for critical servers
5. **Version Control**: Keep configuration in version control
6. **Documentation**: Document custom templates and configurations

## Examples

### Minimal Configuration

```yaml
servers:
  - name: filesystem
    template: npm_official
    variables:
      service: filesystem
```

### Full-Featured Configuration

See `configs/default_config.yaml` for a complete example with all features.
