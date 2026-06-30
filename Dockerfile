FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN pip install --no-cache-dir uv

# Copy dependency files first (better caching)
COPY pyproject.toml uv.lock requirements.txt ./

# Install Python dependencies
RUN uv pip install --system -r requirements.txt

# Copy project source
COPY . .

# Collect static files (best practice even for SPA)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Default command (bisa di-override di docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]