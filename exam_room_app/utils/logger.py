import logging
import colorlog
import sys
from pathlib import Path

def setup_logger(log_file_name="exam_room_assignment.log"):
    """
    Set up and configure the application logger.
    
    Args:
        log_file_name: Name of the log file
        
    Returns:
        Logger: Configured logger instance
    """
    # Create the log directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_path = log_dir / log_file_name
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    
    # Color mapping for different log levels
    color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # Create handlers
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(color_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Prevent log propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger

# Create a default logger instance
logger = setup_logger() 