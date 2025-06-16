# AstroMCP

A Model Context Protocol (MCP) server providing astrological chart functionality for AI assistants.

## 🚀 Quick Start

1. Clone the repository
2. Install dependencies:
   ```bash
   bun install
   ```
3. Start the server:
   ```bash
   bun run start
   ```

## ✨ Key Features

- Generate detailed astrological charts based on date, time, and location
- Seamless integration with AI assistants via Model Context Protocol
- Powered by [chart2txt](https://github.com/simpolism/chart2txt) for natural language chart interpretations
- Uses OpenStreetMap for geocoding locations
- Outputs planetary positions, house placements, and major aspects

## 📂 Project Structure

```
AstroMCP/
├── src/
│   ├── tools/
│   │   ├── getChart/        # Astrological chart functionality
│   │   └── ...              # Other tools
│   ├── utils/               # Shared utilities
│   ├── main.ts              # Server entry point
│   └── types.ts             # Shared type definitions
├── tests/                   # Test files
├── biome.json               # Linting configuration
├── tsconfig.json            # TypeScript configuration
└── package.json             # Project dependencies
```

## 🔮 Using the Astrology Tool

The `get_chart` tool accepts three parameters:

- `date`: Date in YYYY-MM-DD format
- `time`: Time in 24-hour format (HH:MM:SS)
- `location`: Location in "city, country" format

Example response:

```
Astrology Chart (location: New York, USA, at: 1/1/2001, 1:01:00 AM):

Ascendant is at 21° Libra. Sun is at 10° Capricorn. Moon is at 21° Pisces. Mercury is at 14° Capricorn. Venus is at 27° Aquarius. Mars is at 5° Scorpio. Jupiter is at 2° Gemini. Saturn is at 24° Taurus. Uranus is at 18° Aquarius. Neptune is at 5° Aquarius. Pluto is at 13° Sagittarius.

Sun is in house 4. Moon is in house 6. Mercury is in house 4. Venus is in house 5. Mars is in house 2. Jupiter is in house 9. Saturn is in house 8. Uranus is in house 5. Neptune is in house 5. Pluto is in house 3.

Sun is in conjunction with Mercury (orb: 3.8°). Moon is in sextile with Saturn (orb: 2.8°). Venus is in square with Jupiter (orb: 4.9°). Venus is in square with Saturn (orb: 2.7°). Mars is in square with Neptune (orb: 0.3°). Jupiter is in trine with Neptune (orb: 3.2°).
```

## ⚙️ Configuration

### API Endpoints

The server uses the following API endpoints:

- OpenStreetMap API for geocoding locations
- [Simple Astro API](https://github.com/simpolism/simple-astro-api) for planetary calculations (currently using hosted version)

### Creating New Tools

The project includes a script to help create new MCP tools:

```bash
bun run scripts/create-tool.ts <tool-name>
```

## 🛠️ Development

- **Run tests**: `bun test`
- **Format code**: `bun run format`
- **Lint code**: `bun run lint`
- **Build project**: `bun run build`

To add your AstroMCP server to Claude Desktop:

1. Build the project:
   ```bash
   bun run build
   ```
2. Add to your Claude Desktop config:
   ```json
   {
     "mcpServers": {
       "astrology-mcp-server": {
         "command": "/path/to/node",
         "args": ["/path/to/AstroMCP/dist/main.js"]
       }
     }
   }
   ```

## 📦 Publishing to npm

1. Ensure you're logged in to npm:
   ```bash
   npm login
   ```
2. Build the project:
   ```bash
   bun run build
   ```
3. Publish the package:
   ```bash
   npm publish
   ```

## Installing from npm (after publishing)

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "astro-server": {
      "command": "npx",
      "args": ["-y", "astrology-mcp-server"]
    }
  }
}
```
