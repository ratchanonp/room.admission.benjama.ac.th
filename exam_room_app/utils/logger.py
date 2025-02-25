import logging
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
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

# Create a default logger instance
logger = setup_logger() 