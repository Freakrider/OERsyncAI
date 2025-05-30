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
    MoodleExtractedData, LearningResourceType, EducationalLevel, Language, DCMIType
)

logger = structlog.get_logger()


class XMLParsingError(Exception):
    """Fehler beim XML-Parsing"""
    pass


@dataclass
class MoodleBackupInfo:
    """Informationen aus moodle_backup.xml"""
    moodle_version: str
    backup_version: str
    backup_type: str
    backup_date: datetime
    original_course_id: int
    original_course_fullname: str
    original_course_shortname: str
    original_course_format: str
    anonymized: bool = False
    backup_unique_code: Optional[str] = None


@dataclass
class MoodleCourseInfo:
    """Informationen aus course/course.xml"""
    course_id: int
    fullname: str
    shortname: str
    category_id: int
    summary: Optional[str] = None
    format: str = "topics"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    language: str = "de"
    visible: bool = True
    guest_access: bool = False
    enrollment_keys: List[str] = None
    
    def __post_init__(self):
        if self.enrollment_keys is None:
            self.enrollment_keys = []


@dataclass
class MoodleSectionInfo:
    """Informationen zu Kurs-Abschnitten"""
    section_id: int
    section_number: int
    name: Optional[str] = None
    summary: Optional[str] = None
    visible: bool = True
    availability: Optional[Dict[str, Any]] = None
    activities: List[int] = None
    
    def __post_init__(self):
        if self.activities is None:
            self.activities = []


class XMLParser:
    """
    Sicherer XML-Parser für Moodle Backup Dateien
    
    Features:
    - XXE Attack Protection
    - Sichere XML-Validierung
    - Strukturierte Metadaten-Extraktion
    - Dublin Core Mapping
    """
    
    # XML Security Settings - ElementTree unterstützt weniger Optionen
    XML_PARSER_SETTINGS = {
        # ElementTree hat standardmäßig sicherere Defaults
    }
    
    # Mapping von Moodle Activity Types zu Learning Resource Types
    ACTIVITY_TYPE_MAPPING = {
        'assign': LearningResourceType.ASSIGNMENT,
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
        Parst eine XML-Datei sicher mit automatischer Bereinigung
        
        Args:
            xml_path: Pfad zur XML-Datei
            
        Returns:
            XML Element Tree Root
            
        Raises:
            XMLParsingError: Bei Parsing-Fehlern
        """
        if not xml_path.exists():
            raise XMLParsingError(f"XML-Datei nicht gefunden: {xml_path}")
            
        try:
            # Lese und bereinige XML-Inhalt
            with open(xml_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Entferne problematische Zeichen am Ende (wie % oder andere Artefakte)
            content = content.strip()
            
            # Entferne alles nach dem schließenden Root-Tag
            # Finde das letzte schließende Tag
            # Suche nach dem letzten schließenden Tag (z.B. </course>, </section>, etc.)
            last_closing_tag = None
            for match in re.finditer(r'</[^>]+>', content):
                last_closing_tag = match
            
            if last_closing_tag:
                # Schneide alles nach dem letzten schließenden Tag ab
                content = content[:last_closing_tag.end()]
            
            # Parse den bereinigten Inhalt
            root = etree.fromstring(content, self.parser)
            return root
            
        except etree.ParseError as e:
            # Versuche alternative Bereinigung bei Parse-Fehlern
            try:
                self.logger.warning(
                    "XML-Parse-Fehler, versuche alternative Bereinigung",
                    file=str(xml_path),
                    error=str(e)
                )
                
                # Lese Datei erneut und versuche aggressivere Bereinigung
                with open(xml_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Entferne alle Zeichen nach dem letzten >
                last_bracket = content.rfind('>')
                if last_bracket != -1:
                    content = content[:last_bracket + 1]
                
                # Entferne Null-Bytes und andere problematische Zeichen
                content = content.replace('\x00', '').replace('%', '')
                
                root = etree.fromstring(content, self.parser)
                self.logger.info("XML erfolgreich mit alternativer Bereinigung geparst", file=str(xml_path))
                return root
                
            except Exception as e2:
                raise XMLParsingError(f"XML-Syntax-Fehler in {xml_path}: {e} (auch nach Bereinigung: {e2})")
                
        except Exception as e:
            raise XMLParsingError(f"Fehler beim Parsen von {xml_path}: {e}")

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
                # Alte Struktur mit original_course_info Element
                course_id = int(self._get_text(original_course_info.find('courseid')) or '0')
                course_fullname = self._get_text(original_course_info.find('fullname')) or "Unknown Course"
                course_shortname = self._get_text(original_course_info.find('shortname')) or "unknown"
                course_format = self._get_text(original_course_info.find('format')) or "topics"
            else:
                # Neue Struktur - Kurs-Informationen direkt unter information
                course_id = int(self._get_text(information.find('original_course_id')) or '0')
                course_fullname = self._get_text(information.find('original_course_fullname')) or "Unknown Course"
                course_shortname = self._get_text(information.find('original_course_shortname')) or "unknown"
                course_format = self._get_text(information.find('original_course_format')) or "topics"
            
            # Anonymized Check
            anonymized_elem = information.find('anonymized')
            anonymized = anonymized_elem is not None and self._get_text(anonymized_elem) == '1'
            
            # Backup Unique Code
            backup_unique_code = self._get_text(information.find('backup_unique_code'))
            
            backup_info = MoodleBackupInfo(
                moodle_version=moodle_version or "unknown",
                backup_version=backup_version or "unknown", 
                backup_type=backup_type or "course",
                backup_date=backup_date or datetime.now(),
                original_course_id=course_id,
                original_course_fullname=course_fullname,
                original_course_shortname=course_shortname,
                original_course_format=course_format,
                anonymized=anonymized,
                backup_unique_code=backup_unique_code
            )
            
            self.logger.info(
                "moodle_backup.xml parsed successfully",
                course_name=course_fullname,
                moodle_version=moodle_version,
                backup_date=backup_date
            )
            
            return backup_info
            
        except Exception as e:
            raise XMLParsingError(f"Fehler beim Parsen der moodle_backup.xml: {e}")

    def parse_course_xml(self, course_xml_path: Path) -> MoodleCourseInfo:
        """
        Parst course/course.xml für detaillierte Kurs-Informationen
        
        Args:
            course_xml_path: Pfad zu course/course.xml
            
        Returns:
            MoodleCourseInfo mit extrahierten Kurs-Daten
            
        Raises:
            XMLParsingError: Bei Parsing-Fehlern
        """
        self.logger.info("Parsing course.xml", file=str(course_xml_path))
        
        root = self.parse_xml_file(course_xml_path)
        
        try:
            # Course Element ist bereits der Root
            course = root
            if course.tag != 'course':
                raise XMLParsingError(f"Erwartetes 'course' Element, gefunden: '{course.tag}'")
            
            # Basic course information - Die ID ist ein Attribut, nicht ein Sub-Element
            course_id = int(course.get('id') or '0')
            fullname = self._get_text(course.find('fullname')) or "Unknown Course"
            shortname = self._get_text(course.find('shortname')) or "unknown"
            
            # Category ID ist auch ein Attribut im category Element
            category_elem = course.find('category')
            category_id = int(category_elem.get('id') or '0') if category_elem is not None else 0
            
            summary = self._get_text(course.find('summary'))
            course_format = self._get_text(course.find('format')) or "topics"
            
            # Dates
            start_date = self._parse_timestamp(course.find('startdate'))
            end_date = self._parse_timestamp(course.find('enddate'))
            
            # Language
            language = self._get_text(course.find('lang')) or "de"
            
            # Visibility
            visible_elem = course.find('visible')
            visible = visible_elem is None or self._get_text(visible_elem) != '0'
            
            # Guest access
            guest_elem = course.find('guest')
            guest_access = guest_elem is not None and self._get_text(guest_elem) == '1'
            
            # Enrollment keys (if any)
            enrollment_keys = []
            enrol_elem = course.find('enrolments')
            if enrol_elem is not None:
                for enrol in enrol_elem.findall('.//enrol'):
                    password = self._get_text(enrol.find('password'))
                    if password:
                        enrollment_keys.append(password)
            
            course_info = MoodleCourseInfo(
                course_id=course_id,
                fullname=fullname,
                shortname=shortname,
                category_id=category_id,
                summary=summary,
                format=course_format,
                start_date=start_date,
                end_date=end_date,
                language=language,
                visible=visible,
                guest_access=guest_access,
                enrollment_keys=enrollment_keys
            )
            
            self.logger.info(
                "course.xml parsed successfully",
                course_name=fullname,
                format=course_format,
                language=language
            )
            
            return course_info
            
        except Exception as e:
            raise XMLParsingError(f"Fehler beim Parsen der course.xml: {e}")

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
        """Parst eine einzelne section.xml Datei"""
        root = self.parse_xml_file(section_xml_path)
        
        try:
            section = root.find('.//section')
            if section is None:
                raise XMLParsingError("Kein 'section' Element gefunden")
            
            section_id = int(self._get_text(section.find('id')) or '0')
            section_number = int(self._get_text(section.find('number')) or '0')
            name = self._get_text(section.find('name'))
            summary = self._get_text(section.find('summary'))
            
            # Visibility
            visible_elem = section.find('visible')
            visible = visible_elem is None or self._get_text(visible_elem) != '0'
            
            # Activities in this section
            activities = []
            sequence_elem = section.find('sequence')
            if sequence_elem is not None:
                sequence_text = self._get_text(sequence_elem)
                if sequence_text:
                    try:
                        activities = [int(x) for x in sequence_text.split(',') if x.strip()]
                    except ValueError:
                        self.logger.warning("Ungültige Activity-Sequenz", sequence=sequence_text)
            
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
        Parst eine activity/module.xml Datei
        
        Args:
            activity_xml_path: Pfad zu module.xml
            
        Returns:
            MoodleActivityMetadata Objekt
            
        Raises:
            XMLParsingError: Bei Parsing-Fehlern
        """
        self.logger.debug("Parsing activity XML", file=str(activity_xml_path))
        
        root = self.parse_xml_file(activity_xml_path)
        
        try:
            activity = root.find('.//activity')
            if activity is None:
                raise XMLParsingError("Kein 'activity' Element gefunden")
            
            # Basic activity information
            activity_id = int(self._get_text(activity.find('id')) or '0')
            module_name = self._get_text(activity.find('modulename')) or "unknown"
            section_number = int(self._get_text(activity.find('sectionnumber')) or '0')
            
            # Module specific data
            module_elem = activity.find(f'.//module')
            if module_elem is None:
                module_elem = activity
                
            name = self._get_text(module_elem.find('name')) or f"Activity {activity_id}"
            intro = self._get_text(module_elem.find('intro'))
            
            # Visibility
            visible_elem = module_elem.find('visible')
            visible = visible_elem is None or self._get_text(visible_elem) != '0'
            
            # Completion
            completion_elem = module_elem.find('completion')
            completion_enabled = completion_elem is not None and self._get_text(completion_elem) != '0'
            
            # Timestamps
            time_created = self._parse_timestamp(module_elem.find('timecreated'))
            time_modified = self._parse_timestamp(module_elem.find('timemodified'))
            
            # Bestimme Learning Resource Type
            learning_resource_type = self.ACTIVITY_TYPE_MAPPING.get(
                module_name.lower(), 
                LearningResourceType.ACTIVITY
            )
            
            # Activity-spezifische Konfiguration sammeln
            activity_config = {}
            
            # Versuche verschiedene activity-spezifische Felder zu extrahieren
            if module_name.lower() == 'quiz':
                activity_config.update(self._extract_quiz_config(module_elem))
            elif module_name.lower() == 'assign':
                activity_config.update(self._extract_assignment_config(module_elem))
            elif module_name.lower() == 'forum':
                activity_config.update(self._extract_forum_config(module_elem))
            
            return MoodleActivityMetadata(
                activity_id=activity_id,
                activity_type=learning_resource_type,
                module_name=name,
                section_number=section_number,
                visible=visible,
                completion_enabled=completion_enabled,
                time_created=time_created,
                time_modified=time_modified,
                activity_config=activity_config if activity_config else None
            )
            
        except Exception as e:
            raise XMLParsingError(f"Fehler beim Parsen der Activity: {e}")

    def _extract_quiz_config(self, module_elem: etree.Element) -> Dict[str, Any]:
        """Extrahiert Quiz-spezifische Konfiguration"""
        config = {}
        
        # Quiz settings
        time_limit = self._get_text(module_elem.find('timelimit'))
        if time_limit:
            config['time_limit_seconds'] = int(time_limit)
            
        attempts = self._get_text(module_elem.find('attempts'))
        if attempts:
            config['max_attempts'] = int(attempts)
            
        grade_method = self._get_text(module_elem.find('grademethod'))
        if grade_method:
            config['grade_method'] = grade_method
            
        return config

    def _extract_assignment_config(self, module_elem: etree.Element) -> Dict[str, Any]:
        """Extrahiert Assignment-spezifische Konfiguration"""
        config = {}
        
        # Assignment settings
        due_date = self._parse_timestamp(module_elem.find('duedate'))
        if due_date:
            config['due_date'] = due_date.isoformat()
            
        allow_submissions_from = self._parse_timestamp(module_elem.find('allowsubmissionsfromdate'))
        if allow_submissions_from:
            config['allow_submissions_from'] = allow_submissions_from.isoformat()
            
        max_attempts = self._get_text(module_elem.find('maxattempts'))
        if max_attempts:
            config['max_attempts'] = int(max_attempts)
            
        return config

    def _extract_forum_config(self, module_elem: etree.Element) -> Dict[str, Any]:
        """Extrahiert Forum-spezifische Konfiguration"""
        config = {}
        
        # Forum type
        forum_type = self._get_text(module_elem.find('type'))
        if forum_type:
            config['forum_type'] = forum_type
            
        # Max attachments
        max_attachments = self._get_text(module_elem.find('maxattachments'))
        if max_attachments:
            config['max_attachments'] = int(max_attachments)
            
        return config

    def create_dublin_core_from_course(self, course_info: MoodleCourseInfo, backup_info: MoodleBackupInfo) -> DublinCoreMetadata:
        """
        Erstellt Dublin Core Metadaten aus Moodle Kurs-Informationen
        
        Args:
            course_info: Kurs-Informationen aus course.xml
            backup_info: Backup-Informationen aus moodle_backup.xml
            
        Returns:
            DublinCoreMetadata Objekt
        """
        # Language mapping
        language_map = {
            'de': Language.DE,
            'en': Language.EN,
            'fr': Language.FR,
            'es': Language.ES,
            'it': Language.IT,
            'nl': Language.NL
        }
        
        language = language_map.get(course_info.language, Language.DE)
        
        return DublinCoreMetadata(
            title=course_info.fullname,
            description=course_info.summary,
            creator=[],  # Wird später durch LLM-Verarbeitung gefüllt
            type=DCMIType.INTERACTIVE_RESOURCE,
            language=language,
            date=backup_info.backup_date,
            identifier=f"moodle-course-{course_info.course_id}",
            format="Moodle Course Backup",
            source=f"Moodle {backup_info.moodle_version}"
        )

    def _get_text(self, element) -> Optional[str]:
        """Sicher Text aus XML Element extrahieren"""
        if element is not None and element.text:
            return element.text.strip()
        return None

    def _parse_timestamp(self, element) -> Optional[datetime]:
        """Parst einen Unix-Timestamp aus XML Element"""
        if element is not None and element.text:
            try:
                timestamp = int(element.text)
                if timestamp > 0:
                    return datetime.fromtimestamp(timestamp)
            except (ValueError, OSError):
                self.logger.warning("Ungültiger Timestamp", value=element.text)
        return None


# Convenience Functions

def parse_moodle_backup_complete(
    backup_xml_path: Path,
    course_xml_path: Optional[Path] = None,
    sections_path: Optional[Path] = None,
    activities_path: Optional[Path] = None
) -> MoodleExtractedData:
    """
    Vollständiges Parsing eines Moodle-Backups
    
    Args:
        backup_xml_path: Pfad zu moodle_backup.xml
        course_xml_path: Pfad zu course/course.xml (optional)
        sections_path: Pfad zu sections/ oder section.xml (optional)
        activities_path: Pfad zu activities/ Verzeichnis (optional)
        
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
                module_xml = activity_dir / "module.xml"
                if module_xml.exists():
                    try:
                        activity_metadata = parser.parse_activity_xml(module_xml)
                        activities_data.append(activity_metadata)
                    except XMLParsingError as e:
                        logger.warning("Fehler beim Parsen einer Activity", 
                                     activity_dir=str(activity_dir), error=str(e))
    
    # Create basic educational metadata
    educational = EducationalMetadata(
        learning_resource_type=LearningResourceType.COURSE,
        context=EducationalLevel.HIGHER_EDUCATION,  # Default assumption
        intended_end_user_role=["student", "teacher"]
    )
    
    return MoodleExtractedData(
        course_id=course_info.course_id,
        course_name=course_info.fullname,
        course_short_name=course_info.shortname,
        course_summary=course_info.summary,
        dublin_core=dublin_core,
        educational=educational,
        sections=sections_data,
        activities=activities_data,
        moodle_version=backup_info.moodle_version,
        backup_version=backup_info.backup_version
    ) 