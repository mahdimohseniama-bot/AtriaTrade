import logging
import sys
from pathlib import Path

class AtriaLogger:
    def __init__(self, name: str = "AtriaTrade", log_file: str = "logs/atria_trade.log"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            # Create logs directory if not exists
            Path("logs").mkdir(exist_ok=True)
            
            # File Handler
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            
            # Console Handler
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

    def get_logger(self):
        return self.logger

# Global logger instance for quick access
logger = AtriaLogger().get_logger()
