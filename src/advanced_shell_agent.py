
"""
Advanced Shell Agent - An AI agent that can execute complex shell tasks
by breaking them down into steps and executing them sequentially
"""
import json
import os
import subprocess
import sys
import time
from typing import Dict, List, Optional, Any, Union


from strands import Agent, tool
from strands.models import BedrockModel


@tool
def shell_command(command: str) -> Dict[str, Any]:
    """Execute a shell command and return its output.
    
    Args:
        command: The shell command to execute
        
    Returns:
        A dictionary containing stdout, stderr, and exit_code
    """
    if not command:
        raise ValueError("No command provided")
    
    try:
        # Execute the command and capture output
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60  # Timeout after 60 seconds
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        raise ValueError("Command timed out after 60 seconds")
    except Exception as e:
        raise ValueError(f"Error executing command: {str(e)}")

@tool
def create_task_plan(task: str) -> Dict[str, str]:
    """Create a step-by-step plan to accomplish a complex task.
    
    Args:
        task: The complex task that needs to be planned
        
    Returns:
        A dictionary containing a message with the planning request
    """
    if not task:
        raise ValueError("No task provided")
    
    # This tool doesn't actually execute anything - it just asks the agent
    # to create a plan, which it will do using its reasoning capabilities
    return {
        "message": f"Create a JSON array of steps for: {task}. Each step should have a 'description' and 'command' field."
    }

@tool
def read_file(path: str) -> Dict[str, str]:
    """Read the contents of a file.
    
    Args:
        path: Path to the file to read
        
    Returns:
        A dictionary containing the file content
    """
    if not path:
        raise ValueError("No file path provided")
    
    try:
        with open(path, 'r') as file:
            content = file.read()
        return {"content": content}
    except Exception as e:
        raise ValueError(f"Error reading file: {str(e)}")

@tool
def write_file(path: str, content: str, append: bool = False) -> Dict[str, Any]:
    """Write content to a file.
    
    Args:
        path: Path to the file to write
        content: Content to write to the file
        append: Whether to append to the file instead of overwriting
        
    Returns:
        A dictionary indicating success and the file path
    """
    if not path:
        raise ValueError("No file path provided")
    if content is None:
        raise ValueError("No content provided")
    
    try:
        mode = 'a' if append else 'w'
        with open(path, mode) as file:
            file.write(content)
        return {"success": True, "path": path}
    except Exception as e:
        raise ValueError(f"Error writing to file: {str(e)}")

class AdvancedShellAgent:
    """Advanced Shell Agent that can execute complex CLI tasks."""
    
    def __init__(self, model_id: Optional[str] = None, verbose: bool = False):
        """Initialize the Advanced Shell Agent with tools."""
        self.verbose = verbose
        if model_id:
            model = BedrockModel(model_id=model_id)
            self.agent = Agent(
                tools=[
                    shell_command,
                    create_task_plan,
                    read_file,
                    write_file
                ],
                model=model
            )
        else:
            self.agent = Agent(
                tools=[
                    shell_command,
                    create_task_plan,
                    read_file,
                    write_file
                ]
            )
    
    def run(self, task: str) -> str:
        """Run the agent with the given task."""
        if self.verbose:
            print(f"Task: {task}")
            print("Creating plan...")
        
        # First, ask the agent to create a plan
        plan_result = self.agent(
            f"I need to {task}. First, create a detailed step-by-step plan using the create_task_plan tool."
        )
        
        if self.verbose:
            print("Plan created. Executing steps...")
        
        # Now execute the plan
        execution_result = self.agent(
            f"Now execute the plan to {task}. Use the shell_command tool to run commands as needed."
        )
        
        return execution_result

def main():
    """Main function to run the Advanced Shell Agent."""
    if len(sys.argv) < 2:
        print("Usage: python advanced_shell_agent.py 'your complex task here'")
        sys.exit(1)
    
    # Get the task from command line arguments
    task = " ".join(sys.argv[1:])
    
    # Get model ID from environment variable or use default
    model_id = os.environ.get("STRANDS_MODEL_ID")
    
    # Create and run the agent
    agent = AdvancedShellAgent(model_id=model_id, verbose=True)
    response = agent.run(task)
    
    print("\nTask completed. Final response:")
    print(response)

if __name__ == "__main__":
    main()
