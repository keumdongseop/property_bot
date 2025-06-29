const express = require('express');
const path = require('path');
const { spawn } = require('child_process');
const anthropic = require('@anthropic-ai/sdk');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, '../frontend')));

// Initialize Anthropic client
const client = new anthropic.Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
});

// Start MCP server as a child process
let mcpProcess;

function startMCPServer() {
    mcpProcess = spawn('python3', [path.join(__dirname, '../mcp-server/server.py')]);
    
    mcpProcess.on('error', (error) => {
        console.error('Failed to start MCP server:', error);
    });
    
    mcpProcess.stderr.on('data', (data) => {
        console.error('MCP server error:', data.toString());
    });
    
    console.log('MCP server started');
}

// System prompt that instructs Claude to use the MCP tools
const SYSTEM_PROMPT = `You are a helpful assistant that answers questions about thermodynamic properties of chemical components. 

You have access to a ThermoEngine MCP server with the following tools:
- calculate_property: Calculate thermodynamic properties for chemical components
- list_available_components: List all available chemical components
- list_available_properties: List all calculable properties

IMPORTANT RULES:
1. When asked about a specific property, ALWAYS use the calculate_property tool to get the actual value
2. NEVER make up or estimate property values - only report what the tool returns
3. If the tool cannot find a property, clearly state that the data is not available
4. Always specify units when reporting values
5. If temperature is given in Celsius, convert to Kelvin for the tool
6. Default to atmospheric pressure (101325 Pa) if not specified

Example responses:
- "I'll calculate the density of water at 25°C for you." [use tool] "The density of water at 298.15K and 101325Pa is 997.0 kg/m³"
- "I couldn't find vapor pressure data for that component at the specified conditions."`;

// API endpoint for chat
app.post('/api/chat', async (req, res) => {
    try {
        const { message } = req.body;
        
        if (!message) {
            return res.status(400).json({ error: 'Message is required' });
        }

        // Create a message with Claude that has MCP integration
        const response = await client.messages.create({
            model: 'claude-3-opus-20240229',
            max_tokens: 1000,
            system: SYSTEM_PROMPT,
            messages: [
                {
                    role: 'user',
                    content: message
                }
            ],
            tools: [
                {
                    name: 'calculate_property',
                    description: 'Calculate thermodynamic property for a chemical component',
                    input_schema: {
                        type: 'object',
                        properties: {
                            component: {
                                type: 'string',
                                description: 'Chemical component name'
                            },
                            property: {
                                type: 'string',
                                description: 'Property to calculate'
                            },
                            temperature: {
                                type: 'number',
                                description: 'Temperature in Kelvin'
                            },
                            pressure: {
                                type: 'number',
                                description: 'Pressure in Pascal'
                            }
                        },
                        required: ['component', 'property', 'temperature', 'pressure']
                    }
                },
                {
                    name: 'list_available_components',
                    description: 'List all available chemical components',
                    input_schema: {
                        type: 'object',
                        properties: {}
                    }
                },
                {
                    name: 'list_available_properties',
                    description: 'List all available properties that can be calculated',
                    input_schema: {
                        type: 'object',
                        properties: {}
                    }
                }
            ]
        });

        // Process tool calls if any
        let finalResponse = response.content[0].text;
        
        if (response.stop_reason === 'tool_use') {
            // Handle tool calls by communicating with MCP server
            const toolCalls = response.content.filter(c => c.type === 'tool_use');
            
            for (const toolCall of toolCalls) {
                // Send request to MCP server
                const mcpRequest = {
                    jsonrpc: '2.0',
                    id: toolCall.id,
                    method: 'call_tool',
                    params: {
                        name: toolCall.name,
                        arguments: toolCall.input
                    }
                };
                
                // Here you would send to MCP server and get response
                // For now, using mock response
                const toolResult = await callMCPServer(mcpRequest);
                
                // Create follow-up message with tool results
                const followUp = await client.messages.create({
                    model: 'claude-3-opus-20240229',
                    max_tokens: 1000,
                    system: SYSTEM_PROMPT,
                    messages: [
                        {
                            role: 'user',
                            content: message
                        },
                        response,
                        {
                            role: 'user',
                            content: [
                                {
                                    type: 'tool_result',
                                    tool_use_id: toolCall.id,
                                    content: toolResult
                                }
                            ]
                        }
                    ]
                });
                
                finalResponse = followUp.content[0].text;
            }
        }

        res.json({ response: finalResponse });
        
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ 
            error: 'Failed to process request',
            details: error.message 
        });
    }
});

// Mock function to simulate MCP server calls
async function callMCPServer(request) {
    // In production, this would communicate with the actual MCP server process
    const { name, arguments: args } = request.params;
    
    if (name === 'calculate_property') {
        const { component, property, temperature, pressure } = args;
        
        // Mock responses
        if (component.toLowerCase() === 'water' && property.toLowerCase() === 'density') {
            if (Math.abs(temperature - 298.15) < 1) {
                return 'density of water at T=298.15K, P=101325Pa: 997.0 kg/m³';
            }
        } else if (component.toLowerCase() === 'ethanol' && property.toLowerCase() === 'vapor_pressure') {
            if (Math.abs(temperature - 351.15) < 1) { // ~78°C
                return 'vapor_pressure of ethanol at T=351.15K, P=101325Pa: 101325 Pa';
            }
        }
        
        return `Could not find ${property} data for ${component} at T=${temperature}K, P=${pressure}Pa`;
    } else if (name === 'list_available_components') {
        return 'Available components: water, ethanol, methanol, benzene, toluene';
    } else if (name === 'list_available_properties') {
        return 'Available properties: density, viscosity, heat_capacity, vapor_pressure, enthalpy, entropy';
    }
    
    return 'Unknown tool call';
}

// Start server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    startMCPServer();
});

// Cleanup on exit
process.on('SIGINT', () => {
    if (mcpProcess) {
        mcpProcess.kill();
    }
    process.exit();
});