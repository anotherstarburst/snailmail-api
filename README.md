# SnailMail API

A Flask API for analyzing Rubik's cube faces and generating witty taunts. It uses a hybrid system for cube analysis, starting with a fast, local computer vision (CV) algorithm and falling back to a powerful vision language model (VLLM) for difficult cases. It supports both local development with Ollama and production deployment on Google Cloud Run.

## Features

-   📸 **Hybrid Cube Analysis**: Uses OpenCV for fast, robust CV-based color detection with an LLM fallback for improved accuracy.
-   🗣️ **Witty Taunt Generation**: An endpoint to generate dynamic, character-based trash talk using a text-based language model.
-   ✅ **Pydantic Validation**: Ensures all API inputs and outputs are strongly typed and valid.
-   🔄 **Environment-Based Configuration**: Easily switch between local (`ollama`) and production (`cloudrun`) services.
-   🐳 **Docker-Ready**: Fully containerized for easy deployment on Google Cloud Run or other container platforms.

## Quick Start

### Local Development with Ollama

1.  **Install and start Ollama:**
    ```bash
    # Install Ollama
    curl -fsSL https://ollama.com/install.sh | sh

    # Start Ollama service in a separate terminal
    ollama serve
    ```

2.  **Pull the required models:**
    ```bash
    # Pull the models specified in your .env file (defaults shown)
    ollama pull gemma3:1b   # For witty text
    ollama pull gemma3:12b  # For cube analysis fallback
    ```

3.  **Run the API:**
    ```bash
    # Make script executable
    chmod +x run-local.sh

    # Run the Flask app directly
    ./run-local.sh

    # Or, to run inside a Docker container
    ./run-local.sh docker
    ```

4.  **Test the API:**
    ```bash
    # Health check
    curl http://localhost:5000/health

    # Analyze a cube image
    curl -X POST http://localhost:5000/analyze-cube \
      -F "image=@/path/to/your/cube_image.jpg"

    # Generate a taunt
    curl -X POST http://localhost:5000/taunt \
     -H "Content-Type: application/json" \
     -d '{"npc_character": "Sarky the Squirrel", "player_character": "Dave the Developer"}'
    ```

## Environment Configuration

Create a `.env` file in the project root to configure the application:

```.env
# Service Type: 'ollama' for local, 'cloudrun' for production
SERVICE_TYPE=ollama

# URLs for the inference services (can be the same for Ollama)
WITTY_TEXT_INFERENCE_SERVICE_URL=http://localhost:11434
CUBE_ANALYSIS_INFERENCE_SERVICE_URL=http://localhost:11434

# Models for each service
WITTY_TEXT_MODEL=gemma3:1b
CUBE_ANALYSIS_MODEL=gemma3:12b

# API Configuration
PORT=5000
DEBUG=True
CORS_ORIGINS=*
```

## Cloud Run Deployment

### Prerequisites

1.  Install the Google Cloud SDK.
2.  Authenticate with `gcloud auth login`.
3.  Set up a Google Cloud project and enable the Cloud Run and Cloud Build APIs.

### Deploy

The included script automates the build and deployment process.

```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy to Cloud Run (replace with your project ID and desired region)
./deploy.sh YOUR_PROJECT_ID europe-west1
```

The script will:
-   Build the container image using Cloud Build.
-   Push the image to Google Container Registry.
-   Deploy the image to Cloud Run with recommended settings.
-   Output the final service URL.

## API Reference

### `POST /analyze-cube`

Analyzes a Rubik's cube face from an uploaded image. It first attempts analysis with a fast computer vision algorithm and falls back to a vision language model if confidence is low.

**Request:**
-   Content-Type: `multipart/form-data`
-   Body: An `image` field containing the image file.

**Success Response (200):**
```json
{
  "success": true,
  "cube_face": {
    "TL": "R", "TC": "G", "TR": "B",
    "ML": "W", "C": "Y", "MR": "O",
    "BL": "G", "BC": "R", "BR": "W"
  }
}
```

**Color Codes:**
-   `R` - Red
-   `G` - Green
-   `B` - Blue
-   `O` - Orange
-   `Y` - Yellow
-   `W` - White

### `POST /taunt`

Generates a witty taunt from an NPC character directed at a player.

**Request:**
```json
{
  "npc_character": "duck",
  "player_character": "snail",
  "context": "Player just failed a simple puzzle"
}
```

**Success Response (200):**
```json
{
    "success": true,
    "taunt": "Oh, well done. I'm sure the Weighted Companion Cube is very impressed.",
    "npc_character": "duck",
    "player_character": "snail"
}
```

### `GET /health`

A health check endpoint that returns key configuration values.

**Response:**
```json
{
  "SERVICE_TYPE": "ollama",
  "CORS_ORIGINS": "*",
  "WITTY_TEXT_MODEL": "gemma3:1b",
  "CUBE_ANALYSIS_MODEL": "gemma3:12b"
}
```

## Error Handling

The API returns standard HTTP status codes:

-   `200`: Success.
-   `400`: Bad Request (e.g., missing image file, invalid JSON).
-   `422`: Unprocessable Entity (validation error, e.g., invalid color codes).
-   `499`: Client Closed Request (client disconnected during a long process).
-   `500`: Internal Server Error.
-   `503`: Service Unavailable (inference service could not be reached).
