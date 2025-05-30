"""
MBZ (Moodle Backup) File Extractor

Sicherer Extraktor für Moodle Backup Dateien (.mbz) mit
Validierung, Entpackung und Metadaten-Extraktion.
Unterstützt sowohl ZIP- als auch TAR.GZ-Formate.
"""

import os
import tempfile
import zipfile
import tarfile
import gzip
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()


class MBZExtractionError(Exception):
    """Fehler bei der MBZ-Extraktion"""
    pass


@dataclass
class MBZExtractionResult:
    """Ergebnis der MBZ-Extraktion"""
    temp_dir: Path
    moodle_backup_xml: Optional[Path] = None
    files_xml: Optional[Path] = None
    course_xml: Optional[Path] = None
    sections_xml: List[Path] = None
    activities: List[Path] = None
    files_dir: Optional[Path] = None
    extraction_time: datetime = None
    moodle_version: Optional[str] = None
    backup_version: Optional[str] = None
    archive_type: str = "unknown"
    
    def __post_init__(self):
        if self.activities is None:
            self.activities = []
        if self.sections_xml is None:
            self.sections_xml = []
        if self.extraction_time is None:
            self.extraction_time = datetime.now()


class MBZExtractor:
    """
    Sicherer Extraktor für Moodle Backup Dateien
    
    Features:
    - ZIP und TAR.GZ Format Unterstützung
    - ZIP-Bomb Protection
    - Pfad-Traversal Protection  
    - Große Datei Protection
    - Automatische XML-Datei Identifikation
    - Temporäre Verzeichnis-Verwaltung
    """
    
    # Sicherheitslimits
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_TOTAL_SIZE = 500 * 1024 * 1024  # 500MB
    MAX_FILES = 10000
    ALLOWED_EXTENSIONS = {'.xml', '.txt', '.html', '.json', '.csv', '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.doc', '.docx'}
    
    # Wichtige Moodle Backup Dateien
    CRITICAL_FILES = {
        'moodle_backup.xml',
        'course/course.xml',
        'files.xml'
    }
    
    ACTIVITY_PATTERNS = [
        'activities/*/module.xml',
        'activities/*/inforef.xml',
        'sections/section_*/section.xml'
    ]

    def __init__(self, temp_dir: Optional[Path] = None):
        """
        Initialize MBZ Extractor
        
        Args:
            temp_dir: Optionales temporäres Verzeichnis. Falls None, wird automatisch erstellt.
        """
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp(prefix="mbz_extract_"))
        self.logger = logger.bind(temp_dir=str(self.temp_dir))
        
    def detect_archive_type(self, mbz_path: Path) -> str:
        """
        Erkennt den Archiv-Typ einer MBZ-Datei
        
        Args:
            mbz_path: Pfad zur MBZ-Datei
            
        Returns:
            'zip', 'tar.gz', oder 'unknown'
        """
        try:
            # Prüfe auf ZIP
            with zipfile.ZipFile(mbz_path, 'r') as zip_file:
                zip_file.testzip()
                return 'zip'
        except zipfile.BadZipFile:
            pass
        
        try:
            # Prüfe auf TAR.GZ
            with tarfile.open(mbz_path, 'r:gz') as tar_file:
                # Teste ob es ein gültiges TAR ist
                tar_file.getmembers()
                return 'tar.gz'
        except (tarfile.TarError, OSError):
            pass
        
        try:
            # Prüfe auf GZIP-komprimiertes TAR (alternative Methode)
            with gzip.open(mbz_path, 'rb') as gz_file:
                # Lese erste Bytes um TAR-Header zu prüfen
                header = gz_file.read(262)
                if len(header) >= 262:
                    # TAR-Header checken (ustar signature at offset 257)
                    if header[257:262] == b'ustar':
                        return 'tar.gz'
        except (OSError, gzip.BadGzipFile):
            pass
        
        return 'unknown'
        
    def validate_mbz_file(self, mbz_path: Path) -> bool:
        """
        Validiert eine MBZ-Datei vor der Extraktion
        
        Args:
            mbz_path: Pfad zur MBZ-Datei
            
        Returns:
            True wenn gültig, sonst False
            
        Raises:
            MBZExtractionError: Bei Validierungsfehlern
        """
        if not mbz_path.exists():
            raise MBZExtractionError(f"MBZ-Datei nicht gefunden: {mbz_path}")
            
        if not mbz_path.is_file():
            raise MBZExtractionError(f"Pfad ist keine Datei: {mbz_path}")
            
        if mbz_path.stat().st_size > self.MAX_FILE_SIZE:
            raise MBZExtractionError(f"MBZ-Datei zu groß: {mbz_path.stat().st_size} bytes")
        
        # Erkenne Archiv-Typ
        archive_type = self.detect_archive_type(mbz_path)
        
        if archive_type == 'zip':
            return self._validate_zip_file(mbz_path)
        elif archive_type == 'tar.gz':
            return self._validate_tar_gz_file(mbz_path)
        else:
            raise MBZExtractionError(f"Unbekanntes Archiv-Format: {mbz_path}")
    
    def _validate_zip_file(self, mbz_path: Path) -> bool:
        """Validiert ZIP-Datei"""
        try:
            with zipfile.ZipFile(mbz_path, 'r') as zip_file:
                # Teste ZIP-Integrität
                bad_file = zip_file.testzip()
                if bad_file:
                    raise MBZExtractionError(f"Korrupte ZIP-Datei, defekte Datei: {bad_file}")
                    
                # Prüfe auf wichtige Backup-Dateien
                file_list = zip_file.namelist()
                if 'moodle_backup.xml' not in file_list:
                    raise MBZExtractionError("Keine gültige Moodle-Backup-Datei (moodle_backup.xml fehlt)")
                    
        except zipfile.BadZipFile:
            raise MBZExtractionError(f"Keine gültige ZIP-Datei: {mbz_path}")
            
        return True
    
    def _validate_tar_gz_file(self, mbz_path: Path) -> bool:
        """Validiert TAR.GZ-Datei"""
        try:
            with tarfile.open(mbz_path, 'r:gz') as tar_file:
                # Teste TAR-Integrität
                member_names = tar_file.getnames()
                
                # Prüfe auf wichtige Backup-Dateien
                if 'moodle_backup.xml' not in member_names:
                    raise MBZExtractionError("Keine gültige Moodle-Backup-Datei (moodle_backup.xml fehlt)")
                    
        except (tarfile.TarError, gzip.BadGzipFile):
            raise MBZExtractionError(f"Keine gültige TAR.GZ-Datei: {mbz_path}")
            
        return True
        
    def _secure_extract_member(self, zip_file: zipfile.ZipFile, member: zipfile.ZipInfo, extract_to: Path) -> Path:
        """
        Sicherer Extraktor für einzelne ZIP-Member mit Pfad-Traversal-Schutz
        
        Args:
            zip_file: ZipFile Objekt
            member: ZipInfo des zu extrahierenden Members
            extract_to: Zielverzeichnis
            
        Returns:
            Pfad zur extrahierten Datei
            
        Raises:
            MBZExtractionError: Bei Sicherheitsverletzungen
        """
        # Pfad-Traversal-Schutz
        if os.path.isabs(member.filename) or ".." in member.filename:
            raise MBZExtractionError(f"Unsicherer Dateipfad: {member.filename}")
            
        # Dateiendung prüfen
        file_ext = Path(member.filename).suffix.lower()
        if file_ext and file_ext not in self.ALLOWED_EXTENSIONS:
            self.logger.warning("Überspringe Datei mit nicht erlaubter Endung", filename=member.filename, extension=file_ext)
            return None
            
        # Extrahiere Datei
        target_path = extract_to / member.filename
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        with zip_file.open(member) as source, open(target_path, 'wb') as target:
            shutil.copyfileobj(source, target)
            
        return target_path

    def _secure_extract_tar_member(self, tar_file: tarfile.TarFile, member: tarfile.TarInfo, extract_to: Path) -> Optional[Path]:
        """
        Sicherer Extraktor für einzelne TAR-Member mit Pfad-Traversal-Schutz
        
        Args:
            tar_file: TarFile Objekt
            member: TarInfo des zu extrahierenden Members
            extract_to: Zielverzeichnis
            
        Returns:
            Pfad zur extrahierten Datei oder None wenn übersprungen
            
        Raises:
            MBZExtractionError: Bei Sicherheitsverletzungen
        """
        # Überspringe Verzeichnisse
        if member.isdir():
            return None
        
        # Pfad-Traversal-Schutz
        if os.path.isabs(member.name) or ".." in member.name:
            raise MBZExtractionError(f"Unsicherer Dateipfad: {member.name}")
            
        # Dateiendung prüfen
        file_ext = Path(member.name).suffix.lower()
        if file_ext and file_ext not in self.ALLOWED_EXTENSIONS:
            self.logger.warning("Überspringe Datei mit nicht erlaubter Endung", filename=member.name, extension=file_ext)
            return None
            
        # Extrahiere Datei
        target_path = extract_to / member.name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Extrahiere mit sicherer Methode
        try:
            with tar_file.extractfile(member) as source:
                if source:
                    with open(target_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    return target_path
        except Exception as e:
            self.logger.warning("Fehler beim Extrahieren der TAR-Datei", filename=member.name, error=str(e))
            
        return None
        
    def extract_mbz(self, mbz_path: Path) -> MBZExtractionResult:
        """
        Extrahiert eine MBZ-Datei sicher in ein temporäres Verzeichnis
        
        Args:
            mbz_path: Pfad zur MBZ-Datei
            
        Returns:
            MBZExtractionResult mit Pfaden zu wichtigen Dateien
            
        Raises:
            MBZExtractionError: Bei Extraktionsfehlern
        """
        start_time = datetime.now()
        self.logger.info("Beginne MBZ-Extraktion", mbz_file=str(mbz_path))
        
        # Validierung
        self.validate_mbz_file(mbz_path)
        
        # Erkenne Archiv-Typ
        archive_type = self.detect_archive_type(mbz_path)
        
        # Erstelle Extraktionsverzeichnis
        extract_dir = self.temp_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        result = MBZExtractionResult(
            temp_dir=self.temp_dir,
            extraction_time=start_time,
            archive_type=archive_type
        )
        
        try:
            if archive_type == 'zip':
                with zipfile.ZipFile(mbz_path, 'r') as zip_file:
                    file_list = zip_file.namelist()
                    total_size = 0
                    file_count = 0
                    
                    # Sicherheitsprüfungen für ZIP-Bombing
                    for member in zip_file.infolist():
                        total_size += member.file_size
                        file_count += 1
                        
                        if total_size > self.MAX_TOTAL_SIZE:
                            raise MBZExtractionError(f"ZIP-Datei zu groß nach Entpackung: {total_size} bytes")
                        if file_count > self.MAX_FILES:
                            raise MBZExtractionError(f"Zu viele Dateien im ZIP: {file_count}")
                    
                    # Extrahiere alle Dateien sicher
                    for member in zip_file.infolist():
                        if member.is_dir():
                            continue
                            
                        extracted_path = self._secure_extract_member(zip_file, member, extract_dir)
                        if extracted_path is None:
                            continue
                            
                        # Identifiziere wichtige Dateien
                        rel_path = extracted_path.relative_to(extract_dir)
                        self._identify_important_files(rel_path, extracted_path, result)
                        
            elif archive_type == 'tar.gz':
                with tarfile.open(mbz_path, 'r:gz') as tar_file:
                    for member in tar_file.getmembers():
                        extracted_path = self._secure_extract_tar_member(tar_file, member, extract_dir)
                        if extracted_path:
                            # Identifiziere wichtige Dateien
                            rel_path = extracted_path.relative_to(extract_dir)
                            self._identify_important_files(rel_path, extracted_path, result)
            
        except Exception as e:
            raise MBZExtractionError(f"Unerwarteter Fehler bei Extraktion: {e}")
            
        # Validiere Extraktionsergebnis
        self._validate_extraction_result(result)
        
        extraction_time = datetime.now() - start_time
        self.logger.info(
            "MBZ-Extraktion abgeschlossen", 
            extraction_time=extraction_time.total_seconds(),
            files_found=len(result.activities),
            has_backup_xml=result.moodle_backup_xml is not None
        )
        
        return result
        
    def _identify_important_files(self, rel_path: Path, full_path: Path, result: MBZExtractionResult):
        """Identifiziert und kategorisiert wichtige Backup-Dateien"""
        path_str = str(rel_path).replace('\\', '/')
        
        # Hauptdateien
        if path_str == 'moodle_backup.xml':
            result.moodle_backup_xml = full_path
        elif path_str == 'files.xml':
            result.files_xml = full_path
        elif path_str == 'course/course.xml':
            result.course_xml = full_path
            
        # Aktivitäten
        elif path_str.startswith('activities/') and path_str.endswith('/module.xml'):
            result.activities.append(full_path)
            
        # Abschnitte
        elif path_str.startswith('sections/') and path_str.endswith('/section.xml'):
            result.sections_xml.append(full_path)
            
        # Files-Verzeichnis
        elif path_str.startswith('files/'):
            if result.files_dir is None:
                result.files_dir = full_path.parent
                
    def _validate_extraction_result(self, result: MBZExtractionResult):
        """Validiert das Extraktionsergebnis"""
        if result.moodle_backup_xml is None:
            raise MBZExtractionError("Kritische Datei fehlt: moodle_backup.xml")
            
        # Optional: Weitere Validierungen
        # if result.course_xml is None:
        #     self.logger.warning("course.xml nicht gefunden")
            
    def cleanup(self):
        """Räumt temporäre Dateien auf"""
        if self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                self.logger.info("Temporäres Verzeichnis bereinigt", temp_dir=str(self.temp_dir))
            except Exception as e:
                self.logger.error("Fehler beim Bereinigen", temp_dir=str(self.temp_dir), error=str(e))
                
    def __enter__(self):
        """Context Manager Entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Exit - Automatische Bereinigung"""
        self.cleanup()


# Convenience Functions

def extract_mbz_file(mbz_path: Path, temp_dir: Optional[Path] = None) -> MBZExtractionResult:
    """
    Convenience-Funktion für einmalige MBZ-Extraktion
    
    Args:
        mbz_path: Pfad zur MBZ-Datei
        temp_dir: Optionales temporäres Verzeichnis
        
    Returns:
        MBZExtractionResult
        
    Note:
        Bereinigung muss manuell mit result.cleanup() erfolgen
    """
    extractor = MBZExtractor(temp_dir)
    return extractor.extract_mbz(mbz_path)


def extract_mbz_safe(mbz_path: Path) -> Tuple[MBZExtractionResult, Exception]:
    """
    Sichere MBZ-Extraktion mit automatischer Bereinigung
    
    Args:
        mbz_path: Pfad zur MBZ-Datei
        
    Returns:
        Tuple von (Result oder None, Exception oder None)
    """
    try:
        with MBZExtractor() as extractor:
            result = extractor.extract_mbz(mbz_path)
            return result, None
    except Exception as e:
        return None, e 