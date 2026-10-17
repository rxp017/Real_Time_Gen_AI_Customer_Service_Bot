FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-tel tesseract-ocr-spa && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home --uid 1000 bot && mkdir -p /app/data /app/.uploads /app/quarantine && chown -R bot:bot /app
USER bot
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.chatbot:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
