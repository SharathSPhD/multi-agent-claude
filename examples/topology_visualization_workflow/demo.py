#!/usr/bin/env python3
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
    
    print("\n3. Opening dashboard in browser...")
    if os.path.exists("topology_dashboard.html"):
        webbrowser.open("topology_dashboard.html")
    
    print("\nDemo complete! Check the following files:")
    print("• topology_dashboard.html - Main interactive dashboard")
    print("• mobius_visualization.html - Möbius strip")
    print("• torus_visualization.html - Torus surface")
    print("• trefoil_knot_visualization.html - Trefoil knot")
    print("• comparative_topology.html - Comparative analysis")
    print("• educational_sequence.html - Learning progression")

if __name__ == "__main__":
    main()
