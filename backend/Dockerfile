FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
RUN mkdir -p /models && python -c "import urllib.request as u;u.urlretrieve('https://github.com/onnx/models/raw/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx','/models/emotion-ferplus-8.onnx')" || echo 'emotion model download failed: /emotion/frame will return 503'
COPY data data
ENV DATA_DIR=/data PYTHONUNBUFFERED=1
RUN useradd -m api && mkdir /data && chown api /data
USER api
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request as u;u.urlopen('http://localhost:8000/health')"
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
