# OS Shell Agent App

An AI agent that can execute tasks using shell commands. Built with the [Strands Agents](https://strandsagents.com/) framework.

## Features

- Execute shell commands using natural language instructions
- Break down complex tasks into manageable steps
- Support for both basic and advanced agent modes
- File reading and writing capabilities
- Task planning for complex operations

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/kashodiya/os-shell-agent-app.git
   cd os-shell-agent-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   # or
   pip install strands-agents strands-agents-tools
   ```

3. Set up your model provider credentials:
   - For Amazon Bedrock (default provider), set up your AWS credentials following the [Boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
   - Enable model access in Amazon Bedrock for Claude 4 Sonnet
   - The default model used is `us.anthropic.claude-sonnet-4-20250514-v1:0`, but you can specify a different model using the `--model` option or the `STRANDS_MODEL_ID` environment variable

## Usage

### Basic Usage

```bash
# Using the basic shell agent
python shell_agent_cli.py "list all files in the current directory"

# Using the advanced shell agent with planning capabilities
python shell_agent_cli.py --advanced "create a Python script that prints hello world and run it"
```

### Command Line Options

```
usage: shell_agent_cli.py [-h] [--model MODEL] [--advanced] [--verbose] [--output OUTPUT] task [task ...]

Shell Agent CLI - Execute tasks using natural language

positional arguments:
  task                  The task to execute in natural language

options:
  -h, --help            show this help message and exit
  --model MODEL, -m MODEL
                        Model ID to use (overrides STRANDS_MODEL_ID environment variable)
  --advanced, -a        Use the advanced shell agent with planning capabilities
  --verbose, -v         Enable verbose output
  --output OUTPUT, -o OUTPUT
                        Save the agent's response to the specified file
```

### Environment Variables

- `STRANDS_MODEL_ID`: Set this to specify the default model ID to use (e.g., `us.anthropic.claude-sonnet-4-20250514-v1:0`)

## Examples

### Basic Tasks

```bash
# List files
python shell_agent_cli.py "list all files in the current directory"

# Check system information
python shell_agent_cli.py "show me system information"

# Find large files
python shell_agent_cli.py "find files larger than 100MB in /var/log"
```

### Complex Tasks

```bash
# Create and run a script
python shell_agent_cli.py --advanced "create a Python script that generates a Fibonacci sequence and run it"

# Process log files
python shell_agent_cli.py --advanced "find all error messages in the log files and create a summary report"

# Set up a development environment
python shell_agent_cli.py --advanced "set up a React development environment with TypeScript"
```

## Project Structure

- `shell_agent_cli.py`: Main entry point for the CLI
- `src/shell_agent.py`: Basic shell agent implementation
- `src/advanced_shell_agent.py`: Advanced shell agent with planning capabilities
- `src/cli.py`: Basic CLI client
- `src/enhanced_cli.py`: Enhanced CLI client with support for both agent types

## License

MIT
