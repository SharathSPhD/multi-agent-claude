#!/usr/bin/env python3
"""
Topology Visualization Examples
Comprehensive examples and tutorials for using the topology visualization system.
"""

import numpy as np
import matplotlib.pyplot as plt
from topology_visualizer import TopologyVisualizer
from interactive_controls import InteractiveController

def example_basic_surfaces():
    """Example: Basic surface visualizations."""
    print("Example 1: Basic Surface Visualizations")
    print("-" * 40)
    
    visualizer = TopologyVisualizer()
    
    # Create and display Möbius strip
    print("Creating Möbius strip...")
    fig1 = visualizer.visualize_surface_interactive('mobius')
    print("✓ Möbius strip visualization created")
    
    # Create and display torus
    print("Creating torus...")
    fig2 = visualizer.visualize_surface_interactive('torus')
    print("✓ Torus visualization created")
    
    return fig1, fig2

def example_knot_theory():
    """Example: Knot theory visualization."""
    print("Example 2: Knot Theory Visualization")
    print("-" * 40)
    
    visualizer = TopologyVisualizer()
    
    # Create trefoil knot
    print("Creating trefoil knot...")
    fig = visualizer.visualize_knot_interactive('trefoil')
    print("✓ Trefoil knot visualization created")
    
    # Analyze knot properties
    x, y, z = visualizer.create_trefoil_knot()
    
    # Calculate some basic properties
    curve_length = np.sum(np.sqrt(np.diff(x)**2 + np.diff(y)**2 + np.diff(z)**2))
    bounding_box = {
        'x_range': (np.min(x), np.max(x)),
        'y_range': (np.min(y), np.max(y)),
        'z_range': (np.min(z), np.max(z))
    }
    
    print(f"Curve length: {curve_length:.2f}")
    print(f"Bounding box: {bounding_box}")
    
    return fig

def example_homotopy_concepts():
    """Example: Homotopy and continuous deformations."""
    print("Example 3: Homotopy Concepts")
    print("-" * 40)
    
    visualizer = TopologyVisualizer()
    
    # Create homotopy animation
    print("Creating homotopy animation...")
    fig = visualizer.create_homotopy_animation()
    print("✓ Homotopy animation created")
    
    # Educational explanation
    print("\nHomotopy Explanation:")
    print("• Homotopy studies continuous deformations")
    print("• Two curves are homotopic if one can be continuously deformed into the other")
    print("• The animation shows a circle being deformed into a figure-eight")
    print("• In simply connected spaces, all loops are homotopic to a point")
    
    return fig

def example_comparative_analysis():
    """Example: Comparative analysis of topology concepts."""
    print("Example 4: Comparative Analysis")
    print("-" * 40)
    
    controller = InteractiveController()
    
    # Create comparative visualization
    print("Creating comparative visualization...")
    fig = controller.create_comparative_visualization()
    fig.write_html("example_comparative.html")
    print("✓ Comparative visualization saved as example_comparative.html")
    
    # Educational comparison
    concepts = {
        'Möbius Strip': {
            'orientable': False,
            'boundary': True,
            'genus': 0,
            'euler_characteristic': 0
        },
        'Torus': {
            'orientable': True,
            'boundary': False,
            'genus': 1,
            'euler_characteristic': 0
        },
        'Klein Bottle': {
            'orientable': False,
            'boundary': False,
            'genus': 0,
            'euler_characteristic': 0
        }
    }
    
    print("\nTopological Properties Comparison:")
    for name, props in concepts.items():
        print(f"\n{name}:")
        for prop, value in props.items():
            print(f"  {prop}: {value}")
    
    return fig

def example_interactive_exploration():
    """Example: Interactive parameter exploration."""
    print("Example 5: Interactive Parameter Exploration")
    print("-" * 40)
    
    print("This example demonstrates interactive controls.")
    print("Run the following commands in an interactive environment:")
    print()
    print("from interactive_controls import InteractiveController")
    print("controller = InteractiveController()")
    print()
    print("# Explore Möbius strip parameters")
    print("controller.create_parameter_explorer('mobius')")
    print()
    print("# Explore torus parameters")
    print("controller.create_parameter_explorer('torus')")
    print()
    print("# Explore trefoil knot parameters")
    print("controller.create_parameter_explorer('trefoil')")
    
    print("\nNote: Interactive exploration requires matplotlib GUI backend")

def example_mathematical_properties():
    """Example: Computing mathematical properties."""
    print("Example 6: Mathematical Properties")
    print("-" * 40)
    
    visualizer = TopologyVisualizer()
    
    # Analyze torus properties
    print("Analyzing torus properties...")
    x, y, z = visualizer.create_torus(resolution=50, R=2, r=1)
    
    # Surface area calculation (approximation)
    # For torus: A = 4π²Rr
    R, r = 2, 1
    theoretical_area = 4 * np.pi**2 * R * r
    
    print(f"Theoretical surface area: {theoretical_area:.2f}")
    print(f"Major radius (R): {R}")
    print(f"Minor radius (r): {r}")
    print(f"Genus: 1 (one hole)")
    print(f"Euler characteristic: 0")
    
    # Möbius strip properties
    print("\nAnalyzing Möbius strip properties...")
    x_m, y_m, z_m = visualizer.create_mobius_strip()
    
    print("Properties of Möbius strip:")
    print("• Non-orientable surface")
    print("• Has boundary (one edge)")
    print("• Genus: 0")
    print("• Euler characteristic: 0")
    print("• Cannot be embedded in R³ without self-intersection")

def example_educational_sequence():
    """Example: Educational progression sequence."""
    print("Example 7: Educational Sequence")
    print("-" * 40)
    
    controller = InteractiveController()
    
    print("Creating educational progression...")
    fig = controller.create_educational_sequence()
    fig.write_html("example_educational_sequence.html")
    print("✓ Educational sequence saved as example_educational_sequence.html")
    
    # Learning progression explanation
    progression = [
        "1. Circle: Basic closed curve in the plane",
        "2. Möbius Strip: Introduction to non-orientable surfaces",
        "3. Torus: Orientable closed surface with genus 1",
        "4. Trefoil Knot: Simplest non-trivial knot",
        "5. Klein Bottle: Non-orientable closed surface"
    ]
    
    print("\nLearning Progression:")
    for step in progression:
        print(step)
    
    return fig

def run_all_examples():
    """Run all examples in sequence."""
    print("TOPOLOGY VISUALIZATION EXAMPLES")
    print("=" * 50)
    print()
    
    examples = [
        example_basic_surfaces,
        example_knot_theory,
        example_homotopy_concepts,
        example_comparative_analysis,
        example_interactive_exploration,
        example_mathematical_properties,
        example_educational_sequence
    ]
    
    results = []
    for i, example in enumerate(examples, 1):
        try:
            print(f"\n{'='*20} EXAMPLE {i} {'='*20}")
            result = example()
            results.append(result)
            print("✓ Example completed successfully")
        except Exception as e:
            print(f"✗ Example failed: {e}")
            results.append(None)
    
    print("\n" + "="*50)
    print("ALL EXAMPLES COMPLETED")
    print("Check the generated HTML files for interactive visualizations!")
    
    return results

def create_usage_tutorial():
    """Create a comprehensive usage tutorial."""
    tutorial = """
# Topology Visualization System - Usage Tutorial

## Quick Start

1. Import the main classes:
```python
from topology_visualizer import TopologyVisualizer
from interactive_controls import InteractiveController
```

2. Create a visualizer instance:
```python
visualizer = TopologyVisualizer()
```

3. Generate visualizations:
```python
# Create interactive Möbius strip
fig = visualizer.visualize_surface_interactive('mobius')

# Create trefoil knot
fig = visualizer.visualize_knot_interactive('trefoil')

# Generate all visualizations
visualizer.generate_all_visualizations()
```

## Advanced Usage

### Custom Parameters
```python
# Custom Möbius strip
x, y, z = visualizer.create_mobius_strip(resolution=100, width=0.5)

# Custom torus
x, y, z = visualizer.create_torus(resolution=80, R=3, r=0.8)
```

### Interactive Controls
```python
controller = InteractiveController()

# Parameter exploration
controller.create_parameter_explorer('torus')

# Comparative analysis
controller.create_comparative_visualization()
```

### Educational Applications
```python
# Create educational sequence
controller.create_educational_sequence()

# Generate homotopy animation
visualizer.create_homotopy_animation()
```

## Mathematical Concepts Covered

1. **Non-orientable Surfaces**: Möbius strip, Klein bottle
2. **Orientable Surfaces**: Torus, sphere
3. **Knot Theory**: Trefoil knot, linking numbers
4. **Homotopy Theory**: Continuous deformations
5. **Topological Invariants**: Genus, Euler characteristic

## File Outputs

The system generates HTML files with interactive visualizations:
- `mobius_visualization.html`
- `torus_visualization.html`
- `trefoil_knot_visualization.html`
- `homotopy_animation.html`
- `topology_dashboard.html`

## Educational Notes

- All visualizations include mathematical context
- Interactive features allow parameter exploration
- Comparative views show relationships between concepts
- Animations demonstrate continuous transformations
"""
    
    with open("TUTORIAL.md", "w") as f:
        f.write(tutorial)
    
    print("✓ Tutorial saved as TUTORIAL.md")

def main():
    """Main example runner."""
    print("Select an example to run:")
    print("1. Basic Surfaces")
    print("2. Knot Theory")
    print("3. Homotopy Concepts")
    print("4. Comparative Analysis")
    print("5. Interactive Exploration")
    print("6. Mathematical Properties")
    print("7. Educational Sequence")
    print("8. Run All Examples")
    print("9. Create Tutorial")
    
    try:
        choice = input("\nEnter choice (1-9): ").strip()
        
        if choice == '1':
            example_basic_surfaces()
        elif choice == '2':
            example_knot_theory()
        elif choice == '3':
            example_homotopy_concepts()
        elif choice == '4':
            example_comparative_analysis()
        elif choice == '5':
            example_interactive_exploration()
        elif choice == '6':
            example_mathematical_properties()
        elif choice == '7':
            example_educational_sequence()
        elif choice == '8':
            run_all_examples()
        elif choice == '9':
            create_usage_tutorial()
        else:
            print("Invalid choice. Running all examples...")
            run_all_examples()
            
    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        print("Running all examples as fallback...")
        run_all_examples()

if __name__ == "__main__":
    main()