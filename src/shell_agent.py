"""
Shell Agent - An AI agent that can execute shell commands
"""
import os
import subprocess
import sys
from typing import Dict, List, Optional, Any, Union

from strands import Agent, Tool, ToolCall, ToolCallResult, ToolError

class ShellCommandTool(Tool):
    """Tool for executing shell commands."""
    
    def __init__(self):
        super().__init__(
            name="shell_command",
            description="Execute a shell command and return its output",
            parameters={
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                }
            }
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Union[Dict[str, Any], ToolError]:
        """Execute the shell command and return its output."""
        command = parameters.get("command")
        if not command:
            return ToolError("No command provided")
        
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
            return ToolError("Command timed out after 60 seconds")
        except Exception as e:
            return ToolError(f"Error executing command: {str(e)}")

class PlanningTool(Tool):
    """Tool for creating and managing execution plans."""
    
    def __init__(self):
        super().__init__(
            name="create_plan",
            description="Create a step-by-step plan to accomplish a complex task",
            parameters={
                "task": {
                    "type": "string",
                    "description": "The task that needs to be planned"
                }
            }
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Union[Dict[str, Any], ToolError]:
        """Create a plan for the given task."""
        task = parameters.get("task")
        if not task:
            return ToolError("No task provided")
        
        # This tool doesn't actually execute anything - it just asks the agent
        # to create a plan, which it will do using its reasoning capabilities
        return {
            "message": f"Please create a step-by-step plan for: {task}"
        }

class ShellAgent:
    """Shell Agent that can execute CLI commands."""
    
    def __init__(self, model_id: Optional[str] = None):
        """Initialize the Shell Agent with tools."""
        self.agent = Agent(
            tools=[ShellCommandTool(), PlanningTool()],
            model_id=model_id
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
