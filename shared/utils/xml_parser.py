"""
Moodle XML Structure Parser

Sicherer Parser für Moodle Backup XML-Dateien mit
Metadaten-Extraktion und Dublin Core Mapping.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import xml.etree.ElementTree as etree
import structlog
from dataclasses import dataclass

from shared.models.dublin_core import (
    DublinCoreMetadata, EducationalMetadata, MoodleActivityMetadata,
    MoodleExtractedData, LearningResourceType, EducationalLevel, Language, DCMIType,
    FileMetadata, MediaCollection, MediaType, classify_media_type, create_media_collection_from_files
)

logger = structlog.get_logger()


class XMLParsingError(Exception):
    """Fehler beim XML-Parsing"""
    pass


@dataclass
class MoodleBackupInfo:
    """Basis-Informationen aus moodle_backup.xml"""
    original_course_id: int
    original_course_fullname: str
    original_course_shortname: str
    original_course_format: str
    moodle_version: Optional[str] = None
    backup_version: Optional[str] = None
    backup_date: Optional[datetime] = None
    backup_type: Optional[str] = None


@dataclass
class MoodleCourseInfo:
    """Kurs-Informationen aus course.xml"""
    course_id: int
    fullname: str
    shortname: str
    category_id: int
    summary: Optional[str] = None
    format: str = "topics"
    course_start_date: Optional[datetime] = None
    course_end_date: Optional[datetime] = None


@dataclass
class MoodleSectionInfo:
    """Abschnitt-Informationen aus section.xml"""
    section_id: int
    section_number: int
    name: str
    summary: Optional[str] = None
    visible: bool = True
    activities: List[int] = None

    def __post_init__(self):
        if self.activities is None:
            self.activities = []


@dataclass
class MoodleFileInfo:
    """Datei-Informationen aus files.xml"""
    file_id: str  # contenthash
    original_filename: str
    filepath: str
    mimetype: str
    filesize: int
    timecreated: Optional[datetime] = None
    timemodified: Optional[datetime] = None
    userid: Optional[int] = None
    source: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None


class XMLParser:
    """
    Sicherer XML-Parser für Moodle Backup Dateien

    Features:
    - XXE Attack Protection
    - Sichere XML-Validierung
    - Strukturierte Metadaten-Extraktion
    - Dublin Core Mapping
    - Erweiterte Medienintegration
    """

    # XML Security Settings - ElementTree unterstützt weniger Optionen
    XML_PARSER_SETTINGS = {
        # ElementTree hat standardmäßig sicherere Defaults
    }

    # Mapping von Moodle Activity Types zu Learning Resource Types
    ACTIVITY_TYPE_MAPPING = {
        'assign': LearningResourceType.ASSIGNMENT,
        'assignment': LearningResourceType.ASSIGNMENT,
        'booking': LearningResourceType.BOOKING,
        'quiz': LearningResourceType.QUIZ,
        'forum': LearningResourceType.FORUM,
        'wiki': LearningResourceType.WIKI,
        'glossary': LearningResourceType.GLOSSARY,
        'book': LearningResourceType.BOOK,
        'lesson': LearningResourceType.LESSON,
        'workshop': LearningResourceType.WORKSHOP,
        'choice': LearningResourceType.CHOICE,
        'survey': LearningResourceType.SURVEY,
        'feedback': LearningResourceType.FEEDBACK,
        'scorm': LearningResourceType.SCORM,
        'h5pactivity': LearningResourceType.H5P,
        'resource': LearningResourceType.RESOURCE,
        'url': LearningResourceType.RESOURCE,
        'page': LearningResourceType.RESOURCE,
        'folder': LearningResourceType.RESOURCE
    }

    def __init__(self):
        """Initialize XML Parser mit Sicherheitseinstellungen"""
        # ElementTree XMLParser() ohne Parameter ist bereits sicher
        self.parser = etree.XMLParser()
        self.logger = logger.bind(component="XMLParser")

    def parse_xml_file(self, xml_path: Path) -> etree.Element:
        """
        Parst eine XML-Datei sicher

        Args:
            xml_path: Pfad zur XML-Datei

        Returns:
            XML Root Element

        Raises:
            XMLParsingError: Bei Parsing-Fehlern
        """
        try:
            # Lese Dateiinhalt
            with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Bereinige beschädigte XML-Dateien
            content = self._clean_xml_content(content)

            # Parse mit ElementTree
            root = etree.fromstring(content)
            return root

        except etree.ParseError as e:
            # Versuche alternative Bereinigung
            self.logger.warning("XML-Parse-Fehler, versuche alternative Bereinigung",
                              component="XMLParser", error=str(e), file=str(xml_path))

            try:
                # Aggressivere Bereinigung
                cleaned_content = self._clean_xml_content_aggressive(content)
                root = etree.fromstring(cleaned_content)
                return root

            except etree.ParseError as e2:
                raise XMLParsingError(f"XML-Syntax-Fehler in {xml_path}: {e} (auch nach Bereinigung: {e2})")

        except Exception as e:
            raise XMLParsingError(f"Fehler beim Lesen der XML-Datei {xml_path}: {e}")

    def _clean_xml_content(self, content: str) -> str:
        """Bereinigt XML-Inhalt von häufigen Problemen"""
        # Entferne NULL-Bytes
        content = content.replace('\x00', '')

        # Entferne ungültige XML-Zeichen
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)

        # Entferne BOM falls vorhanden
        if content.startswith('\ufeff'):
            content = content[1:]

        return content.strip()

    def _clean_xml_content_aggressive(self, content: str) -> str:
        """Aggressivere XML-Bereinigung für problematische Dateien"""
        # Entferne alle nicht-printable Zeichen außer Tabs und Newlines
        content = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\xA0-\xFF]', '', content)

        # Entferne doppelte Whitespaces
        content = re.sub(r'\s+', ' ', content)

        return content.strip()

    def _safe_int_parse(self, value: Optional[str], default: int = 0) -> int:
        """Sichere Integer-Parsing mit Fallback für ungültige Werte"""
        if value is None:
            return default

        # Bereinige den Wert
        cleaned_value = value.strip()

        # Prüfe auf spezielle NULL-Werte
        if cleaned_value in ['$@NULL@$', 'NULL', 'null', '', 'None', 'none']:
            return default

        try:
            return int(cleaned_value)
        except (ValueError, TypeError):
            self.logger.warning("Konnte Wert nicht als Integer parsen", value=cleaned_value)
            return default

    def _safe_float_parse(self, value: Optional[str], default: float = 0.0) -> float:
        """Sichere Float-Parsing mit Fallback für ungültige Werte"""
        if value is None:
            return default

        # Bereinige den Wert
        cleaned_value = value.strip()

        # Prüfe auf spezielle NULL-Werte
        if cleaned_value in ['$@NULL@$', 'NULL', 'null', '', 'None', 'none']:
            return default

        try:
            return float(cleaned_value)
        except (ValueError, TypeError):
            self.logger.warning("Konnte Wert nicht als Float parsen", value=cleaned_value)
            return default

    def _get_text(self, element: Optional[etree.Element]) -> Optional[str]:
        """Sichere Text-Extraktion aus XML-Elementen"""
        if element is None:
            return None

        text = element.text
        if text is None:
            return None

        return text.strip()

    def _parse_timestamp(self, element: Optional[etree.Element]) -> Optional[datetime]:
        """Parst Timestamp aus XML-Element"""
        if element is None:
            return None

        timestamp_text = self._get_text(element)
        if not timestamp_text:
            return None

        try:
            # Versuche verschiedene Timestamp-Formate
            timestamp = self._safe_int_parse(timestamp_text)
            if timestamp == 0:
                return None
            return datetime.fromtimestamp(timestamp)
        except (ValueError, OSError):
            try:
                # Versuche ISO-Format
                return datetime.fromisoformat(timestamp_text.replace('Z', '+00:00'))
            except ValueError:
                self.logger.warning("Konnte Timestamp nicht parsen", timestamp=timestamp_text)
                return None

    def parse_moodle_backup_xml(self, backup_xml_path: Path) -> MoodleBackupInfo:
        """
        Parst moodle_backup.xml für Basis-Backup-Informationen

        Args:
            backup_xml_path: Pfad zu moodle_backup.xml

        Returns:
            MoodleBackupInfo mit extrahierten Daten

        Raises:
            XMLParsingError: Bei Parsing-Fehlern
        """
        self.logger.info("Parsing moodle_backup.xml", file=str(backup_xml_path))

        root = self.parse_xml_file(backup_xml_path)

        try:
            # Basis-Informationen extrahieren
            information = root.find('.//information')
            if information is None:
                raise XMLParsingError("Keine 'information' Sektion in moodle_backup.xml gefunden")

            # Moodle Version
            moodle_version = self._get_text(information.find('moodle_version'))
            if not moodle_version:
                moodle_version = self._get_text(information.find('original_system_info/moodle_version'))

            # Backup Version
            backup_version = self._get_text(information.find('backup_version'))

            # Backup Type
            backup_type = self._get_text(information.find('type'))

            # Backup Date
            backup_date_elem = information.find('backup_date')
            backup_date = self._parse_timestamp(backup_date_elem)

            # Original Course Information - direkt unter information
            # Versuche zuerst original_course_info (alte Struktur)
            original_course_info = information.find('original_course_info')
            if original_course_info is not None:
                # Alte Struktur
                course_id = self._safe_int_parse(self._get_text(original_course_info.find('id')))
                course_fullname = self._get_text(original_course_info.find('fullname')) or "Unbekannter Kurs"
                course_shortname = self._get_text(original_course_info.find('shortname')) or "unknown"
                course_format = self._get_text(original_course_info.find('format')) or "topics"
            else:
                # Neue Struktur - direkt unter information
                course_id = self._safe_int_parse(self._get_text(information.find('original_course_id')))
                course_fullname = self._get_text(information.find('original_course_fullname')) or "Unbekannter Kurs"
                course_shortname = self._get_text(information.find('original_course_shortname')) or "unknown"
                course_format = self._get_text(information.find('original_course_format')) or "topics"

            return MoodleBackupInfo(
                original_course_id=course_id,
                original_course_fullname=course_fullname,
                original_course_shortname=course_shortname,
                original_course_format=course_format,
                moodle_version=moodle_version,
                backup_version=backup_version,
                backup_date=backup_date,
                backup_type=backup_type
            )

        except Exception as e:
            raise XMLParsingError(f"Fehler beim Parsen von moodle_backup.xml: {e}")

    def parse_course_xml(self, course_xml_path: Path) -> MoodleCourseInfo:
        """
        Parst course/course.xml für detaillierte Kurs-Informationen

        Args:
            course_xml_path: Pfad zu course/course.xml

        Returns:
            MoodleCourseInfo mit extrahierten Daten

        Raises:
            XMLParsingError: Bei Parsing-Fehlern
        """
        self.logger.info("Parsing course.xml", file=str(course_xml_path))

        root = self.parse_xml_file(course_xml_path)

        try:
            # Suche nach course Element
            course = root if root.tag == "course" else root.find('.//course')
            if course is None:
                raise XMLParsingError("Kein 'course' Element in course.xml gefundenn")

            # Course ID
            course_id = self._safe_int_parse(course.get('id'))

            # Course name
            fullname = self._get_text(course.find('fullname')) or "Unbekannter Kurs"
            shortname = self._get_text(course.find('shortname')) or "unknown"

            # Category ID
            category_id = self._safe_int_parse(self._get_text(course.find('categoryid')))

            # Summary
            summary = self._get_text(course.find('summary'))

            # Format
            format_type = self._get_text(course.find('format')) or "topics"

            # Start and End Dates
            course_start_date = self._parse_timestamp(course.find('startdate'))
            course_end_date = self._parse_timestamp(course.find('enddate'))

            return MoodleCourseInfo(
                course_id=course_id,
                fullname=fullname,
                shortname=shortname,
                category_id=category_id,
                summary=summary,
                format=format_type,
                course_start_date=course_start_date,
                course_end_date=course_end_date
            )
        except Exception as e:
            raise XMLParsingError(f"Fehler beim Parsen von course.xml: {e}")

    def parse_files_xml(self, files_xml_path: Path) -> List[MoodleFileInfo]:
        """
        Parst files.xml für Datei-Metadaten

        Args:
            files_xml_path: Pfad zu files.xml

        Returns:
            Liste von MoodleFileInfo Objekten

        Raises:
            XMLParsingError: Bei Parsing-Fehlern
        """
        self.logger.info("Parsing files.xml", file=str(files_xml_path))

        root = self.parse_xml_file(files_xml_path)

        try:
            files = []

            # Suche nach allen file Elementen
            for file_elem in root.findall('.//file'):
                try:
                    # Basis-Informationen
                    file_id = self._get_text(file_elem.find('contenthash'))
                    if not file_id:
                        continue  # Überspringe Dateien ohne contenthash

                    original_filename = self._get_text(file_elem.find('filename')) or "unknown"
                    filepath = self._get_text(file_elem.find('filepath')) or "/"
                    mimetype = self._get_text(file_elem.find('mimetype')) or "application/octet-stream"

                    # Dateigröße
                    filesize_text = self._get_text(file_elem.find('filesize'))
                    filesize = self._safe_int_parse(filesize_text)

                    # Timestamps
                    timecreated = self._parse_timestamp(file_elem.find('timecreated'))
                    timemodified = self._parse_timestamp(file_elem.find('timemodified'))

                    # Zusätzliche Metadaten
                    userid_text = self._get_text(file_elem.find('userid'))
                    userid = self._safe_int_parse(userid_text) if userid_text else None

                    source = self._get_text(file_elem.find('source'))
                    author = self._get_text(file_elem.find('author'))
                    license = self._get_text(file_elem.find('license'))

                    file_info = MoodleFileInfo(
                        file_id=file_id,
                        original_filename=original_filename,
                        filepath=filepath,
                        mimetype=mimetype,
                        filesize=filesize,
                        timecreated=timecreated,
                        timemodified=timemodified,
                        userid=userid,
                        source=source,
                        author=author,
                        license=license
                    )

                    files.append(file_info)

                except Exception as e:
                    self.logger.warning("Fehler beim Parsen einer Datei", error=str(e))
                    continue

            self.logger.info(f"Successfully parsed {len(files)} files from files.xml")
            return files

        except Exception as e:
            raise XMLParsingError(f"Fehler beim Parsen von files.xml: {e}")

    def convert_files_to_metadata(self, files_info: List[MoodleFileInfo]) -> List[FileMetadata]:
        """
        Konvertiert MoodleFileInfo zu FileMetadata mit erweiterten Metadaten

        Args:
            files_info: Liste von MoodleFileInfo Objekten

        Returns:
            Liste von FileMetadata Objekten
        """
        file_metadata_list = []

        for file_info in files_info:
            try:
                # Bestimme Dateiendung
                file_extension = Path(file_info.original_filename).suffix.lower()

                # Klassifiziere Medientyp
                media_type = classify_media_type(file_info.mimetype, file_info.original_filename)

                # Stelle sicher, dass media_type ein MediaType Enum ist
                if not isinstance(media_type, MediaType):
                    try:
                        media_type = MediaType(str(media_type))
                    except ValueError:
                        media_type = MediaType.OTHER

                # Bestimme spezifische Eigenschaften
                is_image = bool(media_type == MediaType.IMAGE)
                is_video = bool(media_type == MediaType.VIDEO)
                is_document = bool(media_type in [MediaType.DOCUMENT, MediaType.PRESENTATION, MediaType.SPREADSHEET])
                is_audio = bool(media_type == MediaType.AUDIO)

                # Erstelle FileMetadata
                file_metadata = FileMetadata(
                    file_id=file_info.file_id,
                    original_filename=file_info.original_filename,
                    filepath=file_info.filepath,
                    mimetype=file_info.mimetype,
                    filesize=file_info.filesize,
                    timecreated=file_info.timecreated,
                    timemodified=file_info.timemodified,
                    media_type=media_type,
                    file_extension=file_extension,
                    title=file_info.original_filename,
                    description=None,  # Könnte später aus anderen Quellen gefüllt werden
                    author=file_info.author,
                    license=None,  # Könnte später aus file_info.license gemappt werden
                    is_image=is_image,
                    is_video=is_video,
                    is_document=is_document,
                    is_audio=is_audio
                )

                file_metadata_list.append(file_metadata)

            except Exception as e:
                self.logger.warning("Fehler beim Konvertieren einer Datei",
                                  file_id=file_info.file_id, error=str(e))
                continue

        return file_metadata_list

    def create_file_statistics(self, files: List[FileMetadata]) -> Dict[str, Any]:
        """
        Erstellt Statistiken über die Dateien

        Args:
            files: Liste von FileMetadata Objekten

        Returns:
            Dictionary mit Statistiken
        """
        if not files:
            return {
                "total_files": 0,
                "total_size": 0,
                "by_type": {},
                "by_extension": {},
                "largest_files": []
            }

        # Basis-Statistiken
        total_files = len(files)
        total_size = sum(f.filesize for f in files)

        # Nach Typ gruppieren
        by_type = {}
        for file_meta in files:
            # Stelle sicher, dass media_type ein Enum ist
            if hasattr(file_meta.media_type, 'value'):
                media_type = file_meta.media_type.value
            else:
                # Fallback: versuche String zu MediaType zu konvertieren
                try:
                    media_type = MediaType(str(file_meta.media_type)).value
                except (ValueError, AttributeError):
                    media_type = "other"

            if media_type not in by_type:
                by_type[media_type] = {"count": 0, "total_size": 0}
            by_type[media_type]["count"] += 1
            by_type[media_type]["total_size"] += file_meta.filesize

        # Nach Dateiendung gruppieren
        by_extension = {}
        for file_meta in files:
            ext = file_meta.file_extension
            if ext not in by_extension:
                by_extension[ext] = {"count": 0, "total_size": 0}
            by_extension[ext]["count"] += 1
            by_extension[ext]["total_size"] += file_meta.filesize

        # Größte Dateien (Top 10)
        largest_files = sorted(files, key=lambda x: x.filesize, reverse=True)[:10]
        largest_files_data = [
            {
                "file_id": f.file_id,
                "filename": f.original_filename,
                "size": f.filesize,
                "media_type": f.media_type.value if hasattr(f.media_type, 'value') else str(f.media_type)
            }
            for f in largest_files
        ]

        return {
            "total_files": total_files,
            "total_size": total_size,
            "by_type": by_type,
            "by_extension": by_extension,
            "largest_files": largest_files_data
        }

    def parse_sections_xml(self, sections_xml_path: Path) -> List[MoodleSectionInfo]:
        """
        Parst sections XML-Dateien für Kurs-Abschnitte

        Args:
            sections_xml_path: Pfad zu section.xml Datei oder Verzeichnis

        Returns:
            Liste von MoodleSectionInfo Objekten

        Raises:
            XMLParsingError: Bei Parsing-Fehlern
        """
        sections = []

        # Handle einzelne section.xml Datei
        if sections_xml_path.is_file():
            sections.append(self._parse_single_section(sections_xml_path))
            return sections

        # Handle sections/ Verzeichnis mit mehreren section.xml Dateien
        if sections_xml_path.is_dir():
            for section_file in sections_xml_path.glob("*/section.xml"):
                try:
                    section_info = self._parse_single_section(section_file)
                    sections.append(section_info)
                except XMLParsingError as e:
                    self.logger.warning("Fehler beim Parsen einer Section", file=str(section_file), error=str(e))
                    continue

        sections.sort(key=lambda s: s.section_number)
        return sections

    def _parse_single_section(self, section_xml_path: Path) -> MoodleSectionInfo:
        """Parst eine einzelne Section-XML-Datei"""
        try:
            root = self.parse_xml_file(section_xml_path)

            # Das Root-Element ist direkt <section id="...">
            section_elem = root
            if section_elem.tag != 'section':
                # Fallback: Suche nach section Element
                section_elem = root.find('.//section')
                if section_elem is None:
                    raise XMLParsingError("Kein 'section' Element gefunden")

            # Section ID
            section_id = self._safe_int_parse(section_elem.get('id'))

            # Section number
            number_elem = section_elem.find('number')
            section_number = self._safe_int_parse(self._get_text(number_elem))

            # Section name
            name_raw = self._get_text(section_elem.find('name'))
            if not name_raw or name_raw.strip() in {"", "$@NULL@$", "NULL", "null"}:
                name = "General" if section_number == 0 else "New section"
            else:
                name = name_raw.strip()

            # Section summary
            summary = self._get_text(section_elem.find('summary'))

            # Visibility
            visible_elem = section_elem.find('visible')
            visible = visible_elem is None or self._get_text(visible_elem) != '0'

            # Activity sequence
            sequence_elem = section_elem.find('sequence')
            sequence_text = self._get_text(sequence_elem) or ''
            activities = []
            if sequence_text:
                try:
                    activities = [self._safe_int_parse(x.strip()) for x in sequence_text.split(',') if x.strip()]
                except ValueError:
                    pass

            return MoodleSectionInfo(
                section_id=section_id,
                section_number=section_number,
                name=name,
                summary=summary,
                visible=visible,
                activities=activities
            )

        except Exception as e:
            raise XMLParsingError(f"Fehler beim Parsen der Section: {e}")

    def parse_activity_xml(self, activity_xml_path: Path) -> MoodleActivityMetadata:
        """
        Parst eine activity/{activity_type}.xml Datei

        Args:
            activity_xml_path: Pfad zu {activity_type}.xml

        Returns:
            MoodleActivityMetadata Objekt

        Raises:
            XMLParsingError: Bei Parsing-Fehlern
        """
        self.logger.debug("Parsing activity XML", file=str(activity_xml_path))

        root = self.parse_xml_file(activity_xml_path)

        try:
            # Bestimme Activity Type und ID aus Ordnernamen (z.B. "book_33" -> "book", 33)
            activity_folder = activity_xml_path.parent.name  # z.B. "book_33"
            activity_type = activity_folder.split('_')[0]  # z.B. "book"

            # Extrahiere Activity-ID aus Ordnernamen (z.B. "book_33" -> 33)
            try:
                activity_id = self._safe_int_parse(activity_folder.split('_')[1])  # z.B. 33
            except (IndexError, ValueError):
                # Fallback: versuche aus XML zu lesen
                activity_id = self._safe_int_parse(self._get_text(root.find('.//activity')))

            # Suche nach activity Element oder verwende Root
            activity = root.find('.//activity')
            if activity is None or not activity.attrib:
                activity = root

            # Basic activity information
            section_number = self._safe_int_parse(self._get_text(activity.find('sectionnumber')))

            # Module specific data - suche nach verschiedenen möglichen Strukturen
            module_elem = activity.find(f'.//{activity_type}')
            if module_elem is None:
                module_elem = activity.find(activity_type)  # fallback to immediate child
            if module_elem is None:
                module_elem = activity

            name_elem = module_elem.find('name') or module_elem.find('.//name') or activity.find('name') or activity.find('.//name')
            name = self._get_text(name_elem) or f"{activity_type.title()} {activity_id}"

            # Module name - verwende verschiedene Quellen
            module_name = self._get_text(activity.find('modulename')) or name or f"{activity_type.title()} {activity_id}"
            intro = self._get_text(module_elem.find('intro'))

            # Visibility
            visible_elem = module_elem.find('visible')
            visible = visible_elem is None or self._get_text(visible_elem) != '0'

            # Completion tracking
            completion_elem = module_elem.find('completion')
            completion_enabled = completion_elem is not None and self._get_text(completion_elem) == '1'

            # Grade item
            grade_item = None
            grade_elem = module_elem.find('grade_item')
            if grade_elem is not None:
                grade_item = {
                    'id': self._safe_int_parse(self._get_text(grade_elem.find('id'))),
                    'grademax': self._safe_float_parse(self._get_text(grade_elem.find('grademax'))),
                    'grademin': self._safe_float_parse(self._get_text(grade_elem.find('grademin'))),
                    'gradetype': self._get_text(grade_elem.find('gradetype'))
                }

            # Timestamps
            time_created = self._parse_timestamp(module_elem.find('timecreated'))
            time_modified = self._parse_timestamp(module_elem.find('timemodified'))

            # Bestimme Learning Resource Type
            learning_resource_type = self.ACTIVITY_TYPE_MAPPING.get(
                activity_type.lower(),
                LearningResourceType.ACTIVITY
            )
            type = learning_resource_type

            # Stelle sicher, dass es ein LearningResourceType Enum ist
            if isinstance(learning_resource_type, str):
                learning_resource_type = LearningResourceType.ACTIVITY

            # Activity-spezifische Konfiguration sammeln
            activity_config = {}

            # Versuche verschiedene activity-spezifische Felder zu extrahieren
            if activity_type.lower() == 'quiz':
                activity_config.update(self._extract_quiz_config(module_elem))
            elif activity_type.lower() == 'assign':
                activity_config.update(self._extract_assignment_config(module_elem))
            elif activity_type.lower() == 'forum':
                activity_config.update(self._extract_forum_config(module_elem))
            elif activity_type.lower() == 'page':
                activity_config.update(self._extract_page_config(module_elem))
            elif activity_type.lower() == 'book':
                activity_config.update(self._extract_book_config(module_elem))
            elif activity_type.lower() == 'resource':
                activity_config.update(self._extract_resource_config(module_elem))
            elif activity_type.lower() == 'url':
                activity_config.update(self._extract_url_config(module_elem))

            timed_data = {}
            # Look for common date-related fields
            for field in ['timeopen', 'timeclose', 'timeavailablefrom', 'timeavailableto',
                        'allowsubmissionsfromdate', 'duedate', 'cutoffdate', 'gradingduedate',
                        'deadline', 'available'
                        ]:
                elem = module_elem.find(field)
                if elem is not None:
                    ts = self._parse_timestamp(elem)
                    if ts:
                        timed_data[field] = int(ts.timestamp())

            # Optionally normalize to general 'start_date' and 'end_date'
            activity_config['start_date'] = next(
                (timed_data.get(f) for f in [
                    'timeopen', 'timeavailablefrom', 'allowsubmissionsfromdate', 'available'
                    ] if timed_data.get(f)),
                None
            )
            activity_config['end_date'] = next(
                (timed_data.get(f) for f in [
                    'timeclose', 'timeavailableto', 'duedate', 'cutoffdate', 'gradingduedate', 'deadline'
                    ] if timed_data.get(f)),
                None
            )

            # Erstelle MoodleActivityMetadata
            activity_metadata = MoodleActivityMetadata(
                activity_id=activity_id,
                activity_type=learning_resource_type,
                type=type,
                module_name=module_name,
                intro=intro,
                section_number=section_number,
                visible=visible,
                completion_enabled=completion_enabled,
                grade_item=grade_item,
                time_created=time_created,
                time_modified=time_modified,
                activity_config=activity_config
            )

            return activity_metadata

        except Exception as e:
            raise XMLParsingError(f"Fehler beim Parsen der Activity: {e}")

    def _extract_quiz_config(self, module_elem: etree.Element) -> Dict[str, Any]:
        """Extrahiert Quiz-spezifische Konfiguration"""
        config = {}

        # Quiz settings
        timeopen = self._get_text(module_elem.find('timeopen'))
        if timeopen:
            config['timeopen'] = self._safe_int_parse(timeopen)

        timeclose = self._get_text(module_elem.find('timeclose'))
        if timeclose:
            config['timeclose'] = self._safe_int_parse(timeclose)

        timelimit = self._get_text(module_elem.find('timelimit'))
        if timelimit:
            config['timelimit'] = self._safe_int_parse(timelimit)

        attempts = self._get_text(module_elem.find('attempts'))
        if attempts:
            config['attempts'] = self._safe_int_parse(attempts)

        return config

    def _extract_assignment_config(self, module_elem: etree.Element) -> Dict[str, Any]:
        """Handles both legacy 'assignment' and modern 'assign' formats."""
        config = {}

        # Legacy fields
        assignmenttype = self._get_text(module_elem.find('assignmenttype'))
        if assignmenttype:
            config['assignmenttype'] = assignmenttype

        resubmit = self._safe_int_parse(self._get_text(module_elem.find('resubmit')))
        if resubmit:
            config['resubmit'] = resubmit

        maxattempts = self._safe_int_parse(self._get_text(module_elem.find('maxattempts')))
        if maxattempts:
            config['maxattempts'] = maxattempts

        return config

    def _extract_forum_config(self, module_elem: etree.Element) -> Dict[str, Any]:
        """Extrahiert Forum-spezifische Konfiguration"""
        config = {}

        # Forum settings
        forumtype = self._get_text(module_elem.find('forumtype'))
        if forumtype:
            config['forumtype'] = forumtype

        maxattachments = self._get_text(module_elem.find('maxattachments'))
        if maxattachments:
            config['maxattachments'] = self._safe_int_parse(maxattachments)

        return config

    def _extract_page_config(self, module_elem: etree.Element) -> Dict[str, Any]:
        """Extrahiert Page-spezifische Konfiguration"""
        config = {}

        # Page content
        content = self._get_text(module_elem.find('content'))
        if content:
            config['content'] = content

        contentformat = self._get_text(module_elem.find('contentformat'))
        if contentformat:
            config['contentformat'] = self._safe_int_parse(contentformat)

        return config

    def _extract_book_config(self, module_elem: etree.Element) -> Dict[str, Any]:
        """Extrahiert Book-spezifische Konfiguration"""
        config = {}

        # Book settings
        numbering = self._get_text(module_elem.find('numbering'))
        if numbering:
            config['numbering'] = self._safe_int_parse(numbering)

        navstyle = self._get_text(module_elem.find('navstyle'))
        if navstyle:
            config['navstyle'] = self._safe_int_parse(navstyle)

        customtitles = self._get_text(module_elem.find('customtitles'))
        if customtitles:
            config['customtitles'] = self._safe_int_parse(customtitles)

        # Chapters
        chapters = []
        for chapter_elem in module_elem.findall('.//chapter'):
            chapter = {
                'id': self._safe_int_parse(self._get_text(chapter_elem.find('id'))),
                'title': self._get_text(chapter_elem.find('title')),
                'content': self._get_text(chapter_elem.find('content')),
                'pagenum': self._safe_int_parse(self._get_text(chapter_elem.find('pagenum'))),
                'subchapter': self._safe_int_parse(self._get_text(chapter_elem.find('subchapter')))
            }
            chapters.append(chapter)

        if chapters:
            config['chapters'] = chapters

        return config

    def _extract_resource_config(self, module_elem: etree.Element) -> Dict[str, Any]:
        """Extrahiert Resource-spezifische Konfiguration"""
        config = {}

        # Resource settings
        reference = self._get_text(module_elem.find('reference'))
        if reference:
            config['reference'] = reference

        filterfiles = self._get_text(module_elem.find('filterfiles'))
        if filterfiles:
            config['filterfiles'] = self._safe_int_parse(filterfiles)

        return config

    def _extract_url_config(self, module_elem: etree.Element) -> Dict[str, Any]:
        """Extrahiert URL-spezifische Konfiguration"""
        config = {}

        # URL settings
        externalurl = self._get_text(module_elem.find('externalurl'))
        if externalurl:
            config['externalurl'] = externalurl

        display = self._get_text(module_elem.find('display'))
        if display:
            config['display'] = self._safe_int_parse(display)

        return config

    def create_dublin_core_from_course(self, course_info: MoodleCourseInfo, backup_info: MoodleBackupInfo) -> DublinCoreMetadata:
        """
        Erstellt Dublin Core Metadaten aus Kurs-Informationen

        Args:
            course_info: MoodleCourseInfo Objekt
            backup_info: MoodleBackupInfo Objekt

        Returns:
            DublinCoreMetadata Objekt
        """
        # Verwende course_info falls verfügbar, sonst backup_info
        title = course_info.fullname if course_info else backup_info.original_course_fullname
        description = course_info.summary if course_info else None
        creator = []  # Könnte später aus anderen Quellen gefüllt werden

        return DublinCoreMetadata(
            title=title,
            description=description,
            creator=creator,
            type=DCMIType.TEXT,
            language=Language.DE,
            date=backup_info.backup_date,
            format="Moodle Course Backup"
        )

    def build_pluginfile_mapping(self, files_info: List[MoodleFileInfo]) -> Dict[str, str]:
        """
        Build a mapping from original pluginfile path to contenthash-based file path.
        Returns:
            Dict where key = plugin path (e.g. 'Bildschirmfoto 2025-09-10 um 07.55.53.png')
                and value = contenthash (or final path)
        """
        mapping = {}

        for f in files_info:
            if f.filepath == '/' and f.original_filename != '.':  # skip directories
                key = f.original_filename.strip()
                mapping[key] = f.file_id  # contenthash

        return mapping

# Convenience Functions
def parse_moodle_backup_complete(
    backup_xml_path: Path,
    course_xml_path: Optional[Path] = None,
    sections_path: Optional[Path] = None,
    activities_path: Optional[Path] = None,
    files_xml_path: Optional[Path] = None,
    job_id: Optional[str] = None
) -> MoodleExtractedData:
    """
    Vollständiges Parsing eines Moodle-Backups mit erweiterter Medienintegration

    Args:
        backup_xml_path: Pfad zu moodle_backup.xml
        course_xml_path: Pfad zu course/course.xml (optional)
        sections_path: Pfad zu sections/ oder section.xml (optional)
        activities_path: Pfad zu activities/ Verzeichnis (optional)
        files_xml_path: Pfad zu files.xml (optional)

    Returns:
        MoodleExtractedData mit vollständigen Informationen

    Raises:
        XMLParsingError: Bei Parsing-Fehlern
    """
    parser = XMLParser()

    # Parse backup info (required)
    backup_info = parser.parse_moodle_backup_xml(backup_xml_path)

    # Parse course info (optional)
    course_info = None
    if course_xml_path and course_xml_path.exists():
        course_info = parser.parse_course_xml(course_xml_path)

    # Use backup info if course info not available
    if course_info is None:
        course_info = MoodleCourseInfo(
            course_id=backup_info.original_course_id,
            fullname=backup_info.original_course_fullname,
            shortname=backup_info.original_course_shortname,
            category_id=0,
            summary=None,
            format=backup_info.original_course_format
        )

    # Create Dublin Core metadata
    dublin_core = parser.create_dublin_core_from_course(course_info, backup_info)

    # Parse sections (optional)
    sections_data = []
    if sections_path and sections_path.exists():
        try:
            sections_info = parser.parse_sections_xml(sections_path)
            for section in sections_info:
                sections_data.append({
                    'id': section.section_id,
                    'number': section.section_number,
                    'name': section.name,
                    'summary': section.summary,
                    'visible': section.visible,
                    'activities': section.activities
                })
        except XMLParsingError as e:
            logger.warning("Fehler beim Parsen der Sections", error=str(e))

    # Parse activities (optional)
    activities_data = []
    if activities_path and activities_path.exists() and activities_path.is_dir():
        for activity_dir in activities_path.iterdir():
            if activity_dir.is_dir():
                # Parse activity type from folder name (e.g., "page_34" -> "page")
                activity_type = activity_dir.name.split('_')[0]
                activity_xml = activity_dir / f"{activity_type}.xml"
                if activity_xml.exists():
                    try:
                        activity_metadata = parser.parse_activity_xml(activity_xml)
                        activities_data.append(activity_metadata)
                    except XMLParsingError as e:
                        logger.warning("Fehler beim Parsen einer Activity",
                                     activity_dir=str(activity_dir), error=str(e))

    # Link activities to sections
    assign_section_numbers_to_activities(activities_data, sections_data)

    # Reorder activities based on section order and sequence
    activities_data = order_activities_by_sections(activities_data, sections_data)

    # Parse files (optional) - NEUE FUNKTIONALITÄT
    files_data = []
    media_collections = []
    file_statistics = {}

    if files_xml_path and files_xml_path.exists():
        try:
            # Parse files.xml
            files_info = parser.parse_files_xml(files_xml_path)
            # Konvertiere zu FileMetadata
            files_data = parser.convert_files_to_metadata(files_info)
            plugin_map = parser.build_pluginfile_mapping(files_info)

            # Replace inside all intros (example for activities)
            for activity in activities_data:
                if activity.intro:
                    activity.intro = replace_pluginfile_urls(activity.intro, plugin_map, export_base_path="/media")

            # Erstelle Statistiken
            file_statistics = parser.create_file_statistics(files_data)

            # Erstelle MediaCollections
            if files_data:
                # Hauptsammlung für den gesamten Kurs
                main_collection = create_media_collection_from_files(
                    files_data,
                    f"course_{course_info.course_id}_media",
                    f"Medien für {course_info.fullname}"
                )
                main_collection.course_id = course_info.course_id
                media_collections.append(main_collection)

                # Separate Sammlungen nach Medientyp
                for media_type in MediaType:
                    type_files = [f for f in files_data if f.media_type == media_type]
                    if type_files:
                        # Stelle sicher, dass media_type.value existiert
                        media_type_str = media_type.value if hasattr(media_type, 'value') else str(media_type)
                        type_collection = create_media_collection_from_files(
                            type_files,
                            f"course_{course_info.course_id}_{media_type_str}",
                            f"{media_type_str.title()} Dateien"
                        )
                        type_collection.course_id = course_info.course_id
                        media_collections.append(type_collection)

            logger.info(f"Successfully parsed {len(files_data)} files with media integration")

        except XMLParsingError as e:
            logger.warning("Fehler beim Parsen der Dateien", error=str(e))

    # Create basic educational metadata
    educational = EducationalMetadata(
        learning_resource_type=LearningResourceType.COURSE,
        context=EducationalLevel.HIGHER_EDUCATION,  # Default assumption
        intended_end_user_role=["student", "teacher"]
    )

    # Create complete extracted data
    extracted_data = MoodleExtractedData(
        course_id=course_info.course_id,
        course_name=course_info.fullname,
        course_short_name=course_info.shortname,
        course_summary=course_info.summary,
        course_start_date=course_info.course_start_date,
        course_end_date=course_info.course_end_date,
        course_language="de",  # Default
        course_format=course_info.format,
        course_visible=True,  # Default
        dublin_core=dublin_core,
        educational=educational,
        sections=sections_data,
        activities=activities_data,
        files=files_data,
        media_collections=media_collections,
        file_statistics=file_statistics,
        backup_date=backup_info.backup_date,
        moodle_version=backup_info.moodle_version,
        backup_version=backup_info.backup_version,
        extraction_timestamp=datetime.now()
    )

    if job_id:
        for activity in activities_data:
            if activity.intro and "/media/" in activity.intro:
                activity.intro = activity.intro.replace(
                    "/media/",
                    f"/media/{job_id}/"
                )

    return extracted_data

def replace_pluginfile_urls(html: str, file_map: Dict[str, str], export_base_path: str = "/media") -> str:
    """
    Replace @@PLUGINFILE@@ paths with resolved URLs or file paths.
    Args:
        html: Original HTML (e.g. intro field)
        file_map: filename → contenthash map
        export_base_path: where files will be copied or served from
    Returns:
        HTML with fixed <img src="/media/..."> paths
    """
    def replacer(match):
        from urllib.parse import unquote
        filename = unquote(match.group(1))
        contenthash = file_map.get(filename)
        if not contenthash:
            return match.group(0)  # fallback to original

        # Construct relative path (could also serve as URL)
        relative_path = f"{export_base_path}/{contenthash[:2]}/{contenthash}/{filename}"
        return f'src="{relative_path}"'

    # Regex to find @@PLUGINFILE@@/filename
    return re.sub(r'src="@@PLUGINFILE@@/([^"]+)"', replacer, html)

def assign_section_numbers_to_activities(
    activities_data: List[MoodleActivityMetadata],
    sections_data: List[Dict[str, Any]]
) -> None:
    """Links activities to their corresponding section numbers by updating activity.section_number"""
    activity_id_to_section = {
        activity_id: section['number']
        for section in sections_data
        for activity_id in section.get('activities', [])
    }

    for activity in activities_data:
        if hasattr(activity, "activity_id") and activity.activity_id in activity_id_to_section:
            activity.section_number = activity_id_to_section[activity.activity_id]

def order_activities_by_sections(
    activities_data: List[MoodleActivityMetadata],
    sections_data: List[Dict[str, Any]]
) -> List[MoodleActivityMetadata]:
    """Orders activities based on section number and activity sequence in each section."""
    activity_lookup = {a.activity_id: a for a in activities_data}
    ordered_activities = []

    for section in sorted(sections_data, key=lambda s: s["number"]):
        for activity_id in section.get("activities", []):
            activity = activity_lookup.get(activity_id)
            if activity:
                ordered_activities.append(activity)

    # Add any activities not assigned to sections
    remaining_activities = [a for a in activities_data if a not in ordered_activities]
    ordered_activities.extend(remaining_activities)

    return ordered_activities