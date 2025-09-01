#!/usr/bin/env python3
"""
AI-Server setup configuration
Enables pip-installable development mode and CLI entry points
"""

from setuptools import setup, find_packages
import pathlib

# Read README for long description
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

# Read requirements
def read_requirements(filename):
    with open(filename) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="ai-server",
    version="1.0.0",
    description="Comprehensive AI infrastructure with Memory Server, LLM orchestration, and ATLAS integration",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Ruben-Alvarez-Dev",
    author_email="ruben.alvarez.dev@gmail.com",
    url="https://github.com/Ruben-Alvarez-Dev/ai-server",
    
    # Package configuration
    packages=find_packages(include=["servers*", "services*", "api*"]),
    python_requires=">=3.11",
    
    # Dependencies
    install_requires=read_requirements("requirements.txt"),
    
    # Development dependencies
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1", 
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "pre-commit>=3.6.0",
        ],
    },
    
    # CLI entry points
    entry_points={
        "console_scripts": [
            "ai-memory-server=servers.memory_server.main:main",
            "ai-llm-server=servers.llm_server.main:main",
            "ai-gui-server=servers.gui_server.main:main",
            "ai-server-cli=tools.cli:main",
        ],
    },
    
    # Package data
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.md", "*.txt"],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    # Keywords
    keywords="ai llm memory-server gui machine-learning atlas",
    
    # Project URLs
    project_urls={
        "Documentation": "https://github.com/Ruben-Alvarez-Dev/ai-server/docs",
        "Source": "https://github.com/Ruben-Alvarez-Dev/ai-server",
        "Tracker": "https://github.com/Ruben-Alvarez-Dev/ai-server/issues",
    },
)