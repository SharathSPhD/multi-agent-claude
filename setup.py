#!/usr/bin/env python3
"""
Setup script for MCP A2A Multi-Agent System.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open("requirements.txt", "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("# "):
            requirements.append(line)

setup(
    name="mcp-a2a-multiagent",
    version="0.1.0",
    description="Multi-Agent System with mcp-agent, A2A protocol, and MCP integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    author="MCP A2A Project",
    author_email="project@example.com",
    url="https://github.com/your-org/mcp-a2a-multiagent",
    
    packages=find_packages(),
    include_package_data=True,
    
    python_requires=">=3.9",
    install_requires=requirements,
    
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0", 
            "pytest-mock>=3.12.0",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "mypy>=1.7.0",
            "flake8>=6.0.0",
        ],
        "llm": [
            "openai>=1.3.0",
            "anthropic>=0.8.0",
            "google-generativeai>=0.3.0",
        ],
        "temporal": [
            "temporalio>=1.4.0",
        ],
        "vector": [
            "chromadb>=0.4.0",
            "faiss-cpu>=1.7.0",
        ],
        "monitoring": [
            "prometheus-client>=0.18.0",
            "grafana-client>=0.6.0",
        ]
    },
    
    entry_points={
        "console_scripts": [
            "mcp-a2a=mcp_a2a.cli:main",
            "mcp-a2a-orchestrator=mcp_a2a.orchestrator.main:main",
            "mcp-a2a-agent=mcp_a2a.agents.cli:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11", 
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],
    
    keywords=[
        "multi-agent",
        "ai",
        "orchestration",
        "mcp", 
        "a2a",
        "agent-to-agent",
        "model-context-protocol",
        "asynchronous",
        "coordination",
        "claude-code"
    ],
    
    project_urls={
        "Documentation": "https://github.com/your-org/mcp-a2a-multiagent#readme",
        "Source": "https://github.com/your-org/mcp-a2a-multiagent",
        "Issues": "https://github.com/your-org/mcp-a2a-multiagent/issues",
        "Changelog": "https://github.com/your-org/mcp-a2a-multiagent/blob/main/CHANGELOG.md",
    },
)