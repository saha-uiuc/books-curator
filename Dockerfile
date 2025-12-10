# Dockerfile for Literary Awards Dataset Pipeline
# Includes pre-extracted Wikipedia awards data, starts from API fetching stage

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY *.py ./
COPY *.sh ./
COPY scrapers/ ./scrapers/

# Copy pre-extracted awards data (from Wikipedia scraping)
# This allows the pipeline to skip scraping and start from API fetching
COPY awards_data/ ./data/

# Create additional directories
RUN mkdir -p data_backup merged_data

# Make shell scripts executable
RUN chmod +x *.sh

# Environment variables for API keys (must be provided at runtime)
ENV GOOGLE_BOOKS_API_KEY=""
ENV NYT_BOOKS_API_KEY=""

# Default command: show usage
CMD ["sh", "-c", "echo '=== Literary Awards Dataset Pipeline ===' && \
    echo '' && \
    echo 'Pre-loaded awards data:' && \
    ls -la data/*.json && \
    echo '' && \
    echo 'Usage:' && \
    echo '  # Fetch API data and merge (requires API keys):' && \
    echo '  docker run -e GOOGLE_BOOKS_API_KEY=... -e NYT_BOOKS_API_KEY=... \\\\'  && \
    echo '    -v $(pwd)/output:/app/merged_data literary-awards ./run_pipeline.sh --skip-scraping' && \
    echo '' && \
    echo '  # Run full pipeline (including re-scraping Wikipedia):' && \
    echo '  docker run -e GOOGLE_BOOKS_API_KEY=... -e NYT_BOOKS_API_KEY=... \\\\'  && \
    echo '    -v $(pwd)/output:/app/merged_data literary-awards ./run_pipeline.sh' && \
    echo ''"]

