"""
File Utilities für OERSync-AI

Sicherheits- und Validierungsfunktionen für Dateiverarbeitung.
"""

import os
import re
import mimetypes
from pathlib import Path
from typing import Optional, Set, Tuple
import structlog

logger = structlog.get_logger()

# Erlaubte Dateierweiterungen
ALLOWED_MBZ_EXTENSIONS = {'.mbz', '.zip'}
ALLOWED_UPLOAD_EXTENSIONS = {'.mbz', '.zip', '.xml', '.json'}

# Maximale Dateigrößen (in Bytes)
MAX_MBZ_SIZE = 100 * 1024 * 1024  # 100MB
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

# Sicherheitsmuster für Dateinamen
SECURE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')
DANGEROUS_PATTERNS = [
    r'\.\.',  # Parent directory traversal
    r'[<>:"|?*]',  # Windows reserved characters
    r'[\x00-\x1f]',  # Control characters
    r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)',  # Windows reserved names
]


class FileValidationError(Exception):
    """Fehler bei der Dateivalidierung"""
    pass


def secure_filename(filename: str, max_length: int = 255) -> str:
    """
    Bereinigt einen Dateinamen für sichere Verwendung
    
    Args:
        filename: Original-Dateiname
        max_length: Maximale Länge des Dateinamens
        
    Returns:
        Bereinigter, sicherer Dateiname
        
    Raises:
        FileValidationError: Bei ungültigen Dateinamen
    """
    if not filename or not filename.strip():
        raise FileValidationError("Dateiname darf nicht leer sein")
        
    # Entferne gefährliche Zeichen
    cleaned = re.sub(r'[^\w\s.-]', '', filename)
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    
    # Prüfe auf gefährliche Muster
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            raise FileValidationError(f"Dateiname enthält gefährliche Zeichen: {filename}")
    
    # Länge beschränken
    if len(cleaned) > max_length:
        name, ext = os.path.splitext(cleaned)
        max_name_length = max_length - len(ext)
        cleaned = name[:max_name_length] + ext
        
    # Sicherstellen, dass der Name nicht leer ist
    if not cleaned or cleaned == '.':
        raise FileValidationError(f"Dateiname nach Bereinigung ungültig: {filename}")
        
    return cleaned


def validate_file_extension(filename: str, allowed_extensions: Set[str]) -> bool:
    """
    Validiert die Dateierweiterung
    
    Args:
        filename: Dateiname
        allowed_extensions: Set erlaubter Erweiterungen (mit Punkt, z.B. {'.mbz', '.zip'})
        
    Returns:
        True wenn erlaubt, False sonst
    """
    if not filename:
        return False
        
    file_ext = Path(filename).suffix.lower()
    return file_ext in allowed_extensions


def validate_file_size(file_path: Path, max_size: int) -> bool:
    """
    Validiert die Dateigröße
    
    Args:
        file_path: Pfad zur Datei
        max_size: Maximale Größe in Bytes
        
    Returns:
        True wenn Größe OK, False sonst
    """
    try:
        return file_path.stat().st_size <= max_size
    except (OSError, IOError):
        return False


def validate_mbz_file(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Umfassende Validierung einer MBZ-Datei
    
    Args:
        file_path: Pfad zur MBZ-Datei
        
    Returns:
        Tuple von (is_valid: bool, error_message: Optional[str])
    """
    try:
        # Prüfe Existenz
        if not file_path.exists():
            return False, f"Datei nicht gefunden: {file_path}"
            
        if not file_path.is_file():
            return False, f"Pfad ist keine Datei: {file_path}"
            
        # Prüfe Erweiterung
        if not validate_file_extension(str(file_path), ALLOWED_MBZ_EXTENSIONS):
            return False, f"Ungültige Dateierweiterung. Erlaubt: {', '.join(ALLOWED_MBZ_EXTENSIONS)}"
            
        # Prüfe Größe
        if not validate_file_size(file_path, MAX_MBZ_SIZE):
            actual_size = file_path.stat().st_size
            return False, f"Datei zu groß: {actual_size} bytes (max: {MAX_MBZ_SIZE} bytes)"
            
        # Prüfe MIME-Type (optional)
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type not in ['application/zip', 'application/x-zip-compressed']:
            logger.warning("Unerwarteter MIME-Type", file=str(file_path), mime_type=mime_type)
            
        return True, None
        
    except Exception as e:
        return False, f"Fehler bei Dateivalidierung: {e}"


def get_safe_upload_path(upload_dir: Path, filename: str) -> Path:
    """
    Erstellt einen sicheren Upload-Pfad
    
    Args:
        upload_dir: Upload-Verzeichnis
        filename: Original-Dateiname
        
    Returns:
        Sicherer Pfad für die Datei
        
    Raises:
        FileValidationError: Bei ungültigen Parametern
    """
    if not upload_dir.exists():
        upload_dir.mkdir(parents=True, exist_ok=True)
        
    safe_name = secure_filename(filename)
    target_path = upload_dir / safe_name
    
    # Handle duplicate filenames
    counter = 1
    original_target = target_path
    while target_path.exists():
        name, ext = os.path.splitext(safe_name)
        target_path = upload_dir / f"{name}_{counter}{ext}"
        counter += 1
        
        # Prevent infinite loop
        if counter > 1000:
            raise FileValidationError("Zu viele Dateien mit ähnlichem Namen")
            
    return target_path


def cleanup_temp_files(temp_dir: Path, max_age_hours: int = 24) -> int:
    """
    Bereinigt temporäre Dateien die älter als max_age_hours sind
    
    Args:
        temp_dir: Temporäres Verzeichnis
        max_age_hours: Maximales Alter in Stunden
        
    Returns:
        Anzahl der gelöschten Dateien
    """
    if not temp_dir.exists():
        return 0
        
    import time
    
    deleted_count = 0
    max_age_seconds = max_age_hours * 3600
    current_time = time.time()
    
    try:
        for item in temp_dir.iterdir():
            if item.is_file():
                file_age = current_time - item.stat().st_mtime
                if file_age > max_age_seconds:
                    item.unlink()
                    deleted_count += 1
                    logger.info("Temporäre Datei gelöscht", file=str(item), age_hours=file_age/3600)
            elif item.is_dir():
                # Rekursiv für Verzeichnisse
                sub_deleted = cleanup_temp_files(item, max_age_hours)
                deleted_count += sub_deleted
                
                # Lösche leere Verzeichnisse
                try:
                    if not any(item.iterdir()):
                        item.rmdir()
                        logger.info("Leeres temporäres Verzeichnis gelöscht", dir=str(item))
                except OSError:
                    pass  # Verzeichnis nicht leer oder andere Fehler ignorieren
                    
    except Exception as e:
        logger.error("Fehler beim Bereinigen temporärer Dateien", error=str(e), temp_dir=str(temp_dir))
        
    return deleted_count


def format_file_size(size_bytes: int) -> str:
    """
    Formatiert Dateigröße in menschenlesbarer Form
    
    Args:
        size_bytes: Größe in Bytes
        
    Returns:
        Formatierte Größe (z.B. "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
        
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
        
    return f"{size_bytes:.1f} {size_names[i]}"


def is_text_file(file_path: Path, sample_size: int = 1024) -> bool:
    """
    Prüft ob eine Datei eine Textdatei ist
    
    Args:
        file_path: Pfad zur Datei
        sample_size: Anzahl Bytes zum Testen
        
    Returns:
        True wenn Textdatei, False sonst
    """
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
            
        # Prüfe auf Null-Bytes (Indikator für Binärdateien)
        if b'\x00' in sample:
            return False
            
        # Versuche als UTF-8 zu dekodieren
        try:
            sample.decode('utf-8')
            return True
        except UnicodeDecodeError:
            # Versuche andere Encodings
            for encoding in ['latin1', 'cp1252']:
                try:
                    sample.decode(encoding)
                    return True
                except UnicodeDecodeError:
                    continue
                    
        return False
        
    except Exception:
        return False


# Convenience Functions

def validate_upload_file(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validierung für allgemeine Upload-Dateien
    
    Args:
        file_path: Pfad zur Datei
        
    Returns:
        Tuple von (is_valid: bool, error_message: Optional[str])
    """
    if not validate_file_extension(str(file_path), ALLOWED_UPLOAD_EXTENSIONS):
        return False, f"Ungültige Dateierweiterung. Erlaubt: {', '.join(ALLOWED_UPLOAD_EXTENSIONS)}"
        
    if not validate_file_size(file_path, MAX_UPLOAD_SIZE):
        actual_size = file_path.stat().st_size
        return False, f"Datei zu groß: {format_file_size(actual_size)} (max: {format_file_size(MAX_UPLOAD_SIZE)})"
        
    return True, None 