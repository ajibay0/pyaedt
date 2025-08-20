# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Claude's Role in This Project

**You are a development assistant helping to build Jupyter notebooks that will become tools for an AI-powered HFSS Assistant application.** Your primary purpose is to help create, test, and refine PyAEDT-based workflows that will be integrated into a larger AI system.

## Project Context: HFSS AI Assistant Application

This PyAEDT repository supports the development of a sophisticated **AI-powered desktop assistant for HFSS** - a conversational AI system that transforms complex electromagnetic simulation workflows into natural language interactions.

### The Larger AI Assistant System:

**Core Purpose**: Users describe electromagnetic problems in plain English, and the AI automatically generates HFSS geometry, sets up simulations, runs them, and analyzes results.

**Key Capabilities of the Full System**:
1. **Natural Language to HFSS**: Converts user descriptions into proper HFSS geometry, materials, boundaries, and simulation setups
2. **Real-Time Simulation Management**: Launches HFSS simulations, monitors progress, and triggers post-processing automatically
3. **Intelligent Code Generation**: AI agents generate PyAEDT code, execute it in Jupyter notebooks, and handle errors intelligently
4. **Multi-Agent Orchestration**: Specialized AI agents coordinate (geometry creation, simulation setup, post-processing, debugging)
5. **Streaming Interface**: Real-time chat interface with live simulation updates

**Architecture**: Three-tier system with Electron frontend, Python FastAPI backend with streaming capabilities, and PyAEDT integration layer with Jupyter notebook execution.

### Your Development Focus:

The notebooks you help create here will become **LLM-callable tools** in that system. Each notebook should demonstrate:
- Complete HFSS workflows from geometry to results
- Error handling and debugging patterns
- Reusable code patterns that can be templated
- Clear documentation for AI agent integration
- Robust parameter handling for automated generation

## Project Overview

This is the core PyAEDT library (`ansys.aedt.core`) - a Python API for Ansys Electronics Desktop (AEDT). The focus here is on **HFSS (High Frequency Structure Simulator)** for building intelligent automation workflows.

## Development Commands

### Testing
- Run unit tests: `pytest tests/unit -m unit -v`
- Run integration tests: `pytest tests/integration -m integration -v`
- Run system tests: `pytest tests/system -m system -v`
- Run HFSS-specific tests: `pytest tests/system/general/test_20_HFSS.py -v`
- Run with coverage: `pytest tests/ --cov=ansys.aedt.core --cov-report=html`

### Code Quality
- Format code: `black src/ tests/ --line-length=120`
- Sort imports: `isort src/ tests/ --profile=black --line-length=120`
- Lint code: `flake8 .`
- Check spelling: `codespell src/ansys/aedt/core`

### Documentation
- Build docs: `cd doc && make html`
- Run doc tests: `pytest --doctest-modules src/ansys/aedt/core/`

## HFSS Architecture Overview

### Core HFSS Class (`src/ansys/aedt/core/hfss.py`)
The main `Hfss` class inherits from:
- `FieldAnalysis3D`: Base 3D electromagnetic simulation functionality
- `ScatteringMethods`: S-parameter and network analysis methods 
- `CreateBoundaryMixin`: Boundary condition creation utilities

**Key solution types:**
- "Modal": Port-based excitation with modal field solutions
- "Terminal": Lumped port excitation for circuit integration
- "SBR+": Shooting and Bouncing Rays for electrically large structures
- "Transient": Time-domain electromagnetic simulation
- "Eigenmode": Resonant frequency and Q-factor analysis

### HFSS Application Structure

#### 1. **Desktop and Session Management** (`desktop.py`)
```python
from ansys.aedt.core import Hfss
with Hfss(version="2025.1", non_graphical=False) as hfss:
    # HFSS operations here
    pass
```

#### 2. **3D Modeler** (`modeler/modeler_3d.py`)
- **Primitives**: Box, cylinder, sphere creation (`modeler/cad/primitives_3d.py`)
- **CAD Operations**: Boolean operations, sweeps, lofts
- **Material Assignment**: Conductor, dielectric, magnetic materials
- **Coordinate Systems**: Local coordinate system management

#### 3. **Boundary Conditions** (`modules/boundary/hfss_boundary.py`)
- **Ports**: Wave ports, lumped ports, Floquet ports
- **Absorbing Boundaries**: PML, radiation boundaries
- **Symmetry**: Perfect E/H, master/slave boundaries
- **Excitations**: Voltage, current, incident wave sources

#### 4. **Mesh Operations** (`modules/mesh.py`)
- **Mesh Refinement**: Adaptive mesh refinement settings
- **Manual Mesh**: Length-based, skin-depth based meshing
- **Mesh Operations**: Surface approximation, curvilinear elements

#### 5. **Analysis Setup** (`modules/solve_setup.py`)
- **Frequency Sweeps**: Linear, logarithmic, single-point
- **Solver Settings**: Matrix solver, iterative solver options
- **Convergence**: Delta S, max passes, error tolerance

#### 6. **Post-Processing** (`visualization/post/post_hfss.py`)
- **Field Plots**: E-field, H-field, current density visualization
- **Far Field**: Radiation patterns, gain, directivity
- **S-Parameters**: Network parameter extraction
- **Reports**: Frequency response, Smith charts

### HFSS Extensions (`extensions/hfss/`)
Pre-built automation workflows:
- `choke_designer.py`: Common mode choke design automation
- `shielding_effectiveness.py`: EMI shielding analysis
- `push_excitation_from_file.py`: Automated excitation setup

### Key HFSS Patterns

#### Application Initialization
```python
# Recommended context manager approach
with Hfss(solution_type="Modal") as hfss:
    # Design operations
    pass

# Direct instantiation (remember to close)
hfss = Hfss(solution_type="Terminal", version="2025.1")
# ... operations ...
hfss.close()
```

#### Geometry Creation
```python
# Access modeler through hfss instance
box = hfss.modeler.create_box([0, 0, 0], [10, 20, 5], "substrate")
hfss.modeler.assign_material(box, "FR4_epoxy")

# Create more complex geometries
cylinder = hfss.modeler.create_cylinder("CS1", [0, 0, 0], 2, 10, 0, "via")
```

#### Boundary and Excitation Setup
```python
# Create wave ports
port1 = hfss.wave_port(assignment=face_id, portname="Port1")

# Assign radiation boundary
hfss.assign_radiation_boundary_to_objects(object_list=["airbox"])

# Set up excitations
hfss.create_wave_port_from_sheet(sheet_object, portname="WavePort1")
```

#### Analysis and Solve
```python
# Create analysis setup
setup = hfss.create_setup(name="Setup1", solution_type="Modal")
setup.props["Frequency"] = "10GHz"

# Add frequency sweep
sweep = hfss.create_linear_count_sweep("Setup1", "GHz", 1, 20, 401)

# Solve
hfss.analyze_setup("Setup1")
```

#### Post-Processing
```python
# Get S-parameters
s_data = hfss.post.get_solution_data("S(Port1,Port1)")

# Create far field plot
ff_setup = hfss.insert_infinite_sphere(name="3D")

# Field visualization
hfss.post.create_fieldplot_volume(objects=["substrate"], 
                                  quantity="Mag_E", 
                                  setup="Setup1")
```

### Variable Management
- Design variables: `hfss["length"] = "10mm"`
- Project variables: `hfss["$global_freq"] = "2.4GHz"`
- Access variable manager: `hfss.variable_manager`

### Error Handling
- All methods use `@pyaedt_function_handler()` decorator
- Check `hfss.logger` for detailed error information
- Most operations return boolean success indicators or objects

### Remote Execution
```python
# Server setup
from ansys.aedt.core.common_rpc import pyaedt_service_manager
pyaedt_service_manager()

# Client connection
hfss = Hfss(machine="server_ip", port=50000)
```

## PyAEDT/HFSS Learnings and Best Practices

**🚨 IMPORTANT: Always check `PYAEDT_LEARNINGS.md` before writing PyAEDT code!**

This repository contains a comprehensive learnings document (`PYAEDT_LEARNINGS.md`) that captures discovered patterns, common pitfalls, and proven solutions when working with the PyAEDT interface. This knowledge base helps avoid repeating the same discovery process and contains:

- **Property Access Patterns**: Correct vs incorrect ways to access HFSS properties
- **Error Handling Strategies**: Robust patterns for PyAEDT API calls
- **Working Code Examples**: Tested code snippets with multiple fallbacks
- **HFSS-specific Gotchas**: Version-specific issues and workarounds
- **Debugging Tips**: Techniques for troubleshooting PyAEDT issues

**Before writing any PyAEDT code, always:**
1. Check `PYAEDT_LEARNINGS.md` for existing patterns
2. Use the provided robust code templates
3. Add new discoveries to the learnings document

## Testing for HFSS Development

### HFSS Test Structure
- **Unit tests**: `tests/unit/` - Mock AEDT interactions
- **System tests**: `tests/system/general/test_20_HFSS.py` - Full HFSS integration
- **Example models**: `tests/system/general/example_models/` - Test geometries

### Running HFSS Tests
```bash
# Run only HFSS system tests  
pytest tests/system/general/test_20_HFSS.py -v

# Run specific test method
pytest tests/system/general/test_20_HFSS.py::TestClass::test_method -v

# Skip tests requiring AEDT license
pytest tests/ -m "not system" -v
```

## Notebook Development Guidelines for AI Assistant Integration

When creating notebooks that will become AI assistant tools, focus on:

### 1. **Complete Workflow Examples**
- Start-to-finish HFSS simulations (geometry → setup → solve → post-process)
- Error handling and recovery patterns
- Parameter validation and bounds checking
- Clear success/failure indicators

### 2. **AI-Friendly Code Structure**
- **Parameterized Functions**: Create reusable functions with clear parameter definitions
- **Modular Design**: Break workflows into logical steps that can be chained together
- **Error Recovery**: Handle common HFSS errors gracefully with suggested fixes
- **Documentation**: Rich docstrings explaining physics concepts and parameter meanings

### 3. **Tool Categories to Develop**
Based on the AI assistant's needs, prioritize notebooks for:

**Geometry Generation Tools:**
- Standard RF components (antennas, filters, couplers, transmission lines)
- Parametric component builders with design equations
- Array generators and periodic structures

**Simulation Setup Assistants:**
- Intelligent port placement and configuration
- Material assignment workflows
- Boundary condition selection based on problem type
- Mesh optimization strategies

**Analysis Configuration:**
- Frequency sweep planning (adaptive vs. interpolating)
- Convergence criteria selection
- Multi-physics setup (thermal-EM coupling)

**Post-Processing Automation:**
- Standard report generation (S-parameters, VSWR, efficiency)
- Field visualization and animation
- Performance metric calculations
- Data export and formatting

**Diagnostic and Troubleshooting:**
- Simulation health checks
- Common error pattern detection and fixes
- Design rule validation
- Performance optimization suggestions

### 4. **Integration Patterns**
Structure notebooks to support the AI assistant's multi-agent architecture:
- **Input Validation**: Robust parameter checking with helpful error messages
- **Progress Reporting**: Status updates that can be streamed to users
- **Result Formatting**: Standardized output formats for AI interpretation
- **Context Preservation**: Save intermediate results for workflow chaining

### 5. **Testing and Validation**
- Test with various parameter combinations
- Validate against known analytical solutions where possible
- Document expected simulation times and resource requirements
- Include example use cases and expected outputs

### Reference Resources

The `extensions/hfss/` folder contains pre-built workflows that demonstrate complete HFSS automation patterns:
- `choke_designer.py`: Common mode choke design automation
- `shielding_effectiveness.py`: EMI shielding analysis  
- `push_excitation_from_file.py`: Automated excitation setup

These are excellent references for building intelligent automation workflows that will be callable by the AI assistant.
- Based on the CLAUDE.md documentation and the orchestrator agent code,
  here's a comprehensive description of the HFSS Assistant software:

  HFSS Assistant Software Overview

  The HFSS Assistant is a sophisticated desktop application that
  provides AI-powered assistance for Ansys HFSS (High Frequency
  Structure Simulator) electromagnetic simulation workflows. Here's how      
  it works:

  Initial User Experience

  1. Launch: User launches the Electron desktop application
  2. Backend Initialization: Python FastAPI backend starts automatically     
   with splash screen
  3. HFSS Connection: User connects to their local HFSS installation
  through the settings modal
  4. Project Loading: User selects an existing HFSS project file (.aedt)     
   to begin working with

  Core Functionality

  Once loaded, users interact through a chat interface where they can        
  ask the AI assistant to:

  - Run simulations ("solve the antenna design")
  - Generate analysis code ("plot the S-parameters")
  - Create parametric sweeps ("sweep the length from 10mm to 20mm")
  - Perform post-processing ("show me the radiation pattern at 5 GHz")       
  - Optimize designs ("find the best gap size for lowest S11")
  - Export results ("save the far-field data to CSV")

  Code Generation and Execution Architecture

  Key Technical Detail: The AI agents don't directly manipulate HFSS -       
  instead, they generate Python code as strings that are written to and      
  executed in a Jupyter notebook kernel. This architecture is crucial        
  because:

  - State Persistence: The Jupyter kernel maintains variable state
  across multiple code executions, allowing the AI to build upon
  previous work
  - Project Continuity: Once a PyAEDT project connection is established      
  in the kernel, all subsequent operations work on the same HFSS project     
   instance
  - Incremental Development: Users can see the generated code, modify it     
   if needed, and continue building analysis workflows step-by-step
  - Session Memory: Objects like simulation results, plots, and data
  structures persist in the kernel memory between different user
  requests

  Execution Flow:
  1. User makes a request ("plot S11")
  2. AI agent generates PyAEDT Python code as a string
  3. Code string is written to a new cell in the Jupyter notebook
  4. Code executes in the persistent kernel with access to the
  previously loaded HFSS project
  5. Results (plots, data, status) are captured and displayed to the
  user
  6. Kernel state is preserved for the next request

  AI Agent Architecture

  The system uses a multi-agent orchestrator that intelligently routes       
  tasks:

  Orchestrator Agent Tools:
  - sim_codegen_tool - Generates HFSS simulation setup code as Python        
  strings
  - postproc_codegen_tool - Creates post-processing and analysis code as     
   Python strings
  - plot_network_data - Direct S/Y/Z parameter plotting (generates
  Python code)
  - plot_far_field - Radiation pattern visualization (generates Python       
  code)
  - plot_smith_chart - Impedance/reflection plotting (generates Python       
  code)
  - execute_code - Writes generated Python code strings to notebook
  cells and executes them
  - get_variations_data - Extracts parametric sweep results via
  generated code
  - discover_sweep_variations - Lists available parameter combinations       
  via generated code
  - set_up_parametric_sweep - Configures parametric studies via
  generated code
  - schedule_post_sim_action - Queues actions after simulations complete     
  - send_notification_by_email - Alerts for long-running tasks

  Key User Capabilities

  Design Analysis:
  - Extract complete project context (geometry, materials, boundaries,       
  setups)
  - Analyze multiple designs within a single project
  - Query simulation status and solved variations

  Simulation Management:
  - Run individual simulations or batch processing
  - Set up parametric sweeps with multiple variables
  - Monitor real-time simulation progress
  - Handle queued tasks that execute after simulations complete

  Data Visualization:
  - Generate network parameter plots (S11, S21, etc.)
  - Create radiation patterns and far-field visualizations
  - Plot Smith charts for impedance analysis
  - Compare results across parameter variations

  Code Generation & Execution:
  - Automatically generates PyAEDT Python code as executable strings
  - Executes code in isolated Jupyter notebook environment with
  persistent kernel state
  - Provides interactive notebook interface for code review and
  modification
  - Maintains execution history, variable state, and plot outputs across     
   sessions

  Real-Time Features

  - Streaming responses via Server-Sent Events for immediate feedback        
  - Background task monitoring for long-running simulations
  - Deferred execution - queue post-processing tasks to run after
  simulations complete
  - Session persistence - maintain both chat context and Jupyter kernel      
  state across multiple interactions

  Use Cases

  Users typically employ this software to:
  - Accelerate simulation workflows through natural language commands        
  that generate executable code
  - Automate repetitive analysis tasks like parameter sweeps and
  optimization through persistent kernel sessions
  - Generate publication-ready plots without manual scripting, with code     
   automatically generated and executed
  - Learn PyAEDT through AI-generated, documented code examples that
  remain visible in the notebook
  - Troubleshoot designs with intelligent error analysis and suggestions     
   via iterative code generation
  - Collaborate by sharing notebook sessions with generated code,
  results, and maintained variable state
  - Build complex analysis workflows incrementally, leveraging the
  persistent kernel state to chain operations together

  The software essentially transforms HFSS from a GUI-driven tool into       
  an AI-assisted, conversational simulation environment where complex        
  electromagnetic analysis becomes as simple as describing what you want     
   to achieve. The underlying Jupyter notebook architecture ensures that     
   each interaction builds upon the previous work, creating a seamless,      
  stateful workflow that mirrors how engineers naturally approach
  simulation tasks.\
\
Some additional info
- Whenever you discover stuff , either how the hfss library works or relevant stuff please record it in PYAEDT_LEARNINGS.md