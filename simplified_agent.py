
"""
Simplified Advanced Shell Agent - A version of the advanced shell agent
that doesn't rely on the strands package
"""
import asyncio
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional, Any, Union, AsyncGenerator

class SimplifiedAdvancedAgent:
    """Simplified version of the Advanced Shell Agent."""
    
    def __init__(self, verbose: bool = False):
        """Initialize the Simplified Advanced Shell Agent."""
        self.verbose = verbose
    
    async def execute_shell_command(self, command: str) -> Dict[str, Any]:
        """Execute a shell command and return its output."""
        if not command:
            return {"error": "No command provided"}
        
        try:
            # Execute the command and capture output
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for the command to complete
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            
            # Convert bytes to string
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            return {
                "stdout": stdout_str,
                "stderr": stderr_str,
                "exit_code": process.returncode
            }
        except asyncio.TimeoutError:
            return {"error": "Command timed out after 60 seconds"}
        except Exception as e:
            return {"error": f"Error executing command: {str(e)}"}
    
    async def read_file(self, path: str) -> Dict[str, str]:
        """Read the contents of a file."""
        if not path:
            return {"error": "No file path provided"}
        
        try:
            with open(path, 'r') as file:
                content = file.read()
            return {"content": content}
        except Exception as e:
            return {"error": f"Error reading file: {str(e)}"}
    
    async def write_file(self, path: str, content: str, append: bool = False) -> Dict[str, Any]:
        """Write content to a file."""
        if not path:
            return {"error": "No file path provided"}
        if content is None:
            return {"error": "No content provided"}
        
        try:
            mode = 'a' if append else 'w'
            with open(path, mode) as file:
                file.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"error": f"Error writing to file: {str(e)}"}
    
    async def process_command(self, command: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a command and yield results."""
        # Initial response
        yield {"type": "stream", "content": f"Executing command: `{command}`\n\n"}
        
        # Execute the command
        result = await self.execute_shell_command(command)
        
        # Format the response in Markdown
        response = f"**Command:** `{command}`\n\n"
        
        if "error" in result:
            response += f"**Error:** {result['error']}\n\n"
        else:
            if result["stdout"]:
                response += f"**Output:**\n```\n{result['stdout']}\n```\n\n"
            
            if result["stderr"]:
                response += f"**Error:**\n```\n{result['stderr']}\n```\n\n"
            
            response += f"**Exit code:** {result['exit_code']}\n"
        
        yield {"type": "stream", "content": response}
        yield {"type": "complete", "content": response}
    
    async def process_file_read(self, path: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a file read command and yield results."""
        # Initial response
        yield {"type": "stream", "content": f"Reading file: `{path}`\n\n"}
        
        # Read the file
        result = await self.read_file(path)
        
        # Format the response in Markdown
        if "error" in result:
            response = f"**Error:** {result['error']}\n\n"
        else:
            file_extension = os.path.splitext(path)[1].lower()
            language = ""
            
            # Determine language for syntax highlighting
            if file_extension in ['.py', '.pyw']:
                language = "python"
            elif file_extension in ['.js', '.jsx']:
                language = "javascript"
            elif file_extension in ['.html', '.htm']:
                language = "html"
            elif file_extension in ['.css']:
                language = "css"
            elif file_extension in ['.json']:
                language = "json"
            elif file_extension in ['.md', '.markdown']:
                language = "markdown"
            elif file_extension in ['.sh', '.bash']:
                language = "bash"
            
            response = f"**File:** `{path}`\n\n"
            if language:
                response += f"```{language}\n{result['content']}\n```\n\n"
            else:
                response += f"```\n{result['content']}\n```\n\n"
        
        yield {"type": "stream", "content": response}
        yield {"type": "complete", "content": response}
    
    async def process_file_write(self, path: str, content: str, append: bool = False) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a file write command and yield results."""
        # Initial response
        action = "Appending to" if append else "Writing to"
        yield {"type": "stream", "content": f"{action} file: `{path}`\n\n"}
        
        # Write to the file
        result = await self.write_file(path, content, append)
        
        # Format the response in Markdown
        if "error" in result:
            response = f"**Error:** {result['error']}\n\n"
        else:
            response = f"**Success:** Content {'appended to' if append else 'written to'} `{path}`\n\n"
        
        yield {"type": "stream", "content": response}
        yield {"type": "complete", "content": response}
    
    async def process_message(self, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a user message and yield results."""
        # Check if the message is a command
        if message.startswith("!"):
            command = message[1:].strip()
            async for response in self.process_command(command):
                yield response
        
        # Check if the message is a file read request
        elif message.startswith("read:"):
            path = message[5:].strip()
            async for response in self.process_file_read(path):
                yield response
        
        # Check if the message is a file write request
        elif message.startswith("write:"):
            # Format: write:path:content
            parts = message[6:].split(":", 1)
            if len(parts) == 2:
                path, content = parts
                async for response in self.process_file_write(path.strip(), content):
                    yield response
            else:
                yield {"type": "stream", "content": "**Error:** Invalid format for write command. Use `write:path:content`\n\n"}
                yield {"type": "complete", "content": "**Error:** Invalid format for write command. Use `write:path:content`\n\n"}
        
        # Check if the message is a file append request
        elif message.startswith("append:"):
            # Format: append:path:content
            parts = message[7:].split(":", 1)
            if len(parts) == 2:
                path, content = parts
                async for response in self.process_file_write(path.strip(), content, append=True):
                    yield response
            else:
                yield {"type": "stream", "content": "**Error:** Invalid format for append command. Use `append:path:content`\n\n"}
                yield {"type": "complete", "content": "**Error:** Invalid format for append command. Use `append:path:content`\n\n"}
        
        # Handle as a regular message
        else:
            help_text = """
# Shell Agent Help

You can interact with the shell agent using the following commands:

## Shell Commands
Start your message with `!` followed by the shell command:
```
!ls -la
!echo "Hello World"
!python -c "print('Hello from Python')"
```

## File Operations
Read a file:
```
read:/path/to/file.txt
```

Write to a file (overwrites existing content):
```
write:/path/to/file.txt:Content to write
```

Append to a file:
```
append:/path/to/file.txt:Content to append
```

## Examples
- `!ls -la` - List all files in the current directory
- `!cat app.py` - Display the content of app.py
- `read:app.py` - Read the content of app.py with syntax highlighting
- `write:test.txt:Hello World` - Create or overwrite test.txt with "Hello World"
- `append:log.txt:New log entry` - Append "New log entry" to log.txt
"""
            yield {"type": "stream", "content": help_text}
            yield {"type": "complete", "content": help_text}
