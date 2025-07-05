FROM python:3.9-slim

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8000

# Start script that runs Ollama and the app
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
