#!/usr/bin/env python3
"""
Test Script für Metadata Mapper

Testet die neue Metadata-Mapping-Engine mit unserer echten MBZ-Datei.
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to Python path  
project_root = Path(__file__).parent.parent  # Go up one level from tests/ to project root
sys.path.insert(0, str(project_root))

from shared.utils.mbz_extractor import MBZExtractor
from shared.utils.xml_parser import XMLParser
from shared.utils.metadata_mapper import MetadataMapper, map_moodle_to_dublin_core, create_complete_extracted_data
import structlog

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def test_metadata_mapper():
    """Test der neuen Metadata-Mapping-Engine"""
    print("\n" + "="*70)
    print("🗂️  TESTE NEUE METADATA MAPPER ENGINE")
    print("="*70)
    
    # 1. MBZ-Extraktion
    print(f"\n1. Extrahiere MBZ-Datei...")
    mbz_path = project_root / "063_PFB1.mbz"  # MBZ file is in project root
    if not mbz_path.exists():
        print(f"⚠️  MBZ-Datei nicht gefunden: {mbz_path}")
        return False
    
    temp_dir = Path(tempfile.mkdtemp(prefix="metadata_test_"))
    extractor = MBZExtractor(temp_dir)
    extraction_result = extractor.extract_mbz(mbz_path)
    
    print(f"✅ MBZ extrahiert: {extraction_result.temp_dir}")
    
    # 2. XML-Parsing
    print(f"\n2. Parse XML-Daten...")
    parser = XMLParser()
    
    # Parse backup info (sollte funktionieren)
    backup_info = parser.parse_moodle_backup_xml(extraction_result.moodle_backup_xml)
    print(f"✅ Backup-Info: {backup_info.original_course_fullname}")
    
    # Parse course info (funktioniert jetzt)
    course_info = None
    if extraction_result.course_xml and extraction_result.course_xml.exists():
        try:
            course_info = parser.parse_course_xml(extraction_result.course_xml)
            print(f"✅ Course-Info: {course_info.fullname}")
        except Exception as e:
            print(f"⚠️  Course-Info nicht verfügbar: {e}")
    
    # 3. Teste Metadata Mapper
    print(f"\n3. Teste Metadata Mapper...")
    mapper = MetadataMapper()
    
    # Test Dublin Core Erstellung
    print(f"\n3.1 Teste Dublin Core Mapping...")
    dublin_core = mapper.create_dublin_core_metadata(
        backup_info=backup_info,
        course_info=course_info,
        sections=None,  # Sections nicht verfügbar wegen XML-Korruption
        activities=None  # Activities nicht verfügbar wegen XML-Korruption
    )
    
    print(f"✅ Dublin Core erstellt:")
    print(f"   📚 Titel: {dublin_core.title}")
    print(f"   👥 Creator: {dublin_core.creator}")
    print(f"   🏷️  Subject: {dublin_core.subject}")
    print(f"   📝 Description: {dublin_core.description[:100]}...")
    print(f"   📅 Date: {dublin_core.date}")
    print(f"   🗣️  Language: {dublin_core.language}")
    print(f"   🏷️  Type: {dublin_core.type}")
    print(f"   📦 Format: {dublin_core.format}")
    print(f"   🔗 Identifier: {dublin_core.identifier}")
    print(f"   🔢 Source: {dublin_core.source}")
    
    # Test Educational Metadata
    print(f"\n3.2 Teste Educational Metadata...")
    educational = mapper.create_educational_metadata(
        backup_info=backup_info,
        course_info=course_info,
        sections=None,
        activities=None
    )
    
    print(f"✅ Educational Metadata erstellt:")
    print(f"   📖 Resource Type: {educational.learning_resource_type}")
    print(f"   👥 Intended Roles: {educational.intended_end_user_role}")
    print(f"   🎓 Context: {educational.context}")
    print(f"   📊 Difficulty: {educational.difficulty}")
    print(f"   ⏱️  Learning Time: {educational.typical_learning_time}")
    print(f"   🎯 Objectives: {educational.learning_objectives}")
    print(f"   📋 Prerequisites: {educational.prerequisites}")
    print(f"   💪 Competencies: {educational.competencies}")
    print(f"   🔍 Assessment Types: {educational.assessment_type}")
    print(f"   🎮 Interactivity: {educational.interactivity_type}")
    
    # 4. Teste Convenience Functions
    print(f"\n4. Teste Convenience Functions...")
    
    # Test map_moodle_to_dublin_core
    dublin_core_conv = map_moodle_to_dublin_core(backup_info, course_info)
    print(f"✅ Convenience Dublin Core: {dublin_core_conv.title}")
    
    # Test create_complete_extracted_data
    extracted_data = create_complete_extracted_data(backup_info, course_info)
    print(f"✅ Complete Extracted Data:")
    print(f"   📚 Course: {extracted_data.course_name}")
    print(f"   🔢 Course ID: {extracted_data.course_id}")
    print(f"   📅 Extraction Time: {extracted_data.extraction_timestamp}")
    print(f"   🔧 Moodle Version: {extracted_data.moodle_version}")
    
    # Teste auch die speziellen Mapper-Klassen
    print(f"\n5. Teste spezielle Mapper...")
    
    # Language Mapper
    from shared.utils.metadata_mapper import MoodleLanguageMapper
    
    test_languages = ['de', 'en', 'en_us', 'unknown', None]
    for lang in test_languages:
        mapped = MoodleLanguageMapper.map_language(lang)
        print(f"   🗣️  {lang} -> {mapped}")
    
    # Activity Type Mapper  
    from shared.utils.metadata_mapper import MoodleActivityTypeMapper
    
    test_activities = ['quiz', 'forum', 'book', 'page', 'unknown']
    for activity in test_activities:
        mapped = MoodleActivityTypeMapper.map_activity_type(activity)
        print(f"   🎯 {activity} -> {mapped}")
    
    # License Detector
    from shared.utils.metadata_mapper import LicenseDetector
    
    test_texts = [
        "This is CC BY licensed content",
        "Creative Commons Attribution Share-Alike",
        "Copyright 2023 All rights reserved",
        "Public domain content",
        "No license mentioned"
    ]
    for text in test_texts:
        detected = LicenseDetector.detect_license(text)
        print(f"   ⚖️  '{text[:30]}...' -> {detected}")
    
    # 6. Validierung
    print(f"\n6. Validiere Ergebnisse...")
    
    # Prüfe ob alle required Dublin Core Felder gesetzt sind
    required_fields = ['title', 'creator', 'subject']
    missing_fields = []
    
    for field in required_fields:
        value = getattr(dublin_core, field)
        if not value or (isinstance(value, list) and not value):
            missing_fields.append(field)
    
    if missing_fields:
        print(f"⚠️  Fehlende Required Fields: {missing_fields}")
    else:
        print(f"✅ Alle Required Dublin Core Fields gesetzt")
    
    # Prüfe Educational Metadata
    if educational.learning_resource_type and educational.context:
        print(f"✅ Educational Metadata vollständig")
    else:
        print(f"⚠️  Educational Metadata unvollständig")
    
    # 7. JSON Serialization Test
    print(f"\n7. Teste JSON Serialization...")
    try:
        dc_json = dublin_core.model_dump_json(indent=2)
        edu_json = educational.model_dump_json(indent=2)
        extracted_json = extracted_data.model_dump_json(indent=2)
        
        print(f"✅ JSON Serialization erfolgreich")
        print(f"   📄 Dublin Core: {len(dc_json)} Zeichen")
        print(f"   📄 Educational: {len(edu_json)} Zeichen") 
        print(f"   📄 Extracted Data: {len(extracted_json)} Zeichen")
        
        # Speichere ein Beispiel
        output_path = Path("test_output_metadata.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_json)
        print(f"   💾 Beispiel-Output gespeichert: {output_path}")
        
    except Exception as e:
        print(f"❌ JSON Serialization fehlgeschlagen: {e}")
    
    # Cleanup
    extractor.cleanup()
    
    print(f"\n" + "="*70)
    print("🎉 METADATA MAPPER TEST ABGESCHLOSSEN")
    print("="*70)
    
    return True


if __name__ == "__main__":
    test_metadata_mapper() 