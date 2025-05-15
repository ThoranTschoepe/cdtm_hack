# 🐍 Basis-Image mit Python 3.11
FROM python:3.11-slim

# 📁 Arbeitsverzeichnis
WORKDIR /app

# 🔧 System-Tools für Pydantic + Audio + FastAPI
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 📦 Abhängigkeiten installieren
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# 📂 App-Code kopieren
COPY . .

# 🌐 Port öffnen
EXPOSE 8080

# 🚀 Start der FastAPI App
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

