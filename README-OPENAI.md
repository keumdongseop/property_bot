# ThermoEngine Web with ChatGPT Integration

This version uses OpenAI's ChatGPT API instead of Claude for the AI integration.

## Quick Start

1. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

2. **Install dependencies and run:**
   ```bash
   cd thermoengine-web
   ./start-openai.sh
   ```

3. **Open http://localhost:3000 in your browser**

## Key Differences from Claude Version

- Uses OpenAI's function calling feature instead of MCP tools
- Supports GPT-4 Turbo for best results (can be changed to GPT-3.5 in the code)
- Same safety features - ChatGPT won't make up property values
- Same web interface and user experience

## Configuration

To use a different model, edit `backend/server-openai.js`:
```javascript
// Change this line to use different models:
model: 'gpt-4-turbo-preview',  // or 'gpt-3.5-turbo' for faster/cheaper
```

## Running Different Versions

```bash
# Run with ChatGPT
npm run start:openai

# Run with Claude
npm run start:claude

# Default (now uses ChatGPT)
npm start
```

## API Cost Considerations

- GPT-4 Turbo: More expensive but better at following instructions
- GPT-3.5 Turbo: Much cheaper, still works well for this use case
- Consider implementing caching to reduce API calls

## Example Usage

Same as before - ask questions like:
- "What is the density of water at 25°C?"
- "Calculate the vapor pressure of ethanol at 78°C"
- "List available components"

ChatGPT will use the function calling to get real data from ThermoEngine, never making up values.