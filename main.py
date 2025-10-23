
import os
import json
import asyncio
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from agent import ShellAgent

# Create FastAPI app
app = FastAPI(title="Shell Agent App")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a directory for static files if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create a connection manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

# Initialize connection manager
manager = ConnectionManager()

# Create a dictionary to store agent instances for each connection
agent_instances = {}

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Serve the index.html file."""
    with open("static/index.html", "r") as f:
        return f.read()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Handle WebSocket connections."""
    await manager.connect(websocket)
    
    # Create a new agent instance for this connection
    agent = ShellAgent()
    agent_instances[client_id] = agent
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "question":
                question = message["content"]
                
                # Get the response from the agent
                response = agent.ask(question)
                
                # Send the response
                await manager.send_message(
                    json.dumps({
                        "type": "response_chunk",
                        "content": response
                    }),
                    websocket
                )
                
                # Send a message indicating the response is complete
                await manager.send_message(
                    json.dumps({
                        "type": "response_complete"
                    }),
                    websocket
                )
            
            elif message["type"] == "get_history":
                # Send the conversation history
                history = agent.get_history()
                await manager.send_message(
                    json.dumps({
                        "type": "history",
                        "content": history
                    }),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Clean up the agent instance
        if client_id in agent_instances:
            del agent_instances[client_id]

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=54302,
        reload=True,
        access_log=False
    )
