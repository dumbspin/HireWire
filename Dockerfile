# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

# Set working directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy download script and pre-download the sentence-transformers model
# This ensures offline execution during space runtime
COPY download_model.py /code/download_model.py
RUN python /code/download_model.py

# Copy the rest of the application files
COPY . /code

# Expose Streamlit's default Hugging Face Space port
EXPOSE 7860

# Run Streamlit on port 7860
CMD ["streamlit", "run", "demo/app.py", "--server.port=7860", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false"]
