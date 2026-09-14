FROM python:3.11-slim

# Логи сразу во stdout (видно в `docker compose logs`), без .pyc файлов
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

# Copy application code
COPY . .

# Create logs directory and run as non-root user
RUN mkdir -p logs \
    && useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Run the bot
CMD ["python", "bot.py"]
