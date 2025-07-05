#!/bin/bash

# Start Ollama service in background
ollama serve &

# Wait for Ollama to start
sleep 10

# Pull the model
ollama pull llama3.1:8b

# Start the FastAPI application
python app.py
