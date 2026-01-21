FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-jre \
    wget \
    unzip \
    libfreetype6 \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Install Audiveris
RUN wget -q https://github.com/Audiveris/audiveris/releases/download/5.3.1/Audiveris_Setup-5.3.1-linux-x64.zip -O /tmp/audiveris.zip \
    && unzip /tmp/audiveris.zip -d /opt/audiveris \
    && rm /tmp/audiveris.zip \
    && chmod +x /opt/audiveris/bin/Audiveris

# Install MuseScore
RUN wget -q https://cdn.jsdelivr.net/musescore/v4.2.1/MuseScore-4.2.1.240230938-x86_64.AppImage -O /opt/musescore.AppImage \
    && chmod +x /opt/musescore.AppImage

ENV PATH="/opt/audiveris/bin:${PATH}"
ENV MUSESCORE_PATH="/opt/musescore.AppImage"

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directories
RUN mkdir -p storage/uploads storage/musicxml storage/pdf

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
