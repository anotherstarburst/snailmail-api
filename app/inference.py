from flask import current_app
import re, json, base64, requests
from app.utils import get_authenticated_headers
from typing import Optional

def call_text_inference(prompt: str, service_url: str, model: str, service_type: str) -> dict | None:
    """
    Calls a text generation model and expects a JSON response.
    """

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    headers = get_authenticated_headers(service_url) if service_type == 'cloudrun' else {}

    try:
        with requests.post(f"{service_url}/api/generate", json=payload, headers=headers, timeout=60) as resp:

            resp.raise_for_status()
            response_data = resp.json()

            # The 'response' field contains the full JSON string from the model
            json_string = response_data.get("response", "")
            if not json_string:
                return None

            return json.loads(json_string)

    except (requests.RequestException, json.JSONDecodeError) as e:
        current_app.logger.error(f"Text inference call failed: {e}")
        print(f"Text inference call failed: {e}")
        return None


def call_vision_inference_streaming(image_data, check_connection, service_url, model, service_type):
    image_b64 = base64.b64encode(image_data).decode('utf-8')

    # Expanded prompt for clarity and reliability
    prompt = """You are an expert vision model specializing in analyzing Rubik's Cube faces. Your task is to identify the color of each of the 9 tiles on the cube face shown in the image.

**Instructions:**
1.  Examine the image to determine the color of each of the 9 tiles.
2.  The valid colors and their required codes are:
    - Red: "R"
    - Green: "G"
    - Blue: "B"
    - Orange: "O"
    - Yellow: "Y"
    - White: "W"
3.  Map each color to its position on the cube face using these keys:
    - `TL`: Top-Left
    - `TC`: Top-Center
    - `TR`: Top-Right
    - `ML`: Middle-Left
    - `C`: Center
    - `MR`: Middle-Right
    - `BL`: Bottom-Left
    - `BC`: Bottom-Center
    - `BR`: Bottom-Right
4.  Your response MUST be a single, valid JSON object. Do not include any text, explanations, or markdown formatting like ```json before or after the JSON object.

**Example of a perfect response:**
{
    "TL": "R", "TC": "G", "TR": "B",
    "ML": "W", "C": "Y", "MR": "O",
    "BL": "G", "BC": "R", "BR": "W"
}
"""

    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_b64],
        "stream": False,
        "format": "json"
    }
    headers = get_authenticated_headers(service_url) if service_type == 'cloudrun' else {}

    try:
        # Use a single request, not a session with streaming
        with requests.post(f"{service_url}/api/generate", json=payload, headers=headers, timeout=60) as resp:
            # Check for HTTP errors
            resp.raise_for_status()

            # The entire response is now in resp.json()
            response_data = resp.json()

            # The 'response' field contains the full JSON string from the model
            json_string = response_data.get("response", "")
            if not json_string:
                current_app.logger.error("Vision model returned an empty 'response' field.")
                return None

            # Strip potential markdown and load the JSON from the string
            json_string_cleaned = re.sub(r'^```json\s*|```\s*$', '', json_string.strip())
            return json.loads(json_string_cleaned)

    except requests.RequestException as e:
        current_app.logger.error(f"Vision inference call failed: {e}")
        return None
    except json.JSONDecodeError as e:
        # Log the problematic string to see what the model is actually returning
        current_app.logger.error(f"Failed to decode JSON from vision model. Response text: '{response_data.get('response', '')}'")
        return None

def call_inference_streaming(image_data, check_connection, service_url, model, service_type):
    # This function is now a wrapper for the new vision-specific function
    return call_vision_inference_streaming(image_data, check_connection, service_url, model, service_type)
