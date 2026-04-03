# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Hugging Face provides PORT 7860 by default
ENV PORT=7860

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (build-essential is sometimes needed for packages like scikit-learn or numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a user with UID 1000 (recommended for Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy the rest of the application code and set ownership to 'user'
COPY --chown=user . .

# Run NLTK setup to pre-download required data
RUN python nltk_setup.py

# Expose the port (informative only for Docker)
EXPOSE 7860

# Start the application using gunicorn
# --bind 0.0.0.0:7860 ensures it listens on all interfaces on the specified port
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]
