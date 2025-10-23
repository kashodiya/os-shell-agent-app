
#!/usr/bin/env python3
"""
CLI client for the Shell Agent
"""
import argparse
import os
import sys
from typing import Optional

from shell_agent import ShellAgent

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Shell Agent CLI - Execute tasks using natural language"
    )
    
    parser.add_argument(
        "task",
        nargs="+",
        help="The task to execute in natural language"
    )
    
    parser.add_argument(
        "--model",
        "-m",
        help="Model ID to use (overrides STRANDS_MODEL_ID environment variable)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()

def main():
    """Main function for the CLI client."""
    args = parse_arguments()
    
    # Get the task from arguments
    task = " ".join(args.task)
    
    # Get model ID from arguments, environment variable, or use default
    default_model = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    model_id = args.model or os.environ.get("STRANDS_MODEL_ID", default_model)
    
    if args.verbose:
        print(f"Task: {task}")
        print(f"Model ID: {model_id or 'Default'}")
        print("Running Shell Agent...\n")
    
    try:
        # Create and run the agent
        agent = ShellAgent(model_id=model_id)
        response = agent.run(task)
        
        # Print the response
        print(response)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
