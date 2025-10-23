
import asyncio
import json
import subprocess
import re
import os
import sys
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, AsyncGenerator, Any

app = FastAPI()

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

manager = ConnectionManager()

# Simple shell command execution
async def execute_shell_command(command: str) -> AsyncGenerator[Dict[str, Any], None]:
    # Initial response
    yield {"type": "stream", "content": f"Executing command: `{command}`\n\n"}
    
    try:
        # Execute the command with a timeout
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
        
        # Format the response in Markdown
        response = f"**Command:** `{command}`\n\n"
        
        if stdout_str:
            response += f"**Output:**\n```\n{stdout_str}\n```\n\n"
        
        if stderr_str:
            response += f"**Error:**\n```\n{stderr_str}\n```\n\n"
        
        response += f"**Exit code:** {process.returncode}\n"
        
        yield {"type": "stream", "content": response}
        yield {"type": "complete", "content": response}
        
    except asyncio.TimeoutError:
        error_msg = "Command execution timed out after 60 seconds."
        yield {"type": "stream", "content": f"**Error:** {error_msg}\n"}
        yield {"type": "complete", "content": f"**Error:** {error_msg}\n"}
    except Exception as e:
        error_msg = f"Error executing command: {str(e)}"
        yield {"type": "stream", "content": f"**Error:** {error_msg}\n"}
        yield {"type": "complete", "content": f"**Error:** {error_msg}\n"}

# Process user message and generate a response
async def process_user_message(message: str) -> AsyncGenerator[Dict[str, Any], None]:
    # Check if the message is a shell command
    if message.startswith("!"):
        command = message[1:].strip()
        async for response in execute_shell_command(command):
            yield response
    else:
        # Handle as a regular chat message
        yield {"type": "stream", "content": "I'm a shell agent assistant. To execute a shell command, start your message with '!' followed by the command.\n\n"}
        yield {"type": "stream", "content": "For example: `!ls -la` or `!echo 'Hello World'`\n\n"}
        yield {"type": "complete", "content": "I'm a shell agent assistant. To execute a shell command, start your message with '!' followed by the command.\n\nFor example: `!ls -la` or `!echo 'Hello World'`\n\n"}

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("index.html", "r") as f:
        return f.read()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "message":
                # Process the message and get a response
                async for response in process_user_message(message["content"]):
                    await manager.send_message(json.dumps(response), client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=54545)
