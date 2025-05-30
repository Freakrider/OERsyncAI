"""
OERSync-AI Shared Data Models

Pydantic-Modelle für Dublin Core Metadaten und didaktische Strukturierung.
"""

from .dublin_core import (
    DublinCoreMetadata,
    EducationalMetadata,
    MoodleExtractedData,
    StructuredCourseData,
    LearningPath,
    MaterialRecommendation,
    MoodleActivityMetadata,
    LearningResourceType,
    EducationalLevel,
    Language,
    DCMIType,
    LicenseType
)

__all__ = [
    "DublinCoreMetadata",
    "EducationalMetadata", 
    "MoodleExtractedData",
    "StructuredCourseData",
    "LearningPath",
    "MaterialRecommendation",
    "MoodleActivityMetadata",
    "LearningResourceType",
    "EducationalLevel",
    "Language",
    "DCMIType",
    "LicenseType"
] 