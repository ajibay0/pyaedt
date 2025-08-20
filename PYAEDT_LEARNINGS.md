# PyAEDT/HFSS Interface Learnings

This document captures discovered patterns, pitfalls, and solutions when working with the PyAEDT interface for HFSS. This is our evolving knowledge base to avoid repeating the same discoveries.

## Property Access Patterns

### ❌ Common Mistake: Using `excitation_names` property
```python
# This often fails silently or returns empty list
excitations = hfss.excitation_names  # Property exists but may fail internally
```

**Problem**: The `excitation_names` property exists in the Analysis class but internally calls `self.oboundary.GetExcitations()` which may not be available for all HFSS design types or configurations. When it fails, it returns an empty list instead of throwing an error.

### ✅ Correct Approach: Use `ports` property
```python
# More robust for HFSS designs
ports = hfss.ports  # Returns list of port names
```

**Why this works**: The `ports` property (defined in Design class) has better error handling and checks for method availability before calling COM methods.

### 🔍 Full Discovery Process
**Inheritance Chain**: `Hfss` → `FieldAnalysis3D` → `Analysis` → `Design`

Properties available at each level:
- **Design level**: `ports`, `boundaries` (most robust)
- **Analysis level**: `excitation_names`, `excitations`, `design_excitations` (may fail)

## Units and Frequency Handling

### ✅ Model Units Extraction
```python
# Get model units from HFSS design
units = hfss.modeler.model_units  # Returns "mm", "meter", "mil", "in", etc.
```

### ✅ Unit Conversion Using Simple Factors
```python
# Manual unit conversion - more reliable than PyAEDT's convert_units
def convert_to_meters(values, from_units):
    unit_factors = {
        "m": 1.0, "meter": 1.0, "meters": 1.0,
        "mm": 0.001, "millimeter": 0.001,
        "cm": 0.01, "centimeter": 0.01,
        "in": 0.0254, "inch": 0.0254, "inches": 0.0254,
        "ft": 0.3048, "foot": 0.3048, "feet": 0.3048,
        "mil": 0.0000254, "mils": 0.0000254,
        "um": 0.000001, "micrometer": 0.000001,
        "nm": 0.000000001, "nanometer": 0.000000001
    }
    
    unit_key = from_units.lower().strip()
    factor = unit_factors.get(unit_key, 1.0)  # Default to 1.0 if unknown
    
    if isinstance(values, (list, tuple)):
        return [v * factor for v in values]
    else:
        return values * factor
```

### ✅ Design Frequency Extraction
```python
# Get frequency from HFSS setup
def get_design_frequency(hfss):
    try:
        if hasattr(hfss, 'setups') and hfss.setups:
            setup = hfss.setups[0]  # Get first setup
            if hasattr(setup, 'props') and 'Frequency' in setup.props:
                freq_str = setup.props['Frequency']  # e.g., "10GHz"
                freq_hz = parse_frequency_string(freq_str)
                return freq_hz
        return 10e9  # Fallback
    except Exception as e:
        return 10e9  # Fallback
```

### ✅ Frequency String Parsing
```python
import re

def parse_frequency_string(freq_str):
    """Parse '10GHz' → 10e9 Hz."""
    freq_str = freq_str.replace(" ", "").lower()
    match = re.match(r'([0-9.]+)([a-z]+)', freq_str)
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        
        if unit == 'hz': return value
        elif unit == 'khz': return value * 1e3
        elif unit == 'mhz': return value * 1e6
        elif unit == 'ghz': return value * 1e9
        elif unit == 'thz': return value * 1e12
        else: return value * 1e9  # Assume GHz
    return 10e9  # Fallback
```

### 🎯 Critical Success Pattern: Units in Beam Steering
```python
# Always convert positions to meters for calculations
def calculate_steering_phases(self, theta_deg, frequency_hz):
    # Use meter-converted positions
    axis_index = {'X': 0, 'Y': 1, 'Z': 2}[self.geometry.array_axis]
    ref_position = self.geometry.port_positions_meters[ref_element]['position'][axis_index]
    
    for port in ports:
        element_pos = self.geometry.port_positions_meters[port]['position'][axis_index]
        relative_pos = element_pos - ref_position  # Distance in meters
        phase_rad = -k * relative_pos * np.sin(theta_rad)  # k in rad/m
```

## Working Code Examples

### Robust Port/Excitation Detection
```python
# Preferred approach - multiple fallbacks
def get_design_ports(hfss):
    """Get ports/excitations with robust error handling."""
    
    # Method 1: Use ports property (most reliable)
    try:
        ports = hfss.ports
        if ports:
            print(f"✓ Found {len(ports)} ports via .ports property:")
            for i, port in enumerate(ports, 1):
                print(f"  {i}. {port}")
            return ports
    except Exception as e:
        print(f"⚠ .ports property failed: {e}")
    
    # Method 2: Use boundaries and filter for excitations
    try:
        boundaries = hfss.boundaries
        excitation_boundaries = [b for b in boundaries if hasattr(b, 'type') and 'port' in str(b.type).lower()]
        if excitation_boundaries:
            port_names = [b.name for b in excitation_boundaries]
            print(f"✓ Found {len(port_names)} excitations via .boundaries:")
            for i, name in enumerate(port_names, 1):
                print(f"  {i}. {name}")
            return port_names
    except Exception as e:
        print(f"⚠ .boundaries property failed: {e}")
    
    # Method 3: Use excitations dictionary
    try:
        excitations_dict = hfss.excitations
        if excitations_dict:
            excitation_names = list(excitations_dict.keys())
            print(f"✓ Found {len(excitation_names)} excitations via .excitations:")
            for i, name in enumerate(excitation_names, 1):
                print(f"  {i}. {name}")
            return excitation_names
    except Exception as e:
        print(f"⚠ .excitations property failed: {e}")
    
    print("❌ Could not retrieve any excitations/ports")
    return []
```

### Robust Project Information Display
```python
def display_project_info(hfss):
    """Display comprehensive project information with error handling."""
    
    if hfss is None:
        print("❌ No HFSS connection available")
        return
    
    print("📊 Project Information:")
    
    # Basic info (usually reliable)
    try:
        print(f"  Project: {hfss.project_name}")
        print(f"  Design: {hfss.design_name}")
        print(f"  Solution Type: {hfss.solution_type}")
        print(f"  Design Type: {hfss.design_type}")
    except Exception as e:
        print(f"  ⚠ Could not get basic info: {e}")
    
    # Get ports/excitations
    print(f"\n🔌 Ports/Excitations:")
    ports = get_design_ports(hfss)
    
    # Get setups
    print(f"\n⚙️ Analysis Setups:")
    try:
        setups = hfss.setups
        if setups:
            for setup in setups:
                print(f"  - {setup.name}")
        else:
            print("  No setups found")
    except Exception as e:
        print(f"  ⚠ Could not retrieve setups: {e}")
```

## Error Handling Strategies

### 1. Always Use Try-Catch for PyAEDT Properties
PyAEDT properties can fail for various reasons:
- AEDT COM interface not fully initialized
- Design not fully loaded
- Property not available for specific design types
- Licensing issues

```python
# Template for robust property access
try:
    result = hfss.some_property
    if result:  # Check for empty results too
        # Process result
        pass
    else:
        print("Property returned empty result")
except Exception as e:
    print(f"Property access failed: {e}")
    # Fallback or alternative approach
```

### 2. Check for Method Availability
```python
# Good practice: Check if method exists before calling
if hasattr(hfss, 'method_name') and callable(getattr(hfss, 'method_name')):
    result = hfss.method_name()
else:
    print("Method not available for this design type")
```

## HFSS-Specific Gotchas

### 1. Student Version Limitations
```python
# Always specify student_version=True for Student licenses
hfss = Hfss(
    project=project_path,
    version="2025.2",
    student_version=True,  # Required for Student AEDT
    non_graphical=False
)
```

### 2. Project Loading vs. Design Creation
```python
# Loading existing project
hfss = Hfss(project=existing_project_path)  # Loads existing .aedt file

# Creating new project
hfss = Hfss()  # Creates new project in memory
```

### 3. Design Type Detection
```python
# Check if it's actually an HFSS design
if hfss.design_type != "HFSS":
    print(f"Warning: Expected HFSS design, got {hfss.design_type}")
```

## Debugging Tips

### 1. Check Object Attributes
```python
# Inspect available attributes
print("Available attributes:")
for attr in dir(hfss):
    if not attr.startswith('_'):
        print(f"  {attr}")
```

### 2. Check COM Object Status
```python
# Verify COM objects are available
print(f"oboundary available: {hfss.oboundary is not None}")
print(f"odesign available: {hfss.odesign is not None}")
print(f"desktop available: {hfss._desktop is not None}")
```

### 3. Enable Verbose Logging
```python
# Enable PyAEDT logging for debugging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Evolution Notes

### Property Reliability Ranking (Most to Least Reliable)
1. **Basic properties**: `project_name`, `design_name`, `solution_type` - Usually work
2. **Design-level properties**: `ports`, `boundaries` - More robust
3. **Analysis-level properties**: `setups` - Generally reliable  
4. **Boundary-dependent properties**: `excitation_names`, `excitations` - May fail

### Version-Specific Issues
- **AEDT 2025.2 Student**: Some boundary methods may not be available
- **Non-graphical mode**: Some visualization methods will fail
- **Remote connections**: Additional latency and potential COM timeouts

## Major Breakthrough: Variable-Based Excitation Management

### ✅ Solved: Getting and Setting Excitation Values

**Problem**: PyAEDT doesn't provide direct methods to get current excitation amplitude/phase values.

**Solution**: Use HFSS variables to manage excitations!

### Working Pattern:
```python
# 1. Create variables for each port
hfss["Port1_Magnitude"] = "1W"
hfss["Port1_Phase"] = "0deg" 

# 2. Use variables in edit_sources with $ prefix
sources = {"Port1:1": ("$Port1_Magnitude", "$Port1_Phase")}
hfss.edit_sources(sources)

# 3. Read current values anytime
current_mag = hfss["Port1_Magnitude"]  # Returns "1W"
current_phase = hfss["Port1_Phase"]    # Returns "0deg"
```

### Variable Types:
- **Design Variables**: `hfss["name"] = "value"` ✅ **WORKS for excitations with $ prefix**
- **Post-Processing Variables**: `hfss.variable_manager.set_variable("name", "value", is_post_processing=True)` ✅ **BEST for real-time tuning**

### Key Benefits:
1. **Bidirectional**: Can both set AND get excitation values
2. **Persistent**: Variables maintain values across operations
3. **Programmable**: Can be used in expressions and calculations
4. **HFSS Native**: Uses standard HFSS variable system

### ✅ OPTIMAL Pattern: Post-Processing Variables WITHOUT $ prefix
```python
# 1. Create post-processing variables (use "Port" prefix for numeric port names)
hfss.variable_manager.set_variable("Port1_Magnitude", "1W", is_post_processing=True)
hfss.variable_manager.set_variable("Port1_Phase", "0deg", is_post_processing=True)

# 2. Use in edit_sources WITHOUT $ prefix
sources = {"1:1": ("Port1_Magnitude", "Port1_Phase")}  # Note: port name "1", variable name "Port1_..."
hfss.edit_sources(sources)

# 3. Update variables for real-time tuning
hfss.variable_manager.set_variable("Port1_Magnitude", "2W", is_post_processing=True)
hfss.variable_manager.set_variable("Port1_Phase", "45deg", is_post_processing=True)
# HFSS automatically uses new values!
```

### Complete Array Management Pattern:
```python
class ArrayExcitationManager:
    def __init__(self, hfss):
        self.hfss = hfss
        self.ports = hfss.ports
        
        # Create POST-PROCESSING variables for each port (use "Port" prefix)
        for port in self.ports:
            self.hfss.variable_manager.set_variable(f"Port{port}_Magnitude", "1W", is_post_processing=True)
            self.hfss.variable_manager.set_variable(f"Port{port}_Phase", "0deg", is_post_processing=True)
        
        # Link to sources WITHOUT $ prefix
        sources = {f"{port}:1": (f"Port{port}_Magnitude", f"Port{port}_Phase") for port in self.ports}
        self.hfss.edit_sources(sources)
    
    def set_excitations(self, excitations):
        # Update post-processing variables - HFSS automatically applies changes!
        for port, vals in excitations.items():
            self.hfss.variable_manager.set_variable(f"Port{port}_Magnitude", vals['mag'], is_post_processing=True)
            self.hfss.variable_manager.set_variable(f"Port{port}_Phase", vals['phase'], is_post_processing=True)
```

### Important Notes:
- ✅ **Post-processing variables work WITHOUT $ prefix in edit_sources()**
- ✅ **Post-processing variables enable real-time tuning in optimization loops** 
- ⚠️ **Use "Port" prefix for numeric port names (e.g., "Port1_Magnitude" not "1_Magnitude")**
- Design variables work with $ prefix but post-processing variables are better for automation
- Variables persist across simulation runs
- Can use variables in expressions: `"Port1_Magnitude * 2"`

## Element Position Extraction from Port Faces

### ✅ Solved: Getting Array Element Positions

**Problem**: Need 3D coordinates of array elements for accurate beam steering calculations.

**Solution**: Extract port face centers from boundary objects!

### Working Pattern:
```python
def extract_port_positions(hfss):
    port_positions = {}
    
    # Loop through all boundaries
    for boundary in hfss.boundaries:
        # Check if it's a port boundary
        if "port" in str(boundary.type).lower():
            # Get face IDs from boundary properties
            if "Faces" in boundary.props:
                face_ids = boundary.props["Faces"]
                face_id = face_ids[0] if isinstance(face_ids, list) else face_ids
                
                # Get face center coordinates
                center = hfss.modeler.oeditor.GetFaceCenter(int(face_id))
                position = [float(x) for x in center]
                
                port_positions[boundary.name] = {
                    'position': position,
                    'x': position[0],
                    'y': position[1], 
                    'z': position[2]
                }
    
    return port_positions
```

### Key API Methods:
- **`hfss.boundaries`** - Get all boundary objects
- **`boundary.props["Faces"]`** - Get face IDs from port boundary
- **`hfss.modeler.oeditor.GetFaceCenter(face_id)`** - Get [x,y,z] coordinates
- **`boundary.type`** - Check if boundary is a port

### Array Geometry Analysis:
```python
# Calculate element spacing
import numpy as np
positions = np.array([info['position'] for info in port_positions.values()])
spacings = [np.linalg.norm(positions[i+1] - positions[i]) 
           for i in range(len(positions)-1)]
avg_spacing = np.mean(spacings)

# Determine array orientation
array_vector = positions[-1] - positions[0]
primary_axis = np.argmax(np.abs(array_vector))  # 0=X, 1=Y, 2=Z
```

### Benefits:
1. **Accurate Positioning**: Real geometry coordinates from HFSS
2. **Automatic Analysis**: Calculates spacing and orientation  
3. **Array Validation**: Checks if elements are uniformly spaced
4. **Foundation for Synthesis**: Enables correct phase calculations

## Far Field Data Extraction and Visualization

### ✅ Solved: Getting Far Field Radiation Pattern Data

**Problem**: Need to extract and visualize radiation patterns from HFSS simulations to validate beam steering.

**Solution**: Use PyAEDT's `get_far_field_data()` method with proper setup requirements.

### Far Field Setup Requirements:
```python
# 1. Create infinite sphere for far field calculations
sphere = hfss.insert_infinite_sphere(name="FarField_Sphere")

# 2. Ensure simulation is solved
setup = hfss.setups[0]  # Get first setup
# setup.solve()  # Solve if needed
```

### ✅ CORRECT Far Field Data Extraction Pattern:
```python
def extract_far_field_data_pandas(hfss, expressions="GainTotal", domain="3D", frequency_ghz=None):
    """Extract far field data using the correct PyAEDT pandas method."""
    
    # Get far field data using PyAEDT method
    ff = hfss.post.get_far_field_data(expressions=expressions, domain=domain)
    
    # Enable pandas output - THIS IS KEY!
    ff.enable_pandas_output = True
    
    # Get magnitude data as pandas DataFrame
    df_mag, _ = ff.full_matrix_mag_phase
    
    if df_mag.empty:
        return None
        
    # Reset index and rename columns properly
    df = (df_mag.reset_index()
               .rename(columns={"level_0": "Frequency",
                               "level_1": "Phi_deg", 
                               "level_2": "Theta_deg"}))
    
    # Filter by frequency if specified
    if frequency_ghz is not None:
        df = df[np.isclose(df["Frequency"], frequency_ghz)]
    
    return df
```

### Key PyAEDT Methods:
- **`hfss.insert_infinite_sphere(name="sphere_name")`** - Creates far field boundary
- **`hfss.post.get_far_field_data(expressions="GainTotal", domain="3D")`** - Gets far field data object  
- **`ff.enable_pandas_output = True`** - ⚠️ **CRITICAL**: Enables pandas DataFrame output
- **`ff.full_matrix_mag_phase`** - Returns (df_magnitude, df_phase) DataFrames
- **`df.reset_index().rename(columns={"level_0":"Frequency", "level_1":"Phi_deg", "level_2":"Theta_deg"})`** - Converts MultiIndex to proper columns

### ✅ CORRECT Radiation Pattern Plotting:
```python
def plot_radiation_pattern_corrected(df, expression="GainTotal", cut_mode="phi", cut_val_deg=0.0):
    """Plot radiation pattern using corrected pandas DataFrame."""
    
    # Extract the specified cut
    if cut_mode.lower() == "phi":
        # Phi cut: varies theta at constant phi
        mask = np.isclose(df["Phi_deg"], cut_val_deg, atol=0.5)
        angles = df.loc[mask, "Theta_deg"].to_numpy()  # 0-180°
        gains = df.loc[mask, expression].to_numpy()
        
        # Mirror theta: 180-0 → 180-360 for full pattern
        angles = np.concatenate([angles, 360 - angles[::-1]])
        gains = np.concatenate([gains, gains[::-1]])
        cut_label = f"φ = {cut_val_deg:.1f}°"
        
    elif cut_mode.lower() == "theta":
        # Theta cut: varies phi at constant theta  
        mask = np.isclose(df["Theta_deg"], cut_val_deg, atol=0.5)
        angles = df.loc[mask, "Phi_deg"].to_numpy()  # -180 to +180
        gains = df.loc[mask, expression].to_numpy()
        
        # Convert to 0-360° and sort
        angles = (angles + 360) % 360
        idx = np.argsort(angles)
        angles, gains = angles[idx], gains[idx]
        cut_label = f"θ = {cut_val_deg:.1f}°"
    
    # Convert to dB and apply floor
    gain_dB = 10 * np.log10(gains)
    gain_dB = np.clip(gain_dB, -40, None)
    
    # Create polar plot
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 8))
    theta_rad = np.deg2rad(angles)
    ax.plot(theta_rad, gain_dB, linewidth=2)
    
    # Style with proper dB scaling
    ax.set_theta_zero_location("N")   # 0° at top
    ax.set_theta_direction(-1)        # clockwise
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_title(f"{expression} - {cut_label}")
```

### Real-Time Pattern Visualization:
- **Step 1**: Update excitations using post-processing variables
- **Step 2**: Extract far field data for current excitation state
- **Step 3**: Plot and compare patterns
- **Step 4**: Repeat for different excitation scenarios

### Benefits:
1. **Visual Validation**: See actual beam steering effects
2. **Real-Time Updates**: Pattern changes immediately with excitation updates
3. **Comparison Capability**: Side-by-side pattern analysis
4. **Debugging Aid**: Identify unexpected pattern behavior
5. **Optimization Guidance**: Visual feedback for beam shaping

### Important Notes:
- ⚠️ **Simulation must be solved** before far field data extraction
- ✅ **Post-processing variables enable real-time pattern updates without re-solving**
- 📊 **Patterns update immediately** when excitation variables change
- 🎯 **Perfect for automated optimization loops** with visual feedback

## Future Learning Areas

### To Investigate:
- [ ] Reliable methods for detecting array vs single element designs
- [ ] Best practices for parametric sweep setup  
- [x] ✅ **SOLVED**: Excitation value get/set (use variables!)
- [x] ✅ **SOLVED**: Far field data extraction and visualization
- [ ] Robust field calculation expression building
- [ ] Optimal post-processing result extraction
- [ ] Error recovery strategies for failed simulations

### Code Patterns to Develop:
- [ ] Universal design validation function
- [ ] Robust result extraction with multiple fallbacks
- [ ] Array element position detection  
- [x] ✅ **DONE**: Automated excitation management (ArrayExcitationManager class)
- [x] ✅ **DONE**: Real-time far field pattern visualization

---

**Note**: This document should be updated every time we discover new PyAEDT behaviors, workarounds, or API quirks. Always check this document before writing new PyAEDT code.