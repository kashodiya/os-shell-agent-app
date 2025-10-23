"""
Shell Agent - An AI agent that can execute shell commands
"""
import os
import subprocess
import sys
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
def create_plan(task: str) -> Dict[str, str]:
    """Create a step-by-step plan to accomplish a complex task.
    
    Args:
        task: The task that needs to be planned
        
    Returns:
        A dictionary containing a message with the planning request
    """
    if not task:
        raise ValueError("No task provided")
    
    # This tool doesn't actually execute anything - it just asks the agent
    # to create a plan, which it will do using its reasoning capabilities
    return {
        "message": f"Please create a step-by-step plan for: {task}"
    }

class ShellAgent:
    """Shell Agent that can execute CLI commands."""
    
    def __init__(self, model_id: Optional[str] = None):
        """Initialize the Shell Agent with tools."""
        if model_id:
            model = BedrockModel(model_id=model_id)
            self.agent = Agent(
                tools=[shell_command, create_plan],
                model=model
            )
        else:
            self.agent = Agent(
                tools=[shell_command, create_plan]
            )
    
    def run(self, task: str) -> str:
        """Run the agent with the given task."""
        return self.agent(task)

def main():
    """Main function to run the Shell Agent."""
    if len(sys.argv) < 2:
        print("Usage: python shell_agent.py 'your task here'")
        sys.exit(1)
    
    # Get the task from command line arguments
    task = " ".join(sys.argv[1:])
    
    # Get model ID from environment variable or use default
    model_id = os.environ.get("STRANDS_MODEL_ID")
    
    # Create and run the agent
    agent = ShellAgent(model_id=model_id)
    response = agent.run(task)
    
    print(response)

if __name__ == "__main__":
    main()
