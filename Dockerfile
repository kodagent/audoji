# Pull the base image
FROM python:3.10

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install necessary system dependencies
RUN apt-get update -y && \
    # Install ffmpeg
    apt-get update && apt-get install -y ffmpeg

# Clean up APT when done
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /code

# Copy project
COPY . /code/

# Install Python dependencies including Whisper
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip install git+https://github.com/openai/whisper.git

# # Collect static files
# RUN python manage.py collectstatic --noinput

# Run the application
# CMD ["daphne", "audojiengine.asgi:application", "--port", "$PORT", "--bind", "0.0.0.0"]
CMD daphne audojiengine.asgi:application --port $PORT --bind 0.0.0.0
