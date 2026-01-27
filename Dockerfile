# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY src/ ./src/

# Create workspace directory
RUN mkdir -p /workspace/skills

# Set environment variables
# PYTHONUNBUFFERED=1 ensures that Python output is sent straight to terminal (e.g. your container logs)
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE_DIR=/workspace
ENV SKILLS_DIR=/workspace/skills

# Run the bot
CMD ["python", "-m", "src.main"]
