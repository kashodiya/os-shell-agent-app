
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

# Import our simplified agent
from simplified_agent import SimplifiedAdvancedAgent

app = FastAPI()

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agents: Dict[str, SimplifiedAdvancedAgent] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        # Create a new agent instance for this client
        self.agents[client_id] = SimplifiedAdvancedAgent(verbose=True)

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.agents:
            del self.agents[client_id]

    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    def get_agent(self, client_id: str) -> SimplifiedAdvancedAgent:
        if client_id not in self.agents:
            self.agents[client_id] = SimplifiedAdvancedAgent(verbose=True)
        return self.agents[client_id]

manager = ConnectionManager()

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
                # Get the agent for this client
                agent = manager.get_agent(client_id)
                
                # Process the message and get a response
                async for response in agent.process_message(message["content"]):
                    await manager.send_message(json.dumps(response), client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=54545)
