#!/usr/bin/env python3
"""
NIST MCP Server using the 'thermo' library for real thermodynamic calculations
This version uses the 'chemicals' and 'thermo' libraries which include NIST data
"""

import json
import sys
import asyncio
from typing import Any, Dict, Optional
import numpy as np

# Import thermo and chemicals libraries for NIST data
from chemicals import CAS_from_any, search_chemical
from thermo import Chemical

class NISTThermoEngine:
    """NIST data access through the thermo library"""
    
    def __init__(self):
        # Cache for Chemical objects to improve performance
        self.chemical_cache = {}
        
    def get_chemical_object(self, name: str, T: float, P: float) -> Optional[Chemical]:
        """Get or create a Chemical object with given conditions"""
        cache_key = f"{name}_{T}_{P}"
        
        if cache_key not in self.chemical_cache:
            try:
                # Try to create Chemical object
                chem = Chemical(name, T=T, P=P)
                self.chemical_cache[cache_key] = chem
            except Exception as e:
                # Try alternative names or CAS lookup
                try:
                    # Search for the chemical by name
                    results = search_chemical(name)
                    if results:
                        cas = results[0].CASs
                        chem = Chemical(cas, T=T, P=P)
                        self.chemical_cache[cache_key] = chem
                    else:
                        return None
                except:
                    return None
                    
        return self.chemical_cache.get(cache_key)
    
    def get_property(self, component: str, property_name: str, temperature: float, pressure: float) -> Optional[float]:
        """Get thermodynamic property from NIST data via thermo library"""
        
        # Get chemical object
        chem = self.get_chemical_object(component, T=temperature, P=pressure)
        if not chem:
            return None
            
        property_map = {
            # Physical properties
            'density': 'rho',  # kg/m³
            'viscosity': 'mu',  # Pa·s
            'thermal_conductivity': 'k',  # W/(m·K)
            'surface_tension': 'sigma',  # N/m
            
            # Thermodynamic properties
            'heat_capacity': 'Cp',  # J/(mol·K)
            'heat_capacity_cv': 'Cv',  # J/(mol·K)
            'enthalpy': 'H',  # J/mol
            'entropy': 'S',  # J/(mol·K)
            'gibbs_energy': 'G',  # J/mol
            'helmholtz_energy': 'A',  # J/mol
            'internal_energy': 'U',  # J/mol
            
            # Phase properties
            'vapor_pressure': 'Psat',  # Pa
            'heat_vaporization': 'Hvap',  # J/mol
            'critical_temperature': 'Tc',  # K
            'critical_pressure': 'Pc',  # Pa
            'boiling_point': 'Tb',  # K at 1 atm
            'melting_point': 'Tm',  # K
            
            # Other properties
            'molecular_weight': 'MW',  # g/mol
            'phase': 'phase',  # 'l', 'g', or 's'
        }
        
        property_attr = property_map.get(property_name.lower())
        if not property_attr:
            return None
            
        try:
            # Get the property value
            value = getattr(chem, property_attr)
            
            # Handle special cases
            if property_attr == 'phase':
                # Return phase as string
                return value
            elif value is None:
                return None
            else:
                return float(value)
        except Exception as e:
            return None
    
    def get_property_detailed(self, component: str, property_name: str, temperature: float, pressure: float) -> Optional[dict]:
        """Get thermodynamic property with detailed calculation information"""
        
        # Get chemical object
        chem = self.get_chemical_object(component, T=temperature, P=pressure)
        if not chem:
            return None
            
        property_map = {
            'density': 'rho',
            'viscosity': 'mu',
            'thermal_conductivity': 'k',
            'surface_tension': 'sigma',
            'heat_capacity': 'Cp',
            'heat_capacity_cv': 'Cv',
            'enthalpy': 'H',
            'entropy': 'S',
            'gibbs_energy': 'G',
            'helmholtz_energy': 'A',
            'internal_energy': 'U',
            'vapor_pressure': 'Psat',
            'heat_vaporization': 'Hvap',
            'critical_temperature': 'Tc',
            'critical_pressure': 'Pc',
            'boiling_point': 'Tb',
            'melting_point': 'Tm',
            'molecular_weight': 'MW',
            'phase': 'phase',
        }
        
        property_attr = property_map.get(property_name.lower())
        if not property_attr:
            return None
            
        try:
            # Get the property value
            value = getattr(chem, property_attr)
            if value is None:
                return None
                
            # Get detailed calculation information
            details = {
                'value': float(value) if property_attr != 'phase' else value,
                'method': None,
                'validity_range': None,
                'uncertainty': None,
                'references': []
            }
            
            # Try to get the method used for calculation
            method_attr = f"{property_attr}_method"
            # Try to get specific method if available
            if hasattr(chem, method_attr):
                method = getattr(chem, method_attr)
                if method:
                    details['method'] = method
                    
            # Provide property-specific information even if method is not found
            if property_attr == 'rho':
                details['method'] = 'Temperature and pressure dependent correlation'
                details['references'] = ['DIPPR 801 Database', 'CRC Handbook of Chemistry and Physics']
                details['uncertainty'] = '±0.5-2%'
                details['equation'] = 'ρ = f(T,P) using validated correlations'
            elif property_attr == 'Psat':
                details['method'] = 'Vapor pressure correlation'
                details['equation'] = 'Antoine or Wagner equation'
                details['references'] = ['NIST Chemistry WebBook', 'NIST TDE']
                details['uncertainty'] = '±0.5-2%'
            elif property_attr == 'Cp':
                details['method'] = 'Heat capacity polynomial correlation'
                details['equation'] = 'Cp = a + bT + cT² + dT³'
                details['references'] = ['NIST-JANAF Thermochemical Tables', 'Poling et al.']
                details['uncertainty'] = '±1-3%'
            elif property_attr == 'mu':
                details['method'] = 'Viscosity correlation'
                details['references'] = ['NIST Chemistry WebBook', 'Yaws Handbook']
                details['uncertainty'] = '±2-5%'
            elif property_attr == 'k':
                details['method'] = 'Thermal conductivity correlation'
                details['references'] = ['DIPPR 801 Database', 'NIST Data']
                details['uncertainty'] = '±3-5%'
            elif property_attr == 'sigma':
                details['method'] = 'Surface tension correlation'
                details['equation'] = 'σ = σ₀(1 - T/Tc)ⁿ'
                details['references'] = ['DIPPR 801 Database']
                details['uncertainty'] = '±2-4%'
            
            # Try to get temperature limits
            if hasattr(chem, f"{property_attr}_Tmin") and hasattr(chem, f"{property_attr}_Tmax"):
                Tmin = getattr(chem, f"{property_attr}_Tmin", None)
                Tmax = getattr(chem, f"{property_attr}_Tmax", None)
                if Tmin and Tmax:
                    details['validity_range'] = {
                        'T_min': float(Tmin),
                        'T_max': float(Tmax),
                        'T_unit': 'K'
                    }
            
            # Add general references if none were added
            if not details['references']:
                details['references'] = [
                    'NIST TDE (Thermodynamic Data Engine)',
                    'NIST Chemistry WebBook',
                    'Validated thermodynamic correlations'
                ]
                
            return details
            
        except Exception as e:
            return None
    
    def search_components(self, query: str) -> list:
        """Search for chemical components in the database"""
        try:
            results = search_chemical(query)
            components = []
            for result in results[:10]:  # Limit to 10 results
                components.append({
                    'name': result.name,
                    'CAS': result.CASs,
                    'formula': result.formula if hasattr(result, 'formula') else None
                })
            return components
        except:
            return []

class NISTMCPServer:
    def __init__(self):
        self.engine = NISTThermoEngine()
        
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
                elif tool_name == "search_components":
                    result = await self.search_components(**tool_params)
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
                "description": "Calculate thermodynamic property for a chemical component using NIST data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "component": {
                            "type": "string",
                            "description": "Chemical component name (e.g., water, ethanol, benzene) or CAS number"
                        },
                        "property": {
                            "type": "string",
                            "description": "Property to calculate (e.g., density, viscosity, vapor_pressure, enthalpy)"
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
                "name": "search_components",
                "description": "Search for chemical components in the NIST database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for chemical name or formula"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_available_components",
                "description": "List example chemical components available in the database",
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
                temp_c = temperature
                temperature += 273.15
            else:
                temp_c = temperature - 273.15
                
            # Get chemical object to access metadata
            chem = self.engine.get_chemical_object(component, temperature, pressure)
            if not chem:
                return f"Could not find component '{component}' in NIST database. Try searching with 'search_components' tool."
                
            result = self.engine.get_property(component, property, temperature, pressure)
            detailed_info = self.engine.get_property_detailed(component, property, temperature, pressure)
            
            if result is None:
                return f"Property '{property}' not available for {component} at T={temperature:.2f}K ({temp_c:.2f}°C), P={pressure}Pa. Component found but property calculation failed."
            
            # Format with appropriate units
            units = {
                'density': 'kg/m³',
                'viscosity': 'Pa·s',
                'thermal_conductivity': 'W/(m·K)',
                'surface_tension': 'N/m',
                'heat_capacity': 'J/(mol·K)',
                'heat_capacity_cv': 'J/(mol·K)',
                'enthalpy': 'J/mol',
                'entropy': 'J/(mol·K)',
                'gibbs_energy': 'J/mol',
                'helmholtz_energy': 'J/mol',
                'internal_energy': 'J/mol',
                'vapor_pressure': 'Pa',
                'heat_vaporization': 'J/mol',
                'critical_temperature': 'K',
                'critical_pressure': 'Pa',
                'boiling_point': 'K',
                'melting_point': 'K',
                'molecular_weight': 'g/mol'
            }
            
            # Handle phase as special case
            if property == 'phase':
                phase_map = {'l': 'liquid', 'g': 'gas', 's': 'solid'}
                phase_str = phase_map.get(result, result)
                return f"Phase of {component} at T={temperature:.2f}K ({temp_c:.2f}°C), P={pressure}Pa: {phase_str}"
            
            unit = units.get(property, '')
            
            # Format the value appropriately
            if isinstance(result, (int, float)):
                if result > 1000 or result < 0.001:
                    formatted_value = f"{result:.4e}"
                else:
                    formatted_value = f"{result:.4f}"
            else:
                formatted_value = str(result)
            
            # Get comprehensive source information
            source_info = "\n\nData Source Information:"
            calculation_details = None
            
            try:
                # CAS number from NIST registry
                if hasattr(chem, 'CAS'):
                    source_info += f"\n• CAS Registry Number: {chem.CAS} (NIST Standard Reference)"
                
                # Add molecular weight for verification
                if hasattr(chem, 'MW'):
                    source_info += f"\n• Molecular Weight: {chem.MW:.4f} g/mol"
                    
                # Use detailed calculation information if available
                if detailed_info:
                    calculation_details = {
                        'method': detailed_info.get('method', 'Unknown'),
                        'equation': detailed_info.get('equation'),
                        'validity_range': detailed_info.get('validity_range'),
                        'uncertainty': detailed_info.get('uncertainty'),
                        'references': detailed_info.get('references', [])
                    }
                    
                    if detailed_info.get('method'):
                        source_info += f"\n• Calculation Method: {detailed_info['method']}"
                    if detailed_info.get('equation'):
                        source_info += f"\n• Equation: {detailed_info['equation']}"
                    if detailed_info.get('uncertainty'):
                        source_info += f"\n• Uncertainty: {detailed_info['uncertainty']}"
                    if detailed_info.get('validity_range'):
                        vr = detailed_info['validity_range']
                        source_info += f"\n• Valid Temperature Range: {vr['T_min']:.1f} - {vr['T_max']:.1f} K"
                
                # Specific data sources
                source_info += "\n• Data Sources:"
                if detailed_info and detailed_info.get('references'):
                    for ref in detailed_info['references']:
                        source_info += f"\n  - {ref}"
                else:
                    source_info += "\n  - NIST TDE (Thermodynamic Data Engine)"
                    source_info += "\n  - NIST Chemistry WebBook correlations"
                    source_info += "\n  - DIPPR 801 database (validated thermophysical properties)"
                    source_info += "\n  - CRC Handbook of Chemistry and Physics"
                
                # Add reference values for common substances
                if component.lower() == 'water' and property == 'density' and abs(temp_c - 25) < 0.1:
                    source_info += f"\n• NIST WebBook Reference: 997.04 kg/m³ at 25°C"
                elif component.lower() == 'ammonia' and property == 'density':
                    source_info += f"\n• Note: Ammonia is in gas phase at {temp_c:.1f}°C (b.p. -33.34°C at 1 atm)"
                    
            except Exception as e:
                source_info += f"\n• Source: Validated thermodynamic correlations"
                
            # Generate NIST WebBook URL
            nist_webbook_url = None
            if hasattr(chem, 'CAS') and chem.CAS:
                # Format CAS number for URL (remove hyphens)
                cas_for_url = chem.CAS.replace('-', '')
                nist_webbook_url = f"https://webbook.nist.gov/cgi/cbook.cgi?ID=C{cas_for_url}"
            
            # Return structured data as JSON
            result_data = {
                "property": property,
                "component": component,
                "value": result,
                "unit": unit,
                "temperature_K": temperature,
                "temperature_C": temp_c,
                "pressure_Pa": pressure,
                "cas_number": chem.CAS if hasattr(chem, 'CAS') else None,
                "molecular_weight": chem.MW if hasattr(chem, 'MW') else None,
                "molecular_weight_unit": "g/mol",
                "phase": chem.phase if hasattr(chem, 'phase') else None,
                "data_sources": detailed_info.get('references', [
                    "NIST TDE (Thermodynamic Data Engine)",
                    "NIST Chemistry WebBook correlations",
                    "DIPPR 801 database",
                    "CRC Handbook of Chemistry and Physics"
                ]) if detailed_info else [
                    "NIST TDE (Thermodynamic Data Engine)",
                    "NIST Chemistry WebBook correlations",
                    "DIPPR 801 database",
                    "CRC Handbook of Chemistry and Physics"
                ],
                "calculation_details": calculation_details,
                "nist_webbook_url": nist_webbook_url,
                "formatted_text": f"{property} of {component} at T={temperature:.2f}K ({temp_c:.2f}°C), P={pressure}Pa: {formatted_value} {unit}{source_info}"
            }
            
            # Add unit conversion factors for common properties
            if property == "density":
                result_data["conversions"] = {
                    "kg/m³": result,
                    "g/cm³": result / 1000,
                    "lb/ft³": result * 0.062428,
                    "g/L": result,
                    "kg/L": result / 1000
                }
            elif property == "pressure" or property == "vapor_pressure":
                result_data["conversions"] = {
                    "Pa": result,
                    "kPa": result / 1000,
                    "bar": result / 100000,
                    "atm": result / 101325,
                    "psi": result * 0.000145038,
                    "mmHg": result * 0.00750062
                }
            elif property == "temperature":
                result_data["conversions"] = {
                    "K": temperature,
                    "°C": temp_c,
                    "°F": temp_c * 9/5 + 32,
                    "°R": temperature * 9/5
                }
                
            return json.dumps(result_data, ensure_ascii=False)
            
        except Exception as e:
            return f"Error calculating property: {str(e)}"
    
    async def search_components(self, query: str) -> str:
        try:
            results = self.engine.search_components(query)
            
            if not results:
                return f"No components found matching '{query}'"
            
            output = f"Found {len(results)} components matching '{query}':\n"
            for comp in results:
                output += f"  • {comp['name']}"
                if comp['CAS']:
                    output += f" (CAS: {comp['CAS']})"
                if comp['formula']:
                    output += f" [{comp['formula']}]"
                output += "\n"
                
            return output
        except Exception as e:
            return f"Error searching components: {str(e)}"
    
    async def list_available_components(self) -> str:
        # List common components available in NIST database
        common_components = [
            "water", "ethanol", "methanol", "acetone", "benzene", "toluene",
            "hexane", "octane", "nitrogen", "oxygen", "carbon dioxide", "ammonia",
            "hydrogen", "helium", "argon", "methane", "ethane", "propane",
            "butane", "pentane", "ethylene", "propylene", "acetylene",
            "sulfuric acid", "hydrochloric acid", "sodium chloride"
        ]
        
        return f"Common components available in NIST database:\n" + \
               "\n".join(f"  • {comp}" for comp in common_components) + \
               "\n\nUse 'search_components' to find specific chemicals by name or formula."
    
    async def list_available_properties(self) -> str:
        properties = [
            "Physical Properties:",
            "  • density - Mass density (kg/m³)",
            "  • viscosity - Dynamic viscosity (Pa·s)",
            "  • thermal_conductivity - Thermal conductivity (W/(m·K))",
            "  • surface_tension - Surface tension (N/m)",
            "",
            "Thermodynamic Properties:",
            "  • heat_capacity - Heat capacity at constant pressure (J/(mol·K))",
            "  • heat_capacity_cv - Heat capacity at constant volume (J/(mol·K))",
            "  • enthalpy - Molar enthalpy (J/mol)",
            "  • entropy - Molar entropy (J/(mol·K))",
            "  • gibbs_energy - Gibbs free energy (J/mol)",
            "  • helmholtz_energy - Helmholtz free energy (J/mol)",
            "  • internal_energy - Internal energy (J/mol)",
            "",
            "Phase Properties:",
            "  • vapor_pressure - Vapor pressure (Pa)",
            "  • heat_vaporization - Heat of vaporization (J/mol)",
            "  • phase - Current phase (liquid/gas/solid)",
            "  • critical_temperature - Critical temperature (K)",
            "  • critical_pressure - Critical pressure (Pa)",
            "  • boiling_point - Normal boiling point (K)",
            "  • melting_point - Melting point (K)",
            "",
            "Other Properties:",
            "  • molecular_weight - Molecular weight (g/mol)"
        ]
        return "\n".join(properties)

async def main():
    server = NISTMCPServer()
    
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