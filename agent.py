import subprocess
import json
from typing import List, Dict, Any, Optional, Generator
from strands import Agent, tool
from strands.models import BedrockModel

@tool
def execute_shell(command: str) -> Dict[str, Any]:
    """Execute a shell command and return the output.
    
    Args:
        command: The shell command to execute
        
    Returns:
        A dictionary containing stdout, stderr, and exit_code
    """
    if not command:
        return {"error": "No command provided"}
    
    try:
        # Execute the command and capture output
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30  # Set a timeout to prevent hanging
        )
        
        # Return both stdout and stderr, along with the exit code
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 30 seconds"}
    except Exception as e:
        return {"error": f"Error executing command: {str(e)}"}

class ShellAgent:
    """Agent that uses shell commands to answer user questions."""
    
    def __init__(self, model_id: str = "us.anthropic.claude-opus-4-1-20250805-v1:0"):
        """Initialize the shell agent with the specified model."""
        # Create a Bedrock model instance
        bedrock_model = BedrockModel(
            model_id=model_id,
            streaming=True,
            temperature=0.3
        )
        
        # Create the agent with the model
        self.agent = Agent(
            tools=[execute_shell],
            model=bedrock_model,
            system_prompt="""You are a helpful assistant that can execute shell commands to answer user questions.
            
When a user asks a question, think about what shell commands would help answer it.
Plan your approach by breaking down complex tasks into smaller steps.
Execute the commands and interpret the results for the user in a clear, concise way.

Guidelines:
1. Always think step-by-step about what commands to run
2. For complex tasks, break them down into smaller steps
3. Explain what each command does before running it
4. Format command outputs nicely using markdown
5. If a command fails, explain why and suggest alternatives
6. Be security-conscious - don't run potentially harmful commands
7. When appropriate, use commands like ls, grep, find, cat, etc. to explore the system
8. Summarize your findings in a clear, user-friendly way

Remember to maintain a conversational memory of what commands have been run and their results.
"""
        )
        self.conversation_history = []
    
    def ask(self, question: str) -> str:
        """Ask the agent a question and get the response."""
        # Add the question to conversation history
        self.conversation_history.append({"role": "user", "content": question})
        
        # Get the response from the agent
        response = self.agent(question)
        
        # Convert the response to a string if it's not already
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)
        
        # Add the response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response_text})
        
        # Return the response as a string
        return response_text
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.conversation_history
