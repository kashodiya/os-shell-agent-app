
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

class TaskPlannerTool(Tool):
    """Tool for creating a task plan."""
    
    def __init__(self):
        super().__init__(
            name="create_task_plan",
            description="Create a step-by-step plan to accomplish a complex task",
            parameters={
                "task": {
                    "type": "string",
                    "description": "The complex task that needs to be planned"
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
            "message": f"Create a JSON array of steps for: {task}. Each step should have a 'description' and 'command' field."
        }

class FileReadTool(Tool):
    """Tool for reading files."""
    
    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read the contents of a file",
            parameters={
                "path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            }
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Union[Dict[str, Any], ToolError]:
        """Read the contents of a file."""
        path = parameters.get("path")
        if not path:
            return ToolError("No file path provided")
        
        try:
            with open(path, 'r') as file:
                content = file.read()
            return {"content": content}
        except Exception as e:
            return ToolError(f"Error reading file: {str(e)}")

class FileWriteTool(Tool):
    """Tool for writing to files."""
    
    def __init__(self):
        super().__init__(
            name="write_file",
            description="Write content to a file",
            parameters={
                "path": {
                    "type": "string",
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                },
                "append": {
                    "type": "boolean",
                    "description": "Whether to append to the file instead of overwriting",
                    "default": False
                }
            }
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Union[Dict[str, Any], ToolError]:
        """Write content to a file."""
        path = parameters.get("path")
        content = parameters.get("content")
        append = parameters.get("append", False)
        
        if not path:
            return ToolError("No file path provided")
        if content is None:
            return ToolError("No content provided")
        
        try:
            mode = 'a' if append else 'w'
            with open(path, mode) as file:
                file.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            return ToolError(f"Error writing to file: {str(e)}")

class AdvancedShellAgent:
    """Advanced Shell Agent that can execute complex CLI tasks."""
    
    def __init__(self, model_id: Optional[str] = None, verbose: bool = False):
        """Initialize the Advanced Shell Agent with tools."""
        self.verbose = verbose
        self.agent = Agent(
            tools=[
                ShellCommandTool(),
                TaskPlannerTool(),
                FileReadTool(),
                FileWriteTool()
            ],
            model_id=model_id
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
