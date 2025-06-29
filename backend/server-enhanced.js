const express = require('express');
const path = require('path');
const { spawn } = require('child_process');
const anthropic = require('@anthropic-ai/sdk');
const readline = require('readline');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, '../frontend')));

// Initialize Anthropic client
const client = new anthropic.Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
});

// MCP Server management
class MCPServerManager {
    constructor() {
        this.process = null;
        this.requestId = 0;
        this.pendingRequests = new Map();
    }

    start() {
        this.process = spawn('python3', [path.join(__dirname, '../mcp-server/server.py')]);
        
        this.rl = readline.createInterface({
            input: this.process.stdout,
            output: this.process.stdin
        });

        this.rl.on('line', (line) => {
            try {
                const response = JSON.parse(line);
                const requestId = response.id;
                
                if (this.pendingRequests.has(requestId)) {
                    const { resolve } = this.pendingRequests.get(requestId);
                    this.pendingRequests.delete(requestId);
                    resolve(response);
                }
            } catch (error) {
                console.error('Error parsing MCP response:', error);
            }
        });

        this.process.on('error', (error) => {
            console.error('MCP server error:', error);
        });

        this.process.stderr.on('data', (data) => {
            console.error('MCP server stderr:', data.toString());
        });

        console.log('MCP server started');
    }

    async callTool(toolName, args) {
        const requestId = ++this.requestId;
        const request = {
            jsonrpc: '2.0',
            id: requestId,
            method: 'call_tool',
            params: {
                name: toolName,
                arguments: args
            }
        };

        return new Promise((resolve, reject) => {
            this.pendingRequests.set(requestId, { resolve, reject });
            
            // Send request to MCP server
            this.process.stdin.write(JSON.stringify(request) + '\n');
            
            // Timeout after 10 seconds
            setTimeout(() => {
                if (this.pendingRequests.has(requestId)) {
                    this.pendingRequests.delete(requestId);
                    reject(new Error('MCP server timeout'));
                }
            }, 10000);
        });
    }

    stop() {
        if (this.process) {
            this.process.kill();
        }
    }
}

const mcpServer = new MCPServerManager();

// Enhanced system prompt
const SYSTEM_PROMPT = `You are a helpful assistant that answers questions about thermodynamic properties of chemical components using ThermoEngine.

You have access to these MCP tools:
- calculate_property: Get actual thermodynamic property values
- list_available_components: Show what components are in the database
- list_available_properties: Show what properties can be calculated

CRITICAL INSTRUCTIONS:
1. ALWAYS use the calculate_property tool when asked about specific property values
2. NEVER estimate, approximate, or make up property values
3. If a property cannot be calculated, say exactly that - do not provide alternative values
4. Convert temperatures to Kelvin if given in Celsius (add 273.15)
5. Use atmospheric pressure (101325 Pa) if pressure is not specified
6. Always include units in your response

Response format:
- First acknowledge the request
- Use the appropriate tool
- Report the exact result from the tool
- If the tool returns an error, report that the property is not available`;

// API endpoint for chat
app.post('/api/chat', async (req, res) => {
    try {
        const { message } = req.body;
        
        if (!message) {
            return res.status(400).json({ error: 'Message is required' });
        }

        // Parse the message to see if it's asking for properties
        const needsCalculation = /density|pressure|heat|capacity|viscosity|enthalpy|entropy|property|calculate/i.test(message);
        const needsComponents = /component|available|list.*component/i.test(message);
        const needsProperties = /what.*properties|available.*properties|list.*properties/i.test(message);

        let response = '';

        if (needsCalculation) {
            // Extract parameters from the message
            const componentMatch = message.match(/(?:of|for)\s+(\w+)/i);
            const tempMatch = message.match(/(\d+\.?\d*)\s*°?C|celsius|(\d+\.?\d*)\s*K|kelvin/i);
            const propertyMatch = message.match(/density|pressure|heat.*capacity|viscosity|enthalpy|entropy/i);

            if (componentMatch && propertyMatch) {
                const component = componentMatch[1];
                const property = propertyMatch[0].toLowerCase().replace(/\s+/g, '_');
                
                let temperature = 298.15; // Default room temperature
                if (tempMatch) {
                    if (tempMatch[1]) { // Celsius
                        temperature = parseFloat(tempMatch[1]) + 273.15;
                    } else if (tempMatch[2]) { // Kelvin
                        temperature = parseFloat(tempMatch[2]);
                    }
                }

                try {
                    const result = await mcpServer.callTool('calculate_property', {
                        component,
                        property,
                        temperature,
                        pressure: 101325 // Default atmospheric pressure
                    });

                    if (result.result && result.result.output) {
                        response = `I'll calculate the ${property.replace(/_/g, ' ')} of ${component} for you.\n\n${result.result.output}`;
                    } else if (result.error) {
                        response = `I couldn't calculate that property. ${result.error.message}`;
                    }
                } catch (error) {
                    response = `There was an error accessing the ThermoEngine database: ${error.message}`;
                }
            } else {
                response = "I need more information to calculate a property. Please specify the component and property you're interested in.";
            }
        } else if (needsComponents) {
            try {
                const result = await mcpServer.callTool('list_available_components', {});
                response = result.result?.output || 'Could not retrieve component list.';
            } catch (error) {
                response = 'Error accessing component database.';
            }
        } else if (needsProperties) {
            try {
                const result = await mcpServer.callTool('list_available_properties', {});
                response = result.result?.output || 'Could not retrieve property list.';
            } catch (error) {
                response = 'Error accessing property list.';
            }
        } else {
            // For general questions, use Claude
            const claudeResponse = await client.messages.create({
                model: 'claude-3-sonnet-20240229',
                max_tokens: 500,
                system: SYSTEM_PROMPT,
                messages: [{ role: 'user', content: message }]
            });
            response = claudeResponse.content[0].text;
        }

        res.json({ response });
        
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ 
            error: 'Failed to process request',
            details: error.message 
        });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    mcpServer.start();
});

// Cleanup on exit
process.on('SIGINT', () => {
    mcpServer.stop();
    process.exit();
});

process.on('SIGTERM', () => {
    mcpServer.stop();
    process.exit();
});