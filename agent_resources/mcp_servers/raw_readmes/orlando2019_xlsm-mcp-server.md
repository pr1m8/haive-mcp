# 📊 Servidor MCP para archivos Excel con macros (.xlsm)

**Autor:** Orlando Ospino (orlando2019)

Este servidor implementa el Model Context Protocol (MCP) para manipular archivos Excel que contienen macros (.xlsm). Utiliza el protocolo stdio para la comunicación, lo que permite integrarse fácilmente con clientes MCP como Claude Desktop, Cursor o Windsurf.

## 🌟 ¿Qué es MCP?

MCP (Model Context Protocol) es un protocolo que permite a los modelos de lenguaje interactuar con herramientas externas. Con este servidor, Claude y otros asistentes AI pueden manipular archivos Excel con macros de forma nativa, ampliando sus capacidades para ayudar en tareas de análisis de datos y automatización de oficina.

## ✨ Características

- Creación y manipulación de archivos Excel con macros (.xlsm)
- Lectura y escritura de datos en hojas de cálculo
- Gestión de hojas (crear, eliminar, renombrar)
- Listar y obtener información de macros VBA
- Aplicar formato a rangos de celdas
- Compatible con Python 3.10+
- Integración sencilla con entornos virtuales y clientes MCP modernos

## 🔧 Instalación

### Usando pip

```bash
pip install xlsm-mcp-server
```

### Usando uv (recomendado)

```bash
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt
```

## 📝 Uso

### Ejecución directa

```bash
python -m xlsm_mcp
```

O, si usas un entorno virtual:

```bash
.venv\Scripts\python.exe -m xlsm_mcp
```

### Configuración para Claude Desktop, Cursor o Windsurf

Agrega a tu configuración (por ejemplo, `settings.json`):

```json
"mcpServers": {
  "xlsm": {
    "command": "python",
    "args": ["-m", "xlsm_mcp"],
    "transport": "stdio"
  }
}
```

- Puedes omitir `"transport": "stdio"` en algunos clientes, pero es recomendable dejarlo para máxima compatibilidad.
- Si usas un entorno virtual, reemplaza `"python"` por la ruta a tu ejecutable Python.

### Argumentos avanzados

Puedes agregar argumentos personalizados en la sección `"args"` según lo requiera tu servidor, por ejemplo:

```json
"args": ["-m", "xlsm_mcp", "--log-level", "DEBUG"]
```

### 🛠️ Herramientas disponibles

- `read_data_from_excel`: Lee datos de una hoja de Excel
- `write_data_to_excel`: Escribe datos en una hoja de Excel
- `create_new_workbook`: Crea un nuevo libro de Excel con opción de habilitar macros
- `create_new_worksheet`: Crea una nueva hoja en un libro de Excel existente
- `get_workbook_metadata`: Obtiene metadatos del libro, incluyendo información sobre macros
- `list_macros_in_workbook`: Lista todas las macros disponibles en un libro
- `get_macro_details`: Obtiene información detallada sobre una macro específica
- `format_cell_range`: Aplica formato a un rango de celdas

## 💡 Ejemplos

### Leer datos de un archivo Excel

```python
# Ejemplo de uso para leer datos
result = await read_data_from_excel("ejemplo.xlsm", "Hoja1", "A1", "C10")
print(result["data"])
```

### Listar macros en un archivo

```python
# Ejemplo para listar macros
macros = await list_macros_in_workbook("ejemplo.xlsm")
for macro in macros["data"]:
    print(f"Macro: {macro['name']}")
```

## 📋 Casos de uso

Este servidor es especialmente útil para:

- Analistas de datos que trabajan con modelos AI
- Automatización de tareas administrativas
- Generación y manipulación de informes financieros
- Integración de IA con flujos de trabajo basados en Excel

## 👥 Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request en el repositorio.

## 👨‍💻 Autor

Desarrollado por Orlando Ospino ([@Orlando_Ospino](https://github.com/orlando2019))

## 📄 Licencia

MIT
