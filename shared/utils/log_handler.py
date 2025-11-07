"""
Custom Logging Handler zum Sammeln von Log-Nachrichten für Frontend-Ausgabe.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime


class InMemoryLogHandler(logging.Handler):
    """
    Logging Handler, der Log-Nachrichten in einer Liste sammelt.
    Kann später ausgelesen und ans Frontend gesendet werden.
    """
    
    def __init__(self, level=logging.INFO):
        super().__init__(level)
        self.logs: List[Dict[str, Any]] = []
        self.max_logs = 1000  # Verhindere Memory-Overflow
    
    def emit(self, record: logging.LogRecord):
        """Wird bei jedem Log-Aufruf aufgerufen."""
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': self.format(record),
                'module': record.module,
                'funcName': record.funcName,
                'lineno': record.lineno
            }
            
            # Füge zur Liste hinzu
            self.logs.append(log_entry)
            
            # Limitiere Anzahl (älteste entfernen)
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
                
        except Exception:
            self.handleError(record)
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Gibt alle gesammelten Logs zurück."""
        return self.logs.copy()
    
    def clear_logs(self):
        """Löscht alle gesammelten Logs."""
        self.logs.clear()
    
    def get_logs_since(self, timestamp: str) -> List[Dict[str, Any]]:
        """Gibt Logs ab einem bestimmten Zeitstempel zurück."""
        return [log for log in self.logs if log['timestamp'] > timestamp]


def create_log_handler(logger_name: str = None, level=logging.INFO) -> InMemoryLogHandler:
    """
    Erstellt und registriert einen InMemoryLogHandler.
    
    Args:
        logger_name: Name des Loggers (None = root logger)
        level: Logging-Level (default: INFO)
    
    Returns:
        Der erstellte Handler
    """
    handler = InMemoryLogHandler(level)
    
    # Format für bessere Lesbarkeit
    formatter = logging.Formatter(
        '%(levelname)s - %(name)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Handler zum Logger hinzufügen
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger()
    
    logger.addHandler(handler)
    logger.setLevel(min(logger.level, level))
    
    return handler


def get_handler_from_logger(logger_name: str = None) -> InMemoryLogHandler:
    """
    Holt einen bestehenden InMemoryLogHandler von einem Logger.
    
    Args:
        logger_name: Name des Loggers (None = root logger)
    
    Returns:
        Der Handler oder None, wenn keiner gefunden wurde
    """
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger()
    
    for handler in logger.handlers:
        if isinstance(handler, InMemoryLogHandler):
            return handler
    
    return None

