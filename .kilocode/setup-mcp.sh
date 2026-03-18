#!/bin/bash
# KILOCODE MCP Setup Script
# Installs dependencies required for Model Context Protocol servers

set -e

echo "Setting up KILOCODE MCP dependencies..."

# Check if we're in the project root
if [ ! -f "package.json" ]; then
    echo "Error: Must run from project root directory"
    exit 1
fi

# Check for pnpm
if ! command -v pnpm &> /dev/null; then
    echo "Error: pnpm is required but not installed"
    exit 1
fi

# Install MCP SDK as dev dependency
echo "Installing @modelcontextprotocol/sdk..."
pnpm add -D @modelcontextprotocol/sdk

echo ""
echo "Setup complete! MCP servers are ready to use."
echo ""
echo "To use MCP servers:"
echo "1. Open Kilo Code settings in VS Code"
echo "2. Navigate to MCP Servers section"
echo "3. Enable the desired servers:"
echo "   - cobalt-api-inspector"
echo "   - cobalt-test-runner"
echo ""
echo "Configuration file: .kilocode/mcp/mcp.json"
