#!/usr/bin/env python3
"""
Einfaches Test-Skript für OERSync-AI Komponenten
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent  # Go up one level from tests/ to project root
sys.path.insert(0, str(project_root))

def test_dublin_core_models():
    """Teste Dublin Core Datenmodelle"""
    print("🏛️  TESTE DUBLIN CORE MODELS")
    print("="*50)
    
    try:
        from shared.models.dublin_core import (
            DublinCoreMetadata, EducationalMetadata, 
            DCMIType, Language, LearningResourceType
        )
        
        # Test: Dublin Core
        dublin_core = DublinCoreMetadata(
            title="Test Course",
            creator=["Test Author"],
            subject=["Programming", "Python"],
            description="A test course for programming",
            type=DCMIType.INTERACTIVE_RESOURCE,
            language=Language.DE
        )
        
        print("✅ Dublin Core Modell erstellt:")
        print(f"   Titel: {dublin_core.title}")
        print(f"   Ersteller: {dublin_core.creator}")
        print(f"   Typ: {dublin_core.type}")
        print(f"   JSON: {len(dublin_core.model_dump_json())} Zeichen")
        
        return True
        
    except Exception as e:
        print(f"❌ Dublin Core Fehler: {e}")
        return False

def test_mbz_extractor():
    """Teste MBZ Extractor (basic)"""
    print("\\n🗂️  TESTE MBZ EXTRACTOR")
    print("="*50)
    
    try:
        from shared.utils.mbz_extractor import MBZExtractor
        
        mbz_file = project_root / "063_PFB1.mbz"  # MBZ file is in project root
        if not mbz_file.exists():
            print(f"❌ MBZ-Datei {mbz_file} nicht gefunden")
            return False
        
        # Test: Extractor erstellen
        extractor = MBZExtractor()
        print(f"✅ MBZ Extractor erstellt: {extractor.temp_dir}")
        
        # Test: Archiv-Typ erkennen
        archive_type = extractor.detect_archive_type(mbz_file)
        print(f"✅ Archiv-Typ erkannt: {archive_type}")
        
        # Test: Validierung
        is_valid = extractor.validate_mbz_file(mbz_file)
        print(f"✅ MBZ-Datei ist gültig: {is_valid}")
        
        # Test: Extraktion
        result = extractor.extract_mbz(mbz_file)
        print(f"✅ MBZ extrahiert:")
        print(f"   Temp Dir: {result.temp_dir}")
        print(f"   Archiv Typ: {result.archive_type}")
        print(f"   Backup XML: {result.moodle_backup_xml is not None}")
        print(f"   Course XML: {result.course_xml is not None}")
        print(f"   Aktivitäten: {len(result.activities)}")
        print(f"   Abschnitte: {len(result.sections_xml)}")
        
        # Cleanup
        extractor.cleanup()
        print("✅ Cleanup erfolgreich")
        
        return True
        
    except Exception as e:
        print(f"❌ MBZ Extractor Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_mapper():
    """Teste Metadata Mapper"""
    print("\\n🗺️  TESTE METADATA MAPPER")
    print("="*50)
    
    try:
        from shared.utils.metadata_mapper import MetadataMapper
        
        # Test: Mapper erstellen
        mapper = MetadataMapper()
        print("✅ MetadataMapper erstellt")
        
        # Test: Language Mapping
        lang_de = mapper.language_mapper.map_language("de")
        lang_en = mapper.language_mapper.map_language("en_us")
        print(f"✅ Language Mapping: de→{lang_de}, en_us→{lang_en}")
        
        # Test: Activity Type Mapping
        quiz_type = mapper.activity_mapper.map_activity_type("quiz")
        page_type = mapper.activity_mapper.map_activity_type("page")
        print(f"✅ Activity Mapping: quiz→{quiz_type}, page→{page_type}")
        
        # Test: License Detection
        cc_license = mapper.license_detector.detect_license("CC BY 4.0")
        copyright_license = mapper.license_detector.detect_license("All rights reserved")
        print(f"✅ License Detection: 'CC BY 4.0'→{cc_license}, 'All rights reserved'→{copyright_license}")
        
        return True
        
    except Exception as e:
        print(f"❌ Metadata Mapper Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Führe alle Tests aus"""
    print("🧪 OERSYNC-AI EINFACHE KOMPONENTEN-TESTS")
    print("="*60)
    print(f"⏰ Test gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Teste Komponenten
    results.append(("Dublin Core Models", test_dublin_core_models()))
    results.append(("Metadata Mapper", test_metadata_mapper()))
    results.append(("MBZ Extractor", test_mbz_extractor()))
    
    # Zusammenfassung
    print("\\n📊 TEST-ZUSAMMENFASSUNG")
    print("="*60)
    
    passed = 0
    for name, result in results:
        status = "✅ BESTANDEN" if result else "❌ FEHLGESCHLAGEN"
        print(f"{name:20} | {status}")
        if result:
            passed += 1
    
    print(f"\\n🎯 Ergebnis: {passed}/{len(results)} Tests bestanden")
    
    if passed == len(results):
        print("🎉 Alle Komponenten funktionieren korrekt!")
    else:
        print("⚠️  Einige Komponenten haben Probleme.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 