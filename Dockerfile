FROM python:3.10

# Set root as working directory
WORKDIR /app

COPY Server ./Server     
COPY Server/requirements.txt . 

# Install dependencies from Server's requirements.txt (optional)
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Cloud Run
EXPOSE 8080

# Run FastAPI app using full import path
CMD ["uvicorn", "Server.backend.app:app", "--host", "0.0.0.0", "--port", "8080"]
