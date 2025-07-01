#!/usr/bin/env python3
"""
Topology Visualization System
A comprehensive educational tool for visualizing mathematical topology concepts.

This system provides interactive visualizations of various topological structures
including knots, surfaces, manifolds, and topological transformations.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from scipy.spatial.distance import cdist
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

class TopologyVisualizer:
    """Main class for topology visualization system."""
    
    def __init__(self):
        """Initialize the topology visualizer."""
        self.current_concept = None
        self.visualization_data = {}
        self.interactive_params = {}
        
    def create_mobius_strip(self, resolution=50, width=0.3):
        """
        Create a Möbius strip parametrization.
        
        Args:
            resolution (int): Number of points along each parameter
            width (float): Width of the strip
            
        Returns:
            tuple: (x, y, z) coordinates of the Möbius strip
        """
        u = np.linspace(0, 2*np.pi, resolution)
        v = np.linspace(-width, width, resolution//2)
        U, V = np.meshgrid(u, v)
        
        x = (1 + V * np.cos(U/2)) * np.cos(U)
        y = (1 + V * np.cos(U/2)) * np.sin(U)
        z = V * np.sin(U/2)
        
        return x, y, z
    
    def create_klein_bottle(self, resolution=50, a=3, b=1):
        """
        Create a Klein bottle parametrization.
        
        Args:
            resolution (int): Number of points along each parameter
            a, b (float): Shape parameters
            
        Returns:
            tuple: (x, y, z) coordinates of the Klein bottle
        """
        u = np.linspace(0, 2*np.pi, resolution)
        v = np.linspace(0, 2*np.pi, resolution)
        U, V = np.meshgrid(u, v)
        
        x = a * (np.cos(U) * (1 + np.sin(U)) + 
                 (1 - np.cos(U)/2) * np.cos(U) * np.cos(V))
        y = b * np.sin(U) * (1 + np.cos(V))
        z = -(1 - np.cos(U)/2) * np.sin(U) * np.sin(V)
        
        return x, y, z
    
    def create_trefoil_knot(self, resolution=1000, scale=1.0):
        """
        Create a trefoil knot parametrization.
        
        Args:
            resolution (int): Number of points along the knot
            scale (float): Scaling factor
            
        Returns:
            tuple: (x, y, z) coordinates of the trefoil knot
        """
        t = np.linspace(0, 2*np.pi, resolution)
        
        x = scale * np.sin(t) + 2 * scale * np.sin(2*t)
        y = scale * np.cos(t) - 2 * scale * np.cos(2*t)
        z = -scale * np.sin(3*t)
        
        return x, y, z
    
    def create_torus(self, resolution=50, R=2, r=1):
        """
        Create a torus parametrization.
        
        Args:
            resolution (int): Number of points along each parameter
            R (float): Major radius
            r (float): Minor radius
            
        Returns:
            tuple: (x, y, z) coordinates of the torus
        """
        u = np.linspace(0, 2*np.pi, resolution)
        v = np.linspace(0, 2*np.pi, resolution)
        U, V = np.meshgrid(u, v)
        
        x = (R + r * np.cos(V)) * np.cos(U)
        y = (R + r * np.cos(V)) * np.sin(U)
        z = r * np.sin(V)
        
        return x, y, z
    
    def compute_curvature(self, x, y, z, method='gaussian'):
        """
        Compute curvature for a surface.
        
        Args:
            x, y, z (arrays): Surface coordinates
            method (str): Type of curvature ('gaussian', 'mean')
            
        Returns:
            array: Curvature values
        """
        # Simplified curvature computation
        if method == 'gaussian':
            dx = np.gradient(x)
            dy = np.gradient(y)
            dz = np.gradient(z)
            curvature = np.sqrt(dx[0]**2 + dy[0]**2 + dz[0]**2)
        else:
            curvature = np.ones_like(x)
            
        return curvature
    
    def visualize_surface_interactive(self, surface_type='mobius', save_html=True):
        """
        Create interactive surface visualization using Plotly.
        
        Args:
            surface_type (str): Type of surface to visualize
            save_html (bool): Whether to save as HTML file
            
        Returns:
            plotly.graph_objects.Figure: Interactive figure
        """
        if surface_type == 'mobius':
            x, y, z = self.create_mobius_strip()
            title = "Möbius Strip - Non-orientable Surface"
        elif surface_type == 'klein':
            x, y, z = self.create_klein_bottle()
            title = "Klein Bottle - Non-orientable Closed Surface"
        elif surface_type == 'torus':
            x, y, z = self.create_torus()
            title = "Torus - Orientable Closed Surface"
        else:
            raise ValueError(f"Unknown surface type: {surface_type}")
        
        curvature = self.compute_curvature(x, y, z)
        
        fig = go.Figure(data=[
            go.Surface(
                x=x, y=y, z=z,
                surfacecolor=curvature,
                colorscale='Viridis',
                opacity=0.8,
                showscale=True,
                colorbar=dict(title="Curvature")
            )
        ])
        
        fig.update_layout(
            title=title,
            scene=dict(
                xaxis_title="X",
                yaxis_title="Y",
                zaxis_title="Z",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            width=800,
            height=600
        )
        
        if save_html:
            filename = f"{surface_type}_visualization.html"
            fig.write_html(filename)
            print(f"Interactive visualization saved as {filename}")
        
        return fig
    
    def visualize_knot_interactive(self, knot_type='trefoil', save_html=True):
        """
        Create interactive knot visualization.
        
        Args:
            knot_type (str): Type of knot to visualize
            save_html (bool): Whether to save as HTML file
            
        Returns:
            plotly.graph_objects.Figure: Interactive figure
        """
        if knot_type == 'trefoil':
            x, y, z = self.create_trefoil_knot()
            title = "Trefoil Knot - Simplest Non-trivial Knot"
        else:
            raise ValueError(f"Unknown knot type: {knot_type}")
        
        # Create tube around the knot curve
        fig = go.Figure()
        
        # Main knot curve
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode='lines',
            line=dict(width=8, color='red'),
            name='Knot Curve'
        ))
        
        # Add direction indicators
        n_arrows = 20
        indices = np.linspace(0, len(x)-1, n_arrows, dtype=int)
        
        for i in indices:
            if i < len(x) - 1:
                dx = x[i+1] - x[i]
                dy = y[i+1] - y[i]
                dz = z[i+1] - z[i]
                
                fig.add_trace(go.Scatter3d(
                    x=[x[i], x[i] + 0.3*dx],
                    y=[y[i], y[i] + 0.3*dy],
                    z=[z[i], z[i] + 0.3*dz],
                    mode='lines',
                    line=dict(width=3, color='blue'),
                    showlegend=False
                ))
        
        fig.update_layout(
            title=title,
            scene=dict(
                xaxis_title="X",
                yaxis_title="Y",
                zaxis_title="Z",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
                aspectmode='cube'
            ),
            width=800,
            height=600
        )
        
        if save_html:
            filename = f"{knot_type}_knot_visualization.html"
            fig.write_html(filename)
            print(f"Interactive knot visualization saved as {filename}")
        
        return fig
    
    def create_homotopy_animation(self, save_html=True):
        """
        Create animation showing homotopy between curves.
        
        Args:
            save_html (bool): Whether to save as HTML file
            
        Returns:
            plotly.graph_objects.Figure: Animated figure
        """
        t = np.linspace(0, 2*np.pi, 100)
        
        # Create frames for animation
        frames = []
        n_frames = 50
        
        for i in range(n_frames):
            s = i / (n_frames - 1)  # Parameter from 0 to 1
            
            # Homotopy from circle to figure-eight
            if s <= 0.5:
                # Circle to oval
                a = 1 + s
                b = 1
                x = a * np.cos(t)
                y = b * np.sin(t)
            else:
                # Oval to figure-eight
                s_adj = (s - 0.5) * 2
                x = (1 + s_adj) * np.cos(t)
                y = np.sin(t) * (1 - s_adj * 0.8)
                # Add figure-eight component
                x += s_adj * 0.5 * np.cos(2*t)
            
            frame = go.Frame(
                data=[go.Scatter(x=x, y=y, mode='lines', 
                                line=dict(width=3, color='red'),
                                name='Curve')],
                name=str(i)
            )
            frames.append(frame)
        
        # Initial frame
        x0 = np.cos(t)
        y0 = np.sin(t)
        
        fig = go.Figure(
            data=[go.Scatter(x=x0, y=y0, mode='lines',
                           line=dict(width=3, color='red'),
                           name='Curve')],
            frames=frames
        )
        
        fig.update_layout(
            title="Homotopy: Continuous Deformation of Curves",
            xaxis=dict(range=[-3, 3], title="X"),
            yaxis=dict(range=[-2, 2], title="Y"),
            updatemenus=[
                dict(type="buttons",
                     buttons=[
                         dict(label="Play",
                              method="animate",
                              args=[None, {"frame": {"duration": 100}}]),
                         dict(label="Pause",
                              method="animate",
                              args=[[None], {"frame": {"duration": 0}}])
                     ])
            ],
            width=700,
            height=500
        )
        
        if save_html:
            filename = "homotopy_animation.html"
            fig.write_html(filename)
            print(f"Homotopy animation saved as {filename}")
        
        return fig
    
    def create_interactive_dashboard(self, save_html=True):
        """
        Create comprehensive interactive dashboard with multiple topology concepts.
        
        Args:
            save_html (bool): Whether to save as HTML file
            
        Returns:
            plotly.graph_objects.Figure: Dashboard figure
        """
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{"type": "surface"}, {"type": "surface"}],
                   [{"type": "scatter3d"}, {"type": "scatter"}]],
            subplot_titles=("Möbius Strip", "Torus", 
                           "Trefoil Knot", "Fundamental Group"),
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # Möbius Strip
        x_m, y_m, z_m = self.create_mobius_strip()
        fig.add_trace(
            go.Surface(x=x_m, y=y_m, z=z_m, 
                      colorscale='Viridis', showscale=False),
            row=1, col=1
        )
        
        # Torus
        x_t, y_t, z_t = self.create_torus()
        fig.add_trace(
            go.Surface(x=x_t, y=y_t, z=z_t, 
                      colorscale='Plasma', showscale=False),
            row=1, col=2
        )
        
        # Trefoil Knot
        x_k, y_k, z_k = self.create_trefoil_knot()
        fig.add_trace(
            go.Scatter3d(x=x_k, y=y_k, z=z_k, 
                        mode='lines', line=dict(width=6, color='red')),
            row=2, col=1
        )
        
        # Fundamental Group Example (circle)
        t = np.linspace(0, 2*np.pi, 100)
        x_c = np.cos(t)
        y_c = np.sin(t)
        fig.add_trace(
            go.Scatter(x=x_c, y=y_c, mode='lines', 
                      line=dict(width=4, color='blue')),
            row=2, col=2
        )
        
        fig.update_layout(
            title="Topology Visualization Dashboard",
            height=800,
            showlegend=False
        )
        
        if save_html:
            filename = "topology_dashboard.html"
            fig.write_html(filename)
            print(f"Interactive dashboard saved as {filename}")
        
        return fig
    
    def generate_all_visualizations(self):
        """Generate all available visualizations and save to files."""
        print("Generating topology visualizations...")
        
        # Individual surface visualizations
        surfaces = ['mobius', 'klein', 'torus']
        for surface in surfaces:
            try:
                self.visualize_surface_interactive(surface)
                print(f"✓ Generated {surface} visualization")
            except Exception as e:
                print(f"✗ Failed to generate {surface}: {e}")
        
        # Knot visualizations
        try:
            self.visualize_knot_interactive('trefoil')
            print("✓ Generated trefoil knot visualization")
        except Exception as e:
            print(f"✗ Failed to generate trefoil knot: {e}")
        
        # Homotopy animation
        try:
            self.create_homotopy_animation()
            print("✓ Generated homotopy animation")
        except Exception as e:
            print(f"✗ Failed to generate homotopy animation: {e}")
        
        # Interactive dashboard
        try:
            self.create_interactive_dashboard()
            print("✓ Generated interactive dashboard")
        except Exception as e:
            print(f"✗ Failed to generate dashboard: {e}")
        
        print("\nAll visualizations generated successfully!")
        print("Open the HTML files in your browser to explore the interactive features.")


def main():
    """Main function to demonstrate the topology visualization system."""
    print("=" * 60)
    print("TOPOLOGY VISUALIZATION SYSTEM")
    print("=" * 60)
    print()
    
    visualizer = TopologyVisualizer()
    
    print("This system provides interactive visualizations of:")
    print("• Möbius Strip (non-orientable surface)")
    print("• Klein Bottle (non-orientable closed surface)")
    print("• Torus (orientable closed surface)")
    print("• Trefoil Knot (simplest non-trivial knot)")
    print("• Homotopy animations (continuous deformations)")
    print("• Interactive dashboard with multiple concepts")
    print()
    
    # Generate all visualizations
    visualizer.generate_all_visualizations()
    
    print()
    print("=" * 60)
    print("EDUCATIONAL NOTES:")
    print("=" * 60)
    print("• Topology studies properties preserved under continuous deformations")
    print("• Non-orientable surfaces have only one side (like Möbius strip)")
    print("• Knot theory classifies different types of knots and links")
    print("• Homotopy groups measure the 'holes' in topological spaces")
    print("• Interactive features allow exploration of mathematical parameters")


if __name__ == "__main__":
    main()