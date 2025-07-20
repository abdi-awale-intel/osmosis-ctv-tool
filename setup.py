#!/usr/bin/env python3
"""
Setup script for Osmosis CTV Tool
Modern Python packaging with source organization
"""

import os
import sys
from pathlib import Path
from setuptools import setup, find_packages

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Read version from config
import json
with open('config.json', 'r') as f:
    config = json.load(f)
    version = config['application']['version']
    description = config['application']['description']

# Read requirements
with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read README
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="osmosis-ctv-tool",
    version=version,
    author="Intel Corporation",
    author_email="abdi.awale@intel.com",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abdi-awale-intel/osmosis-ctv-tool",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Database :: Database Engines/Servers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "build": [
            "pyinstaller>=4.5",
            "setuptools>=45.0",
            "wheel>=0.35",
        ],
    },
    entry_points={
        "console_scripts": [
            "osmosis=osmosis_main:main",
            "osmosis-gui=ctvlist_gui:main",
            "osmosis-deploy=deploy_ctvlist:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.txt", "*.md"],
    },
    data_files=[
        (".", ["config.json", "requirements.txt"]),
        ("resources", ["resources/config.json"] if os.path.exists("resources/config.json") else []),
    ],
    zip_safe=False,
)
