# ZapDelivery API

## 📋 Pré-requisitos

- Python 3.10+
- Docker
- Git

## 🚀 Configuração Inicial

### 1. Clonar o repositório

```bash
git clone git@github.com:edupoli/zapdelivery.git
cd zapdelivery
```

### 2. Instalar UV (gerenciador de pacotes)

# macOS/Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

# Windows (PowerShell)

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. Criar e ativar ambiente virtual

```bash
uv venv
```

# Linux/Mac

```bash
source .venv/bin/activate
```

# Windows

```bash
.\.venv\Scripts\activate
```

### 4. Instalar dependências

```bash
uv sync
```

### 5. Iniciar container PostgreSQL

```bash
docker run --name zapdelivery-db \
  -e POSTGRES_USER=zapuser \
  -e POSTGRES_PASSWORD=zappassword \
  -e POSTGRES_DB=zapdelivery \
  -p 5432:5432 \
  -v ~/postgres-data:/var/lib/postgresql/data \
  -d postgres:latest
```

### 6. Configurar variáveis de ambiente

Crie um arquivo .env na raiz do projeto com:

```bash
DATABASE_URL="postgresql://zapuser:zappassword@localhost:5432/zapdelivery?schema=public"
GROQ_API_KEY="sua_chave_aqui"
```

### 🔄 Migrações do Banco de Dados

```bash
prisma generate
prisma db push
```

▶️ Executar a Aplicação

```bash
uv run src/main.py
```

A API estará disponível em:

📄 Documentação: http://localhost:8000/docs

🔌 Endpoint MCP: http://localhost:8000/mcp

🛠 Configuração do Cursor IDE
Adicione no arquivo de configuração do Cursor:

```bash
{
  "mcpServers": {
    "postgres-api": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```
