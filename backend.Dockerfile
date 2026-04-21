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
RUN pip install --no-cache-dir -r requirements.txt

# Copy MeloTTS and install dependencies with CPU index to avoid large CUDA downloads
COPY MeloTTS ./MeloTTS
RUN pip install --no-cache-dir -r ./MeloTTS/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install -e ./MeloTTS && \
    python -m unidic download

# Copy the rest of the backend code
COPY . .

# Pre-download NLTK data
RUN python -m nltk.downloader averaged_perceptron_tagger averaged_perceptron_tagger_eng cmudict

# Expose the backend port
EXPOSE 8001


# Run the backend
CMD ["uvicorn", "app1:app", "--host", "0.0.0.0", "--port", "8001"]
