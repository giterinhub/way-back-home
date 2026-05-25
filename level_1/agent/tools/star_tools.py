"""
Star Analysis Tools

This module provides tools for astronomical analysis using TWO different patterns:

1. LOCAL FUNCTION TOOL (extract_star_features):
   - Uses Gemini Vision directly to analyze star field images
   - Returns structured stellar features (primary_star, nebula_type, etc.)

2. Google Cloud MCP server for BigQuery (query via MCPToolset):
   - Connects to Google Cloud's managed BigQuery MCP server (in Vertex mode)
   - Or connects to a local SQLite star database (in AI Studio mode)
   - Exposes a unified execute_query tool
"""

import os
import json
import logging

from google import genai
from google.genai import types as genai_types
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
import google.auth
import google.auth.transport.requests

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
# CONFIGURATION - Environment variables only
# =============================================================================

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "")

# Initialize the Gemini client (auto-detect AI Studio API key or Vertex AI)
if os.environ.get("GEMINI_API_KEY"):
    genai_client = genai.Client() # Uses the key from environment
    is_vertex = False
else:
    genai_client = genai.Client(
        vertexai=True,
        project=PROJECT_ID or "placeholder",
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    )
    is_vertex = True

logger.info(f"[Star Tools] Initialized for project: {PROJECT_ID}")


# =============================================================================
# Google Cloud MCP server for BigQuery Connection
# =============================================================================

BIGQUERY_MCP_URL = "https://bigquery.googleapis.com/mcp"
_bigquery_toolset = None


def get_bigquery_mcp_toolset():
    """
    Get the BigQuery tool connection.
    If in AI Studio mode, returns a local SQLite FunctionTool.
    """
    global _bigquery_toolset

    if _bigquery_toolset is not None:
        return _bigquery_toolset

    if os.environ.get("GEMINI_API_KEY"):
        logger.info("[Star Tools] AI Studio Mode: Connecting to local SQLite Star Catalog...")
        
        def execute_query(query: str) -> str:
            """
            Execute a SQL query against the star catalog database.
            
            Args:
                query: The SQL query string (e.g. SELECT * FROM star_catalog)
                
            Returns:
                A JSON string containing the query results or error message.
            """
            import sqlite3
            import re
            
            # Clean the query: BigQuery uses backticks and project names like:
            # `project_id.way_back_home.star_catalog`
            # We need to translate this to just `star_catalog` for SQLite!
            cleaned_query = query
            # Replace `project_id.way_back_home.star_catalog` or similar with `star_catalog`
            cleaned_query = re.sub(r'`[^`.]+\.way_back_home\.star_catalog`', 'star_catalog', cleaned_query)
            cleaned_query = re.sub(r'`star_catalog`', 'star_catalog', cleaned_query)
            cleaned_query = re.sub(r'"[^".]+\.way_back_home\.star_catalog"', 'star_catalog', cleaned_query)
            
            # Locate db in the level_1 folder
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "star_catalog.db")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(cleaned_query)
                columns = [d[0] for d in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                cursor.close()
                conn.close()
                return json.dumps(results)
            except Exception as e:
                return json.dumps({"error": f"SQLite error: {str(e)}", "query_run": cleaned_query})
                
        # Wrap as FunctionTool so the agent treats it identically
        _bigquery_toolset = FunctionTool(execute_query)
        logger.info("[Star Tools] Connected to local SQLite Star Catalog successfully")
        return _bigquery_toolset

    logger.info("[Star Tools] Connecting to Google Cloud MCP server for BigQuery...")

    # Get OAuth credentials
    credentials, project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )

    # Refresh to get a valid token
    credentials.refresh(google.auth.transport.requests.Request())
    oauth_token = credentials.token

    # Use discovered project_id if not set in environment
    effective_project_id = PROJECT_ID or project_id

    # Configure headers for BigQuery MCP
    headers = {
        "Authorization": f"Bearer {oauth_token}",
        "x-goog-user-project": effective_project_id
    }

    # Create MCPToolset with StreamableHTTP connection
    _bigquery_toolset = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=BIGQUERY_MCP_URL,
            headers=headers
        )
    )

    logger.info(f"[Star Tools] Connected to BigQuery MCP for project: {effective_project_id}")
    return _bigquery_toolset


# =============================================================================
# Local FunctionTool: Star Feature Extraction
# =============================================================================

STAR_EXTRACTION_PROMPT = """Analyze this alien night sky image and extract stellar features.

Look for and identify:

1. PRIMARY STAR TYPE - What kind of star dominates the sky?
   Options: blue_giant, blue_supergiant, red_dwarf, red_dwarf_binary, red_giant, 
            green_pulsar, pulsar, magnetar, yellow_sun, yellow_dwarf, orange_sun

2. NEBULA TYPE - What kind of nebula or cosmic formation is visible?
   Options: ice_blue, crystalline, orange_red, fire, purple_magenta, purple, 
            bioluminescent, golden, amber, golden_brown

3. STELLAR COLOR - What's the overall color temperature of the stars?
   Options: blue_white, cyan, red_orange, deep_red, green_purple, green, 
            cyan_purple, yellow_gold, warm_yellow, amber

Examine the image carefully and identify the BEST match for each category.

Respond ONLY with valid JSON (no markdown, no explanation):
{"primary_star": "...", "nebula_type": "...", "stellar_color": "...", "description": "brief description of what you observe"}
"""


def _parse_json_response(text: str) -> dict:
    """Parse JSON from Gemini response, handling markdown formatting."""
    cleaned = text.strip()

    # Remove markdown code blocks if present
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
        logger.error(f"Failed to parse JSON: {e}")
        return {
            "error": f"Failed to parse response: {str(e)}",
            "raw_response": text[:500]
        }


def extract_star_features(image_url: str) -> dict:
    """
    Extract stellar features from a star field image using Gemini Vision.

    Args:
        image_url: Cloud Storage URL of the star field image (gs://...) or local path
    """
    logger.info(f"[Stars] Extracting features from: {image_url}")

    try:
        # If in AI Studio mode or we don't have GCS auth, read local file fallback
        if not is_vertex or image_url.startswith("outputs/") or not image_url.startswith("gs://"):
            local_path = image_url
            if image_url.startswith("gs://"):
                local_path = os.path.join("outputs", "star_field.png")
                # Fallback check
                if not os.path.exists(local_path):
                    local_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "level_1", "outputs", "star_field.png")
            
            print(f"[Stars] Reading local file for analysis: {local_path}")
            from PIL import Image
            img = Image.open(local_path)
            
            model_name = get_model_name("flash", "gemini-3.5-flash")
            response = genai_client.models.generate_content(
                model=model_name,
                contents=[STAR_EXTRACTION_PROMPT, img]
            )
        else:
            model_name = get_model_name("flash", "gemini-3.5-flash")
            response = genai_client.models.generate_content(
                model=model_name,
                contents=[
                    STAR_EXTRACTION_PROMPT,
                    genai_types.Part.from_uri(file_uri=image_url, mime_type="image/png")
                ]
            )

        result = _parse_json_response(response.text)

        logger.info(f"[Stars] Extracted: primary_star={result.get('primary_star')}, "
                   f"nebula={result.get('nebula_type')}")

        return result

    except Exception as e:
        logger.error(f"[Stars] Feature extraction failed: {str(e)}")
        return {
            "error": str(e),
            "primary_star": "unknown",
            "nebula_type": "unknown",
            "stellar_color": "unknown"
        }


# Create the local FunctionTool
extract_star_features_tool = FunctionTool(extract_star_features)
