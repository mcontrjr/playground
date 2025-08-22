#!/usr/bin/env python3
"""
Personalized logger utility with colored output and dual stream configuration.
- INFO level logs go to stdout with colors
- DEBUG level logs go to <filename>.log in logs/ directory

Features:
- Smart coloring: Only colors symbols, brackets, and special characters
- Preserves natural text color for readability
- Dual output: stdout for INFO+, file for DEBUG+
- Professional terminal symbols instead of emojis
"""
import logging
import sys
import inspect
import re
from pathlib import Path
from typing import Optional

# ============================================================================
# ICONS - Terminal-style characters for professional output
# ============================================================================
ICONS = {
    # Section headers and dividers
    'header': '>>',
    'section': '::',
    'divider': '--',
    
    # Status indicators
    'success': '[OK]',
    'check': '[+]',
    'warning': '[!]',
    'error': '[X]',
    'critical': '[!!]',
    'info': '[i]',
    
    # Content types
    'config': '[CFG]',
    'database': '[DB]',
    'api': '[API]',
    'cache': '[CHE]',
    'file': '[FIL]',
    'directory': '[DIR]',
    'network': '[NET]',
    'system': '[SYS]',
    
    # Data and metrics
    'location': '[LOC]',
    'coordinate': '[XY]',
    'price': '[$]',
    'stats': '[#]',
    'time': '[T]',
    'size': '[SZ]',
    
    # Operations
    'upload': '[UP]',
    'download': '[DL]',
    'backup': '[BKP]',
    'cleanup': '[CLN]',
    'retry': '[RTY]',
    'process': '[PRC]',
    
    # Special characters
    'arrow': '->',
    'star': '*',
    'bullet': '•',
    'dash': '-',
    'pipe': '|',
    'progress': '=',
    'healthy': '+',
    'unhealthy': '-',
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    
    # Terminal symbols (better than emojis)
    SYMBOLS = {
        'DEBUG': '[DEBUG]',
        'INFO': '[+]',
        'WARNING': '[!]',
        'ERROR': '[X]',
        'CRITICAL': '[!!]',
    }
    
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self, use_colors=True):
        self.use_colors = use_colors
        super().__init__()
    
    def format(self, record):
        if self.use_colors:
            color = self.COLORS.get(record.levelname, '')
            symbol = self.SYMBOLS.get(record.levelname, '[LOG]')
            reset = self.RESET
            bold = self.BOLD
            
            # Format: [COLORED_SYMBOL] Plain_Message
            # Only the symbol gets colored, message stays in natural color
            formatted = f"{color}{bold}{symbol}{reset} {record.getMessage()}"
        else:
            symbol = self.SYMBOLS.get(record.levelname, '[LOG]')
            formatted = f"{symbol} {record.getMessage()}"
            
        return formatted


class FileFormatter(logging.Formatter):
    """Simple formatter for file output without colors."""
    
    def format(self, record):
        # Format: TIMESTAMP [LEVEL] MESSAGE
        return f"{self.formatTime(record)} [{record.levelname}] {record.getMessage()}"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name. If None, uses the calling module's filename.
    
    Returns:
        Configured logger instance
    """
    if name is None:
        # Get the calling module's filename
        frame = inspect.currentframe().f_back
        filename = Path(frame.f_code.co_filename).stem
        name = filename
    
    logger = logging.getLogger(name)
    
    # Don't add handlers if they already exist
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console handler for INFO and above (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter(use_colors=True))
    
    # File handler for DEBUG and above
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / f"{name}.log"
    
    file_handler = logging.FileHandler(log_file, mode='w')  # Overwrite each run
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(FileFormatter())
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger


def setup_logger_for_module(module_name: str) -> logging.Logger:
    """
    Setup a logger specifically for a given module name.
    
    Args:
        module_name: The module name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    # Extract just the filename from module path
    if '.' in module_name:
        name = module_name.split('.')[-1]
    else:
        name = module_name
    
    return get_logger(name)


# Convenience function for quick logger setup
def init_logger() -> logging.Logger:
    """Initialize logger for the calling module."""
    return get_logger()


def main():
    """Comprehensive demo of logger features and capabilities."""
    print("\n" + "=" * 60)
    print(f"{ICONS['header']} PERSONALIZED LOGGER DEMO")
    print("=" * 60)
    print(f"\n{ICONS['info']} Features:")
    print(f"  {ICONS['bullet']} Smart coloring: Only symbols/brackets get colored")
    print(f"  {ICONS['bullet']} Dual output: INFO+ to stdout, DEBUG+ to file")
    print(f"  {ICONS['bullet']} Professional symbols instead of emojis")
    print(f"  {ICONS['bullet']} Preserves text readability")
    
    # Initialize logger
    logger = get_logger("logger_demo")
    
    print("\n" + "-" * 40)
    print(f"{ICONS['stats']} LOG LEVELS DEMONSTRATION")
    print("-" * 40)
    
    # Test all log levels
    logger.debug("Debug info: Internal state = {active: true, threads: 3}")
    logger.info("Application started successfully")
    logger.info("Connected to database: postgresql://localhost:5432")
    logger.warning("API rate limit approaching: 85% of quota used")
    logger.error("Failed to connect to external service: timeout after 30s")
    logger.critical("System memory critically low: 2MB remaining")
    
    print("\n" + "-" * 40)
    print(f"{ICONS['config']} STRUCTURED DATA EXAMPLES")
    print("-" * 40)
    
    # Test with structured data (brackets, symbols)
    logger.info("[CONFIG] Loading configuration from config.yaml")
    logger.info("[DB] Connected to PostgreSQL on port 5432")
    logger.info("[API] Processing request: GET /api/v1/users")
    logger.info("[CACHE] Hit ratio: 87.3% (1,234 hits / 1,413 requests)")
    
    print("\n" + "-" * 40)
    print(f"{ICONS['star']} SYMBOLS & RATINGS DEMO")
    print("-" * 40)
    
    # Test with symbols and ratings
    logger.info(f"Restaurant rating: 4.8 {ICONS['star']}{ICONS['star']}{ICONS['star']}{ICONS['star']}{ICONS['star']} (127 reviews)")
    logger.info(f"Photo upload: IMG_2024.jpg {ICONS['arrow']} 1.2MB successfully saved")
    logger.info(f"Progress: [{ICONS['progress'] * 20}] 100% complete")
    logger.info(f"Status: {ICONS['healthy']} Healthy {ICONS['pipe']} {ICONS['warning']} Warning: disk 85% {ICONS['pipe']} {ICONS['unhealthy']} Error: network")
    
    print("\n" + "-" * 40)
    print(f"{ICONS['location']} LOCATION & COORDINATES")
    print("-" * 40)
    
    # Test with location data
    logger.info("[LOC] Address: 123 Main St, San Jose, CA 95110, USA")
    logger.info("[COORD] Latitude: 37.3382, Longitude: -121.8863")
    logger.info("[RADIUS] Searching within 2.5km of current location")
    
    print("\n" + "-" * 40)
    print(f"{ICONS['price']} NUMBERS & PRICING")
    print("-" * 40)
    
    # Test with various number formats
    logger.info("[PRICE] Menu item: $12.99 (was $15.99, save $3.00)")
    logger.info("[STATS] Downloads: 1,234,567 files (2.1TB total)")
    logger.info("[TIME] Process completed in 3.47 seconds")
    logger.info("[SIZE] Image dimensions: 1920x1080 pixels (2.1MB)")
    
    print("\n" + "-" * 40)
    print(f"{ICONS['error']} ERROR HANDLING EXAMPLES")
    print("-" * 40)
    
    # Test error scenarios
    logger.warning("[RETRY] Attempt 2/3 failed: Connection timeout")
    logger.error("[HTTP] 404 Not Found: /api/v1/missing-endpoint")
    logger.error("[DB] Query failed: SQLSTATE[23000] - Duplicate key")
    logger.critical("[SYSTEM] Out of memory! Available: 128KB/8GB")
    
    print("\n" + "-" * 40)
    print(f"{ICONS['file']} FILE & DIRECTORY OPERATIONS")
    print("-" * 40)
    
    # Test file operations
    logger.info("[FILE] Created: /tmp/upload_abc123.jpg (856KB)")
    logger.info("[DIR] Scanning directory: /var/log/*.log (47 files)")
    logger.info("[BACKUP] Archive created: backup_2024-08-21.tar.gz")
    logger.warning("[CLEANUP] Removed 15 temp files, freed 234MB")
    
    print("\n" + "=" * 60)
    print(f"{ICONS['success']} DEMO COMPLETE")
    print("=" * 60)
    print(f"\n{ICONS['info']} Summary:")
    print(f"  {ICONS['bullet']} Console output: Only INFO, WARNING, ERROR, CRITICAL")
    print(f"  {ICONS['bullet']} File output: ALL levels including DEBUG")
    print(f"  {ICONS['bullet']} Log file location: logs/logger_demo.log")
    print(f"  {ICONS['bullet']} Colored elements: [BRACKETS], symbols ({ICONS['star']}, {ICONS['healthy']}, {ICONS['unhealthy']}), progress bars")
    print(f"  {ICONS['bullet']} Natural text: addresses, numbers, descriptions, URLs")
    
    print(f"\n{ICONS['section']} To view all logs including DEBUG:")
    print(f"  cat logs/logger_demo.log")
    print(f"\n{ICONS['info']} Integration example:")
    print(f"  from utils.logger import get_logger")
    print(f"  logger = get_logger('my_module')")
    print(f"  logger.info('[API] Request processed successfully')")


if __name__ == "__main__":
    main()
