# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY src/ ./src/

# Set environment variables
# PYTHONUNBUFFERED=1 ensures that Python output is sent straight to terminal (e.g. your container logs)
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "-m", "src.main"]
