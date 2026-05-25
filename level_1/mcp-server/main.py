"""
Level 1: Location Analyzer MCP Server

This MCP server provides tools for analyzing crash site evidence:
- analyze_geological: Analyze soil sample images
- analyze_botanical: Analyze flora video recordings (visual + audio)

Built with FastMCP for simple, Pythonic MCP server development.
Deployed to Cloud Run (for Vertex AI mode) or run locally (for AI Studio mode).
"""

import os
import json
import asyncio
import logging
from typing import Annotated

from pydantic import Field
from fastmcp import FastMCP

from google import genai
from google.genai import types as genai_types

# =============================================================================
# LOGGING SETUP
# =============================================================================

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_model_name(model_key: str, default: str) -> str:
    import os, json
    curr = os.path.abspath(__file__)
    for _ in range(5):
        curr = os.path.dirname(curr)
        cfg_path = os.path.join(curr, "workshop.config.json")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path) as f:
                    return json.load(f).get("models", {}).get(model_key, default)
            except Exception:
                pass
    return default


# =============================================================================
# FASTMCP SERVER INITIALIZATION
# =============================================================================

mcp = FastMCP("Location Analyzer MCP Server 🛸")

# =============================================================================
# GEMINI CLIENT INITIALIZATION
# =============================================================================

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

if not PROJECT_ID:
    logger.warning("GOOGLE_CLOUD_PROJECT not set - tools will fail in Vertex mode")

# Initialize Gemini client for multimodal analysis
if os.environ.get("GEMINI_API_KEY"):
    client = genai.Client() # Uses the key from environment
    is_vertex = False
else:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )
    is_vertex = True

logger.info(f"Initialized Gemini client (is_vertex={is_vertex}) for project: {PROJECT_ID}")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def parse_json_response(text: str) -> dict:
    """Parse JSON from Gemini response, handling markdown formatting."""
    cleaned = text.strip()
    
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return {
            "error": f"Failed to parse JSON: {str(e)}",
            "raw_response": text[:500]
        }


# =============================================================================
# GEOLOGICAL ANALYSIS TOOL
# =============================================================================

GEOLOGICAL_PROMPT = """Analyze this alien soil sample image.

Classify the PRIMARY characteristic (choose exactly one):

1. CRYO - Frozen/icy minerals, crystalline structures, frost patterns,
   blue-white coloration, permafrost indicators

2. VOLCANIC - Volcanic rock, basalt, obsidian, sulfur deposits,
   red-orange minerals, heat-formed crystite structures

3. BIOLUMINESCENT - Glowing particles, phosphorescent minerals,
   organic-mineral hybrids, purple-green luminescence

4. FOSSILIZED - Ancient compressed minerals, amber deposits,
   petrified organic matter, golden-brown stratification

Examine the image carefully and determine which biome this soil
sample most likely originated from.

Respond ONLY with valid JSON (no markdown, no explanation):
{
    "biome": "CRYO|VOLCANIC|BIOLUMINESCENT|FOSSILIZED",
    "confidence": 0.0-1.0,
    "minerals_detected": ["mineral1", "mineral2"],
    "description": "Brief description of what you observe"
}
"""


@mcp.tool()
def analyze_geological(
    image_url: Annotated[
        str,
        Field(description="Cloud Storage URL (gs://...) or local file path of the soil sample image")
    ]
) -> dict:
    """
    Analyzes a soil sample image to identify mineral composition and classify the planetary biome.
    """
    logger.info(f">>> 🔬 Tool: 'analyze_geological' called for '{image_url}'")
    
    try:
        # If in AI Studio mode or we don't have GCS auth, read local file fallback
        if not is_vertex or image_url.startswith("outputs/") or not image_url.startswith("gs://"):
            local_path = image_url
            if image_url.startswith("gs://"):
                local_path = os.path.join("outputs", "soil_sample.png")
                # Fallback to checking parent folder level_1/outputs
                if not os.path.exists(local_path):
                    local_path = os.path.join(os.path.dirname(__file__), "..", "outputs", "soil_sample.png")
            
            logger.info(f"    [Local Fallback] Reading: {local_path}")
            from PIL import Image
            img = Image.open(local_path)
            contents = [GEOLOGICAL_PROMPT, img]
        else:
            contents = [
                GEOLOGICAL_PROMPT,
                genai_types.Part.from_uri(file_uri=image_url, mime_type="image/png")
            ]

        # Call Gemini with the image
        model_name = get_model_name("flash", "gemini-3.5-flash")
        response = client.models.generate_content(
            model=model_name,
            contents=contents
        )
        
        result = parse_json_response(response.text)
        logger.info(f"    ✓ Geological analysis complete: {result.get('biome', 'UNKNOWN')}")
        return result
        
    except Exception as e:
        logger.error(f"    ✗ Geological analysis failed: {str(e)}")
        return {
            "error": str(e),
            "biome": "UNKNOWN",
            "confidence": 0.0,
            "minerals_detected": [],
            "description": f"Analysis failed: {str(e)}"
        }


# =============================================================================
# BOTANICAL ANALYSIS TOOL
# =============================================================================

BOTANICAL_PROMPT = """Analyze this alien flora video recording.

Pay attention to BOTH:
1. VISUAL elements: Plant appearance, movement patterns, colors, bioluminescence
2. AUDIO elements: Ambient sounds, rustling, organic noises, frequencies

Classify the PRIMARY biome (choose exactly one):

1. CRYO - Crystalline ice-plants, frost-covered vegetation, 
   crackling/tinkling sounds, slow brittle movements, blue-white flora

2. VOLCANIC - Heat-resistant plants, sulfur-adapted species,
   hissing/bubbling sounds, smoke-filtering vegetation, red-orange flora

3. BIOLUMINESCENT - Glowing plants, pulsing light patterns,
   humming/resonating sounds, reactive to stimuli, purple-green flora

4. FOSSILIZED - Ancient petrified plants, amber-preserved specimens,
   deep resonant sounds, minimal movement, golden-brown flora

Examine BOTH the visuals AND audio of this recording to determine
which biome this flora most likely belongs to.

Respond ONLY with valid JSON (no markdown, no explanation):
{
    "biome": "CRYO|VOLCANIC|BIOLUMINESCENT|FOSSILIZED",
    "confidence": 0.0-1.0,
    "species_detected": ["species1", "species2"],
    "audio_signatures": ["sound1", "sound2"],
    "visual_features": ["feature1", "feature2"],
    "description": "Brief description of visual and audio observations"
}
"""


@mcp.tool()
def analyze_botanical(
    video_url: Annotated[
        str,
        Field(description="Cloud Storage URL (gs://...) or local file path of the flora video recording")
    ]
) -> dict:
    """
    Analyzes a flora video recording (visual + audio) to identify plant species and classify the biome.
    """
    logger.info(f">>> 🌿 Tool: 'analyze_botanical' called for '{video_url}'")
    
    try:
        # If in AI Studio mode or we don't have GCS auth, read local file fallback
        if not is_vertex or video_url.startswith("outputs/") or not video_url.startswith("gs://"):
            local_path = video_url
            if video_url.startswith("gs://"):
                local_path = os.path.join("outputs", "flora_recording.mp4")
                if not os.path.exists(local_path):
                    local_path = os.path.join(os.path.dirname(__file__), "..", "outputs", "flora_recording.mp4")
            
            logger.info(f"    [Local Fallback] Reading video: {local_path}")
            # Upload file for local analysis in AI Studio
            uploaded_file = client.files.upload(file=local_path)
            contents = [BOTANICAL_PROMPT, uploaded_file]
        else:
            contents = [
                BOTANICAL_PROMPT,
                genai_types.Part.from_uri(file_uri=video_url, mime_type="video/mp4")
            ]

        # Call Gemini with the video
        model_name = get_model_name("flash", "gemini-3.5-flash")
        response = client.models.generate_content(
            model=model_name,
            contents=contents
        )
        
        result = parse_json_response(response.text)
        logger.info(f"    ✓ Botanical analysis complete: {result.get('biome', 'UNKNOWN')}")
        return result
        
    except Exception as e:
        logger.error(f"    ✗ Botanical analysis failed: {str(e)}")
        return {
            "error": str(e),
            "biome": "UNKNOWN",
            "confidence": 0.0,
            "species_detected": [],
            "audio_signatures": [],
            "visual_features": [],
            "description": f"Analysis failed: {str(e)}"
        }


# =============================================================================
# SERVER STARTUP (HTTP Transport for Cloud Run)
# =============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"🚀 Location Analyzer MCP Server starting on port {port}")
    logger.info(f"📍 MCP endpoint: http://0.0.0.0:{port}/mcp")
    logger.info(f"🔧 Tools: analyze_geological, analyze_botanical")
    
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=port,
        )
    )
