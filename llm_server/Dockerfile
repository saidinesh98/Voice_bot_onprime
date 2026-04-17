# LLM Server Dockerfile
# Adapts your Python script into a container

FROM python:3.10-slim-bullseye

WORKDIR /app

# Install dependencies for AI models (if any)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy your requirements if you have them, or install core ones
# COPY requirements.txt .
# RUN pip install -r requirements.txt
RUN pip install fastapi uvicorn openai llama-cpp-python

# Copy your LLM script
COPY . .

# Adjust the port to match your script (e.g., 8000)
EXPOSE 8000

# Update 'main.py' to your actual script filename
CMD ["python", "main1.py"]
