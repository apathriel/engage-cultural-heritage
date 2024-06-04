import logging
from pathlib import Path

def get_logger(name: str, level: str = 'INFO', log_to_file: bool = False, log_file: str = 'logfile.log') -> logging.Logger:
    """
    Creates and configures a logger with the specified name.

    Parameters:
        name (str): The name of the logger. Convention is to use __name__.
        level (str): The logging level. Default is 'INFO'.
        log_to_file (bool): If True, logs are saved to a file. Otherwise, logs are output to the console.
        log_file (str): The name of the log file. Only used if log_to_file is True.

    Returns:
        logging.Logger: The configured logger object.
    """
    name = name.upper()
    logger = logging.getLogger(name)

    levels = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
    }

    logger.setLevel(levels.get(level.upper(), logging.INFO))

    if log_to_file:
        log_dir = Path('logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / log_file)
    else:
        handler = logging.StreamHandler()

    handler.setFormatter(
        logging.Formatter("[%(levelname)s] - [%(name)s] - %(asctime)s - %(message)s")
    )
    logger.addHandler(handler)
    return logger