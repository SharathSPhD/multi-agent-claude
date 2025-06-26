# Topology Visualization Workflow

## Overview

This workflow creates comprehensive educational visualizations of unique mathematical concepts from topology. The system combines mathematical expertise, visualization design, programming implementation, and educational documentation to produce interactive learning tools.

## Workflow Structure

### Agents (4 specialists)
- **topology_mathematician.json** - Mathematical expert for concept selection and analysis
- **visualization_architect.json** - 3D visualization designer and technical architect
- **python_developer.json** - Python implementation and code development specialist  
- **documentation_specialist.json** - Educational content creator and documentation expert

### Tasks (5 sequential phases)
- **concept_selection_and_analysis.json** - Mathematical concept research and analysis
- **visualization_design_and_architecture.json** - Technical design and architecture planning
- **python_implementation_development.json** - Python code implementation and development
- **educational_documentation_creation.json** - Comprehensive documentation and tutorials
- **integration_testing_and_optimization.json** - System integration and quality assurance

### Workflow Pattern
- **topology_visualization_workflow_pattern.json** - Complete workflow configuration

### Configuration Files
- **step2_objective_analysis.txt** - Detailed objective for workflow analysis step
- **step3_configure_create.txt** - Configuration details for workflow creation step

## Usage Instructions

### Loading into MCP Multi-Agent System

1. **Load Agents:**
   - Navigate to Agents page
   - Use "Load from File" for each agent JSON file
   - Verify all 4 agents are created successfully

2. **Load Tasks:**
   - Navigate to Tasks page  
   - Use "Load from File" for each task JSON file
   - Verify all 5 tasks are created successfully

3. **Create Workflow:**
   - Navigate to Orchestration page
   - Click "Analyze & Create"
   - **Step 1:** Select all 4 agents and all 5 tasks
   - **Step 2:** Copy content from `step2_objective_analysis.txt` into objective field, then analyze
   - **Step 3:** Use configuration from `step3_configure_create.txt`, set project directory to this folder

### Expected Outcomes

The workflow will produce:
- Interactive topology visualization (Python application)
- Mathematical analysis and theoretical foundations
- Technical implementation documentation
- Educational materials and user guides
- Deployment package for distribution

### Target Concepts

Examples of topology concepts suitable for visualization:
- **Knot Theory:** Trefoil knots, torus knots, knot invariants
- **Manifolds:** Klein bottles, Möbius strips, hyperbolic surfaces  
- **Homotopy:** Fundamental groups, covering spaces
- **Topological Invariants:** Euler characteristic, genus
- **Fiber Bundles:** Hopf fibrations, vector bundles

## Directory Structure

```
topology_visualization_workflow/
├── agents/
│   ├── topology_mathematician.json
│   ├── visualization_architect.json
│   ├── python_developer.json
│   └── documentation_specialist.json
├── tasks/
│   ├── concept_selection_and_analysis.json
│   ├── visualization_design_and_architecture.json
│   ├── python_implementation_development.json
│   ├── educational_documentation_creation.json
│   └── integration_testing_and_optimization.json
├── outputs/
│   └── (generated files will appear here)
├── topology_visualization_workflow_pattern.json
├── step2_objective_analysis.txt
├── step3_configure_create.txt
└── README.md
```

## Technical Requirements

- Python 3.8+ with mathematical and visualization libraries
- Libraries: numpy, scipy, matplotlib, plotly, mayavi, vtk
- Interactive development environment (Jupyter recommended)
- Cross-platform compatibility (Windows, macOS, Linux)

## Educational Impact

This workflow demonstrates the intersection of:
- Advanced mathematical theory (topology)
- Modern visualization techniques
- Educational technology
- Collaborative multi-agent development

The resulting visualizations serve as powerful tools for mathematics education, research, and public engagement with mathematical concepts.