# Experimental: Wav2Lip pins old libraries, so expect to tweak versions. GPU strongly recommended.
FROM python:3.9-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg git libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN git clone --depth 1 https://github.com/Rudrabha/Wav2Lip.git
RUN pip install --no-cache-dir torch torchvision opencv-python-headless "numpy<1.24" "librosa==0.9.2" numba scipy tqdm fastapi "uvicorn[standard]" python-multipart
RUN mkdir -p Wav2Lip/face_detection/detection/sfd && python -c "import urllib.request as u;u.urlretrieve('https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth','Wav2Lip/face_detection/detection/sfd/s3fd.pth')" || echo "download s3fd.pth manually (see README)"
COPY app.py .
EXPOSE 8030
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8030"]
