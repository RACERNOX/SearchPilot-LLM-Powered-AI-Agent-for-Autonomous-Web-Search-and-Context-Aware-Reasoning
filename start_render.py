#!/usr/bin/env python3
"""
Render startup script for SearchPilot
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Start the SearchPilot application"""
    logger.info("Starting SearchPilot on Render...")
    
    # Check environment
    port = os.environ.get("PORT", "10000")
    groq_key = os.environ.get("GROQ_API_KEY")
    
    logger.info(f"Port: {port}")
    logger.info(f"Groq API Key configured: {'Yes' if groq_key else 'No'}")
    
    # Import and run the app
    from app_railway import app
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(port),
        log_level="info"
    )

if __name__ == "__main__":
    main()
