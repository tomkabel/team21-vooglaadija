# GitAI Installation and Configuration Summary

## Installation

GitAI has been successfully installed system-wide using pnpm with the following method:

```bash
# Install using pnpm globally
pnpm add -g @lastwhisper-dev/gitai-cli

# Create system alias (added to ~/.zshrc)
alias gitai="/home/tomkabel/.local/share/pnpm/gitai"
```

## Configuration

### 1. Project Initialization
- Initialized GitAI in the current project with `gitai init`
- Created `.gitai/` directory with configuration files
- Created `.env-example` file with environment variable templates

### 2. OpenRouter Configuration
Configured GitAI to use OpenRouter with minimax model:

**`.gitai/config.yaml`:**
```yaml
llm:
    default:
        provider: openai
        model: minimax/minimax-m2.5:free
        apiKeyEnvVar: 'OPENAI_API_KEY'
        baseUrlEnvVar: 'OPENAI_BASE_URL'
        temperature: 0.7
```

**`.env` file:**
```bash
# OpenRouter Configuration (using OpenAI-compatible endpoint)
OPENAI_API_KEY="your-openrouter-api-key-here"
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

### 3. Model Configuration
- **Primary Model**: minimax/minimax-m2.5:free (via OpenRouter)
- **Provider**: OpenRouter (configured as OpenAI-compatible endpoint)
- **Temperature**: 0.7 (balanced creativity/consistency)

## Usage

### Commands Available:
- `gitai commit -n 3` - Generate 3 commit message suggestions
- `gitai pr --target main` - Generate PR description
- `gitai show-config` - Display current configuration
- `gitai --help` - Show help information

### Setup Required:
1. Add your OpenRouter API key to the `.env` file:
   ```bash
   OPENAI_API_KEY="your-actual-openrouter-api-key"
   ```

2. Ensure you're in a git repository with staged changes

3. Run `gitai commit` to generate AI-powered commit messages

## Alternative Models

If minimax-m2.5:free is not available, you can update the configuration to use:
- **Moonshot AI**: `moonshot-ai/kimi-k2-turbo-preview`
- **Other OpenRouter models**: Any model supported by OpenRouter

To change models, edit `.gitai/config.yaml` and update the `model` field.
