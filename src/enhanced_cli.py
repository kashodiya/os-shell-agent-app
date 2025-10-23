
#!/usr/bin/env python3
"""
Enhanced CLI client for Shell Agents
"""
import argparse
import os
import sys
from typing import Optional

from shell_agent import ShellAgent
from advanced_shell_agent import AdvancedShellAgent

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
        "--advanced",
        "-a",
        action="store_true",
        help="Use the advanced shell agent with planning capabilities"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        help="Save the agent's response to the specified file"
    )
    
    return parser.parse_args()

def main():
    """Main function for the enhanced CLI client."""
    args = parse_arguments()
    
    # Get the task from arguments
    task = " ".join(args.task)
    
    # Get model ID from arguments, environment variable, or use default
    default_model = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    model_id = args.model or os.environ.get("STRANDS_MODEL_ID", default_model)
    
    if args.verbose:
        print(f"Task: {task}")
        print(f"Model ID: {model_id or 'Default'}")
        print(f"Agent type: {'Advanced' if args.advanced else 'Basic'}")
        print("Running Shell Agent...\n")
    
    try:
        # Create and run the appropriate agent
        if args.advanced:
            agent = AdvancedShellAgent(model_id=model_id, verbose=args.verbose)
        else:
            agent = ShellAgent(model_id=model_id)
        
        response = agent.run(task)
        
        # Print the response
        print(response)
        
        # Save to file if requested
        if args.output:
            try:
                with open(args.output, 'w') as f:
                    f.write(response)
                if args.verbose:
                    print(f"\nResponse saved to {args.output}")
            except Exception as e:
                print(f"Error saving response to file: {str(e)}", file=sys.stderr)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
