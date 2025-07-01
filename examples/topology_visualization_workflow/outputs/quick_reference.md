# Topology Visualization Quick Reference

## Essential Controls Cheat Sheet

### Mouse Controls
| Action | Control |
|--------|---------|
| Rotate View | Left-click + drag |
| Zoom In/Out | Mouse wheel |
| Pan View | Right-click + drag |
| Reset View | Double-click empty space |
| Select Object | Single left-click |
| Object Menu | Right-click on object |

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| **R** | Reset view |
| **F** | Fit all objects |
| **Space** | Play/pause animation |
| **W** | Toggle wireframe |
| **T** | Toggle transparency |
| **G** | Toggle grid |
| **Ctrl+S** | Save state |
| **F11** | Fullscreen |
| **Esc** | Cancel operation |

---

## Core Concepts Quick Guide

### Basic Topology Terms
| Term | Definition | Example |
|------|------------|---------|
| **Homeomorphism** | Continuous deformation between shapes | Coffee cup ↔ Donut |
| **Genus** | Number of "holes" in a surface | Sphere: 0, Torus: 1 |
| **Orientable** | Has consistent inside/outside | Sphere: Yes, Möbius: No |
| **Euler Characteristic** | χ = V - E + F | Sphere: 2, Torus: 0 |

### Topological Objects
| Object | Properties | Key Features |
|--------|------------|--------------|
| **Sphere** | Genus 0, χ = 2, Orientable | No holes, simply connected |
| **Torus** | Genus 1, χ = 0, Orientable | One hole, two independent loops |
| **Möbius Strip** | Non-orientable, one boundary | One side, one edge |
| **Klein Bottle** | Genus 1, χ = 0, Non-orientable | No inside/outside, closed |
| **Projective Plane** | Non-orientable, χ = 1 | Cannot exist in 3D |

---

## Navigation Quick Start

### Getting Started (2 minutes)
1. **Launch**: `python topology_viz.py`
2. **Select Concept**: Choose from left panel
3. **Basic Navigation**: Left-drag to rotate, wheel to zoom
4. **Try Parameters**: Adjust sliders on right panel

### Essential Interface Elements
```
[Menu Bar] File Edit View Tools Examples Help
├── [Concept Panel] Browse topics
├── [3D Viewport] Main visualization  
├── [Controls] Parameters & settings
└── [Status Bar] Performance info
```

---

## Mathematical Formulas

### Euler Characteristic
- **Polyhedra**: χ = V - E + F
- **Closed Surfaces**: χ = 2 - 2g (g = genus)
- **Sphere**: χ = 2
- **Torus**: χ = 0  
- **Surface of genus g**: χ = 2 - 2g

### Fundamental Group
- **Circle**: π₁(S¹) = ℤ
- **Sphere**: π₁(S²) = 0 (trivial)
- **Torus**: π₁(T²) = ℤ × ℤ
- **Figure-8 knot complement**: Non-abelian

### Knot Invariants
- **Crossing Number**: Minimum crossings in any diagram
- **Alexander Polynomial**: Δ(t) = det(V - tVᵀ)
- **Trefoil**: Δ(t) = t - 1 + t⁻¹
- **Figure-8**: Δ(t) = t - 3 + t⁻¹

---

## Common Tasks Quick Reference

### Loading and Viewing
| Task | Steps |
|------|-------|
| **Load Concept** | Concept Panel → Category → Click concept |
| **Reset View** | Press 'R' or double-click viewport |
| **Save Image** | File → Export → Image |
| **Change Quality** | View → Rendering → Quality Level |

### Parameter Manipulation
| Task | Location |
|------|----------|
| **Shape Parameters** | Control Panel → Geometry |
| **Visual Settings** | Control Panel → Appearance |
| **Animation Speed** | Control Panel → Animation |
| **Reset Parameters** | Control Panel → Reset Button |

### Measurement Tools
| Measurement | Access |
|-------------|--------|
| **Distance** | Tools → Measure → Distance |
| **Curvature** | Tools → Analyze → Curvature |
| **Topology** | Tools → Analyze → Topology |
| **Invariants** | Tools → Compute → Invariants |

---

## Troubleshooting Quick Fixes

### Performance Issues
| Problem | Quick Fix |
|---------|-----------|
| **Slow rendering** | Lower mesh quality in preferences |
| **High memory** | Close unused concepts |
| **Choppy animation** | Reduce animation quality |
| **Crashes** | Update graphics drivers |

### Display Problems
| Problem | Solution |
|---------|----------|
| **Distorted view** | Press 'R' to reset view |
| **Missing colors** | View → Rendering → Reset Materials |
| **Black screen** | Check graphics drivers |
| **Wrong aspect** | Resize window to 16:9 ratio |

### Mathematical Errors
| Problem | Fix |
|---------|-----|
| **Wrong genus** | Increase mesh resolution |
| **Bad invariants** | Tools → Analysis → Exact Mode |
| **Numerical errors** | Reset parameters to defaults |
| **Inconsistent results** | Reload concept (Ctrl+R) |

---

## Learning Pathways

### Beginner (2-3 hours)
1. **Möbius Strip** (30 min) → Basic non-orientability
2. **Torus vs Sphere** (30 min) → Genus concept
3. **Klein Bottle** (45 min) → Advanced non-orientability
4. **Simple Knots** (45 min) → Knot theory basics

### Intermediate (4-5 hours)
1. **Surface Classification** (60 min) → Euler characteristic
2. **Knot Invariants** (90 min) → Alexander polynomials
3. **Covering Spaces** (90 min) → Fundamental groups
4. **Manifolds** (60 min) → Higher dimensions

### Advanced (6+ hours)
1. **Fiber Bundles** (120 min) → Advanced topology
2. **Homology Groups** (180 min) → Algebraic topology
3. **Characteristic Classes** (120 min) → Differential topology
4. **Research Applications** (Variable) → Current topics

---

## Essential Vocabulary

### Beginner Terms
- **Continuous**: Smooth deformation without tearing
- **Boundary**: Edge of a surface
- **Connected**: All in one piece
- **Loop**: Closed curve
- **Hole**: Topological feature that can't be filled

### Intermediate Terms
- **Homotopy**: Continuous deformation of functions
- **Covering**: Local homeomorphism onto base space
- **Retraction**: Projection onto subspace
- **Invariant**: Property preserved by homeomorphisms
- **Classification**: Organizing objects by topological type

### Advanced Terms
- **Cohomology**: Dual to homology, studies cochains
- **Sheaf**: Tool for local-to-global analysis
- **Characteristic Class**: Invariant of vector bundles
- **Spectral Sequence**: Computational tool for homology
- **K-Theory**: Generalized cohomology theory

---

## File Formats and Export

### Import Formats
| Format | Description | Use Case |
|--------|-------------|----------|
| **OBJ** | 3D mesh format | General 3D models |
| **PLY** | Polygon format | Research data |
| **STL** | Stereolithography | 3D printing |
| **VTK** | Visualization toolkit | Scientific data |

### Export Options
| Format | Quality | Use Case |
|--------|---------|----------|
| **PNG** | High | Publications, presentations |
| **SVG** | Vector | Scalable graphics |
| **PDF** | Print | Academic papers |
| **MP4** | Video | Animations, tutorials |

---

## Useful Web Resources

### Quick Links
- **Documentation**: https://topology-viz.readthedocs.io
- **Tutorials**: https://topology-viz.org/tutorials
- **Forum**: https://forum.topology-viz.org
- **Examples**: https://topology-viz.org/gallery

### Mathematical References
- **Wolfram MathWorld**: Comprehensive math encyclopedia
- **nLab**: Category theory and topology wiki
- **Topology Atlas**: Research-level resources
- **KnotInfo**: Database of knot invariants

---

## Contact and Support

### Getting Help
- **Built-in Help**: Press F1 or Help menu
- **Video Tutorials**: Help → Video Library
- **User Manual**: Help → User Guide
- **FAQ**: Help → Frequently Asked Questions

### Technical Support
- **Email**: support@topology-viz.org
- **Response**: 24-48 hours
- **Include**: Error messages, system info
- **Before contacting**: Run Help → System Diagnostics

### Community
- **Forum**: https://forum.topology-viz.org
- **Discord**: https://discord.gg/topology-viz
- **Reddit**: r/TopologyVisualization
- **GitHub**: Report bugs and feature requests

---

## Version Information

**Current Version**: 1.0  
**Release Date**: 2024  
**Python Support**: 3.8+  
**Platform Support**: Windows, macOS, Linux  
**License**: Educational Use  

### Recent Updates
- ✅ Improved knot rendering performance
- ✅ Added persistent homology tools
- ✅ Enhanced collaborative features
- ✅ Better touch screen support
- ✅ Expanded concept library

### Upcoming Features
- 🔄 Virtual reality support
- 🔄 Advanced animation tools
- 🔄 Machine learning integration
- 🔄 Cloud-based collaboration
- 🔄 Mobile applications

---

*Keep this reference handy while using the Topology Visualization System. For detailed explanations, consult the full User Guide.*