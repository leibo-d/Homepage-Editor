FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/ ./app/
COPY templates/ ./templates/

# Create necessary directories
RUN mkdir -p /data/backups

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Health check using Python instead of curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()" || exit 1

# Run as non-root user
RUN useradd -m -u 1000 yamluser && \
    chown -R yamluser:yamluser /app /data
USER yamluser

# Start the application
CMD ["python", "app/yaml_editor.py"]
