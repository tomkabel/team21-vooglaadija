# KILOCODE Configuration

AI agent configuration and development tooling for the Cobalt media downloader project.

## Overview

This directory contains project-specific configuration for Kilo Code AI assistants, including:

- **Project context** (`agents.md`) - Architecture documentation and coding guidelines
- **Custom modes** (`modes/`) - Specialized AI personas for different tasks
- **Development skills** (`skills/`) - Reusable expertise modules
- **MCP servers** (`mcp/`) - Model Context Protocol servers for enhanced capabilities
- **Subagents** (`subagents/`) - Specialized AI task runners
- **Templates** (`templates/`) - Code generation templates
- **CI configuration** (`ci-config.json`) - Code review preferences

## Directory Structure

```
.kilocode/
├── README.md              # This file
├── agents.md              # Project context and guidelines
├── settings.json          # AI assistant configuration
├── ci-config.json         # Code review preferences
├── .gitignore            # Excludes generated artifacts
│
├── modes/                # Custom AI modes
│   ├── cobalt-api-dev.json
│   ├── cobalt-security.json
│   └── cobalt-web-dev.json
│
├── skills/               # Reusable expertise modules
│   └── cobalt-dev/
│       └── SKILL.md
│
├── mcp/                  # Model Context Protocol servers
│   ├── mcp.json          # Server registry
│   └── servers/          # MCP server implementations
│       ├── api-inspector.js
│       └── test-runner.js
│
├── subagents/            # Specialized task runners
│   ├── microservices-planner.md
│   ├── service-auditor.md
│   └── test-generator.md
│
├── templates/            # Code generation templates
│   └── new-service.md
│
├── workflows/            # Process documentation
│   ├── microservices-migration.md
│   └── new-service.md
│
├── shell/                # Shell configuration
│   └── aliases.sh
│
├── local-ai/             # Local AI settings (gitignored)
│   └── config.json
│
└── rules/                # Custom linting/rules (if any)
```

## Setup

### Prerequisites

- Kilo Code extension installed in VS Code
- Node.js 18+ (for MCP servers)

### MCP Server Dependencies

The MCP servers require the Model Context Protocol SDK. Install at the project root:

```bash
# From project root
pnpm add -D @modelcontextprotocol/sdk
```

Or use the setup script:

```bash
# Make the setup script executable and run it
chmod +x .kilocode/setup-mcp.sh
./.kilocode/setup-mcp.sh
```

### Configuration

1. **VS Code Settings**: The `settings.json` in this directory is automatically loaded by Kilo Code
2. **API Keys**: Configure in `local-ai/config.json` (created on first run, gitignored)
3. **Shell Aliases**: Source `.kilocode/shell/aliases.sh` in your shell profile

## Usage

### Available Modes

Switch between specialized AI personas:

- **cobalt-api-dev**: Backend development, service implementation, API design
- **cobalt-web-dev**: Frontend development, Svelte components, UI/UX
- **cobalt-security**: Security auditing, vulnerability assessment, hardening

### MCP Servers

Enable in Kilo Code settings to use:

- **cobalt-api-inspector**: List and inspect API services
- **cobalt-test-runner**: Execute and analyze tests

### Subagents

Spawn specialized agents for complex tasks:

```
"Spawn service-auditor to audit the YouTube service"
"Spawn test-generator to create tests for TikTok service"
"Spawn microservices-planner to plan service extraction"
```

### Adding a New Service

Follow the workflow in `workflows/new-service.md` or use the template in `templates/new-service.md`.

## Security

- **Never commit secrets**: `local-ai/config.json` and `shell/auto-launch.json` are gitignored
- **No vendored dependencies**: `node_modules/` is never committed; install via package manager
- **Review generated code**: Always review AI-generated code before committing

## Maintenance

### Updating Dependencies

If MCP servers need updated dependencies:

```bash
# Update at project root, never in .kilocode/
pnpm update @modelcontextprotocol/sdk
```

### Adding New Skills

1. Create a new directory under `skills/`
2. Add a `SKILL.md` with proper frontmatter
3. Follow the format in `skills/cobalt-dev/SKILL.md`

### Adding New Modes

1. Create a JSON file in `modes/`
2. Follow the schema in existing mode files
3. Update `settings.json` to enable the mode

## Best Practices

1. **Keep it minimal**: Only include configuration and documentation, not generated code
2. **Document everything**: Every skill, mode, and subagent should have clear documentation
3. **Version control**: Changes to .kilocode should be reviewed like any other code
4. **Test MCP servers**: Verify MCP servers work before committing changes
5. **Stay organized**: Use consistent naming and organization patterns

## Troubleshooting

### MCP Servers Not Starting

1. Ensure `@modelcontextprotocol/sdk` is installed: `pnpm list @modelcontextprotocol/sdk`
2. Check the MCP configuration in Kilo Code settings
3. Review server logs for errors

### Modes Not Appearing

1. Verify `settings.json` syntax is valid JSON
2. Check that mode files are valid JSON
3. Reload VS Code window

### Skills Not Triggering

1. Check SKILL.md frontmatter is correct
2. Verify the skill file is in the correct location
3. Restart Kilo Code extension

## Contributing

When adding to .kilocode:

1. Follow existing naming conventions
2. Document new additions in this README
3. Ensure `.gitignore` properly excludes generated files
4. Test thoroughly before submitting PR

## References

- [Kilo Code Documentation](https://kilo.ai/docs)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Project Architecture](agents.md)
