

from setuptools import setup, find_packages

setup(
    name="os-shell-agent",
    version="0.1.0",
    description="AI Agent that can execute tasks using shell commands",
    author="Kalpesh Ashodiya",
    author_email="kashodiya@gmail.com",
    url="https://github.com/kashodiya/os-shell-agent-app",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "strands-agents>=1.13.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "shell-agent=enhanced_cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

