#!/usr/bin/env python3
import json
import sys
import asyncio
from typing import Any, Dict, List, Optional
import numpy as np

# MCP server implementation for ThermoEngine
# Note: In production, you'd import ThermoEngine here
# from thermoengine import model

class MockThermoEngine:
    """Mock ThermoEngine with temperature-dependent calculations"""
    @staticmethod
    def get_property(component: str, property_name: str, temperature: float, pressure: float) -> Optional[float]:
        component_lower = component.lower()
        property_lower = property_name.lower()
        
        # Water properties with temperature dependence
        if component_lower == "water":
            if property_lower == "density":
                # Simplified water density calculation (kg/m³)
                # More accurate for 0-150°C range
                T_C = temperature - 273.15
                if 0 <= T_C <= 150:
                    # Polynomial approximation for water density
                    density = 999.97 - 0.0467 * T_C - 0.0088 * T_C**2 + 0.000015 * T_C**3
                    return round(density, 1)
                else:
                    return None
            elif property_lower == "viscosity":
                # Temperature-dependent viscosity (Pa·s)
                T_C = temperature - 273.15
                if 0 <= T_C <= 150:
                    # Andrade equation approximation
                    viscosity = 0.00002414 * 10**(247.8 / (temperature - 140))
                    return round(viscosity, 6)
            elif property_lower == "vapor_pressure":
                # Antoine equation for water vapor pressure (Pa)
                T_C = temperature - 273.15
                if 0 <= T_C <= 150:
                    A, B, C = 8.07131, 1730.63, 233.426
                    log_P_mmHg = A - B / (C + T_C)
                    P_Pa = (10**log_P_mmHg) * 133.322
                    return round(P_Pa, 1)
            elif property_lower == "heat_capacity":
                return 4184.0  # Approximate Cp for liquid water
                
        # Ethanol properties
        elif component_lower == "ethanol":
            if property_lower == "density":
                T_C = temperature - 273.15
                if -114 <= T_C <= 78:
                    # Linear approximation for ethanol density
                    density = 789 - 0.85 * (T_C - 20)
                    return round(density, 1)
            elif property_lower == "vapor_pressure":
                T_C = temperature - 273.15
                if -114 <= T_C <= 78:
                    # Antoine equation for ethanol
                    A, B, C = 8.11220, 1592.864, 226.184
                    log_P_mmHg = A - B / (C + T_C)
                    P_Pa = (10**log_P_mmHg) * 133.322
                    return round(P_Pa, 1)
            elif property_lower == "heat_capacity":
                return 2440.0
                
        # Basic data for other components
        elif component_lower == "methanol":
            if property_lower == "density":
                return 791.8
            elif property_lower == "heat_capacity":
                return 2534.0
                
        elif component_lower == "benzene":
            if property_lower == "density":
                return 876.5
            elif property_lower == "heat_capacity":
                return 1740.0
                
        elif component_lower == "toluene":
            if property_lower == "density":
                return 866.9
            elif property_lower == "heat_capacity":
                return 1687.0
                
        return None

class ThermoEngineMCPServer:
    def __init__(self):
        self.engine = MockThermoEngine()  # Replace with: model.Database()
        
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
                            "description": "Chemical component name (e.g., 'water', 'ethanol')"
                        },
                        "property": {
                            "type": "string",
                            "description": "Property to calculate (e.g., 'density', 'vapor_pressure')"
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
            # Convert temperature to Kelvin if needed
            if temperature < 200:  # Assume Celsius if too low
                temperature += 273.15
                
            result = self.engine.get_property(component, property, temperature, pressure)
            
            if result is None:
                return f"Could not find {property} data for {component} at T={temperature}K, P={pressure}Pa"
            
            return f"{property} of {component} at T={temperature}K, P={pressure}Pa: {result}"
            
        except Exception as e:
            return f"Error calculating property: {str(e)}"
    
    async def list_available_components(self) -> str:
        # In production, query ThermoEngine for available components
        components = ["water", "ethanol", "methanol", "benzene", "toluene"]
        return f"Available components: {', '.join(components)}"
    
    async def list_available_properties(self) -> str:
        properties = ["density", "viscosity", "heat_capacity", "vapor_pressure", "enthalpy", "entropy"]
        return f"Available properties: {', '.join(properties)}"

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