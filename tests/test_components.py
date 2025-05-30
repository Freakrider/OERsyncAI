#!/usr/bin/env python3
"""
Test-Skript für einzelne OERSync-AI Komponenten

Testet alle Komponenten einzeln ohne API-Server:
- MBZ Extractor
- XML Parser  
- Metadata Mapper
- Dublin Core Models
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent  # Go up one level from tests/ to project root
sys.path.insert(0, str(project_root))

def test_mbz_extractor():
    """Teste MBZ-Datei-Extraktion"""
    print("\\n🗂️  TESTE MBZ EXTRACTOR")
    print("="*50)
    
    try:
        from shared.utils.mbz_extractor import MBZExtractor
        
        mbz_file = project_root / "063_PFB1.mbz"  # MBZ file is in project root
        if not mbz_file.exists():
            print(f"❌ MBZ-Datei {mbz_file} nicht gefunden")
            return False
            
        extractor = MBZExtractor(mbz_file)
        
        # Test: Archiv öffnen
        extractor.extract_archive()
        print(f"✅ Archiv erfolgreich extrahiert nach: {extractor.temp_dir}")
        
        # Test: Backup-Info laden
        backup_info = extractor.get_backup_info()
        print(f"✅ Backup Info geladen:")
        print(f"   Moodle Version: {backup_info.moodle_version}")
        print(f"   Backup Datum: {backup_info.backup_date}")
        print(f"   Kurs Name: {backup_info.original_course_fullname}")
        
        # Test: Kurs-Info laden
        course_info = extractor.get_course_info()
        if course_info:
            print(f"✅ Kurs Info geladen:")
            print(f"   Kurs ID: {course_info.id}")
            print(f"   Kurs Name: {course_info.fullname}")
            print(f"   Kurze Bezeichnung: {course_info.shortname}")
        
        # Test: Cleanup
        extractor.cleanup()
        print("✅ Cleanup erfolgreich")
        
        return True
        
    except Exception as e:
        print(f"❌ MBZ Extractor Fehler: {e}")
        return False

def test_dublin_core_models():
    """Teste Dublin Core Datenmodelle"""
    print("\\n🏛️  TESTE DUBLIN CORE MODELS")
    print("="*50)
    
    try:
        from shared.models.dublin_core import (
            DublinCoreMetadata, EducationalMetadata, 
            DCMIType, Language, LearningResourceType, EducationalLevel
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
        
        print("✅ Dublin Core Modell:")
        print(f"   Titel: {dublin_core.title}")
        print(f"   Ersteller: {dublin_core.creator}")
        print(f"   Typ: {dublin_core.type}")
        
        # Test: Educational Metadata
        educational = EducationalMetadata(
            learning_resource_type=LearningResourceType.COURSE,
            context=EducationalLevel.HIGHER_EDUCATION,
            difficulty="intermediate",
            intended_end_user_role=["student"]
        )
        
        print("✅ Educational Metadata Modell:")
        print(f"   Typ: {educational.learning_resource_type}")
        print(f"   Kontext: {educational.context}")
        print(f"   Schwierigkeit: {educational.difficulty}")
        
        # Test: JSON Serialisierung
        dublin_core_json = dublin_core.model_dump_json(indent=2)
        educational_json = educational.model_dump_json(indent=2)
        
        print("✅ JSON Serialisierung erfolgreich")
        print(f"   Dublin Core JSON: {len(dublin_core_json)} Zeichen")
        print(f"   Educational JSON: {len(educational_json)} Zeichen")
        
        return True
        
    except Exception as e:
        print(f"❌ Dublin Core Models Fehler: {e}")
        return False

def main():
    """Führe alle Tests aus"""
    print("🧪 OERSYNC-AI KOMPONENTEN-TESTS")
    print("="*60)
    print(f"⏰ Test gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Teste Komponenten
    results.append(("Dublin Core Models", test_dublin_core_models()))
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
        return True
    else:
        print("⚠️  Einige Komponenten haben Probleme.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 