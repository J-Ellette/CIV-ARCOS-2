"""Setup configuration for CIV-ARCOS."""
from setuptools import setup, find_packages

setup(
    name="civ-arcos",
    version="0.1.0",
    description="Civilian Assurance-based Risk Computation and Orchestration System",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.9",
    install_requires=[],
    extras_require={
        "dev": ["pytest", "coverage", "black", "mypy", "flake8"],
    },
    entry_points={
        "console_scripts": [
            "civ-arcos=civ_arcos.api:run_server",
        ],
    },
)
