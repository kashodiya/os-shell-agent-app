
#!/usr/bin/env python3
"""
Example script showing how to use the Shell Agent in a Python script
"""
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the shell agents
from src.shell_agent import ShellAgent
from src.advanced_shell_agent import AdvancedShellAgent

def main():
    """Example of using the Shell Agent in a script."""
    # Get model ID from environment variable or use default
    model_id = os.environ.get("STRANDS_MODEL_ID")
    
    print("=== Basic Shell Agent Example ===")
    basic_agent = ShellAgent(model_id=model_id)
    basic_result = basic_agent.run("list all Python files in the current directory")
    print(f"Basic Agent Result:\n{basic_result}\n")
    
    print("=== Advanced Shell Agent Example ===")
    advanced_agent = AdvancedShellAgent(model_id=model_id, verbose=True)
    advanced_result = advanced_agent.run(
        "create a Python script that calculates the factorial of a number and run it with input 5"
    )
    print(f"Advanced Agent Result:\n{advanced_result}")

if __name__ == "__main__":
    main()
