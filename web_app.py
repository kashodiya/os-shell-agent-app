import asyncio
import json
import logging
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
from cli_agent import CLIAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OS Shell Agent Web App")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agents: Dict[str, CLIAgent] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        # Create a new agent instance for this client
        self.agents[client_id] = CLIAgent(session_id=client_id, safe_mode=True)
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.agents:
            del self.agents[client_id]
        logger.info(f"Client {client_id} disconnected")

    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))

    async def send_stream_chunk(self, chunk: str, client_id: str, message_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps({
                "type": "stream_chunk",
                "message_id": message_id,
                "chunk": chunk
            }))

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main index.html file"""
    index_path = Path(__file__).parent / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        # Return a basic HTML if index.html doesn't exist yet
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OS Shell Agent</title>
        </head>
        <body>
            <h1>OS Shell Agent Web App</h1>
            <p>Index.html file not found. Please create it.</p>
        </body>
        </html>
        """)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info(f"Received message from {client_id}: {message}")
            
            # Handle different message types
            if message["type"] == "chat_message":
                await handle_chat_message(message, client_id)
            elif message["type"] == "command":
                await handle_command_message(message, client_id)
            elif message["type"] == "toggle_safety_mode":
                await handle_safety_toggle(message, client_id)
            elif message["type"] == "get_safety_status":
                await handle_safety_status(message, client_id)
            elif message["type"] == "ping":
                await manager.send_message({"type": "pong"}, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Error in websocket for client {client_id}: {e}")
        manager.disconnect(client_id)

async def handle_chat_message(message: dict, client_id: str):
    """Handle chat messages from the client"""
    try:
        user_message = message.get("content", "")
        message_id = message.get("message_id", "")
        
        # Send acknowledgment
        await manager.send_message({
            "type": "message_received",
            "message_id": message_id
        }, client_id)
        
        # Get the agent for this client
        agent = manager.agents.get(client_id)
        if not agent:
            await manager.send_message({
                "type": "error",
                "message": "Agent not initialized"
            }, client_id)
            return
        
        # Send typing indicator
        await manager.send_message({
            "type": "typing",
            "message_id": message_id
        }, client_id)
        
        # Process the message with the agent
        try:
            # Use the agent's answer_question method for natural language queries
            result = agent.answer_question(user_message)
            
            # Send the response back to the client
            await manager.send_message({
                "type": "agent_response",
                "message_id": message_id,
                "content": result.get("answer", ""),
                "command_used": result.get("command_used", ""),
                "success": result.get("success", False),
                "raw_output": result.get("raw_output", {})
            }, client_id)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await manager.send_message({
                "type": "error",
                "message_id": message_id,
                "message": f"Error processing your request: {str(e)}"
            }, client_id)
        
        # Stop typing indicator
        await manager.send_message({
            "type": "typing_stop",
            "message_id": message_id
        }, client_id)
        
    except Exception as e:
        logger.error(f"Error in handle_chat_message: {e}")
        await manager.send_message({
            "type": "error",
            "message": f"Internal error: {str(e)}"
        }, client_id)

async def handle_command_message(message: dict, client_id: str):
    """Handle direct command execution requests"""
    try:
        command = message.get("command", "")
        working_directory = message.get("working_directory", None)
        force = message.get("force", False)
        message_id = message.get("message_id", "")
        
        # Get the agent for this client
        agent = manager.agents.get(client_id)
        if not agent:
            await manager.send_message({
                "type": "error",
                "message": "Agent not initialized"
            }, client_id)
            return
        
        # Send acknowledgment
        await manager.send_message({
            "type": "command_received",
            "message_id": message_id
        }, client_id)
        
        # Execute the command
        try:
            result = agent.execute_command(command, working_directory, force)
            
            # Send the response back to the client
            await manager.send_message({
                "type": "command_response",
                "message_id": message_id,
                "command": command,
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "return_code": result.get("return_code", -1),
                "success": result.get("success", False),
                "blocked": result.get("blocked", False),
                "requires_confirmation": result.get("requires_confirmation", False),
                "risk_level": result.get("risk_level", "unknown")
            }, client_id)
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            await manager.send_message({
                "type": "error",
                "message_id": message_id,
                "message": f"Error executing command: {str(e)}"
            }, client_id)
        
    except Exception as e:
        logger.error(f"Error in handle_command_message: {e}")
        await manager.send_message({
            "type": "error",
            "message": f"Internal error: {str(e)}"
        }, client_id)

async def handle_safety_toggle(message: dict, client_id: str):
    """Handle safety mode toggle requests"""
    try:
        enable_safe_mode = message.get("enable_safe_mode", None)
        message_id = message.get("message_id", "")
        
        # Get the agent for this client
        agent = manager.agents.get(client_id)
        if not agent:
            await manager.send_message({
                "type": "error",
                "message": "Agent not initialized"
            }, client_id)
            return
        
        # Send acknowledgment
        await manager.send_message({
            "type": "safety_toggle_received",
            "message_id": message_id
        }, client_id)
        
        # Toggle safety mode
        try:
            result = agent.toggle_safety_mode(enable_safe_mode)
            
            # Send the response back to the client
            await manager.send_message({
                "type": "safety_toggle_response",
                "message_id": message_id,
                "safe_mode": result["safe_mode"],
                "message": result["message"],
                "warning": result.get("warning"),
                "success": True
            }, client_id)
            
        except Exception as e:
            logger.error(f"Error toggling safety mode: {e}")
            await manager.send_message({
                "type": "error",
                "message_id": message_id,
                "message": f"Error toggling safety mode: {str(e)}"
            }, client_id)
        
    except Exception as e:
        logger.error(f"Error in handle_safety_toggle: {e}")
        await manager.send_message({
            "type": "error",
            "message": f"Internal error: {str(e)}"
        }, client_id)

async def handle_safety_status(message: dict, client_id: str):
    """Handle safety status requests"""
    try:
        message_id = message.get("message_id", "")
        
        # Get the agent for this client
        agent = manager.agents.get(client_id)
        if not agent:
            await manager.send_message({
                "type": "error",
                "message": "Agent not initialized"
            }, client_id)
            return
        
        # Get safety status
        try:
            status = agent.get_safety_status()
            
            # Send the response back to the client
            await manager.send_message({
                "type": "safety_status_response",
                "message_id": message_id,
                "safe_mode": status["safe_mode"],
                "status": status["status"],
                "description": status["description"],
                "success": True
            }, client_id)
            
        except Exception as e:
            logger.error(f"Error getting safety status: {e}")
            await manager.send_message({
                "type": "error",
                "message_id": message_id,
                "message": f"Error getting safety status: {str(e)}"
            }, client_id)
        
    except Exception as e:
        logger.error(f"Error in handle_safety_status: {e}")
        await manager.send_message({
            "type": "error",
            "message": f"Internal error: {str(e)}"
        }, client_id)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "active_connections": len(manager.active_connections)}

if __name__ == "__main__":
    # Use the port specified in the runtime information
    port = 52458  # First available port from runtime info
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info",
        access_log=True
    )
