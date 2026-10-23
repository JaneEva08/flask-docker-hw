# Лёгкий официальный образ Python
FROM python:3.12-slim

# Не создавать .pyc и сразу выводить логи (видно в Docker Desktop → Logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

WORKDIR /app

# Сначала только зависимости: этот слой кэшируется,
# и при правке кода пересборка проходит за секунды
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения (лишнее отсекает .dockerignore)
COPY app.py .

# Запуск не от root — меньше вреда, если приложение взломают
RUN useradd --create-home --shell /usr/sbin/nologin appuser
USER appuser

EXPOSE 5000

# Docker сам проверяет /health. curl в slim-образе нет, поэтому проверка на Python
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health', timeout=3)"

# Production-сервер gunicorn вместо встроенного dev-сервера Flask
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
