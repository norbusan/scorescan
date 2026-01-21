# Use Ubuntu 24.04 as base for Audiveris compatibility
FROM ubuntu:24.04

WORKDIR /app

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    wget \
    libfreetype6 \
    fontconfig \
    libasound2t64 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libgtk-3-0 \
    libnss3 \
    libgbm1 \
    libxss1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libpango-1.0-0 \
    libcairo2 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Audiveris 5.9.0 from .deb package (includes JRE)
RUN wget -q https://github.com/Audiveris/audiveris/releases/download/5.9.0/Audiveris-5.9.0-ubuntu24.04-x86_64.deb -O /tmp/audiveris.deb \
    && apt-get update \
    && mkdir -p /usr/share/desktop-directories/ \
    && apt-get install -y /tmp/audiveris.deb \
    && rm /tmp/audiveris.deb \
    && rm -rf /var/lib/apt/lists/*

# Install MuseScore 4 - Extract AppImage instead of running it (FUSE doesn't work in Docker)
RUN wget -q https://github.com/musescore/MuseScore/releases/download/v4.4.4/MuseScore-Studio-4.4.4.243461245-x86_64.AppImage -O /tmp/musescore.AppImage \
    && chmod +x /tmp/musescore.AppImage \
    && cd /opt \
    && /tmp/musescore.AppImage --appimage-extract \
    && mv squashfs-root musescore \
    && rm /tmp/musescore.AppImage \
    && ln -s /opt/musescore/AppRun /usr/local/bin/musescore

# Set environment variables
ENV AUDIVERIS_PATH="/opt/audiveris/bin/Audiveris"
ENV MUSESCORE_PATH="/usr/local/bin/musescore"
ENV QT_QPA_PLATFORM=offscreen

# Create symlink for python
RUN ln -sf /usr/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/bin/python3 /usr/bin/python

# Copy requirements first for caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application code
COPY . .

# Create storage directories
RUN mkdir -p storage/uploads storage/musicxml storage/pdf

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
