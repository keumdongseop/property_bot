# ThermoEngine Web Interface with Claude Integration

This project provides a web interface for querying thermodynamic properties of chemical components using Claude AI integrated with ThermoEngine through the Model Context Protocol (MCP).

## Architecture

```
User -> Web Frontend -> Backend Server -> Claude API
                                      -> MCP Server -> ThermoEngine
```

## Components

### 1. MCP Server (`mcp-server/`)
- Python server implementing the MCP protocol
- Provides tools for calculating thermodynamic properties
- Currently uses mock data (replace with actual ThermoEngine imports)

### 2. Web Frontend (`frontend/`)
- Clean, responsive interface for asking questions
- Real-time chat interface with Claude
- Example queries for easy testing

### 3. Backend Server (`backend/`)
- Express.js server
- Handles Claude API integration
- Manages MCP server communication
- Serves the frontend

## Setup Instructions

### Prerequisites
- Node.js (v14 or higher)
- Python 3.8+
- Anthropic API key

### Installation

1. **Install Python dependencies:**
   ```bash
   cd mcp-server
   pip install -r requirements.txt
   # Install actual ThermoEngine when available
   # pip install thermoengine
   ```

2. **Install Node.js dependencies:**
   ```bash
   cd backend
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

### Running the Application

1. **Start the backend server (which also starts the MCP server):**
   ```bash
   cd backend
   npm start
   ```

2. **Access the web interface:**
   Open http://localhost:3000 in your browser

## Usage

Ask natural language questions about thermodynamic properties:
- "What is the density of water at 25°C?"
- "Calculate the vapor pressure of ethanol at 78°C"
- "What properties can you calculate?"
- "List all available components"

## How It Works

1. **User asks a question** through the web interface
2. **Backend receives the question** and sends it to Claude with MCP tool definitions
3. **Claude interprets the question** and decides which MCP tools to use
4. **MCP server executes the tools** to calculate actual properties from ThermoEngine
5. **Claude formats the response** with the actual calculated values
6. **User sees the response** with real data (never made up)

## Key Features

- **No hallucination**: Claude only reports actual calculated values
- **Error handling**: Clear messages when properties can't be calculated
- **Unit awareness**: Automatic conversion between Celsius/Kelvin
- **Default values**: Uses atmospheric pressure when not specified

## Production Notes

To use with actual ThermoEngine:

1. Replace the `MockThermoEngine` class in `mcp-server/server.py` with:
   ```python
   from thermoengine import model
   self.engine = model.Database()
   ```

2. Update the property calculation methods to use actual ThermoEngine API calls

3. Consider implementing:
   - Connection pooling for MCP server
   - Caching for frequently requested properties
   - Rate limiting for API calls
   - Better error recovery

## Troubleshooting

- **MCP server not starting**: Check Python path and dependencies
- **No response from Claude**: Verify API key is set correctly
- **Properties not found**: Currently using mock data; implement actual ThermoEngine integration

## Security Considerations

- Never commit API keys
- Implement rate limiting in production
- Validate all user inputs
- Use HTTPS in production
- Consider authentication for public deployment# property_bot
