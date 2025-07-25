"""
Dublin Core Metadata Models für OERSync-AI

Basiert auf Dublin Core Metadata Element Set (ISO 15836-1:2017)
und erweitert für didaktische Anwendungsfälle.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl, validator, field_validator


class DCMIType(str, Enum):
    """DCMI Type Vocabulary für Ressourcentypen"""
    COLLECTION = "Collection"
    DATASET = "Dataset"
    EVENT = "Event"
    IMAGE = "Image"
    INTERACTIVE_RESOURCE = "InteractiveResource"
    MOVING_IMAGE = "MovingImage"
    PHYSICAL_OBJECT = "PhysicalObject"
    SERVICE = "Service"
    SOFTWARE = "Software"
    SOUND = "Sound"
    STILL_IMAGE = "StillImage"
    TEXT = "Text"


class LearningResourceType(str, Enum):
    """Spezifische Lernressourcentypen für Moodle"""
    COURSE = "course"
    MODULE = "module"
    ACTIVITY = "activity"
    RESOURCE = "resource"
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    FORUM = "forum"
    WIKI = "wiki"
    GLOSSARY = "glossary"
    BOOK = "book"
    LESSON = "lesson"
    WORKSHOP = "workshop"
    CHOICE = "choice"
    SURVEY = "survey"
    FEEDBACK = "feedback"
    SCORM = "scorm"
    H5P = "h5p"


class EducationalLevel(str, Enum):
    """Bildungsebenen nach ISO/IEC 19788-2"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    HIGHER_EDUCATION = "higher_education"
    VOCATIONAL = "vocational"
    PROFESSIONAL_DEVELOPMENT = "professional_development"
    OTHER = "other"


class Language(str, Enum):
    """ISO 639-1 Sprachcodes (häufigste)"""
    DE = "de"  # Deutsch
    EN = "en"  # Englisch
    FR = "fr"  # Französisch
    ES = "es"  # Spanisch
    IT = "it"  # Italienisch
    NL = "nl"  # Niederländisch


class LicenseType(str, Enum):
    """Creative Commons und andere Lizenztypen"""
    CC_BY = "CC BY"
    CC_BY_SA = "CC BY-SA"
    CC_BY_NC = "CC BY-NC"
    CC_BY_NC_SA = "CC BY-NC-SA"
    CC_BY_ND = "CC BY-ND"
    CC_BY_NC_ND = "CC BY-NC-ND"
    CC0 = "CC0"
    COPYRIGHT = "Copyright"
    PUBLIC_DOMAIN = "Public Domain"
    UNKNOWN = "Unknown"


class MediaType(str, Enum):
    """Medientypen für Dateien"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    PRESENTATION = "presentation"
    SPREADSHEET = "spreadsheet"
    ARCHIVE = "archive"
    CODE = "code"
    OTHER = "other"


class FileMetadata(BaseModel):
    """Metadaten für eine einzelne Datei"""
    
    # Basis-Identifikation
    file_id: str = Field(..., description="Eindeutige Datei-ID (contenthash)")
    original_filename: str = Field(..., description="Ursprünglicher Dateiname")
    filepath: str = Field(..., description="Pfad innerhalb des Kurses")
    mimetype: str = Field(..., description="MIME-Type der Datei")
    
    # Datei-Eigenschaften
    filesize: int = Field(..., description="Dateigröße in Bytes")
    timecreated: Optional[datetime] = Field(None, description="Erstellungszeitpunkt")
    timemodified: Optional[datetime] = Field(None, description="Letzte Änderung")
    
    # Medienklassifikation
    media_type: MediaType = Field(..., description="Klassifizierter Medientyp")
    file_extension: str = Field(..., description="Dateiendung")
    
    # Dublin Core Metadaten für die Datei
    title: Optional[str] = Field(None, description="Titel der Datei")
    description: Optional[str] = Field(None, description="Beschreibung der Datei")
    author: Optional[str] = Field(None, description="Autor der Datei")
    license: Optional[LicenseType] = Field(None, description="Lizenz der Datei")
    
    # Verwendungskontext
    used_in_activities: List[str] = Field(default_factory=list, description="IDs der Aktivitäten, die diese Datei verwenden")
    used_in_sections: List[str] = Field(default_factory=list, description="IDs der Abschnitte, die diese Datei verwenden")
    
    # Technische Details
    is_image: bool = Field(False, description="Ist es ein Bild?")
    is_video: bool = Field(False, description="Ist es ein Video?")
    is_document: bool = Field(False, description="Ist es ein Dokument?")
    is_audio: bool = Field(False, description="Ist es eine Audiodatei?")
    
    # Bildspezifische Eigenschaften (falls zutreffend)
    image_width: Optional[int] = Field(None, description="Bildbreite in Pixeln")
    image_height: Optional[int] = Field(None, description="Bildhöhe in Pixeln")
    image_format: Optional[str] = Field(None, description="Bildformat (JPEG, PNG, etc.)")
    
    # Videospezifische Eigenschaften (falls zutreffend)
    video_duration: Optional[float] = Field(None, description="Videolänge in Sekunden")
    video_format: Optional[str] = Field(None, description="Videoformat")
    video_resolution: Optional[str] = Field(None, description="Videoauflösung")
    
    @field_validator('media_type', mode='before')
    @classmethod
    def validate_media_type(cls, v):
        """Validiert und konvertiert media_type zu MediaType Enum"""
        if isinstance(v, MediaType):
            return v
        if isinstance(v, str):
            try:
                return MediaType(v)
            except ValueError:
                return MediaType.OTHER
        return MediaType.OTHER
    
    @field_validator('is_image', 'is_video', 'is_document', 'is_audio', mode='before')
    @classmethod
    def validate_boolean_fields(cls, v):
        """Validiert Boolean-Felder"""
        if isinstance(v, bool):
            return v
        return False
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class MediaCollection(BaseModel):
    """Sammlung von Medien mit Kategorisierung"""
    
    # Sammlungsmetadaten
    collection_id: str = Field(..., description="Eindeutige ID der Sammlung")
    name: str = Field(..., description="Name der Sammlung")
    description: Optional[str] = Field(None, description="Beschreibung der Sammlung")
    
    # Dateien nach Typ kategorisiert
    images: List[FileMetadata] = Field(default_factory=list, description="Bilddateien")
    videos: List[FileMetadata] = Field(default_factory=list, description="Videodateien")
    documents: List[FileMetadata] = Field(default_factory=list, description="Dokumente")
    audio_files: List[FileMetadata] = Field(default_factory=list, description="Audiodateien")
    other_files: List[FileMetadata] = Field(default_factory=list, description="Sonstige Dateien")
    
    # Statistiken
    total_files: int = Field(0, description="Gesamtanzahl der Dateien")
    total_size: int = Field(0, description="Gesamtgröße in Bytes")
    
    # Verwendungskontext
    course_id: Optional[int] = Field(None, description="Zugehörige Kurs-ID")
    section_id: Optional[int] = Field(None, description="Zugehörige Abschnitt-ID")
    activity_id: Optional[int] = Field(None, description="Zugehörige Aktivitäts-ID")
    
    class Config:
        use_enum_values = True


class DublinCoreMetadata(BaseModel):
    """
    Dublin Core Metadata Element Set (ISO 15836-1:2017)
    Vollständige Implementierung aller 15 Core-Elemente
    """
    
    # Core Dublin Core Elements
    title: str = Field(..., description="Name der Ressource")
    creator: List[str] = Field(default_factory=list, description="Primäre Verantwortliche für den Inhalt")
    subject: List[str] = Field(default_factory=list, description="Thema/Schlagwörter der Ressource")
    description: Optional[str] = Field(None, description="Beschreibung der Ressource")
    publisher: Optional[str] = Field(None, description="Veröffentlichende Institution")
    contributor: List[str] = Field(default_factory=list, description="Weitere Beitragende")
    date: Optional[datetime] = Field(None, description="Erstellungs- oder Veröffentlichungsdatum")
    type: Optional[DCMIType] = Field(None, description="Art/Typ der Ressource")
    format: Optional[str] = Field(None, description="Dateiformat oder physisches Medium")
    identifier: Optional[str] = Field(None, description="Eindeutige Kennung der Ressource")
    source: Optional[str] = Field(None, description="Verweis auf verwandte Ressource")
    language: Optional[Language] = Field(None, description="Sprache der Ressource")
    relation: List[str] = Field(default_factory=list, description="Verweis auf verwandte Ressourcen")
    coverage: Optional[str] = Field(None, description="Räumliche/zeitliche Abdeckung")
    rights: Optional[LicenseType] = Field(None, description="Rechte und Lizenzen")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class EducationalMetadata(BaseModel):
    """
    Erweiterte didaktische Metadaten basierend auf IEEE LOM und ISO/IEC 19788-2
    """
    
    # Educational Properties
    learning_resource_type: Optional[LearningResourceType] = Field(None, description="Typ der Lernressource")
    intended_end_user_role: List[str] = Field(default_factory=list, description="Zielgruppe (student, teacher, etc.)")
    context: Optional[EducationalLevel] = Field(None, description="Bildungskontext")
    typical_age_range: Optional[str] = Field(None, description="Typische Altersgruppe")
    difficulty: Optional[str] = Field(None, description="Schwierigkeitsgrad (beginner, intermediate, advanced)")
    typical_learning_time: Optional[str] = Field(None, description="Typische Lernzeit (ISO 8601 Duration)")
    
    # Learning Objectives & Outcomes
    learning_objectives: List[str] = Field(default_factory=list, description="Lernziele")
    learning_outcomes: List[str] = Field(default_factory=list, description="Erwartete Lernergebnisse")
    prerequisites: List[str] = Field(default_factory=list, description="Voraussetzungen")
    
    # Competencies & Skills
    competencies: List[str] = Field(default_factory=list, description="Vermittelte Kompetenzen")
    skills: List[str] = Field(default_factory=list, description="Entwickelte Fähigkeiten")
    
    # Assessment & Activities
    assessment_type: List[str] = Field(default_factory=list, description="Bewertungsarten")
    interactivity_type: Optional[str] = Field(None, description="Interaktivitätstyp (active, expositive, mixed)")
    
    class Config:
        use_enum_values = True


class MoodleActivityMetadata(BaseModel):
    """Spezifische Metadaten für Moodle-Aktivitäten"""
    
    activity_id: int = Field(..., description="Moodle Activity ID")
    activity_type: LearningResourceType = Field(..., description="Typ der Moodle-Aktivität")
    module_name: str = Field(..., description="Name des Moduls")
    section_number: Optional[int] = Field(None, description="Kursabschnitt Nummer")
    visible: bool = Field(True, description="Sichtbarkeit für Studierende")
    completion_enabled: bool = Field(False, description="Abschlussverfolgung aktiviert")
    grade_item: Optional[Dict[str, Any]] = Field(None, description="Bewertungseinstellungen")
    
    # Zeitbezogene Daten
    time_created: Optional[datetime] = Field(None, description="Erstellungszeitpunkt")
    time_modified: Optional[datetime] = Field(None, description="Letzte Änderung")
    
    # Spezifische Einstellungen je nach Aktivitätstyp
    activity_config: Optional[Dict[str, Any]] = Field(None, description="Spezifische Konfiguration")
    
    # Medienintegration
    attached_files: List[str] = Field(default_factory=list, description="IDs der angehängten Dateien")
    embedded_media: List[str] = Field(default_factory=list, description="IDs der eingebetteten Medien")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class MoodleExtractedData(BaseModel):
    """Vollständige Datenstruktur für extrahierte Moodle-Kursdaten"""
    
    # Course Metadata
    course_id: int = Field(..., description="Moodle Course ID")
    course_name: str = Field(..., description="Kursname")
    course_short_name: str = Field(..., description="Kurze Bezeichnung")
    course_summary: Optional[str] = Field(None, description="Kursbeschreibung")
    course_language: str = Field("de", description="Kurssprache")
    course_format: str = Field("topics", description="Kursformat")
    course_start_date: Optional[datetime] = Field(None, description="Kursstartdatum")
    course_end_date: Optional[datetime] = Field(None, description="Kursenddatum")
    course_visible: bool = Field(True, description="Kurs sichtbar")
    
    # Backup Metadata
    backup_date: Optional[datetime] = Field(None, description="Backup-Datum")
    moodle_version: Optional[str] = Field(None, description="Moodle-Version")
    backup_version: Optional[str] = Field(None, description="Backup-Format-Version")
    
    # Basic Dublin Core
    dublin_core: DublinCoreMetadata = Field(..., description="Dublin Core Metadaten")
    
    # Educational Metadata
    educational: EducationalMetadata = Field(..., description="Didaktische Metadaten")
    
    # Course Structure
    sections: List[Dict[str, Any]] = Field(default_factory=list, description="Kursabschnitte")
    activities: List[Union[MoodleActivityMetadata, Dict[str, Any]]] = Field(default_factory=list, description="Alle Aktivitäten")
    
    # Erweiterte Medienintegration
    files: List[FileMetadata] = Field(default_factory=list, description="Alle Dateien mit Metadaten")
    media_collections: List[MediaCollection] = Field(default_factory=list, description="Kategorisierte Mediensammlungen")
    
    # Dateistatistiken
    file_statistics: Dict[str, Any] = Field(default_factory=dict, description="Statistiken zu Dateien und Medien")
    
    # Extraction Metadata
    extraction_timestamp: datetime = Field(default_factory=datetime.now, description="Zeitpunkt der Extraktion")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class MaterialRecommendation(BaseModel):
    """Empfehlung für Lernmaterialien"""
    
    title: str = Field(..., description="Titel der Empfehlung")
    description: str = Field(..., description="Beschreibung der Empfehlung")
    resource_type: LearningResourceType = Field(..., description="Art der Ressource")
    difficulty_level: str = Field(..., description="Schwierigkeitsgrad")
    estimated_duration: Optional[str] = Field(None, description="Geschätzte Bearbeitungszeit")
    prerequisites: List[str] = Field(default_factory=list, description="Voraussetzungen")
    learning_objectives: List[str] = Field(default_factory=list, description="Lernziele")
    tags: List[str] = Field(default_factory=list, description="Schlagwörter")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Vertrauenswert der Empfehlung")
    
    # Medienintegration
    recommended_media: List[str] = Field(default_factory=list, description="Empfohlene Mediendateien")
    
    class Config:
        use_enum_values = True


class LearningPath(BaseModel):
    """Strukturierter Lernpfad"""
    
    path_id: str = Field(..., description="Eindeutige ID des Lernpfads")
    title: str = Field(..., description="Titel des Lernpfads")
    description: str = Field(..., description="Beschreibung des Lernpfads")
    total_estimated_duration: Optional[str] = Field(None, description="Gesamte geschätzte Lernzeit")
    difficulty_progression: str = Field(..., description="Schwierigkeitsverlauf")
    
    # Lernpfad-Struktur
    steps: List[Dict[str, Any]] = Field(..., description="Lernschritte in Reihenfolge")
    milestones: List[Dict[str, Any]] = Field(default_factory=list, description="Wichtige Meilensteine")
    
    # Empfehlungen
    recommended_materials: List[MaterialRecommendation] = Field(default_factory=list, description="Empfohlene Materialien")
    
    # Metadaten
    created_timestamp: datetime = Field(default_factory=datetime.now, description="Erstellungszeitpunkt")
    target_audience: List[str] = Field(default_factory=list, description="Zielgruppe")
    learning_outcomes: List[str] = Field(default_factory=list, description="Erwartete Lernergebnisse")
    
    # Medienintegration
    required_media: List[str] = Field(default_factory=list, description="Benötigte Mediendateien")
    optional_media: List[str] = Field(default_factory=list, description="Optionale Mediendateien")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class StructuredCourseData(BaseModel):
    """
    Finale strukturierte Kursdaten nach LLM-Verarbeitung
    Kombiniert Dublin Core, didaktische Metadaten und KI-generierte Inhalte
    """
    
    # Basis-Daten
    extracted_data: MoodleExtractedData = Field(..., description="Original extrahierte Daten")
    
    # KI-generierte Strukturierung
    enhanced_dublin_core: DublinCoreMetadata = Field(..., description="Erweiterte Dublin Core Metadaten")
    enhanced_educational: EducationalMetadata = Field(..., description="Erweiterte didaktische Metadaten")
    
    # Didaktische Strukturierung
    learning_paths: List[LearningPath] = Field(default_factory=list, description="Generierte Lernpfade")
    material_recommendations: List[MaterialRecommendation] = Field(default_factory=list, description="Materialempfehlungen")
    
    # Semantische Analyse
    topics_taxonomy: Dict[str, Any] = Field(default_factory=dict, description="Thematische Taxonomie")
    knowledge_graph: Optional[Dict[str, Any]] = Field(None, description="Wissensgruppierung")
    
    # Erweiterte Medienanalyse
    media_analysis: Dict[str, Any] = Field(default_factory=dict, description="Analyse der Mediennutzung")
    visual_content_summary: Optional[str] = Field(None, description="Zusammenfassung der visuellen Inhalte")
    
    # Processing Metadata
    processing_timestamp: datetime = Field(default_factory=datetime.now, description="Verarbeitungszeitpunkt")
    llm_model_used: Optional[str] = Field(None, description="Verwendetes LLM-Modell")
    processing_version: str = Field(default="1.0", description="Verarbeitungsversion")
    confidence_metrics: Optional[Dict[str, float]] = Field(None, description="Vertrauensmetriken")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# Utility Functions

def validate_dublin_core_required_fields(metadata: DublinCoreMetadata) -> bool:
    """Validiert erforderliche Dublin Core Felder"""
    return bool(metadata.title and metadata.creator)


def convert_moodle_to_dublin_core(
    course_name: str,
    course_summary: Optional[str] = None,
    creator: Optional[str] = None,
    **kwargs
) -> DublinCoreMetadata:
    """Konvertiert Moodle-Kursdaten zu Dublin Core Metadaten"""
    return DublinCoreMetadata(
        title=course_name,
        description=course_summary,
        creator=[creator] if creator else [],
        **kwargs
    )


def classify_media_type(mimetype: str, filename: str) -> MediaType:
    """Klassifiziert eine Datei basierend auf MIME-Type und Dateiname"""
    mimetype_lower = mimetype.lower()
    filename_lower = filename.lower()
    
    # Bilddateien
    if mimetype_lower.startswith('image/') or any(ext in filename_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']):
        return MediaType.IMAGE
    
    # Videodateien
    elif mimetype_lower.startswith('video/') or any(ext in filename_lower for ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']):
        return MediaType.VIDEO
    
    # Audiodateien
    elif mimetype_lower.startswith('audio/') or any(ext in filename_lower for ext in ['.mp3', '.wav', '.ogg', '.aac', '.flac']):
        return MediaType.AUDIO
    
    # Dokumente
    elif mimetype_lower in ['application/pdf', 'text/plain', 'text/html'] or any(ext in filename_lower for ext in ['.pdf', '.txt', '.html', '.htm']):
        return MediaType.DOCUMENT
    
    # Präsentationen
    elif mimetype_lower in ['application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'] or any(ext in filename_lower for ext in ['.ppt', '.pptx']):
        return MediaType.PRESENTATION
    
    # Tabellen
    elif mimetype_lower in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'] or any(ext in filename_lower for ext in ['.xls', '.xlsx']):
        return MediaType.SPREADSHEET
    
    # Archive
    elif mimetype_lower.startswith('application/') and 'zip' in mimetype_lower or any(ext in filename_lower for ext in ['.zip', '.rar', '.7z', '.tar', '.gz']):
        return MediaType.ARCHIVE
    
    # Code
    elif any(ext in filename_lower for ext in ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.sql']):
        return MediaType.CODE
    
    else:
        return MediaType.OTHER


def create_media_collection_from_files(files: List[FileMetadata], collection_id: str, name: str) -> MediaCollection:
    """Erstellt eine MediaCollection aus einer Liste von Dateien"""
    collection = MediaCollection(
        collection_id=collection_id,
        name=name,
        total_files=len(files),
        total_size=sum(f.filesize for f in files)
    )
    
    for file_meta in files:
        # Stelle sicher, dass media_type ein MediaType Enum ist
        if hasattr(file_meta.media_type, 'value'):
            media_type = file_meta.media_type
        else:
            # Fallback: versuche String zu MediaType zu konvertieren
            try:
                media_type = MediaType(str(file_meta.media_type))
            except ValueError:
                media_type = MediaType.OTHER
        
        if media_type == MediaType.IMAGE:
            collection.images.append(file_meta)
        elif media_type == MediaType.VIDEO:
            collection.videos.append(file_meta)
        elif media_type == MediaType.AUDIO:
            collection.audio_files.append(file_meta)
        elif media_type in [MediaType.DOCUMENT, MediaType.PRESENTATION, MediaType.SPREADSHEET]:
            collection.documents.append(file_meta)
        else:
            collection.other_files.append(file_meta)
    
    return collection 