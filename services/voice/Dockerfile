FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install --no-cache-dir "TTS==0.22.0" fastapi "uvicorn[standard]"
COPY app.py .
EXPOSE 8020
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8020"]
