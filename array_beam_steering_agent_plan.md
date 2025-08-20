# Array Beam Steering Agent: Tool Architecture Plan

## Executive Summary
Transform the antenna array beam steering notebook into a specialized AI agent with a suite of tools for the HFSS Assistant. The agent will handle 1D linear array analysis, beam steering, and pattern validation through the OpenAI Agents SDK.

## Architecture Overview

### Agent Pattern
- **Type**: Specialized Agent (Array Beam Steering Expert)
- **Integration**: Agent-as-Tool pattern - orchestrator calls this specialized agent
- **Execution**: Tools execute code in persistent Jupyter notebook with HFSS connection
- **Context**: Uses `RunContextWrapper[HFSSAgentContext]` for state management

### Tool Design Philosophy
- **Granularity**: Medium-grain tools that encapsulate complete workflows
- **Composability**: Tools can be chained for complex operations
- **State Management**: Leverage notebook namespace for persistent state between tools
- **Error Recovery**: Robust error handling with actionable feedback

## Tool Suite Definition

### 1. **analyze_array_configuration**
**Purpose**: Complete array geometry analysis and characterization
**Inputs**: 
- `design_name` (optional)
- `frequency_hz` (optional, defaults to design frequency)
**Workflow**:
1. Extract port positions from HFSS boundaries
2. Detect array axis and orientation
3. Sort ports by physical position
4. Calculate element spacing
5. Store results in notebook namespace as `array_geometry`
**Returns**: Structured array configuration data

### 2. **initialize_beam_steering**
**Purpose**: Set up excitation control system
**Inputs**: 
- `design_name` (optional)
**Workflow**:
1. Check if array geometry exists (run analysis if needed)
2. Create post-processing variables for each port
3. Link variables to HFSS sources
4. Store setup state as `beam_steering_ready`
**Returns**: Success status with port configuration

### 3. **steer_beam_to_angle**
**Purpose**: Apply beam steering to specified angle
**Inputs**:
- `steering_angle` (degrees)
- `frequency_hz` (optional)
- `amplitude_taper` (optional, default "uniform")
**Workflow**:
1. Ensure beam steering is initialized
2. Calculate progressive phase shifts
3. Apply excitations to HFSS
4. Store current steering state
**Returns**: Applied excitation details

### 4. **extract_radiation_pattern**
**Purpose**: Get far-field pattern data
**Inputs**:
- `frequency_ghz` (optional)
- `cut_type` ("phi" or "theta")
- `cut_angle` (degrees)
- `expression` (default "GainTotal")
**Workflow**:
1. Extract far-field data using PyAEDT pandas method
2. Filter by frequency if specified
3. Extract specified cut
4. Store pattern data in notebook
**Returns**: Pattern data as structured output

### 5. **validate_beam_steering**
**Purpose**: Check steering accuracy
**Inputs**:
- `target_angle` (degrees)
- `tolerance_degrees` (optional, default 2.0)
**Workflow**:
1. Get current pattern data (extract if needed)
2. Find main beam direction
3. Calculate steering error
4. Grade accuracy (Excellent/Good/Fair/Poor)
**Returns**: Validation report with metrics

### 6. **plot_radiation_pattern**
**Purpose**: Visualize radiation patterns
**Inputs**:
- `plot_type` ("polar" or "cartesian")
- `title` (optional)
- `show_target` (optional, shows target angle)
**Workflow**:
1. Use stored pattern data or extract new
2. Generate matplotlib plot
3. Add annotations (main beam, target, etc.)
**Returns**: Plot display with description

### 7. **compare_steering_angles**
**Purpose**: Analyze multiple steering configurations
**Inputs**:
- `angles_list` (list of angles to test)
- `frequency_hz` (optional)
- `generate_report` (boolean)
**Workflow**:
1. Iterate through angles
2. Apply steering and extract patterns
3. Collect metrics for each angle
4. Generate comparison table/plot
**Returns**: Comparison results and visualizations

### 8. **optimize_beam_steering**
**Purpose**: Find optimal steering configuration
**Inputs**:
- `target_angle` (degrees)
- `optimization_goal` ("max_gain", "min_sll", "accuracy")
- `constraints` (optional)
**Workflow**:
1. Test variations around target
2. Evaluate based on goal
3. Apply best configuration
**Returns**: Optimization results and applied settings

## State Management Strategy

### Notebook Namespace Variables
```python
# Persistent state in notebook
array_geometry = {
    'axis': 'Y',
    'ports': ['1', '2', '3', '4', '5'],
    'positions': {...},
    'spacing': {'meters': 0.1, 'wavelengths': 0.634}
}

beam_steering_state = {
    'initialized': True,
    'current_angle': 30,
    'current_frequency': 1.9e9,
    'excitations': {...}
}

pattern_cache = {
    'last_extraction': timestamp,
    'data': DataFrame,
    'frequency': 1.9e9
}
```

### Context Object Extensions
```python
class ArraySteeringContext:
    active_design: str
    array_analyzed: bool
    steering_initialized: bool
    last_steering_angle: float
    pattern_available: bool
```

## Tool Chaining Patterns

### Common Workflows

**Basic Beam Steering**:
1. `analyze_array_configuration` → 
2. `initialize_beam_steering` → 
3. `steer_beam_to_angle(30)` → 
4. `validate_beam_steering(30)`

**Pattern Analysis**:
1. `extract_radiation_pattern` → 
2. `plot_radiation_pattern` → 
3. `validate_beam_steering`

**Optimization Flow**:
1. `analyze_array_configuration` → 
2. `initialize_beam_steering` → 
3. `optimize_beam_steering(target=45)`

## Error Handling Strategy

### Graceful Degradation
- If array not analyzed → automatically run analysis
- If steering not initialized → automatically initialize
- If pattern data missing → extract before validation

### Error Categories
1. **Configuration Errors**: Missing HFSS design, no ports found
2. **Geometry Errors**: Unable to determine array axis
3. **Steering Errors**: Invalid angle, frequency out of range
4. **Data Errors**: No simulation results, pattern extraction failed

### Recovery Actions
- Provide clear error messages with suggested fixes
- Offer alternative approaches when primary method fails
- Log detailed diagnostics for debugging

## Implementation Phases

### Phase 1: Core Tools (MVP)
- `analyze_array_configuration`
- `initialize_beam_steering`
- `steer_beam_to_angle`
- `validate_beam_steering`

### Phase 2: Visualization & Analysis
- `extract_radiation_pattern`
- `plot_radiation_pattern`
- `compare_steering_angles`

### Phase 3: Advanced Features
- `optimize_beam_steering`
- Support for amplitude tapering
- Grating lobe detection

## Success Metrics

### Functional Metrics
- Successfully steer beam within 2° accuracy
- Handle arrays with 2-20 elements
- Process requests in <5 seconds per tool

### User Experience Metrics
- Clear, actionable error messages
- Intuitive tool names and parameters
- Consistent output format

## Future Extensions

### 2D Array Support
- Extend geometry analyzer for planar arrays
- Add 2D phase gradient calculations
- Support θ and φ steering simultaneously

### Advanced Synthesis
- Null steering capability
- Sidelobe level control
- Pattern shaping algorithms

### Performance Optimization
- Cache pattern data between calls
- Batch multiple steering angles
- Parallel pattern extraction

## Tool Registration Example

```python
@function_tool
async def steer_beam_to_angle(
    context: RunContextWrapper[HFSSAgentContext],
    steering_angle: float,
    frequency_hz: Optional[float] = None,
    amplitude_taper: Optional[str] = "uniform"
) -> str:
    """
    Steers the antenna array beam to a specified angle.
    
    Args:
        steering_angle: Target steering angle in degrees
        frequency_hz: Operating frequency (uses design freq if not specified)
        amplitude_taper: Amplitude distribution ("uniform", "taylor", etc.)
    
    Returns:
        JSON string with steering results and applied excitations
    """
    # Implementation using notebook code execution
    ...
```

## Conclusion

This architecture provides a robust, extensible foundation for array beam steering capabilities in the HFSS Assistant. The medium-grain tool design balances flexibility with usability, while the state management approach leverages the notebook's persistent context effectively. The phased implementation allows for immediate value delivery while building toward advanced capabilities.