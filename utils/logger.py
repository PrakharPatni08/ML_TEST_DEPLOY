import logging
import os
import sys
from datetime import datetime

def get_logger(name="municipal_ai"):
    """
    Get a configured logger instance for the Municipal AI application.
    
    Args:
        name (str): Logger name, defaults to "municipal_ai"
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Prevent adding multiple handlers to the same logger
    if not logger.handlers:
        # Check if we're in a deployment environment
        is_deployment = (
            os.getenv('RENDER') or 
            os.getenv('DYNO') or 
            os.getenv('HEROKU') or
            os.getenv('PORT') or 
            not os.path.exists('logs')
        )
        
        if is_deployment:
            # Use console output for deployment environments
            handler = logging.StreamHandler(sys.stdout)
            logger.info("🚀 Logger configured for deployment environment (console output)")
        else:
            # Use file output for local development
            try:
                from config.settings import LOG_FILE
                # Create logs directory if it doesn't exist
                log_dir = os.path.dirname(LOG_FILE)
                os.makedirs(log_dir, exist_ok=True)
                handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
                print(f"📁 Logger configured for local development (file: {LOG_FILE})")
            except (ImportError, FileNotFoundError, AttributeError):
                # Fallback to console if settings file or directory issues
                handler = logging.StreamHandler(sys.stdout)
                print("⚠️  Logger fallback to console output due to settings issues")
        
        # Set up detailed formatter for better debugging
        if is_deployment:
            # More detailed formatter for production monitoring
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s'
            )
        else:
            # Simpler formatter for local development
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Set appropriate log level based on environment
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        if is_deployment:
            # More verbose logging in production for monitoring
            logger.setLevel(getattr(logging, log_level, logging.INFO))
        else:
            # Standard logging for local development
            logger.setLevel(logging.INFO)
        
        # Prevent propagation to root logger to avoid duplicate messages
        logger.propagate = False
        
        # Log initial setup message
        logger.info(f"🔧 Logger '{name}' initialized successfully")
        logger.info(f"📊 Log level: {logger.level} | Deployment: {is_deployment}")
    
    return logger

def setup_model_logger(model_name):
    """
    Set up a specialized logger for ML models with model-specific formatting.
    
    Args:
        model_name (str): Name of the ML model (e.g., 'translator', 'classifier')
    
    Returns:
        logging.Logger: Configured model logger
    """
    logger_name = f"municipal_ai.{model_name}"
    logger = logging.getLogger(logger_name)
    
    if not logger.handlers:
        # Check deployment environment
        is_deployment = (
            os.getenv('RENDER') or 
            os.getenv('DYNO') or 
            os.getenv('PORT') or 
            not os.path.exists('logs')
        )
        
        if is_deployment:
            handler = logging.StreamHandler(sys.stdout)
        else:
            try:
                log_file = f"logs/{model_name}.log"
                os.makedirs('logs', exist_ok=True)
                handler = logging.FileHandler(log_file, encoding='utf-8')
            except:
                handler = logging.StreamHandler(sys.stdout)
        
        # Model-specific formatter
        formatter = logging.Formatter(
            f'%(asctime)s - {model_name.upper()} - %(levelname)s - %(message)s'
        )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        logger.info(f"🤖 {model_name.capitalize()} model logger initialized")
    
    return logger

def setup_database_logger():
    """
    Set up a specialized logger for database operations.
    
    Returns:
        logging.Logger: Configured database logger
    """
    return setup_model_logger('database')

def setup_processing_logger():
    """
    Set up a specialized logger for document processing operations.
    
    Returns:
        logging.Logger: Configured processing logger
    """
    return setup_model_logger('processing')

def log_system_info():
    """Log system information for debugging purposes."""
    logger = get_logger("system_info")
    
    logger.info("🖥️  System Information:")
    logger.info(f"   Python version: {sys.version}")
    logger.info(f"   Platform: {sys.platform}")
    logger.info(f"   Current working directory: {os.getcwd()}")
    
    # Log environment variables (without sensitive data)
    env_vars = ['RENDER', 'DYNO', 'PORT', 'LOG_LEVEL', 'SOURCE_DB', 'DEST_DB']
    logger.info("🔧 Environment Variables:")
    for var in env_vars:
        value = os.getenv(var, 'Not Set')
        logger.info(f"   {var}: {value}")

def log_performance(func_name, start_time, end_time, additional_info=None):
    """
    Log performance metrics for functions.
    
    Args:
        func_name (str): Name of the function being measured
        start_time (datetime): Function start time
        end_time (datetime): Function end time
        additional_info (dict): Additional information to log
    """
    logger = get_logger("performance")
    
    duration = (end_time - start_time).total_seconds()
    
    log_message = f"⏱️  {func_name} completed in {duration:.3f} seconds"
    
    if additional_info:
        for key, value in additional_info.items():
            log_message += f" | {key}: {value}"
    
    logger.info(log_message)

def log_ml_metrics(model_name, metrics):
    """
    Log ML model performance metrics.
    
    Args:
        model_name (str): Name of the ML model
        metrics (dict): Dictionary of metrics to log
    """
    logger = setup_model_logger(model_name)
    
    logger.info(f"📈 {model_name.capitalize()} Model Metrics:")
    for metric, value in metrics.items():
        if isinstance(value, float):
            logger.info(f"   {metric}: {value:.4f}")
        else:
            logger.info(f"   {metric}: {value}")

def log_processing_stats(stats):
    """
    Log document processing statistics.
    
    Args:
        stats (dict): Processing statistics
    """
    logger = setup_processing_logger()
    
    logger.info("📊 Document Processing Statistics:")
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")

def log_error_with_context(error, context=None):
    """
    Log errors with additional context information.
    
    Args:
        error (Exception): The error that occurred
        context (dict): Additional context information
    """
    logger = get_logger("error_handler")
    
    error_msg = f"❌ Error: {type(error).__name__}: {str(error)}"
    
    if context:
        error_msg += f" | Context: {context}"
    
    logger.error(error_msg)
    
    # Log stack trace for debugging
    import traceback
    logger.debug(f"Stack trace: {traceback.format_exc()}")

def create_log_rotation():
    """
    Set up log rotation for production environments (optional).
    This helps manage log file sizes in long-running applications.
    """
    try:
        from logging.handlers import RotatingFileHandler
        
        logger = logging.getLogger("municipal_ai")
        
        # Only set up rotation for file handlers in non-deployment environments
        if not (os.getenv('RENDER') or os.getenv('DYNO') or os.getenv('PORT')):
            # Remove existing handlers
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # Add rotating file handler
            log_file = "logs/app.log"
            os.makedirs('logs', exist_ok=True)
            
            # Rotate when file reaches 10MB, keep 5 backups
            rotating_handler = RotatingFileHandler(
                log_file, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
            )
            rotating_handler.setFormatter(formatter)
            
            logger.addHandler(rotating_handler)
            logger.info("🔄 Log rotation configured successfully")
    
    except ImportError:
        # Rotating handler not available, continue with regular logging
        pass

# Initialize system logging on module import
if __name__ == "__main__":
    # Test the logger configuration
    test_logger = get_logger("test")
    test_logger.info("✅ Logger test successful")
    
    # Test model logger
    model_logger = setup_model_logger("test_model")
    model_logger.info("✅ Model logger test successful")
    
    # Test performance logging
    from datetime import datetime
    start = datetime.now()
    import time
    time.sleep(0.1)  # Simulate some work
    end = datetime.now()
    log_performance("test_function", start, end, {"documents_processed": 5})
    
    # Test system info logging
    log_system_info()