# Use a lightweight Python base image
FROM python:3.10-slim

# HF Spaces require a non-root user for security
RUN useradd -m -u 1000 user
USER user

# Set up environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR $HOME/app

# Copy the requirements file and install dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your environment code
COPY --chown=user . .

# Expose the required Hugging Face port
EXPOSE 7860


# We bypass openenv serve and run Uvicorn directly
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]