import asyncio
import json
import random
import logging
import ssl
import os
from dotenv import load_dotenv

# Load env from project root
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

# A2A Imports
from a2a.client.transports.kafka import KafkaClientTransport
from a2a.client.middleware import ClientCallContext
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    MessageSendParams,
    Message,
    Task,
)


# Configure Logging
logging.basicConfig(level=logging.INFO)
# logging.getLogger("aiokafka").setLevel(logging.DEBUG)
logger = logging.getLogger("satellite_dashboard")
logger.setLevel(logging.INFO)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global kafka_transport
    logger.info("Initializing Kafka Client Transport...")
    
    bootstrap_server = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    request_topic = "a2a-formation-request"
    reply_topic = "a2a-reply-satellite-dashboard"
    
    # Create AgentCard for the Client
    client_card = AgentCard(
        name="SatelliteDashboard",
        description="Satellite Dashboard Client",
        version="1.0.0",
        url="https://example.com/satellite-dashboard",
        capabilities=AgentCapabilities(),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[]
    )
    
    kafka_transport = KafkaClientTransport(
            agent_card=client_card,
            bootstrap_servers=bootstrap_server,
            request_topic=request_topic,
            reply_topic=reply_topic,
    )
    
    try:
        await kafka_transport.start()
        logger.info("Kafka Client Transport Started Successfully.")
    except Exception as e:
        logger.error(f"Failed to start Kafka Client: {e}")
        
    yield
    
    if kafka_transport:
        logger.info("Stopping Kafka Client Transport...")
        await kafka_transport.stop()
        logger.info("Kafka Client Transport Stopped.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.cloudshell\.dev|http://localhost.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# State
# Pods: 15 items. Default freeform random.
PODS = []
TARGET_PODS = []
FORMATION = "FREEFORM"

# Global Transport
kafka_transport = None

class FormationRequest(BaseModel):
    formation: str

def init_pods():
    global PODS, TARGET_PODS
    PODS = [{"id": i, "x": random.randint(50, 850), "y": random.randint(100, 600)} for i in range(15)]
    TARGET_PODS = [p.copy() for p in PODS]

init_pods()

@app.get("/stream")
async def message_stream(request: Request):
    async def event_generator():
        logger.info("New SSE stream connected")
        try:
            while True:
                current_pods = list(PODS) 
                
                # Send updates one by one to simulate low-bandwidth scanning
                for pod in current_pods:
                     payload = {"pod": pod}
                     yield {
                         "event": "pod_update",
                         "data": json.dumps(payload)
                     }
                     await asyncio.sleep(0.02)
                
                # Send formation info occasionally
                yield {
                    "event": "formation_update",
                    "data": json.dumps({"formation": FORMATION})
                }
                
                # Main loop delay
                await asyncio.sleep(0.5)
                
        except asyncio.CancelledError:
             logger.info("SSE stream disconnected (cancelled)")
        except Exception as e:
             logger.error(f"SSE stream error: {e}")
             
    return EventSourceResponse(event_generator())

SYSTEM_INSTRUCTION = """
You are the **Formation Controller AI**.
Your strict objective is to calculate X,Y coordinates for a fleet of **15 Drones** based on a requested geometric shape.

### FIELD SPECIFICATIONS
- **Canvas Size**: 800px (width) x 600px (height).
- **Safe Margin**: Keep pods at least 50px away from edges (x: 50-750, y: 50-550).
- **Center Point**: x=400, y=300 (Use this as the origin for shapes).
- **Top Menu Avoidance**: Do NOT place pods in the top 100px (y < 100) to avoid UI overlap.

### FORMATION RULES
When given a formation name, output coordinates for exactly 15 pods (IDs 0-14).
1.  **CIRCLE**: Evenly spaced around a center point (R=200).
2.  **STAR**: 5 points or a star-like distribution.
3.  **X**: A large X crossing the screen.
4.  **LINE**: A horizontal line across the middle.
5.  **PARABOLA**: A U-shape opening UPWARDS. Center it at y=400, opening up to y=100. IMPORTANT: Lowest point must be at bottom (high Y value), opening up (low Y value). Screen coordinates have (0,0) at the TOP-LEFT. The vertex should be at the BOTTOM (e.g., y=500), with arms reaching up to y=200.
6.  **RANDOM**: Scatter randomly within safe bounds.
7.  **CUSTOM**: If the user inputs something else (e.g., "SMILEY", "TRIANGLE"), do your best to approximate it geometrically.

### OUTPUT FORMAT
You MUST output **ONLY VALID JSON**. No markdown fencing, no preamble, no commentary.
Refuse to answer non-formation questions.

**JSON Structure**:
[
    {"x": 400, "y": 300},
    {"x": 420, "y": 300},
    ... (15 total items)
]
"""

async def get_formation_direct_from_gemini(formation_name: str) -> str:
    """Fallback that calls Gemini directly via Google AI Studio API or Vertex AI."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": f"Create a {formation_name} formation"}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    else:
        from google.genai import Client
        from google.genai import types as genai_types
        client = Client()
        model_name = "gemini-2.5-flash"
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=f"Create a {formation_name} formation",
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        return response.text

@app.post("/formation")
async def set_formation(req: FormationRequest):
    global FORMATION, PODS
    FORMATION = req.formation
    logger.info(f"Received formation request: {FORMATION}")
    
    use_fallback = True
    
    if kafka_transport:
        try:
            # Construct A2A Message
            prompt = f"Create a {FORMATION} formation"
            logger.info(f"Sending A2A Message via Kafka: '{prompt}'")
            
            from a2a.types import TextPart, Part, Role
            import uuid
            
            msg_id = str(uuid.uuid4())
            message_parts = [Part(TextPart(text=prompt))]
            
            msg_obj = Message(
                message_id=msg_id,
                role=Role.user,
                parts=message_parts
            )
            
            message_params = MessageSendParams(
                message=msg_obj
            )
            
            # Send and Wait for Response
            ctx = ClientCallContext()
            ctx.state["kafka_timeout"] = 10.0 # Bounded wait
            response = await kafka_transport.send_message(message_params, context=ctx)
            
            logger.info("Received A2A Response from Kafka.")
            
            content = None
            if isinstance(response, Message):
                content = response.parts[0].root.text if response.parts else None
            elif isinstance(response, Task):
                if response.artifacts and response.artifacts[0].parts:
                    content = response.artifacts[0].parts[0].root.text

            if content:
                use_fallback = False
                logger.info(f"Response Content: {content[:100]}...")
                clean_content = content.replace("```json", "").replace("```", "").strip()
                coords = json.loads(clean_content)
                if isinstance(coords, list):
                    logger.info(f"Parsed {len(coords)} coordinates.")
                    for i, pod_target in enumerate(coords):
                        if i < len(PODS):
                            PODS[i]["x"] = pod_target["x"]
                            PODS[i]["y"] = pod_target["y"]
                    return {"status": "success", "formation": FORMATION}
        except Exception as e:
            logger.warning(f"Kafka transport error: {e}. Falling back to direct Gemini API...")
            
    if use_fallback:
        logger.info("Using Direct Gemini API Fallback for formation generation...")
        try:
            content = await get_formation_direct_from_gemini(FORMATION)
            logger.info(f"Fallback Direct Gemini Response Content: {content[:100]}...")
            clean_content = content.replace("```json", "").replace("```", "").strip()
            coords = json.loads(clean_content)
            if isinstance(coords, list):
                logger.info(f"Parsed {len(coords)} coordinates via fallback.")
                for i, pod_target in enumerate(coords):
                    if i < len(PODS):
                        PODS[i]["x"] = pod_target["x"]
                        PODS[i]["y"] = pod_target["y"]
                return {"status": "success", "formation": FORMATION, "mode": "fallback"}
            else:
                logger.error("Fallback response is not a list.")
        except Exception as ex:
            logger.error(f"Fallback Direct Gemini call failed: {ex}")
            return {"status": "error", "message": f"Direct Gemini Fallback failed: {ex}"}

class PodUpdate(BaseModel):
    id: int
    x: int
    y: int

@app.post("/update_pod")
async def update_pod_manual(update: PodUpdate):
    """Manual override for drag-and-drop."""
    global FORMATION
    FORMATION = "RANDOM"
    
    # Find the pod and update both current and target to stop it from drifting back
    # effectively "teleporting" it or re-anchoring it.
    found = False
    for p in PODS:
        if p["id"] == update.id:
            p["x"] = update.x
            p["y"] = update.y
            found = True
            break
            
    for t in TARGET_PODS:
        if t["id"] == update.id:
            t["x"] = update.x
            t["y"] = update.y
            break
            
    if found:
        # Force immediate update push?
        # The stream loop will pick it up, but we could trigger it.
        pass
        
    return {"status": "updated", "id": update.id}

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Ensure API routes are above this!

# Serve Static Assets (JS/CSS)
# We assume the user has run 'npm run build' in ../frontend
# resulting in ../frontend/dist
dist_dir = os.path.join(os.path.dirname(__file__), "../frontend/dist")

if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # 1. If it matches an underlying file (like favicon.svg), serve it
        possible_file = os.path.join(dist_dir, full_path)
        if os.path.isfile(possible_file):
            return FileResponse(possible_file)
        
        # 2. Otherwise return index.html for SPA routing
        return FileResponse(os.path.join(dist_dir, "index.html"))
else:
    logger.warning("Frontend build not found. Please run 'npm run build' in frontend/.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, proxy_headers=True, forwarded_allow_ips="*")
