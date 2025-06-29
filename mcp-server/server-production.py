#!/usr/bin/env python3
"""
Production MCP Server for ThermoEngine
This version uses actual ThermoEngine library for real calculations
"""

import json
import sys
import asyncio
from typing import Any, Dict, Optional
import numpy as np

# Import actual ThermoEngine
from thermoengine import model

class ThermoEngineMCPServer:
    def __init__(self):
        # Initialize ThermoEngine database
        self.modelDB = model.Database()
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "list_tools":
                return self.list_tools(request_id)
            elif method == "call_tool":
                tool_name = params.get("name", "")
                tool_params = params.get("arguments", {})
                
                if tool_name == "calculate_property":
                    result = await self.calculate_property(**tool_params)
                elif tool_name == "list_available_components":
                    result = await self.list_available_components()
                elif tool_name == "list_available_properties":
                    result = await self.list_available_properties()
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                    
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"output": result}
                }
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            }
    
    def list_tools(self, request_id: Any) -> Dict[str, Any]:
        tools = [
            {
                "name": "calculate_property",
                "description": "Calculate thermodynamic property for a chemical component",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "component": {
                            "type": "string",
                            "description": "Chemical component name (e.g., 'Water', 'Ethanol')"
                        },
                        "property": {
                            "type": "string",
                            "description": "Property to calculate (e.g., 'density', 'gibbs_energy')"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature in Kelvin"
                        },
                        "pressure": {
                            "type": "number",
                            "description": "Pressure in Pascal"
                        }
                    },
                    "required": ["component", "property", "temperature", "pressure"]
                }
            },
            {
                "name": "list_available_components",
                "description": "List all available chemical components in the database",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_available_properties",
                "description": "List all available properties that can be calculated",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools}
        }
    
    async def calculate_property(self, component: str, property: str, temperature: float, pressure: float) -> str:
        try:
            # Get phase object for the component
            phase = self.modelDB.get_phase(component)
            
            if phase is None:
                return f"Component '{component}' not found in database"
            
            # Set temperature and pressure
            phase.set_state(temperature, pressure)
            
            # Calculate requested property
            property_map = {
                'density': 'density',
                'gibbs_energy': 'gibbs_energy',
                'enthalpy': 'enthalpy',
                'entropy': 'entropy',
                'heat_capacity': 'heat_capacity_p',
                'volume': 'volume',
                'helmholtz_energy': 'helmholtz_energy',
                'internal_energy': 'internal_energy'
            }
            
            if property not in property_map:
                return f"Property '{property}' not available. Use list_available_properties to see options."
            
            # Get the property value
            method_name = property_map[property]
            if hasattr(phase, method_name):
                value = getattr(phase, method_name)()
                
                # Format with appropriate units
                units = {
                    'density': 'kg/m³',
                    'gibbs_energy': 'J/mol',
                    'enthalpy': 'J/mol',
                    'entropy': 'J/(mol·K)',
                    'heat_capacity': 'J/(mol·K)',
                    'volume': 'm³/mol',
                    'helmholtz_energy': 'J/mol',
                    'internal_energy': 'J/mol'
                }
                
                unit = units.get(property, '')
                return f"{property} of {component} at T={temperature}K, P={pressure}Pa: {value:.4f} {unit}"
            else:
                return f"Unable to calculate {property} for {component}"
                
        except Exception as e:
            return f"Error calculating property: {str(e)}"
    
    async def list_available_components(self) -> str:
        try:
            # Get all phases from the database
            phases = self.modelDB.phases
            
            # Extract unique component names
            components = sorted(set(phase.phase_name for phase in phases))
            
            return f"Available components ({len(components)}): {', '.join(components[:20])}..." \
                   if len(components) > 20 else f"Available components: {', '.join(components)}"
        except Exception as e:
            return f"Error listing components: {str(e)}"
    
    async def list_available_properties(self) -> str:
        properties = [
            "density - Mass density (kg/m³)",
            "gibbs_energy - Gibbs free energy (J/mol)",
            "enthalpy - Enthalpy (J/mol)",
            "entropy - Entropy (J/(mol·K))",
            "heat_capacity - Heat capacity at constant pressure (J/(mol·K))",
            "volume - Molar volume (m³/mol)",
            "helmholtz_energy - Helmholtz free energy (J/mol)",
            "internal_energy - Internal energy (J/mol)"
        ]
        return "Available properties:\n" + "\n".join(f"  • {prop}" for prop in properties)

async def main():
    server = ThermoEngineMCPServer()
    
    # Read from stdin and write to stdout (MCP protocol)
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            request = json.loads(line)
            response = await server.handle_request(request)
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())