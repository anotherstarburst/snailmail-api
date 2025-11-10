# SnailMail API

A Flask API for analyzing Rubik's cube faces using vision models. Supports both local development with Ollama and production deployment on Google Cloud Run.

## Features

- 📸 Image upload and analysis
- 🔍 Vision model inference (Gemma via Ollama or Cloud Run)
- 🗣️ Witty text service (Gemma via Ollama or Cloud Run)
- ✅ Pydantic validation of cube face colors
- 🔄 Environment-based service switching
- 🐳 Docker-ready for Cloud Run deployment

## Quick Start

### Local Development with Ollama

1. **Install and start Ollama:**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh

   # Start Ollama service
   ollama serve

   # Pull Gemma model (in another terminal)
   ollama pull gemma3:1b
   ollama pull gemma3:12b
   ```

2. **Run the API:**
   ```bash
   # Make script executable
   chmod +x run-local.sh

   # Run locally
   ./run-local.sh

   # Or run in Docker
   ./run-local.sh docker
   ```

3. **Test the API:**
   ```bash
   # Health check
   curl http://localhost:5000/health

   # Analyze a cube image
   curl -X POST http://localhost:5000/analyze \
     -F "image=@path/to/cube_image.jpg"

   # Validate cube data directly
   curl -X POST http://localhost:5000/validate-cube \
     -H "Content-Type: application/json" \
     -d '{"TL":"R","TC":"R","TR":"R","ML":"O","C":"R","MR":"G","BL":"Y","BC":"G","BR":"B"}'
   ```

## Environment Configuration

Create a `.env` file in the project root:

```bash
# Service Type: 'ollama' or 'cloudrun'
SERVICE_TYPE=ollama

# Inference Service URL
# Local: http://localhost:11434
# Cloud Run: https://your-inference-service.run.app
INFERENCE_SERVICE_URL=http://localhost:11434

WITTY_TEXT_MODEL=gemma3:1b
CUBE_ANALYSIS_MODEL=gemma3:12b

# API Configuration
PORT=5000
DEBUG=True
```

## Cloud Run Deployment

### Prerequisites

1. Install Google Cloud SDK
2. Set up a Google Cloud project
3. Enable Cloud Run and Cloud Build APIs

### Deploy

```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy to Cloud Run
./deploy.sh YOUR_PROJECT_ID us-central1
```

The script will:
- Build your container image
- Push to Google Container Registry
- Deploy to Cloud Run
- Output the service URL

### Manual Deployment

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Build the image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/snailmail-api

# Deploy to Cloud Run
gcloud run deploy snailmail-api \
  --image gcr.io/YOUR_PROJECT_ID/snailmail-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars SERVICE_TYPE=cloudrun,INFERENCE_SERVICE_URL=https://your-inference-service.run.app
```

## API Reference

### `POST /analyze-cube`

Analyzes a Rubik's cube face from an uploaded image.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `image` field with image file

**Response:**
```json
{
  "success": true,
  "cube_face": {
    "TL": "R", "TC": "R", "TR": "R",
    "ML": "O", "C": "R", "MR": "G",
    "BL": "Y", "BC": "G", "BR": "B"
  }
}
```

**Color Codes:**
- `R` - Red
- `G` - Green
- `B` - Blue
- `O` - Orange
- `Y` - Yellow
- `W` - White

**Tile Positions:**
- `TL` - Top Left
- `TC` - Top Center
- `TR` - Top Right
- `ML` - Middle Left
- `C` - Center
- `MR` - Middle Right
- `BL` - Bottom Left
- `BC` - Bottom Center
- `BR` - Bottom Right

### `POST /validate-cube`

Validates cube face data directly (useful for testing).

**Request:**
```json
{
  "TL": "R", "TC": "R", "TR": "R",
  "ML": "O", "C": "R", "MR": "G",
  "BL": "Y", "BC": "G", "BR": "B"
}
```

**Response:**
```json
{
  "valid": true,
  "cube_face": { ... }
}
```

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service_type": "ollama",
  "inference_url": "http://localhost:11434"
}
```

## Development

### Running Tests Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Run the app
python app.py

# In another terminal, test endpoints
curl http://localhost:5000/health
```

### Building Docker Image Locally

```bash
# Build
docker build -t snailmail-api .

# Run
docker run -p 5000:8080 \
  -e SERVICE_TYPE=ollama \
  -e INFERENCE_SERVICE_URL=http://host.docker.internal:11434 \
  -e PORT=8080 \
  snailmail-api

# Test
curl http://localhost:5000/health
```

## Validation

The API uses Pydantic for strict validation:

- ✅ Only valid color codes (`R`, `G`, `B`, `O`, `Y`, `W`)
- ✅ All 9 tiles must be present
- ✅ Descriptive error messages for invalid data

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `400` - Bad request (missing image)
- `422` - Validation error (invalid cube data)
- `500` - Server error
- `503` - Inference service unavailable

## License

MIT

## Contributing

Issues and pull requests welcome!
