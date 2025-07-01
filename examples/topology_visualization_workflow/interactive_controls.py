#!/usr/bin/env python3
"""
Interactive Controls Module
Provides enhanced interactive controls and parameter manipulation for topology visualizations.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons, CheckButtons
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from topology_visualizer import TopologyVisualizer

class InteractiveController:
    """Enhanced interactive controls for topology visualizations."""
    
    def __init__(self):
        """Initialize the interactive controller."""
        self.visualizer = TopologyVisualizer()
        self.current_fig = None
        self.parameters = {}
    
    def create_parameter_explorer(self, concept='mobius'):
        """
        Create interactive parameter explorer for topology concepts.
        
        Args:
            concept (str): Topology concept to explore
            
        Returns:
            matplotlib.figure.Figure: Interactive figure with controls
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        plt.subplots_adjust(bottom=0.3)
        
        # Initial parameters
        if concept == 'mobius':
            self.parameters = {'resolution': 50, 'width': 0.3}
            param_ranges = {'resolution': (10, 100), 'width': (0.1, 1.0)}
        elif concept == 'torus':
            self.parameters = {'resolution': 50, 'R': 2.0, 'r': 1.0}
            param_ranges = {'resolution': (10, 100), 'R': (1.0, 5.0), 'r': (0.5, 2.0)}
        elif concept == 'trefoil':
            self.parameters = {'resolution': 500, 'scale': 1.0}
            param_ranges = {'resolution': (100, 2000), 'scale': (0.5, 3.0)}
        
        # Create initial plot
        self.update_plot(ax, concept)
        
        # Create sliders
        slider_axes = []
        sliders = []
        
        y_pos = 0.1
        for i, (param, value) in enumerate(self.parameters.items()):
            ax_slider = plt.axes([0.2, y_pos - i*0.05, 0.5, 0.03])
            slider_axes.append(ax_slider)
            
            min_val, max_val = param_ranges[param]
            slider = Slider(ax_slider, param, min_val, max_val, 
                          valinit=value, valfmt='%.2f')
            sliders.append(slider)
            
            # Connect slider to update function
            slider.on_changed(lambda val, p=param, c=concept, a=ax: 
                            self.on_parameter_change(val, p, c, a))
        
        # Add reset button
        ax_reset = plt.axes([0.8, 0.05, 0.1, 0.04])
        button_reset = Button(ax_reset, 'Reset')
        button_reset.on_clicked(lambda x: self.reset_parameters(concept, ax, sliders))
        
        plt.suptitle(f'Interactive {concept.title()} Explorer', fontsize=16)
        plt.show()
        
        return fig
    
    def update_plot(self, ax, concept):
        """Update the plot with current parameters."""
        ax.clear()
        
        if concept == 'mobius':
            x, y, z = self.visualizer.create_mobius_strip(
                resolution=int(self.parameters['resolution']),
                width=self.parameters['width']
            )
            ax.plot_surface(x, y, z, alpha=0.7, cmap='viridis')
            ax.set_title('Möbius Strip')
            
        elif concept == 'torus':
            x, y, z = self.visualizer.create_torus(
                resolution=int(self.parameters['resolution']),
                R=self.parameters['R'],
                r=self.parameters['r']
            )
            ax.plot_surface(x, y, z, alpha=0.7, cmap='plasma')
            ax.set_title('Torus')
            
        elif concept == 'trefoil':
            x, y, z = self.visualizer.create_trefoil_knot(
                resolution=int(self.parameters['resolution']),
                scale=self.parameters['scale']
            )
            ax.plot(x, y, z, 'r-', linewidth=3)
            ax.set_title('Trefoil Knot')
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plt.draw()
    
    def on_parameter_change(self, val, param, concept, ax):
        """Handle parameter change events."""
        self.parameters[param] = val
        self.update_plot(ax, concept)
    
    def reset_parameters(self, concept, ax, sliders):
        """Reset parameters to default values."""
        if concept == 'mobius':
            defaults = {'resolution': 50, 'width': 0.3}
        elif concept == 'torus':
            defaults = {'resolution': 50, 'R': 2.0, 'r': 1.0}
        elif concept == 'trefoil':
            defaults = {'resolution': 500, 'scale': 1.0}
        
        for slider, (param, value) in zip(sliders, defaults.items()):
            slider.reset()
            self.parameters[param] = value
        
        self.update_plot(ax, concept)
    
    def create_comparative_visualization(self):
        """Create comparative visualization of different topology concepts."""
        fig = make_subplots(
            rows=2, cols=3,
            specs=[[{"type": "surface"}, {"type": "surface"}, {"type": "surface"}],
                   [{"type": "scatter3d"}, {"type": "scatter3d"}, {"type": "scatter"}]],
            subplot_titles=("Möbius Strip", "Klein Bottle", "Torus",
                           "Trefoil Knot", "Hopf Link", "Circle Packing"),
            vertical_spacing=0.08,
            horizontal_spacing=0.05
        )
        
        # Row 1: Surfaces
        x_m, y_m, z_m = self.visualizer.create_mobius_strip()
        fig.add_trace(go.Surface(x=x_m, y=y_m, z=z_m, colorscale='Viridis', 
                                showscale=False, name='Möbius'), row=1, col=1)
        
        x_k, y_k, z_k = self.visualizer.create_klein_bottle()
        fig.add_trace(go.Surface(x=x_k, y=y_k, z=z_k, colorscale='Plasma', 
                                showscale=False, name='Klein'), row=1, col=2)
        
        x_t, y_t, z_t = self.visualizer.create_torus()
        fig.add_trace(go.Surface(x=x_t, y=y_t, z=z_t, colorscale='Cividis', 
                                showscale=False, name='Torus'), row=1, col=3)
        
        # Row 2: Knots and other structures
        x_tr, y_tr, z_tr = self.visualizer.create_trefoil_knot()
        fig.add_trace(go.Scatter3d(x=x_tr, y=y_tr, z=z_tr, mode='lines',
                                  line=dict(width=6, color='red'), name='Trefoil'), 
                     row=2, col=1)
        
        # Simple Hopf link (two interlocked circles)
        t = np.linspace(0, 2*np.pi, 100)
        x_h1 = np.cos(t)
        y_h1 = np.sin(t)
        z_h1 = np.zeros_like(t)
        
        x_h2 = np.zeros_like(t)
        y_h2 = np.cos(t)
        z_h2 = np.sin(t)
        
        fig.add_trace(go.Scatter3d(x=x_h1, y=y_h1, z=z_h1, mode='lines',
                                  line=dict(width=6, color='blue'), name='Link1'), 
                     row=2, col=2)
        fig.add_trace(go.Scatter3d(x=x_h2, y=y_h2, z=z_h2, mode='lines',
                                  line=dict(width=6, color='green'), name='Link2'), 
                     row=2, col=2)
        
        # Circle packing in the plane
        n_circles = 20
        centers = np.random.random((n_circles, 2)) * 4 - 2
        radii = np.random.random(n_circles) * 0.3 + 0.1
        
        for i, (center, radius) in enumerate(zip(centers, radii)):
            circle_t = np.linspace(0, 2*np.pi, 50)
            x_circle = center[0] + radius * np.cos(circle_t)
            y_circle = center[1] + radius * np.sin(circle_t)
            
            fig.add_trace(go.Scatter(x=x_circle, y=y_circle, mode='lines',
                                   line=dict(width=2, color=px.colors.qualitative.Set3[i % 10]),
                                   showlegend=False), row=2, col=3)
        
        fig.update_layout(
            title="Comparative Topology Visualization",
            height=700,
            showlegend=False
        )
        
        return fig
    
    def create_educational_sequence(self):
        """Create educational sequence showing topology concepts progression."""
        concepts = [
            ("Circle", "Simplest closed curve"),
            ("Möbius Strip", "Non-orientable surface"),
            ("Torus", "Genus 1 surface"),
            ("Trefoil Knot", "Non-trivial knot"),
            ("Klein Bottle", "Non-orientable closed surface")
        ]
        
        fig = make_subplots(
            rows=1, cols=len(concepts),
            subplot_titles=[f"{name}\n{desc}" for name, desc in concepts],
            specs=[[{"type": "scatter3d" if i > 0 else "scatter"} 
                   for i in range(len(concepts))]],
            horizontal_spacing=0.02
        )
        
        # Circle
        t = np.linspace(0, 2*np.pi, 100)
        x_c = np.cos(t)
        y_c = np.sin(t)
        fig.add_trace(go.Scatter(x=x_c, y=y_c, mode='lines',
                               line=dict(width=4, color='blue')), row=1, col=1)
        
        # Möbius Strip
        x_m, y_m, z_m = self.visualizer.create_mobius_strip(resolution=30)
        fig.add_trace(go.Surface(x=x_m, y=y_m, z=z_m, colorscale='Viridis',
                               showscale=False), row=1, col=2)
        
        # Torus
        x_t, y_t, z_t = self.visualizer.create_torus(resolution=30)
        fig.add_trace(go.Surface(x=x_t, y=y_t, z=z_t, colorscale='Plasma',
                               showscale=False), row=1, col=3)
        
        # Trefoil Knot
        x_tr, y_tr, z_tr = self.visualizer.create_trefoil_knot(resolution=300)
        fig.add_trace(go.Scatter3d(x=x_tr, y=y_tr, z=z_tr, mode='lines',
                                 line=dict(width=6, color='red')), row=1, col=4)
        
        # Klein Bottle
        x_k, y_k, z_k = self.visualizer.create_klein_bottle(resolution=30)
        fig.add_trace(go.Surface(x=x_k, y=y_k, z=z_k, colorscale='Cividis',
                               showscale=False), row=1, col=5)
        
        fig.update_layout(
            title="Educational Progression: From Simple to Complex Topology",
            height=400,
            showlegend=False
        )
        
        return fig


def main():
    """Demonstrate interactive controls."""
    print("Interactive Topology Controls Demo")
    print("=" * 40)
    
    controller = InteractiveController()
    
    # Create comparative visualization
    print("Creating comparative visualization...")
    comp_fig = controller.create_comparative_visualization()
    comp_fig.write_html("comparative_topology.html")
    print("✓ Saved: comparative_topology.html")
    
    # Create educational sequence
    print("Creating educational sequence...")
    edu_fig = controller.create_educational_sequence()
    edu_fig.write_html("educational_sequence.html")
    print("✓ Saved: educational_sequence.html")
    
    print("\nFor interactive parameter exploration, run:")
    print("controller.create_parameter_explorer('mobius')")
    print("controller.create_parameter_explorer('torus')")
    print("controller.create_parameter_explorer('trefoil')")


if __name__ == "__main__":
    main()