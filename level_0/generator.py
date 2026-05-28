"""
Level 0: Avatar Generator

This module generates your unique space explorer avatar using
multi-turn image generation with Gemini (Nano Banana) for
character consistency across portrait and icon.

=== CODELAB INSTRUCTIONS ===

You will implement three steps in the generate_explorer_avatar() function:

1. MODULE_5_STEP_1_CREATE_CHAT_SESSION
   Create a chat session to maintain character consistency

2. MODULE_5_STEP_2_GENERATE_PORTRAIT
   Generate the explorer portrait with your customizations

3. MODULE_5_STEP_3_GENERATE_ICON
   Generate a consistent map icon using the same chat session

Follow the instructions in the codelab to complete each step.
"""

from google import genai
from google.genai import types
from PIL import Image
import json
import os
import io

# Load configuration from setup (config.json is in project root)
CONFIG_PATH = "../config.json"

with open(CONFIG_PATH) as f:
    config = json.load(f)

USERNAME = config.get("username", "explorer")

if "suit_color" not in config or "appearance" not in config:
    print("⚠️  Warning: Explorer customization properties ('suit_color', 'appearance') not found in config.json.")
    print("   Please run 'python customize.py' to select your space suit color and appearance!")
    print("   Using default explorer traits for now...\n")

SUIT_COLOR = config.get("suit_color", "metallic silver with blue accents")
APPEARANCE = config.get("appearance", "friendly smile, short styled hair")

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

# Initialize the Gemini client (auto-detect AI Studio API key or Vertex AI)
if os.environ.get("GEMINI_API_KEY"):
    client = genai.Client() # Uses the key from environment
    image_model = get_model_name("image", "gemini-3.1-flash-image-preview")
    is_vertex = False
else:
    client = genai.Client(
        vertexai=True,
        project=os.environ.get("GOOGLE_CLOUD_PROJECT", config.get("project_id")),
        location="us-central1"
    )
    image_model = "gemini-2.5-flash-image"
    is_vertex = True


def generate_explorer_avatar() -> dict:
    """
    Generate portrait and icon using multi-turn chat for consistency.

    The key technique here is using a CHAT SESSION rather than independent
    API calls. This allows Gemini to "remember" the character it created
    in the first turn, ensuring the icon matches the portrait.

    Returns:
        dict with portrait_path and icon_path
    """

    # =========================================================================
    # MODULE_5_STEP_1_CREATE_CHAT_SESSION
    # =========================================================================
    # TODO: Create a chat session for multi-turn generation
    #
    # Create a chat session using client.chats.create() with:
    # - model: "gemini-2.5-flash-image" (Nano Banana)
    # - config: GenerateContentConfig with response_modalities=["TEXT", "IMAGE"]
    #
    # Hint: You need to use types.GenerateContentConfig
    # =========================================================================
    if not is_vertex and image_model.startswith("imagen-"):
        # Create a mock chat class to handle image generation via AI Studio's Imagen API
        # while keeping the participant's multi-turn code completely identical.
        class AIStudioImageChat:
            def __init__(self, client, image_model):
                self.client = client
                self.image_model = image_model
                self.history = []

            def send_message(self, prompt_text: str):
                print(f"Generating image via AI Studio {self.image_model}...")
                response = self.client.models.generate_images(
                    model=self.image_model,
                    prompt=prompt_text,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="1:1",
                        output_mime_type="image/png"
                    )
                )
                
                class MockPart:
                    def __init__(self, data):
                        class MockInlineData:
                            def __init__(self, d):
                                self.data = d
                        self.inline_data = MockInlineData(data)

                class MockContent:
                    def __init__(self, data):
                        self.parts = [MockPart(data)]

                class MockCandidate:
                    def __init__(self, data):
                        self.content = MockContent(data)

                class MockResponse:
                    def __init__(self, data):
                        self.candidates = [MockCandidate(data)]

                img_bytes = response.generated_images[0].image.image_bytes
                return MockResponse(img_bytes)

        chat = AIStudioImageChat(client, image_model)
    else:
        chat = client.chats.create(
            model=image_model,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

    # =========================================================================
    # MODULE_5_STEP_2_GENERATE_PORTRAIT
    # =========================================================================
    # TODO: Generate the explorer portrait
    #
    # 1. Create a portrait_prompt string that includes:
    #    - APPEARANCE, USERNAME, and SUIT_COLOR variables
    #    - Style requirements (digital illustration, white background, etc.)
    #
    # 2. Send the prompt using chat.send_message(portrait_prompt)
    #
    # 3. Extract the image from the response:
    #    - Loop through portrait_response.candidates[0].content.parts
    #    - Find the part where part.inline_data is not None
    #    - Convert to PIL Image: Image.open(io.BytesIO(part.inline_data.data))
    #    - Save to "outputs/portrait.png"
    #
    # 4. Print progress messages for user feedback
    # =========================================================================
    portrait_image = None # Replace this section

    # =========================================================================
    # MODULE_5_STEP_3_GENERATE_ICON
    # =========================================================================
    # TODO: Generate a consistent map icon
    #
    # 1. Create an icon_prompt that asks for the SAME character
    #    - Emphasize consistency: "SAME person, SAME face, SAME suit"
    #    - Request tighter crop (head and shoulders only)
    #    - Request white background and square aspect ratio
    #
    # 2. Send the prompt using chat.send_message(icon_prompt)
    #    - The chat session remembers the character from step 2!
    #
    # 3. Extract and save the icon image to "outputs/icon.png"
    #
    # 4. Print progress messages for user feedback
    # =========================================================================
    portrait_prompt = f"""Create a stylized space explorer portrait.

Character appearance: {APPEARANCE}
Name on suit patch: "{USERNAME}"
Suit color: {SUIT_COLOR}

CRITICAL STYLE REQUIREMENTS:
- Digital illustration style, clean lines, vibrant saturated colors
- Futuristic but weathered space suit with visible mission patches
- Background: Pure solid white (#FFFFFF) - absolutely no gradients, patterns, or elements
- Frame: Head and shoulders only, 3/4 view facing slightly left
- Lighting: Soft diffused studio lighting, no harsh shadows
- Expression: Determined but approachable
- Art style: Modern animated movie character portrait (similar to Pixar or Dreamworks style)

The white background is essential - the avatar will be composited onto a map."""

    print("🎨 Generating your portrait...")
    portrait_response = chat.send_message(portrait_prompt)

    # Extract the image from the response.
    # Gemini returns a response with multiple "parts" - we need to find the image part.
    portrait_image = None
    for part in portrait_response.candidates[0].content.parts:
        if part.inline_data is not None:
            # Found the image! Convert from bytes to PIL Image and save.
            image_bytes = part.inline_data.data
            portrait_image = Image.open(io.BytesIO(image_bytes))
            portrait_image.save("outputs/portrait.png")
            break

    if portrait_image is None:
        raise Exception("Failed to generate portrait - no image in response")

    print("✓ Portrait generated!")

    # MODULE_5_STEP_3_GENERATE_ICON
    # Second turn: Generate a consistent icon for the map.
    # Because we're in the same chat session, Gemini remembers the character
    # from the portrait and will maintain visual consistency.
    icon_prompt = """Now create a circular map icon of this SAME character.

CRITICAL REQUIREMENTS:
- SAME person, SAME face, SAME expression, SAME suit — maintain perfect consistency with the portrait
- Tighter crop: just the head and very top of shoulders
- Background: Pure solid white (#FFFFFF)
- Optimized for small display sizes (will be used as a 64px map marker)
- Keep the exact same art style, colors, and lighting as the portrait
- Square 1:1 aspect ratio

This icon must be immediately recognizable as the same character from the portrait."""

    print("🖼️  Creating map icon...")
    icon_response = chat.send_message(icon_prompt)


    return {
        "portrait_path": "outputs/portrait.png",
        "icon_path": "outputs/icon.png"
    }


if __name__ == "__main__":
    # Create outputs directory if it doesn't exist
    os.makedirs("outputs", exist_ok=True)

    print(f"Generating avatar for {USERNAME}...")
    result = generate_explorer_avatar()
    print(f"✅ Avatar created!")
    print(f"   Portrait: {result['portrait_path']}")
    print(f"   Icon: {result['icon_path']}")
