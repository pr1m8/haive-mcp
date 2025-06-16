# VPS MCP SERVER - Automação para Servidores MCP

Sistema de automação para configuração de servidores com suporte ao [Model Context Protocol (MCP)](https://docs.cursor.com/context/model-context-protocol) que permite que assistentes AI (como Cursor AI) gerenciem sua infraestrutura através de comandos em linguagem natural.

## 🌟 Visão Geral

Este projeto oferece scripts para configurar rapidamente servidores MCP com as seguintes opções:

1. **Configuração de Servidor Único**: Tudo em um só servidor (MCP Server, aplicações, bancos de dados e armazenamento de objetos)
2. **Configuração de Dois Servidores**:
   - **Servidor de Aplicações**: MCP Server e aplicações
   - **Servidor de Banco de Dados**: MCP Server, bancos de dados (PostgreSQL/MySQL) e armazenamento de objetos

## 🚀 Instalação Rápida

### Servidor Único (Tudo em uma VPS)

```bash
curl -fsSL https://raw.githubusercontent.com/LuizBranco-ClickHype/VPS-MCP-SERVER/main/install.sh | bash
```

### Configuração de Dois Servidores (Duas VPS)

**Na primeira VPS (Servidor de Aplicações)**:

```bash
curl -fsSL https://raw.githubusercontent.com/LuizBranco-ClickHype/VPS-MCP-SERVER/main/install.sh | bash -s -- --mode app
```

**Na segunda VPS (Servidor de Banco de Dados)**:

```bash
curl -fsSL https://raw.githubusercontent.com/LuizBranco-ClickHype/VPS-MCP-SERVER/main/install.sh | bash -s -- --mode db
```

## 💻 Requisitos do Sistema

- Ubuntu 20.04+ ou Debian 11+
- Acesso root ou usuário com privilégios sudo
- Conexão à internet
- Mínimo 2GB RAM (recomendado 4GB)
- 20GB de espaço em disco

## 🛠 Recursos

### Serviços MCP Disponíveis

- **VPS MCP Server**: Gerenciamento central de infraestrutura
- **PostgreSQL MCP**: Acesso a banco de dados com suporte a vetores para IA
- **Storage MCP**: Operações de armazenamento compatível com S3
- **Context7 MCP**: Acesso a documentação e conhecimento externo

### Componentes Integrados

- **Docker / Docker Compose**: Para containerização dos serviços
- **PostgreSQL**: Banco de dados com suporte a pgvector para embeddings de IA
- **MinIO**: Armazenamento de objetos compatível com S3
- **Context7**: Integração para acesso a documentação e conhecimento externo

### Segurança

- Firewall configurado (ufw)
- Tokens de autenticação gerados aleatoriamente
- Comunicação segura entre servidores
- Certificados SSL automáticos (Let's Encrypt) quando configurado com domínio

## ⚙️ Opções de Configuração

O script de instalação aceita os seguintes parâmetros:

| Parâmetro    | Descrição                                                   | Padrão     |
| ------------ | ----------------------------------------------------------- | ---------- |
| `--mode`     | Modo de instalação (`single`, `app`, `db`)                  | `single`   |
| `--domain`   | Domínio para configurar SSL                                 | -          |
| `--email`    | Email para certificados Let's Encrypt                       | -          |
| `--db-type`  | Tipo de banco de dados (`postgres`, `mysql`)                | `postgres` |
| `--db-host`  | Endereço IP do servidor de banco de dados (para modo `app`) | -          |
| `--app-host` | Endereço IP do servidor de aplicações (para modo `db`)      | -          |
| `--port`     | Porta para o MCP Server                                     | `3000`     |
| `--help`     | Exibe ajuda                                                 | -          |

## 🌐 Model Context Protocol (MCP)

O [Model Context Protocol (MCP)](https://docs.cursor.com/context/model-context-protocol) é um protocolo aberto que padroniza como aplicativos fornecem contexto e ferramentas para LLMs. Este projeto implementa servidores MCP que podem ser consumidos pelo Cursor AI e outros clientes compatíveis.

### Arquitetura MCP

![Arquitetura MCP](https://docs.cursor.com/img/mcp-architecture.png)

A implementação neste projeto fornece:

1. **Transporte stdio**: Executa em máquina local e é gerenciado pelo Cursor
2. **Transporte SSE**: Permite execução local ou remota via HTTP

### Configurando o Cursor AI

Para conectar o Cursor AI aos servidores MCP:

1. Crie uma pasta `.cursor` na raiz do seu projeto
2. Crie um arquivo `mcp.json` com o seguinte conteúdo (ajuste os IPs conforme necessário):

```json
{
  "mcpServers": {
    "vps_mcp_server": {
      "description": "Servidor MCP unificado para gerenciamento de infraestrutura",
      "command": "bash",
      "args": ["./mcp-service.sh", "--endpoint", "/api/mcp"]
    },
    "postgresql": {
      "description": "Acesso a banco de dados PostgreSQL com suporte a vetores",
      "command": "bash",
      "args": ["./mcp-service.sh", "--endpoint", "/api/postgres"]
    },
    "storage": {
      "description": "Gerenciamento de armazenamento de objetos S3 compatível",
      "command": "bash",
      "args": ["./mcp-service.sh", "--endpoint", "/api/storage"]
    },
    "context7": {
      "description": "Acesso a documentação e conhecimento via Context7",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

## 📝 Funções Disponíveis

O sistema oferece diversas funções para gerenciamento do servidor:

### Gerenciamento MCP

```bash
# Listar serviços MCP disponíveis
./mcp-service.sh list

# Verificar status dos serviços MCP
./mcp-service.sh status

# Testar conexão com serviço específico
./mcp-service.sh test-mcp postgresql

# Ver logs de comunicação MCP
./mcp-service.sh logs 20

# Iniciar como servidor MCP
./mcp-service.sh --endpoint /api/mcp
```

### Banco de Dados

```bash
# Configurar PostgreSQL com pgvector
./postgres-mcp-setup.sh

# Backup de banco de dados
source common.sh
backup_database
```

## 🔍 Diagnóstico e Resolução de Problemas

Se você encontrar problemas:

1. Verifique o status dos serviços MCP:

   ```bash
   ./mcp-service.sh status
   ```

2. Verifique os logs específicos:

   ```bash
   ./mcp-service.sh logs 50
   ```

3. Teste a conexão com serviços específicos:
   ```bash
   ./mcp-service.sh test-mcp postgresql
   ./mcp-service.sh test-mcp storage
   ./mcp-service.sh test-mcp context7
   ```

## 🔧 Implantação em Produção

### 1. Configuração Inicial do Servidor

1. Atualize o sistema e instale dependências:

   ```bash
   apt update && apt upgrade -y
   apt install -y curl git jq
   ```

2. Clone o repositório:

   ```bash
   git clone https://github.com/LuizBranco-ClickHype/VPS-MCP-SERVER.git
   cd VPS-MCP-SERVER
   ```

3. Torne o script executável:

   ```bash
   chmod +x mcp-service.sh
   ```

4. Crie o diretório de logs:
   ```bash
   mkdir -p /var/log/vps-mcp
   touch /var/log/vps-mcp/mcp-communication.log
   ```

### 2. Configuração do Servidor MCP

1. Edite o arquivo `mcp-model.json` para substituir `IP_DO_SERVIDOR` pelo seu IP público ou domínio:

   ```bash
   # Exemplo com sed
   sed -i 's/IP_DO_SERVIDOR/seu.ip.ou.dominio/g' mcp-model.json
   ```

2. Instale dependências NPM:

   ```bash
   npm install
   ```

3. Configure o firewall para permitir acesso às portas MCP:
   ```bash
   # Se estiver usando ufw
   ufw allow 3000/tcp  # Porta MCP principal
   ```

### 3. Configuração para Execução Contínua

1. Crie um serviço systemd para manter o MCP em execução:

   ```bash
   cat > /etc/systemd/system/vps-mcp.service << EOF
   [Unit]
   Description=VPS MCP Server
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/caminho/para/VPS-MCP-SERVER
   ExecStart=/bin/bash mcp-service.sh --endpoint /api/mcp
   Restart=on-failure
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   EOF
   ```

2. Habilite e inicie o serviço:

   ```bash
   systemctl enable vps-mcp
   systemctl start vps-mcp
   ```

3. Verifique o status:
   ```bash
   systemctl status vps-mcp
   ```

## 🤝 Contribuições

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça commit das suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Envie para o GitHub (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE)
