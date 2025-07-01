#!/usr/bin/env python3
"""
Setup and Run Script for Topology Visualization System
Handles installation, testing, and execution of the complete system.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✓ Python version: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Install required packages."""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ All packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install packages: {e}")
        return False

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    try:
        import numpy
        import matplotlib.pyplot
        import plotly.graph_objects
        import scipy
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def run_basic_tests():
    """Run basic functionality tests."""
    print("Running basic functionality tests...")
    try:
        from topology_visualizer import TopologyVisualizer
        
        v = TopologyVisualizer()
        
        # Test surface generation
        x, y, z = v.create_mobius_strip(resolution=20)
        assert x.shape == (10, 20), "Möbius strip generation failed"
        
        x, y, z = v.create_torus(resolution=20)
        assert x.shape == (20, 20), "Torus generation failed"
        
        x, y, z = v.create_trefoil_knot(resolution=100)
        assert len(x) == 100, "Trefoil knot generation failed"
        
        print("✓ All basic tests passed")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def generate_visualizations():
    """Generate all visualizations."""
    print("Generating visualizations...")
    try:
        from topology_visualizer import TopologyVisualizer
        
        visualizer = TopologyVisualizer()
        visualizer.generate_all_visualizations()
        
        # Check if files were created
        expected_files = [
            "mobius_visualization.html",
            "torus_visualization.html", 
            "trefoil_knot_visualization.html",
            "topology_dashboard.html"
        ]
        
        missing_files = []
        for file in expected_files:
            if not Path(file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"✗ Missing files: {missing_files}")
            return False
        
        print("✓ All visualizations generated successfully")
        return True
    except Exception as e:
        print(f"✗ Visualization generation failed: {e}")
        return False

def run_interactive_examples():
    """Run interactive examples."""
    print("Generating interactive examples...")
    try:
        from interactive_controls import InteractiveController
        
        controller = InteractiveController()
        
        # Generate comparative visualization
        fig = controller.create_comparative_visualization()
        fig.write_html("comparative_topology.html")
        
        # Generate educational sequence
        fig = controller.create_educational_sequence()
        fig.write_html("educational_sequence.html")
        
        print("✓ Interactive examples generated")
        return True
    except Exception as e:
        print(f"✗ Interactive examples failed: {e}")
        return False

def create_demo_script():
    """Create a demo script for easy access."""
    demo_content = '''#!/usr/bin/env python3
"""
Topology Visualization Demo
Quick demo script to showcase the system capabilities.
"""

from topology_visualizer import TopologyVisualizer
from interactive_controls import InteractiveController
import webbrowser
import os

def main():
    print("TOPOLOGY VISUALIZATION DEMO")
    print("=" * 40)
    
    # Generate visualizations
    print("1. Generating basic visualizations...")
    visualizer = TopologyVisualizer()
    visualizer.generate_all_visualizations()
    
    # Generate interactive examples
    print("2. Generating interactive examples...")
    controller = InteractiveController()
    controller.create_comparative_visualization()
    controller.create_educational_sequence()
    
    print("\\n3. Opening dashboard in browser...")
    if os.path.exists("topology_dashboard.html"):
        webbrowser.open("topology_dashboard.html")
    
    print("\\nDemo complete! Check the following files:")
    print("• topology_dashboard.html - Main interactive dashboard")
    print("• mobius_visualization.html - Möbius strip")
    print("• torus_visualization.html - Torus surface")
    print("• trefoil_knot_visualization.html - Trefoil knot")
    print("• comparative_topology.html - Comparative analysis")
    print("• educational_sequence.html - Learning progression")

if __name__ == "__main__":
    main()
'''
    
    with open("demo.py", "w") as f:
        f.write(demo_content)
    print("✓ Demo script created: demo.py")

def main():
    """Main setup and run procedure."""
    print("=" * 60)
    print("TOPOLOGY VISUALIZATION SYSTEM - SETUP & RUN")
    print("=" * 60)
    print()
    
    # Check environment
    if not check_python_version():
        return False
    
    # Install packages
    if not install_requirements():
        print("Trying to continue with existing packages...")
    
    # Test imports
    if not test_imports():
        print("Please install missing packages manually")
        return False
    
    # Run tests
    if not run_basic_tests():
        print("Basic tests failed - system may not work correctly")
        return False
    
    # Generate visualizations
    if not generate_visualizations():
        print("Visualization generation failed")
        return False
    
    # Run interactive examples
    if not run_interactive_examples():
        print("Interactive examples failed - continuing...")
    
    # Create demo script
    create_demo_script()
    
    print()
    print("=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print()
    print("System is ready to use. Available commands:")
    print("• python topology_visualizer.py - Generate all visualizations")
    print("• python examples.py - Run examples and tutorials")
    print("• python demo.py - Quick demo")
    print("• python interactive_controls.py - Interactive features")
    print()
    print("Open the generated HTML files in your browser for interactive exploration!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("Setup encountered errors. Please check the output above.")
        sys.exit(1)