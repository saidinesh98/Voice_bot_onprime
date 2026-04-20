# Dockerfile for Backend (App1)
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for audio and heavy libraries
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend code
# (Exclusions are handled by .dockerignore)
COPY . .

# Expose the backend port
EXPOSE 8001

# Run the backend
CMD ["uvicorn", "app1:app", "--host", "0.0.0.0", "--port", "8001"]
