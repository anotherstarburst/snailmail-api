# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY main.py .
COPY app/ ./app/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment setup
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose port (for documentation only; Cloud Run respects $PORT)
EXPOSE 8080

# Use Gunicorn to serve Flask app (the "app" object inside main.py)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
