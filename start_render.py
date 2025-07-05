#!/usr/bin/env python3
"""
Render startup script for SearchPilot
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Start the SearchPilot application"""
    logger.info("Starting SearchPilot on Render...")
    
    # Check environment
    port = os.environ.get("PORT", "10000")
    groq_key = os.environ.get("GROQ_API_KEY")
    
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Port: {port}")
    logger.info(f"Groq API Key configured: {'Yes' if groq_key else 'No'}")
    
    # Check if files exist
    logger.info(f"Files in directory: {os.listdir('.')}")
    
    try:
        # Import and run the app
        logger.info("Importing app...")
        from app_railway import app
        logger.info("App imported successfully")
        
        import uvicorn
        logger.info("Starting uvicorn server...")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(port),
            log_level="info",
            access_log=True
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
