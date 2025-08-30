import logging
import os

def get_logger(name="municipal_ai"):
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Check if we're in a deployment environment (Render, Heroku, etc.)
        is_deployment = (
            os.getenv('RENDER') or 
            os.getenv('DYNO') or 
            os.getenv('PORT') or 
            not os.path.exists('logs')
        )
        
        if is_deployment:
            # Use console output for deployment
            handler = logging.StreamHandler()
        else:
            # Use file output for local development
            try:
                from config.settings import LOG_FILE
                # Create logs directory if it doesn't exist
                os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
                handler = logging.FileHandler(LOG_FILE)
            except (ImportError, FileNotFoundError):
                # Fallback to console if settings file or directory issues
                handler = logging.StreamHandler()
        
        # Set up formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger