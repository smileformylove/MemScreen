# MemScreen Docker Image
# Multi-stage build for optimization

# Stage 1: Base image with system dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DISPLAY=:99 \
    OLLAMA_HOST=0.0.0.0:11434

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Display server for GUI
    xvfb \
    x11vnc \
    fluxbox \
    # Screen capture
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    # Audio support
    portaudio19-dev \
    python3-pyaudio \
    # Other utilities
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies
FROM base as dependencies

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Ollama installation
FROM dependencies as ollama

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Download models (optional - can be done at runtime)
# RUN ollama pull qwen2.5vl:3b
# RUN ollama pull mxbai-embed-large

# Stage 4: Final application
FROM ollama as app

WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p ./db/videos ./db/audio ./db/screenshots

# Expose ports
EXPOSE 11434 5901

# Start script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
