# Dockerfile for LLM Server
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if any
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies (only what's needed for LLM server)
# Note: requirements.txt is shared, but we only need fastapi, uvicorn, pydantic, ollama
RUN pip install --no-cache-dir fastapi uvicorn pydantic ollama

# Copy the multi_lingual directory
COPY multi_lingual/ ./multi_lingual/

# Expose the port
EXPOSE 8000

# Run the server
CMD ["uvicorn", "multi_lingual.server:server", "--host", "0.0.0.0", "--port", "8000"]
