#!/bin/bash
# Cobalt Project Shell Aliases
# Source this file: source .kilocode/shell/aliases.sh

# ============================================
# Navigation Aliases
# ============================================

# Quick navigation to common directories
alias ca='cd /home/notroot/Documents/cobalt/ai1'
alias cw='cd /home/notroot/Documents/cobalt/ai1/web'
alias capi='cd /home/notroot/Documents/cobalt/ai1/api'
alias cpkg='cd /home/notroot/Documents/cobalt/ai1/packages'

# Navigation to specific service directories
alias cservices='cd /home/notroot/Documents/cobalt/ai1/api/src/services'
alias cutils='cd /home/notroot/Documents/cobalt/ai1/api/src/utils'
alias croutes='cd /home/notroot/Documents/cobalt/ai1/api/src/routes'

# ============================================
# Development Aliases
# ============================================

# Development server shortcuts
alias cdev='pnpm dev'
alias cdev-api='pnpm --prefix api dev'
alias cdev-web='pnpm --prefix web dev'
alias cdev-all='pnpm dev:all'

# Build commands
alias cbuild='pnpm build'
alias cbuild-api='pnpm --prefix api build'
alias cbuild-web='pnpm --prefix web build'

# Lint and formatting
alias clint='pnpm lint'
alias clint-fix='pnpm lint:fix'
alias cformat='pnpm format'

# Type checking
alias ctype='pnpm typecheck'
alias ctype-api='pnpm --prefix api typecheck'
alias ctype-web='pnpm --prefix web check'

# Package management
alias cinstall='pnpm install'
alias cadd='pnpm add'
alias cadd-dev='pnpm add -D'
alias cupdate='pnpm update'

# ============================================
# Test Aliases
# ============================================

# General test commands
alias ctest='pnpm test'
alias ctest-watch='pnpm test:watch'
alias ctest-coverage='pnpm test -- --coverage'
alias ctest-ui='pnpm test:ui'

# Service-specific tests
alias ctest-yt='pnpm --prefix api test youtube'
alias ctest-tiktok='pnpm --prefix api test tiktok'
alias ctest-twitter='pnpm --prefix api test twitter'
alias ctest-reddit='pnpm --prefix api test reddit'
alias ctest-bili='pnpm --prefix api test bilibili'
alias ctest-sound='pnpm --prefix api test soundcloud'

# Web-specific tests
alias ctest-web='pnpm --prefix web test'
alias ctest-e2e='pnpm test:e2e'

# ============================================
# Docker Aliases
# ============================================

# Docker Compose commands
alias cbuild='docker-compose build'
alias crun='docker-compose up'
alias crun-d='docker-compose up -d'
alias cstop='docker-compose down'
alias crestart='docker-compose restart'
alias clog='docker-compose logs -f'
alias cps='docker-compose ps'

# Individual container management
alias cbuild-api='docker-compose build api'
alias cbuild-web='docker-compose build web'
alias crun-api='docker-compose up api'
alias crun-web='docker-compose up web'

# ============================================
# Git Aliases
# ============================================

# Git shortcuts with Cobalt context
alias cstatus='git status'
alias cbranch='git branch'
alias ccheckout='git checkout'
alias ccommit='git commit'
alias cpush='git push'
alias cpull='git pull'
alias cfetch='git fetch'
alias cmerge='git merge'
alias crebase='git rebase'

# Feature branch workflow
alias cfeature='git checkout -b feature/'
alias cbugfix='git checkout -b bugfix/'
alias chotfix='git checkout -b hotfix/'

# ============================================
# Utility Aliases
# ============================================

# Search and grep
alias cgrep='grep -r --include="*.js" --include="*.ts" --include="*.svelte"'
alias cfind='find . -type f -name'

# File operations
alias cls='ls -la'
alias cclear='clear'

# Environment
alias cenv='cat .env'
alias cenv-local='cp .env.example .env'

# Logs
alias ctail='tail -f'
alias ctail-api='tail -f api/logs/*.log 2>/dev/null || echo "No API logs found"'
alias ctail-web='tail -f web/logs/*.log 2>/dev/null || echo "No web logs found"'

# ============================================
# Kilo Code Integration Aliases
# ============================================

# MCP Server management
alias cmcp-start='node .kilocode/mcp/servers/api-inspector.js'
alias cmcp-test='node .kilocode/mcp/servers/test-runner.js'

# Quick edit common files
alias cedit-env='${EDITOR:-nano} .env'
alias cedit-config='${EDITOR:-nano} .kilocode/mcp/mcp.json'
alias cedit-aliases='${EDITOR:-nano} .kilocode/shell/aliases.sh'

# ============================================
# Export functions for more complex operations
# ============================================

# Quick service test with pattern
cservice-test() {
  if [ -z "$1" ]; then
    echo "Usage: cservice-test <service-name> [test-pattern]"
    echo "Example: cservice-test youtube 'should download'"
    return 1
  fi
  
  local service=$1
  local pattern=$2
  
  if [ -n "$pattern" ]; then
    pnpm --prefix api test "$service" -- --testNamePattern="$pattern"
  else
    pnpm --prefix api test "$service"
  fi
}

# Quick URL validation
validate-url() {
  if [ -z "$1" ]; then
    echo "Usage: validate-url <url> [service-type]"
    echo "Example: validate-url 'https://youtube.com/watch?v=...' youtube"
    return 1
  fi
  
  node -e "
    const url = '$1';
    const patterns = {
      youtube: /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\/.+/,
      tiktok: /^https?:\/\/(www\.)?tiktok\.com\/.+/,
      twitter: /^https?:\/\/(www\.)?(twitter\.com|x\.com)\/.+/,
      reddit: /^https?:\/\/(www\.)?reddit\.com\/.+/,
      bilibili: /^https?:\/\/(www\.)?bilibili\.com\/.+/,
      soundcloud: /^https?:\/\/(www\.)?soundcloud\.com\/.+/
    };
    
    const detected = Object.entries(patterns)
      .filter(([_, p]) => p.test(url))
      .map(([s, _]) => s);
    
    console.log('URL:', url);
    console.log('Detected services:', detected.length > 0 ? detected.join(', ') : 'none');
    console.log('Valid:', detected.length > 0 ? '✓' : '✗');
  "
}

# Show Cobalt project status
cstatus-full() {
  echo "=== Cobalt Project Status ==="
  echo ""
  echo "Directory: $(pwd)"
  echo "Git branch: $(git branch --show-current 2>/dev/null || echo 'N/A')"
  echo ""
  echo "Node version: $(node --version 2>/dev/null || echo 'N/A')"
  echo "pnpm version: $(pnpm --version 2>/dev/null || echo 'N/A')"
  echo ""
  echo "Docker status:"
  docker-compose ps 2>/dev/null || echo "  Not running or not configured"
  echo ""
  echo "Recent commits:"
  git log --oneline -5 2>/dev/null || echo "  N/A"
}

export -f cservice-test validate-url cstatus-full

# ============================================
# Welcome message
# ============================================

echo "Cobalt project aliases loaded!"
echo "Quick commands: ca (root), cw (web), capi (api), cdev (dev), ctest (test)"
echo "Run 'cstatus-full' for project status"
