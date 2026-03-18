# GitAI Complete Setup Guide

## ✅ Installation Complete

GitAI has been successfully installed and configured with OpenRouter integration.

### Installation Method
```bash
# Primary installation via pnpm (recommended)
pnpm add -g @lastwhisper-dev/gitai-cli

# System alias created in ~/.zshrc
alias gitai="/home/tomkabel/.local/share/pnpm/gitai"
```

## 🔧 Configuration Details

### Current Setup
- **Primary Model**: `minimax/minimax-m2.5:free` (via OpenRouter)
- **Provider**: OpenRouter (OpenAI-compatible endpoint)
- **Base URL**: https://openrouter.ai/api/v1
- **Temperature**: 0.7

### Configuration Files Created
- `.gitai/config.yaml` - Main configuration
- `.gitai/prompts/` - Prompt templates
- `.env` - Environment variables (API keys)

## 🚀 Available Models

### Primary (Configured)
- **minimax/minimax-m2.5:free** - Free, 196K context, excellent for coding

### Alternative Models (Available on OpenRouter)
- **moonshotai/kimi-k2:free** - Free Kimi K2 model, 131K context
- **moonshotai/kimi-k2-0905** - Updated Kimi with 256K context (paid)
- **moonshotai/kimi-k2.5** - Multimodal Kimi (paid)

## 📖 Usage Commands

```bash
# Generate commit messages
gitai commit -n 3                    # 3 suggestions
gitai commit --verbose              # With detailed output

# Generate PR descriptions  
gitai pr --target main              # Against main branch
gitai pr --target develop --verbose # Against develop with details

# Configuration
gitai show-config                   # Show current config
gitai --help                        # Help information
```

## 🔑 API Key Setup

1. **Get OpenRouter API Key**:
   - Visit https://openrouter.ai
   - Create account (free)
   - Go to API Keys section
   - Create new key (starts with "sk-or-v1-")

2. **Configure API Key**:
   ```bash
   # Edit .env file
   OPENAI_API_KEY="sk-or-v1-your-actual-key"
   OPENAI_BASE_URL=https://openrouter.ai/api/v1
   ```

## 🔄 Switching Models

To use different models, edit `.gitai/config.yaml`:

```yaml
# For Kimi K2 Free
model: moonshotai/kimi-k2:free

# For Kimi K2 Turbo (highest throughput)
model: moonshotai/kimi-k2-0905

# For Kimi K2.5 (multimodal)
model: moonshotai/kimi-k2.5
```

## 🎯 Model Recommendations

### For Git Commits & PRs
1. **minimax/minimax-m2.5:free** (current) - Excellent coding understanding
2. **moonshotai/kimi-k2:free** - Alternative free option

### For High Throughput
- **moonshotai/kimi-k2-0905** - Fastest Kimi model

### For Multimodal (if needed)
- **moonshotai/kimi-k2.5** - Supports images + text

## ✅ Testing Your Setup

```bash
# Stage some changes first
git add some-file.txt

# Test commit generation (will show API key error if not configured)
gitai commit -n 1

# If you see "Missing Authentication header", add your API key to .env
```

## 📊 Model Performance

- **MiniMax M2.5**: 80.2% SWE-Bench Verified, optimized for real-world productivity
- **Kimi K2**: 1T parameters, 32B active, excellent for coding and reasoning
- **Kimi K2.5**: Native multimodal, state-of-the-art visual coding

## 🔒 Security Notes

- API keys are stored in `.env` file (git-ignored)
- Configuration supports environment variables
- Never commit API keys to version control

---

**Status**: ✅ Ready to use with OpenRouter + MiniMax M2.5 Free
**Next Step**: Add your OpenRouter API key to `.env` file and test with `gitai commit`
