#!/bin/bash
# Setup script for GitAI with OpenRouter configuration

echo "🚀 Setting up GitAI with OpenRouter configuration..."

# Create the patched script directory
mkdir -p ~/.gitai-patched

# Copy and patch the original script
cp /home/tomkabel/.local/share/pnpm/global/5/.pnpm/@suhailroushan+gitai@1.0.6/node_modules/@suhailroushan/gitai/bin/gitai.sh ~/.gitai-patched/gitai-openrouter.sh

# Make it configurable
sed -i 's|DEEPSEEK_API_URL="https://api.deepseek.com/v1/chat/completions"|DEEPSEEK_API_URL="${DEEPSEEK_API_URL:-https://api.deepseek.com/v1/chat/completions}"|' ~/.gitai-patched/gitai-openrouter.sh
sed -i 's|DEEPSEEK_MODEL="deepseek-chat"|DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-deepseek-chat}"|' ~/.gitai-patched/gitai-openrouter.sh

# Make it executable
chmod +x ~/.gitai-patched/gitai-openrouter.sh

# Create configuration file
cat > ~/.gitai-openrouter-config << 'CONFIGEOF'
# GitAI OpenRouter Configuration
# Add these to your shell profile (~/.zshrc or ~/.bashrc)

# OpenRouter API Configuration
export DEEPSEEK_API_KEY="sk-or-v1-your-openrouter-api-key-here"
export DEEPSEEK_API_URL="https://openrouter.ai/api/v1/chat/completions"

# Model Selection - Choose your preferred model:

# FREE OPTIONS:
export DEEPSEEK_MODEL="minimax/minimax-m2.5:free"     # Recommended for coding (196K context)
# export DEEPSEEK_MODEL="moonshotai/kimi-k2:free"       # Alternative free model (131K context)

# PAID OPTIONS (if you prefer):
# export DEEPSEEK_MODEL="moonshotai/kimi-k2-0905"       # High-throughput Kimi (256K context)
# export DEEPSEEK_MODEL="gpt-4o-mini"                   # OpenAI via OpenRouter
# export DEEPSEEK_MODEL="anthropic/claude-3-haiku"      # Claude via OpenRouter

# Alias for easy usage
gitai() {
    source ~/.gitai-openrouter-config
    ~/.gitai-patched/gitai-openrouter.sh "$@"
}

export -f gitai
CONFIGEOF

echo "✅ GitAI OpenRouter setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Get your OpenRouter API key from https://openrouter.ai"
echo "2. Edit ~/.gitai-openrouter-config and add your API key"
echo "3. Add this line to your ~/.zshrc or ~/.bashrc:"
echo "   source ~/.gitai-openrouter-config"
echo ""
echo "🎯 Current model configured: minimax/minimax-m2.5:free"
echo "   (excellent for coding, 196K context window)"
echo ""
echo "🚀 Test it: source ~/.gitai-openrouter-config && gitai"
