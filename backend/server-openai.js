const express = require('express');
const path = require('path');
const { spawn } = require('child_process');
const OpenAI = require('openai');
const readline = require('readline');
const { translateQuery } = require('./korean-translator');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(express.json());
// Serve the enhanced frontend if it exists, otherwise the original
const enhancedFrontend = path.join(__dirname, '../frontend/index-enhanced.html');
const originalFrontend = path.join(__dirname, '../frontend');

app.get('/', (req, res) => {
    // Check for Korean version first
    const koreanFrontend = path.join(__dirname, '../frontend/index-korean.html');
    if (require('fs').existsSync(koreanFrontend)) {
        res.sendFile(koreanFrontend);
    } else if (require('fs').existsSync(enhancedFrontend)) {
        res.sendFile(enhancedFrontend);
    } else {
        res.sendFile(path.join(originalFrontend, 'index.html'));
    }
});

app.use(express.static(originalFrontend));

// Initialize OpenAI client
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

// MCP Server management
class MCPServerManager {
    constructor() {
        this.process = null;
        this.requestId = 0;
        this.pendingRequests = new Map();
    }

    start() {
        // Use the virtual environment's Python if it exists, otherwise use python3
        const venvPython = path.join(__dirname, '..', 'venv', 'bin', 'python');
        const pythonPath = require('fs').existsSync(venvPython) ? venvPython : 'python3';
        console.log('Using Python:', pythonPath);
        this.process = spawn(pythonPath, [path.join(__dirname, '../mcp-server/server-nist.py')]);
        
        this.rl = readline.createInterface({
            input: this.process.stdout,
            output: this.process.stdin
        });

        this.rl.on('line', (line) => {
            console.log('MCP response:', line);
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
        
        console.log('Calling MCP tool:', toolName, 'with args:', args);

        return new Promise((resolve, reject) => {
            this.pendingRequests.set(requestId, { resolve, reject });
            
            // Send request to MCP server
            console.log('Sending to MCP:', JSON.stringify(request));
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

// System prompt for ChatGPT
const SYSTEM_PROMPT = `You are a ThermoEngine assistant that calculates thermodynamic properties using NIST data.

MANDATORY RULES:
- When asked for ANY property value (density, vapor pressure, heat capacity, etc.), you MUST use the calculate_property function
- You cannot provide property values without using the calculate_property function
- If someone asks "What is the density of water at 25°C?", you MUST call calculate_property with component="water", property="density", temperature=298.15, pressure=101325
- NEVER say "I'll calculate" or "Let me calculate" without actually calling the function
- ALWAYS convert Celsius to Kelvin (add 273.15)
- Use pressure=101325 Pa if not specified
- If a component is not found, use search_components to help the user find the correct name

CRITICAL: When you receive results from calculate_property, you MUST include the COMPLETE response including:
- The calculated value with units
- ALL Data Source Information provided
- CAS Registry Number
- Molecular Weight
- Calculation Method (if provided)
- Data Sources list
- Any reference notes

DO NOT summarize or shorten the response. Show the FULL output from the calculation tool.

Available functions:
- calculate_property(component, property, temperature, pressure) - REQUIRED for all property calculations
- search_components(query) - search for chemicals by name or formula in NIST database
- list_available_components() - lists common chemicals
- list_available_properties() - lists all available properties with units`;

// Define tools for OpenAI function calling
const tools = [
    {
        type: 'function',
        function: {
            name: 'calculate_property',
            description: 'Calculate thermodynamic property for a chemical component',
            parameters: {
                type: 'object',
                properties: {
                    component: {
                        type: 'string',
                        description: 'Chemical component name (e.g., water, ethanol)'
                    },
                    property: {
                        type: 'string',
                        description: 'Property to calculate (e.g., density, vapor_pressure)'
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
        }
    },
    {
        type: 'function',
        function: {
            name: 'list_available_components',
            description: 'List all available chemical components in the database',
            parameters: {
                type: 'object',
                properties: {}
            }
        }
    },
    {
        type: 'function',
        function: {
            name: 'list_available_properties',
            description: 'List all available properties that can be calculated',
            parameters: {
                type: 'object',
                properties: {}
            }
        }
    },
    {
        type: 'function',
        function: {
            name: 'search_components',
            description: 'Search for chemical components in the NIST database by name or formula',
            parameters: {
                type: 'object',
                properties: {
                    query: {
                        type: 'string',
                        description: 'Search query for chemical name or formula'
                    }
                },
                required: ['query']
            }
        }
    }
];

// API endpoint for chat
app.post('/api/chat', async (req, res) => {
    try {
        let { message } = req.body;
        const { language } = req.body;
        
        // Translate Korean to English if needed
        if (language === 'ko' || /[가-힣]/.test(message)) {
            console.log('Korean query detected:', message);
            message = translateQuery(message);
            console.log('Translated to:', message);
        }
        
        if (!message) {
            return res.status(400).json({ error: 'Message is required' });
        }

        // Create initial chat completion with tools
        const completion = await openai.chat.completions.create({
            model: 'gpt-4-0125-preview', // Using GPT-4 for better instruction following
            messages: [
                { role: 'system', content: SYSTEM_PROMPT },
                { role: 'user', content: message }
            ],
            tools: tools,
            tool_choice: 'auto'
        });

        const responseMessage = completion.choices[0].message;
        
        // Check if ChatGPT wants to use a tool
        console.log('Response message:', JSON.stringify(responseMessage, null, 2));
        if (responseMessage.tool_calls) {
            console.log('Tool calls detected:', responseMessage.tool_calls);
            const toolCallResults = [];
            
            // Execute each tool call
            for (const toolCall of responseMessage.tool_calls) {
                const functionName = toolCall.function.name;
                const functionArgs = JSON.parse(toolCall.function.arguments);
                
                try {
                    // Call MCP server
                    const result = await mcpServer.callTool(functionName, functionArgs);
                    console.log('MCP result:', result);
                    
                    // Check if the result contains JSON data
                    let content = result.result?.output || result.result || 'No result returned';
                    let structuredData = null;
                    
                    // If it's a JSON string starting with {, parse it and include in response
                    if (typeof content === 'string' && content.includes('"property":')) {
                        try {
                            const jsonData = JSON.parse(content);
                            // Keep the formatted text but also include the structured data
                            content = jsonData.formatted_text || content;
                            // Store the structured data for potential frontend use
                            structuredData = jsonData;
                            console.log('Parsed structured data:', JSON.stringify(structuredData, null, 2));
                        } catch (e) {
                            console.error('Failed to parse JSON data:', e);
                            // If parsing fails, use the original content
                        }
                    }
                    
                    toolCallResults.push({
                        tool_call_id: toolCall.id,
                        role: 'tool',
                        name: functionName,
                        content: content,
                        structuredData: structuredData
                    });
                } catch (error) {
                    toolCallResults.push({
                        tool_call_id: toolCall.id,
                        role: 'tool',
                        name: functionName,
                        content: `Error: ${error.message}`
                    });
                }
            }
            
            // Get final response with tool results
            const finalCompletion = await openai.chat.completions.create({
                model: 'gpt-4-0125-preview', // Same model as above
                messages: [
                    { role: 'system', content: SYSTEM_PROMPT },
                    { role: 'user', content: message },
                    responseMessage,
                    ...toolCallResults
                ]
            });
            
            // Check if we have structured data from tool calls
            let structuredData = null;
            for (const toolResult of toolCallResults) {
                if (toolResult.structuredData) {
                    structuredData = toolResult.structuredData;
                    break;
                }
            }
            
            res.json({ 
                response: finalCompletion.choices[0].message.content,
                structuredData: structuredData
            });
        } else {
            // No tool calls needed
            res.json({ response: responseMessage.content });
        }
        
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