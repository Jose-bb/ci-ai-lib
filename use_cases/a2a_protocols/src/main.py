import sys
import warnings
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

# Eliminate flaml's harmless warning
warnings.filterwarnings("ignore", category=UserWarning, module="flaml")

from use_cases.a2a_protocols.src.swarm_setup import setup_swarm

# Initialize FastAPI application
app = FastAPI(title="A2A Troubleshooting Swarm API", version="3.0.0")

# Pydantic schema for the incoming incident report
class IncidentPayload(BaseModel):
    incident: str

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint to handle real-time communication with the frontend."""
    await websocket.accept()
    try:
        # Wait for the initial JSON from the frontend
        raw_data = await websocket.receive_json()
        
        # Validate the payload using Pydantic
        try:
            payload = IncidentPayload(**raw_data)
        except ValidationError as ve:
            await websocket.send_json({"type": "error", "content": f"Invalid payload structure: {ve.errors()}"})
            await websocket.close()
            return

        incident_report = payload.incident.strip()

        if not incident_report:
            await websocket.send_json({"type": "error", "content": "No incident provided. Closing connection."})
            await websocket.close()
            return

        await websocket.send_json({"type": "status", "content": "Initializing the Troubleshooting Swarm..."})
        
        # Setup the swarm
        try:
            proxy, manager = setup_swarm(websocket=websocket)
        except Exception as e:
            await websocket.send_json({"type": "error", "content": f"Error initializing the swarm: {e}"})
            await websocket.close()
            return

        await websocket.send_json({"type": "status", "content": "Starting the Committee Debate..."})

        # Initiate the chat asynchronously
        await proxy.a_initiate_chat(
            manager, 
            message=f"INCIDENT REPORT:\n{incident_report}", 
            summary_method="reflection_with_llm"
        )

        await websocket.send_json({"type": "status", "content": "Committee Session Terminated"})
        await websocket.close()

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"Internal server error: {e}")
        if websocket.client_state.name == "CONNECTED":
            await websocket.close()