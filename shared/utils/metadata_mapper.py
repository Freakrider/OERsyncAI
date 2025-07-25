"""
Metadata Mapper für OERSync-AI

Intelligente Mapping-Engine die Moodle-Metadaten auf Dublin Core Schema überträgt.
Beinhaltet Fallback-Strategien, Validierung und erweiterte Metadaten-Anreicherung.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import re
from enum import Enum

from shared.models.dublin_core import (
    DublinCoreMetadata, EducationalMetadata, MoodleExtractedData,
    DCMIType, LearningResourceType, EducationalLevel, Language, LicenseType
)
from shared.utils.xml_parser import MoodleBackupInfo, MoodleCourseInfo, MoodleSectionInfo
import structlog

logger = structlog.get_logger(__name__)


class MoodleLanguageMapper:
    """Mapping von Moodle-Sprachcodes zu ISO 639-1 Codes"""
    
    LANGUAGE_MAPPING = {
        # Moodle language codes to ISO 639-1
        'de': Language.DE,
        'en': Language.EN,
        'en_us': Language.EN,
        'en_gb': Language.EN,
        'fr': Language.FR,
        'es': Language.ES,
        'it': Language.IT,
        'nl': Language.NL,
        # Fallbacks
        'german': Language.DE,
        'english': Language.EN,
        'french': Language.FR,
        'spanish': Language.ES,
        'italian': Language.IT,
        'dutch': Language.NL,
    }
    
    @classmethod
    def map_language(cls, moodle_lang: Optional[str]) -> Language:
        """Mappe Moodle-Sprachcode zu ISO 639-1 Language Enum"""
        if not moodle_lang:
            return Language.DE  # Default
        
        # Normalisiere zu lowercase
        normalized = moodle_lang.lower().strip()
        
        # Direkte Mappings
        if normalized in cls.LANGUAGE_MAPPING:
            return cls.LANGUAGE_MAPPING[normalized]
        
        # Partieller Match für zusammengesetzte Codes
        for code, lang in cls.LANGUAGE_MAPPING.items():
            if normalized.startswith(code):
                return lang
        
        logger.warning("Unbekannter Sprachcode, verwende Default", moodle_lang=moodle_lang)
        return Language.DE


class MoodleActivityTypeMapper:
    """Mapping von Moodle-Aktivitätstypen zu Learning Resource Types"""
    
    ACTIVITY_TYPE_MAPPING = {
        # Content-based activities
        'page': LearningResourceType.RESOURCE,
        'url': LearningResourceType.RESOURCE,
        'file': LearningResourceType.RESOURCE,
        'folder': LearningResourceType.RESOURCE,
        'book': LearningResourceType.BOOK,
        'lesson': LearningResourceType.LESSON,
        'resource': LearningResourceType.RESOURCE,
        
        # Interactive activities
        'quiz': LearningResourceType.QUIZ,
        'assignment': LearningResourceType.ASSIGNMENT,
        'workshop': LearningResourceType.WORKSHOP,
        'choice': LearningResourceType.CHOICE,
        'survey': LearningResourceType.SURVEY,
        'feedback': LearningResourceType.FEEDBACK,
        
        # Communication
        'forum': LearningResourceType.FORUM,
        'chat': LearningResourceType.FORUM,  # Ähnlich wie Forum
        'wiki': LearningResourceType.WIKI,
        'glossary': LearningResourceType.GLOSSARY,
        
        # External content
        'scorm': LearningResourceType.SCORM,
        'h5p': LearningResourceType.H5P,
        'lti': LearningResourceType.ACTIVITY,  # Learning Tools Interoperability
        
        # Others
        'label': LearningResourceType.RESOURCE,
        'hotpot': LearningResourceType.QUIZ,  # HotPotatoes
        'imscp': LearningResourceType.RESOURCE,  # IMS Content Package
    }
    
    @classmethod
    def map_activity_type(cls, moodle_type: str) -> LearningResourceType:
        """Mappe Moodle-Aktivitätstyp zu Learning Resource Type"""
        normalized = moodle_type.lower().strip()
        return cls.ACTIVITY_TYPE_MAPPING.get(normalized, LearningResourceType.ACTIVITY)


class LicenseDetector:
    """Erkennung von Lizenzen aus Moodle-Metadaten"""
    
    LICENSE_PATTERNS = {
        LicenseType.CC_BY: [
            r'cc\s*by\b',
            r'creative\s*commons\s*attribution',
            r'cc-by'
        ],
        LicenseType.CC_BY_SA: [
            r'cc\s*by[-\s]*sa',
            r'creative\s*commons.*share\s*alike',
            r'cc-by-sa'
        ],
        LicenseType.CC_BY_NC: [
            r'cc\s*by[-\s]*nc',
            r'creative\s*commons.*non[-\s]*commercial',
            r'cc-by-nc'
        ],
        LicenseType.CC_BY_NC_SA: [
            r'cc\s*by[-\s]*nc[-\s]*sa',
            r'creative\s*commons.*non[-\s]*commercial.*share\s*alike',
            r'cc-by-nc-sa'
        ],
        LicenseType.CC_BY_ND: [
            r'cc\s*by[-\s]*nd',
            r'creative\s*commons.*no\s*deriv',
            r'cc-by-nd'
        ],
        LicenseType.CC_BY_NC_ND: [
            r'cc\s*by[-\s]*nc[-\s]*nd',
            r'creative\s*commons.*non[-\s]*commercial.*no\s*deriv',
            r'cc-by-nc-nd'
        ],
        LicenseType.CC0: [
            r'cc0',
            r'creative\s*commons\s*zero',
            r'public\s*domain\s*dedication'
        ],
        LicenseType.PUBLIC_DOMAIN: [
            r'public\s*domain',
            r'gemeinfrei',
            r'pd\b'
        ]
    }
    
    @classmethod
    def detect_license(cls, text: Optional[str]) -> LicenseType:
        """Erkenne Lizenz aus Text"""
        if not text:
            return LicenseType.UNKNOWN
        
        normalized = text.lower().strip()
        
        for license_type, patterns in cls.LICENSE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, normalized, re.IGNORECASE):
                    logger.info("Lizenz erkannt", license=license_type.value, pattern=pattern)
                    return license_type
        
        # Check for generic copyright indicators
        copyright_patterns = [r'copyright', r'©', r'\(c\)', r'alle\s*rechte\s*vorbehalten']
        for pattern in copyright_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                return LicenseType.COPYRIGHT
        
        return LicenseType.UNKNOWN


class MetadataMapper:
    """
    Hauptklasse für Mapping von Moodle-Metadaten zu Dublin Core
    """
    
    def __init__(self):
        self.logger = structlog.get_logger(self.__class__.__name__)
        self.language_mapper = MoodleLanguageMapper()
        self.activity_mapper = MoodleActivityTypeMapper()
        self.license_detector = LicenseDetector()
    
    def create_dublin_core_metadata(
        self,
        backup_info: MoodleBackupInfo,
        course_info: Optional[MoodleCourseInfo] = None,
        sections: Optional[List[MoodleSectionInfo]] = None,
        activities: Optional[List[Any]] = None
    ) -> DublinCoreMetadata:
        """
        Erstelle vollständige Dublin Core Metadaten aus Moodle-Daten
        
        Args:
            backup_info: Backup-Informationen aus moodle_backup.xml
            course_info: Optional, Kurs-Informationen aus course.xml
            sections: Optional, Liste der Kurs-Abschnitte
            activities: Optional, Liste der Aktivitäten
            
        Returns:
            DublinCoreMetadata Objekt mit gemappten Metadaten
        """
        self.logger.info("Erstelle Dublin Core Metadaten", course_name=backup_info.original_course_fullname)
        
        # Title - Verwende vollständigen Kursnamen
        title = backup_info.original_course_fullname
        
        # Creator - Analysiere Kurs-Metadaten für Ersteller-Informationen
        creators = self._extract_creators(backup_info, course_info)
        
        # Subject - Verwende Kurzkürzel und extrahiere Themen
        subjects = self._extract_subjects(backup_info, course_info, sections)
        
        # Description - Kombiniere verfügbare Beschreibungen
        description = self._create_description(backup_info, course_info, sections, activities)
        
        # Publisher - Ableiten aus Backup-Informationen
        publisher = self._extract_publisher(backup_info, course_info)
        
        # Contributors - Weitere Beitragende aus Kurs-Struktur
        contributors = self._extract_contributors(course_info, activities)
        
        # Date - Backup-Datum oder Kurs-Erstellungsdatum
        date = self._extract_date(backup_info, course_info)
        
        # Type - Bestimme Resource-Typ basierend auf Kurs-Struktur
        resource_type = self._determine_resource_type(course_info, activities)
        
        # Format - MBZ/Moodle Format
        format_info = f"application/x-moodle-backup (Moodle {backup_info.moodle_version})"
        
        # Identifier - Eindeutige Kennung
        identifier = self._create_identifier(backup_info, course_info)
        
        # Source - Moodle-Instanz Information
        source = self._extract_source(backup_info)
        
        # Language - Kurs-Sprache
        language = self._extract_language(course_info)
        
        # Relations - Verwandte Ressourcen
        relations = self._extract_relations(sections, activities)
        
        # Coverage - Räumliche/zeitliche Abdeckung
        coverage = self._extract_coverage(course_info)
        
        # Rights - Lizenz und Rechte-Informationen
        rights = self._extract_rights(backup_info, course_info)
        
        return DublinCoreMetadata(
            title=title,
            creator=creators,
            subject=subjects,
            description=description,
            publisher=publisher,
            contributor=contributors,
            date=date,
            type=resource_type,
            format=format_info,
            identifier=identifier,
            source=source,
            language=language,
            relation=relations,
            coverage=coverage,
            rights=rights
        )
    
    def create_educational_metadata(
        self,
        backup_info: MoodleBackupInfo,
        course_info: Optional[MoodleCourseInfo] = None,
        sections: Optional[List[MoodleSectionInfo]] = None,
        activities: Optional[List[Any]] = None
    ) -> EducationalMetadata:
        """
        Erstelle erweiterte didaktische Metadaten
        """
        self.logger.info("Erstelle Educational Metadaten", course_name=backup_info.original_course_fullname)
        
        # Learning Resource Type basierend auf Aktivitäten
        learning_resource_type = self._determine_learning_resource_type(activities)
        
        # Intended End User Role
        intended_roles = self._extract_intended_roles(course_info, activities)
        
        # Educational Context
        context = self._determine_educational_context(course_info, backup_info)
        
        # Difficulty Level
        difficulty = self._estimate_difficulty(activities, sections)
        
        # Learning Objectives aus Kurs- und Section-Beschreibungen
        learning_objectives = self._extract_learning_objectives(course_info, sections)
        
        # Prerequisites
        prerequisites = self._extract_prerequisites(course_info, sections)
        
        # Learning Time Estimation
        learning_time = self._estimate_learning_time(activities, sections)
        
        # Competencies
        competencies = self._extract_competencies(course_info, sections, activities)
        
        # Assessment Types
        assessment_types = self._identify_assessment_types(activities)
        
        # Interactivity Type
        interactivity_type = self._determine_interactivity_type(activities)
        
        return EducationalMetadata(
            learning_resource_type=learning_resource_type,
            intended_end_user_role=intended_roles,
            context=context,
            difficulty=difficulty,
            typical_learning_time=learning_time,
            learning_objectives=learning_objectives,
            prerequisites=prerequisites,
            competencies=competencies,
            assessment_type=assessment_types,
            interactivity_type=interactivity_type
        )
    
    def _extract_creators(self, backup_info: MoodleBackupInfo, course_info: Optional[MoodleCourseInfo]) -> List[str]:
        """Extrahiere Creator-Informationen"""
        creators = []
        
        # Default: Moodle System als Creator
        creators.append("Moodle Course")
        
        # TODO: Wenn verfügbar, echte Kurs-Ersteller aus Metadaten extrahieren
        # Dies würde zusätzliche XML-Parsing in users.xml erfordern
        
        return creators
    
    def _extract_subjects(self, backup_info: MoodleBackupInfo, course_info: Optional[MoodleCourseInfo], sections: Optional[List[MoodleSectionInfo]]) -> List[str]:
        """Extrahiere Subject/Schlagwörter"""
        subjects = []
        
        # Kurzkürzel als Hauptthema
        if backup_info.original_course_shortname:
            subjects.append(backup_info.original_course_shortname)
        
        # Extrahiere Themen aus Kurstitel
        title_keywords = self._extract_keywords_from_title(backup_info.original_course_fullname)
        subjects.extend(title_keywords)
        
        # Themen aus Section-Namen
        if sections:
            for section in sections:
                if section.name and section.name.strip():
                    subjects.append(section.name.strip())
        
        return list(set(subjects))  # Entferne Duplikate
    
    def _extract_keywords_from_title(self, title: str) -> List[str]:
        """Extrahiere Schlüsselwörter aus Titel"""
        # Einfache Keyword-Extraktion
        # Entferne häufige Stopwörter
        stopwords = {'der', 'die', 'das', 'und', 'oder', 'für', 'in', 'mit', 'von', 'zu', 'im', 'am', 'an', 'auf', 
                    'the', 'and', 'or', 'for', 'in', 'with', 'of', 'to', 'at', 'on', 'a', 'an', 'is', 'are'}
        
        # Split auf verschiedene Zeichen
        words = re.split(r'[\s\-_\(\)\[\]]+', title.lower())
        
        # Filtere und bereinige
        keywords = []
        for word in words:
            word = word.strip('.,!?;:')
            if len(word) > 2 and word not in stopwords and word.isalpha():
                keywords.append(word.capitalize())
        
        return keywords[:5]  # Beschränke auf 5 Keywords
    
    def _create_description(self, backup_info: MoodleBackupInfo, course_info: Optional[MoodleCourseInfo], 
                          sections: Optional[List[MoodleSectionInfo]], activities: Optional[List[Any]]) -> str:
        """Erstelle umfassende Beschreibung"""
        description_parts = []
        
        # Basis-Info aus Backup
        description_parts.append(f"Moodle course backup from {backup_info.backup_date.strftime('%Y-%m-%d')}")
        
        # Kurs-Beschreibung wenn verfügbar
        if course_info and course_info.summary:
            description_parts.append(f"Course Summary: {course_info.summary.strip()}")
        
        # Struktur-Informationen
        if sections:
            description_parts.append(f"Course contains {len(sections)} sections")
        
        if activities:
            description_parts.append(f"with {len(activities)} learning activities")
        
        # Moodle-Version und Format
        description_parts.append(f"Created with Moodle {backup_info.moodle_version}")
        
        return ". ".join(description_parts) + "."
    
    def _extract_publisher(self, backup_info: MoodleBackupInfo, course_info: Optional[MoodleCourseInfo]) -> Optional[str]:
        """Extrahiere Publisher-Informationen"""
        # Standardmäßig Moodle als Publisher
        return "Moodle"
    
    def _extract_contributors(self, course_info: Optional[MoodleCourseInfo], activities: Optional[List[Any]]) -> List[str]:
        """Extrahiere Contributors"""
        contributors = []
        
        # TODO: Contributors aus activity creators, teachers, etc.
        # Würde erweiterte XML-Analyse erfordern
        
        return contributors
    
    def _extract_date(self, backup_info: MoodleBackupInfo, course_info: Optional[MoodleCourseInfo]) -> datetime:
        """Bestimme relevantes Datum"""
        # Priorität: Kurs-Startdatum > Backup-Datum
        if course_info and course_info.start_date:
            return course_info.start_date
        
        return backup_info.backup_date
    
    def _determine_resource_type(self, course_info: Optional[MoodleCourseInfo], activities: Optional[List[Any]]) -> DCMIType:
        """Bestimme DCMI Resource Type"""
        # Moodle-Kurse sind meist Interactive Resources
        return DCMIType.INTERACTIVE_RESOURCE
    
    def _create_identifier(self, backup_info: MoodleBackupInfo, course_info: Optional[MoodleCourseInfo]) -> str:
        """Erstelle eindeutige Kennung"""
        return f"moodle-course-{backup_info.original_course_id}-{backup_info.backup_date.strftime('%Y%m%d')}"
    
    def _extract_source(self, backup_info: MoodleBackupInfo) -> str:
        """Extrahiere Source-Information"""
        return f"Moodle {backup_info.moodle_version} (Backup Format {backup_info.backup_version})"
    
    def _extract_language(self, course_info: Optional[MoodleCourseInfo]) -> Language:
        """Bestimme Kurs-Sprache"""
        if course_info and course_info.language:
            return self.language_mapper.map_language(course_info.language)
        
        return Language.DE  # Default
    
    def _extract_relations(self, sections: Optional[List[MoodleSectionInfo]], activities: Optional[List[Any]]) -> List[str]:
        """Extrahiere verwandte Ressourcen"""
        relations = []
        
        # TODO: Links zu externen Ressourcen aus Activities extrahieren
        # URL-Activities, externe Links, etc.
        
        return relations
    
    def _extract_coverage(self, course_info: Optional[MoodleCourseInfo]) -> Optional[str]:
        """Bestimme räumliche/zeitliche Abdeckung"""
        if course_info and course_info.start_date and course_info.end_date:
            start = course_info.start_date.strftime('%Y-%m-%d')
            end = course_info.end_date.strftime('%Y-%m-%d')
            return f"Course duration: {start} to {end}"
        
        return None
    
    def _extract_rights(self, backup_info: MoodleBackupInfo, course_info: Optional[MoodleCourseInfo]) -> LicenseType:
        """Erkenne Lizenz-Informationen"""
        # Prüfe Kurs-Beschreibung auf Lizenz-Hinweise
        if course_info and course_info.summary:
            detected_license = self.license_detector.detect_license(course_info.summary)
            if detected_license != LicenseType.UNKNOWN:
                return detected_license
        
        # Default für Moodle-Kurse ohne explizite Lizenz
        return LicenseType.UNKNOWN
    
    # Educational Metadata Helper-Methoden
    
    def _determine_learning_resource_type(self, activities: Optional[List[Any]]) -> LearningResourceType:
        """Bestimme Learning Resource Type"""
        # Standardmäßig Course für Moodle-Kurse
        return LearningResourceType.COURSE
    
    def _extract_intended_roles(self, course_info: Optional[MoodleCourseInfo], activities: Optional[List[Any]]) -> List[str]:
        """Bestimme Zielgruppe"""
        return ["student", "teacher"]  # Standard für Moodle-Kurse
    
    def _determine_educational_context(self, course_info: Optional[MoodleCourseInfo], backup_info: MoodleBackupInfo) -> EducationalLevel:
        """Bestimme Bildungskontext"""
        # Heuristik basierend auf Kurs-Namen
        title = backup_info.original_course_fullname.lower()
        
        if any(word in title for word in ['university', 'universität', 'bachelor', 'master', 'phd']):
            return EducationalLevel.HIGHER_EDUCATION
        elif any(word in title for word in ['school', 'schule', 'gymnasium', 'realschule']):
            return EducationalLevel.SECONDARY
        elif any(word in title for word in ['professional', 'training', 'workshop', 'seminar']):
            return EducationalLevel.PROFESSIONAL_DEVELOPMENT
        
        return EducationalLevel.OTHER  # Default
    
    def _estimate_difficulty(self, activities: Optional[List[Any]], sections: Optional[List[MoodleSectionInfo]]) -> str:
        """Schätze Schwierigkeitsgrad"""
        # Heuristik basierend auf Anzahl Aktivitäten und Sections
        if activities and sections:
            complexity_score = len(activities) + len(sections) * 2
            
            if complexity_score > 30:
                return "advanced"
            elif complexity_score > 15:
                return "intermediate"
            else:
                return "beginner"
        
        return "intermediate"  # Default
    
    def _extract_learning_objectives(self, course_info: Optional[MoodleCourseInfo], sections: Optional[List[MoodleSectionInfo]]) -> List[str]:
        """Extrahiere Lernziele"""
        objectives = []
        
        # Aus Kurs-Beschreibung
        if course_info and course_info.summary:
            # Einfache Heuristik für Lernziele
            summary = course_info.summary.lower()
            if any(word in summary for word in ['learn', 'understand', 'master', 'lernen', 'verstehen']):
                objectives.append("Master the fundamentals of the course content")
        
        # Aus Section-Namen ableiten
        if sections:
            for section in sections[:3]:  # Erste 3 Sections
                if section.name and section.name.strip():
                    objectives.append(f"Complete {section.name.strip()}")
        
        return objectives
    
    def _extract_prerequisites(self, course_info: Optional[MoodleCourseInfo], sections: Optional[List[MoodleSectionInfo]]) -> List[str]:
        """Extrahiere Voraussetzungen"""
        prerequisites = []
        
        # Basis-Voraussetzungen für Moodle-Kurse
        prerequisites.append("Basic computer literacy")
        prerequisites.append("Access to Moodle learning management system")
        
        return prerequisites
    
    def _estimate_learning_time(self, activities: Optional[List[Any]], sections: Optional[List[MoodleSectionInfo]]) -> Optional[str]:
        """Schätze Lernzeit"""
        if activities and sections:
            # Grobe Schätzung: 30min pro Activity, 1h pro Section
            activity_time = len(activities) * 30
            section_time = len(sections) * 60
            total_minutes = activity_time + section_time
            
            hours = total_minutes // 60
            minutes = total_minutes % 60
            
            return f"PT{hours}H{minutes}M"  # ISO 8601 Duration
        
        return None
    
    def _extract_competencies(self, course_info: Optional[MoodleCourseInfo], sections: Optional[List[MoodleSectionInfo]], activities: Optional[List[Any]]) -> List[str]:
        """Extrahiere Kompetenzen"""
        competencies = []
        
        # Basis-Kompetenzen
        competencies.append("Digital literacy")
        competencies.append("Self-directed learning")
        
        # Fach-spezifische Kompetenzen aus Kurs-Titel ableiten
        if course_info:
            title = course_info.fullname.lower()
            if 'python' in title:
                competencies.append("Programming skills")
                competencies.append("Problem-solving")
            elif any(word in title for word in ['math', 'mathematik']):
                competencies.append("Mathematical reasoning")
            elif any(word in title for word in ['language', 'sprache']):
                competencies.append("Communication skills")
        
        return competencies
    
    def _identify_assessment_types(self, activities: Optional[List[Any]]) -> List[str]:
        """Identifiziere Bewertungsarten"""
        assessment_types = []
        
        # TODO: Analysiere Activity-Typen für spezifische Assessments
        # Standardmäßige Bewertungsformen in Moodle
        assessment_types.extend(["formative", "peer assessment"])
        
        return assessment_types
    
    def _determine_interactivity_type(self, activities: Optional[List[Any]]) -> str:
        """Bestimme Interaktivitätstyp"""
        # Moodle-Kurse sind normalerweise mixed (active + expositive)
        return "mixed"


def map_moodle_to_dublin_core(
    backup_info: MoodleBackupInfo,
    course_info: Optional[MoodleCourseInfo] = None,
    sections: Optional[List[MoodleSectionInfo]] = None,
    activities: Optional[List[Any]] = None
) -> DublinCoreMetadata:
    """
    Convenience-Funktion für Moodle zu Dublin Core Mapping
    
    Args:
        backup_info: Backup-Informationen aus moodle_backup.xml
        course_info: Optional, Kurs-Informationen aus course.xml
        sections: Optional, Liste der Kurs-Abschnitte
        activities: Optional, Liste der Aktivitäten
        
    Returns:
        DublinCoreMetadata Objekt
    """
    mapper = MetadataMapper()
    return mapper.create_dublin_core_metadata(backup_info, course_info, sections, activities)


def create_complete_extracted_data(
    backup_info: MoodleBackupInfo,
    course_info: Optional[MoodleCourseInfo] = None,
    sections: Optional[List[MoodleSectionInfo]] = None,
    activities: Optional[List[Any]] = None
) -> MoodleExtractedData:
    """
    Erstelle vollständige MoodleExtractedData mit allen Metadaten
    
    Args:
        backup_info: Backup-Informationen aus moodle_backup.xml
        course_info: Optional, Kurs-Informationen aus course.xml
        sections: Optional, Liste der Kurs-Abschnitte
        activities: Optional, Liste der Aktivitäten
        
    Returns:
        MoodleExtractedData Objekt mit vollständigen Metadaten
    """
    mapper = MetadataMapper()
    
    # Dublin Core Metadaten
    dublin_core = mapper.create_dublin_core_metadata(backup_info, course_info, sections, activities)
    
    # Educational Metadaten
    educational = mapper.create_educational_metadata(backup_info, course_info, sections, activities)
    
    # Basis-Kurs-Informationen
    course_name = backup_info.original_course_fullname
    course_short_name = backup_info.original_course_shortname
    course_summary = course_info.summary if course_info else None
    course_language = course_info.language if course_info else "de"
    course_format = course_info.format if course_info else "topics"
    course_start_date = course_info.start_date if course_info else None
    course_end_date = course_info.end_date if course_info else None
    course_visible = course_info.visible if course_info else True
    
    # Sections und Activities als Dicts
    sections_data = []
    if sections:
        for section in sections:
            sections_data.append({
                'id': section.section_id,
                'number': section.section_number,
                'name': section.name,
                'summary': section.summary,
                'visible': section.visible,
                'activities': section.activities
            })
    
    # Activities sollten bereits MoodleActivityMetadata Objekte sein
    activities_data = activities or []
    
    return MoodleExtractedData(
        course_id=backup_info.original_course_id,
        course_name=course_name,
        course_short_name=course_short_name,
        course_summary=course_summary,
        course_language=course_language,
        course_format=course_format,
        course_start_date=course_start_date,
        course_end_date=course_end_date,
        course_visible=course_visible,
        backup_date=backup_info.backup_date,
        moodle_version=backup_info.moodle_version,
        backup_version=backup_info.backup_version,
        dublin_core=dublin_core,
        educational=educational,
        sections=sections_data,
        activities=activities_data,
        files=[],
        media_collections=[],
        file_statistics={},
        extraction_timestamp=datetime.now()
    ) 