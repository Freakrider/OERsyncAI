#!/usr/bin/env python3
"""
Test Script für echte MBZ-Datei: 063_PFB1.mbz

Testet unsere implementierten Module mit realen Moodle-Daten:
- MBZ Extraktion
- XML Parsing
- Dublin Core Metadaten-Erstellung
- File Utilities
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent  # Go up one level from tests/ to project root
sys.path.insert(0, str(project_root))

from shared.utils.mbz_extractor import MBZExtractor
from shared.utils.xml_parser import XMLParser, parse_moodle_backup_complete
from shared.utils.file_utils import validate_mbz_file, format_file_size
from shared.models.dublin_core import MoodleExtractedData
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


def test_real_mbz_extraction():
    """Test MBZ-Extraktion mit echter Datei"""
    print("\n" + "="*60)
    print("🗂️  TESTE MBZ-EXTRAKTION MIT ECHTER DATEI")
    print("="*60)
    
    mbz_path = project_root / "063_PFB1.mbz"  # MBZ file is in project root
    if not mbz_path.exists():
        print(f"❌ MBZ-Datei {mbz_path} nicht gefunden")
        return False, None
        
    file_size = mbz_path.stat().st_size
    print(f"✅ Datei gültig - Größe: {format_file_size(file_size)}")
    
    # 2. MBZ-Extraktion
    print(f"\n2. Extrahiere MBZ-Datei...")
    
    try:
        # Erstelle MBZExtractor mit permanentem temporärem Verzeichnis  
        # damit die Dateien nach der Extraktion noch existieren
        temp_dir = Path(tempfile.mkdtemp(prefix="mbz_test_"))
        extractor = MBZExtractor(temp_dir)
        
        # Extrahiere MBZ-Datei
        extraction_result = extractor.extract_mbz(mbz_path)
        
        print(f"✅ MBZ erfolgreich extrahiert")
        print(f"   📁 Extraktions-Verzeichnis: {extraction_result.temp_dir}")
        print(f"   ⏱️  Extraktionszeit: {extraction_result.extraction_time}")
        
        # Zeige wichtige Dateien
        important_files = [
            ("moodle_backup.xml", extraction_result.moodle_backup_xml),
            ("course.xml", extraction_result.course_xml),
            ("files.xml", extraction_result.files_xml),
        ]
        
        print(f"\n   🔍 Wichtige Dateien gefunden:")
        for file_desc, file_path in important_files:
            if file_path and file_path.exists():
                print(f"     ✅ {file_desc}: {file_path}")
            else:
                print(f"     ❌ {file_desc}: nicht gefunden")
        
        # Zeige Sections (als Liste)
        if extraction_result.sections_xml:
            print(f"     ✅ sections.xml: {len(extraction_result.sections_xml)} gefunden")
            for section_file in extraction_result.sections_xml[:3]:  # Zeige max 3
                print(f"        - {section_file}")
            if len(extraction_result.sections_xml) > 3:
                print(f"        ... und {len(extraction_result.sections_xml) - 3} weitere")
        else:
            print(f"     ❌ sections.xml: nicht gefunden")
        
        # Zeige Activities
        if extraction_result.activities:
            print(f"     ✅ Activities: {len(extraction_result.activities)} gefunden")
            for activity in extraction_result.activities[:3]:  # Zeige max 3
                print(f"        - {activity}")
            if len(extraction_result.activities) > 3:
                print(f"        ... und {len(extraction_result.activities) - 3} weitere")
        else:
            print(f"     ❌ Activities: nicht gefunden")
        
        # Zeige Archiv-Typ
        print(f"     🗂️  Archiv-Typ: {extraction_result.archive_type}")
        if extraction_result.moodle_version:
            print(f"     🔧 Moodle-Version: {extraction_result.moodle_version}")
        if extraction_result.backup_version:
            print(f"     📦 Backup-Version: {extraction_result.backup_version}")
        
        # Zeige Statistiken
        extract_dir = extraction_result.temp_dir / "extracted"
        if extract_dir.exists():
            all_files = list(extract_dir.rglob("*"))
            extracted_files = [f for f in all_files if f.is_file()]
            print(f"   📄 Gesamt extrahierte Dateien: {len(extracted_files)}")
        
        return extraction_result, extractor
            
    except Exception as e:
        print(f"❌ Fehler bei MBZ-Extraktion: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_real_xml_parsing(extraction_result):
    """Test XML-Parsing mit echten Daten"""
    print("\n" + "="*60)
    print("📋 TESTE XML-PARSING MIT ECHTEN DATEN")
    print("="*60)
    
    parser = XMLParser()
    
    # 1. Parse moodle_backup.xml
    print(f"\n1. Parse moodle_backup.xml...")
    backup_xml = extraction_result.moodle_backup_xml
    
    if not backup_xml or not backup_xml.exists():
        print(f"❌ moodle_backup.xml nicht gefunden")
        return False
    
    try:
        backup_info = parser.parse_moodle_backup_xml(backup_xml)
        print(f"✅ moodle_backup.xml erfolgreich geparst")
        print(f"   📚 Kurs: {backup_info.original_course_fullname}")
        print(f"   🏷️  Kurzname: {backup_info.original_course_shortname}")
        print(f"   🔢 Kurs-ID: {backup_info.original_course_id}")
        print(f"   📅 Backup-Datum: {backup_info.backup_date}")
        print(f"   🔧 Moodle-Version: {backup_info.moodle_version}")
        print(f"   📦 Backup-Version: {backup_info.backup_version}")
        print(f"   🎭 Anonymisiert: {backup_info.anonymized}")
        
    except Exception as e:
        print(f"❌ Fehler beim Parsen von moodle_backup.xml: {e}")
        return False
    
    # 2. Parse course.xml
    print(f"\n2. Parse course/course.xml...")
    course_xml = extraction_result.course_xml
    
    if course_xml and course_xml.exists():
        try:
            course_info = parser.parse_course_xml(course_xml)
            print(f"✅ course.xml erfolgreich geparst")
            print(f"   📚 Vollständiger Name: {course_info.fullname}")
            print(f"   📝 Beschreibung: {course_info.summary[:100] if course_info.summary else 'Keine'}...")
            print(f"   🗣️  Sprache: {course_info.language}")
            print(f"   📊 Format: {course_info.format}")
            print(f"   👁️  Sichtbar: {course_info.visible}")
            print(f"   📅 Startdatum: {course_info.start_date}")
            print(f"   📅 Enddatum: {course_info.end_date}")
            
        except Exception as e:
            print(f"❌ Fehler beim Parsen von course.xml: {e}")
            course_info = None
    else:
        print(f"⚠️  course.xml nicht gefunden")
        course_info = None
    
    # 3. Parse sections
    print(f"\n3. Parse Sections...")
    sections_to_parse = extraction_result.sections_xml
    
    if sections_to_parse:
        try:
            sections_info = []
            for section_file in sections_to_parse:
                if section_file.exists():
                    section_info = parser._parse_single_section(section_file)
                    sections_info.append(section_info)
                
            # Sortiere nach Section-Nummer
            sections_info.sort(key=lambda s: s.section_number)
            
            print(f"✅ {len(sections_info)} Sections erfolgreich geparst")
            
            for section in sections_info[:5]:  # Zeige max 5
                print(f"   📑 Section {section.section_number}: {section.name or 'Ohne Namen'}")
                print(f"      👁️ Sichtbar: {section.visible}")
                print(f"      🎯 Aktivitäten: {len(section.activities)}")
                if section.summary:
                    print(f"      📝 Beschreibung: {section.summary[:80]}...")
                
            if len(sections_info) > 5:
                print(f"   ... und {len(sections_info) - 5} weitere Sections")
                
        except Exception as e:
            print(f"❌ Fehler beim Parsen von Sections: {e}")
            sections_info = []
    else:
        print(f"⚠️  Keine section.xml Dateien gefunden")
        sections_info = []
    
    # 4. Parse activities
    print(f"\n4. Parse Activities...")
    activities_to_parse = extraction_result.activities
    
    if activities_to_parse:
        print(f"   🎯 Gefunden: {len(activities_to_parse)} Activity-Dateien")
        
        activities_parsed = 0
        activity_types = {}
        
        for activity_file in activities_to_parse[:10]:  # Parse max 10 für Test
            if activity_file.exists():
                try:
                    activity_metadata = parser.parse_activity_xml(activity_file)
                    activities_parsed += 1
                    
                    # Sammle Activity-Typen
                    activity_type = activity_metadata.activity_type.value
                    activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
                    
                    print(f"   ✅ {activity_metadata.module_name} ({activity_type})")
                    if activity_metadata.activity_config:
                        print(f"      ⚙️ Konfiguration: {len(activity_metadata.activity_config)} Einstellungen")
                    
                except Exception as e:
                    print(f"   ❌ Fehler beim Parsen von {activity_file.name}: {e}")
        
        print(f"\n   📊 Activity-Typen Zusammenfassung:")
        for activity_type, count in activity_types.items():
            print(f"      {activity_type}: {count}")
        
        if len(activities_to_parse) > 10:
            print(f"   ... {len(activities_to_parse) - 10} weitere Activities nicht getestet")
            
    else:
        print(f"⚠️  Keine Activities gefunden")
    
    return backup_info, course_info, sections_info


def test_dublin_core_creation(backup_info, course_info=None):
    """Test Dublin Core Metadaten-Erstellung"""
    print("\n" + "="*60)
    print("🏛️  TESTE DUBLIN CORE METADATEN-ERSTELLUNG")
    print("="*60)
    
    try:
        from shared.utils.xml_parser import XMLParser
        parser = XMLParser()
        
        # Erstelle Dublin Core aus verfügbaren Informationen
        if course_info:
            dublin_core = parser.create_dublin_core_from_course(course_info, backup_info)
            print(f"✅ Dublin Core aus vollständigen Kurs-Informationen erstellt")
        else:
            # Erstelle minimale Dublin Core nur aus backup_info
            from shared.models.dublin_core import DublinCoreMetadata, Language, DCMIType
            
            dublin_core = DublinCoreMetadata(
                title=backup_info.original_course_fullname,
                creator=["Moodle Course"],  # Als Liste
                subject=[backup_info.original_course_shortname],  # Als Liste
                description=f"Moodle course backup from {backup_info.backup_date}",
                date=backup_info.backup_date,
                language=Language.DE,  # Default
                type=DCMIType.INTERACTIVE_RESOURCE,
                format="application/x-moodle-backup",
                identifier=f"moodle-course-{backup_info.original_course_id}",
                source=f"Moodle {backup_info.moodle_version}"
            )
            print(f"✅ Minimale Dublin Core aus Backup-Informationen erstellt")
        
        print(f"   📚 Titel: {dublin_core.title}")
        print(f"   🏷️  Typ: {dublin_core.type}")
        print(f"   🗣️  Sprache: {dublin_core.language}")
        print(f"   📅 Datum: {dublin_core.date}")
        print(f"   🔗 Identifier: {dublin_core.identifier}")
        
        return dublin_core
        
    except Exception as e:
        print(f"❌ Fehler bei Dublin Core Erstellung: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_complete_parsing(extraction_result):
    """Test vollständiges Parsing mit convenience function"""
    print("\n" + "="*60)
    print("🔄 TESTE VOLLSTÄNDIGES PARSING")
    print("="*60)
    
    backup_xml = extraction_result.moodle_backup_xml
    course_xml = extraction_result.course_xml
    sections_path = extraction_result.temp_dir / "extracted" / "sections"
    activities_path = extraction_result.temp_dir / "extracted" / "activities"
    
    try:
        extracted_data = parse_moodle_backup_complete(
            backup_xml_path=backup_xml,
            course_xml_path=course_xml if course_xml and course_xml.exists() else None,
            sections_path=sections_path if sections_path.exists() else None,
            activities_path=activities_path if activities_path.exists() else None
        )
        
        print(f"✅ Vollständiges Parsing erfolgreich")
        print(f"   📚 Kurs: {extracted_data.course_name}")
        print(f"   🏷️  Kurzname: {extracted_data.course_short_name}")
        print(f"   📝 Beschreibung: {extracted_data.course_summary[:100] if extracted_data.course_summary else 'Keine'}...")
        print(f"   📑 Sections: {len(extracted_data.sections)}")
        print(f"   🎯 Activities: {len(extracted_data.activities)}")
        print(f"   🔧 Moodle Version: {extracted_data.moodle_version}")
        
        # Dublin Core Details
        dc = extracted_data.dublin_core
        print(f"\n   🏛️  Dublin Core Metadaten:")
        print(f"      📚 Titel: {dc.title}")
        print(f"      🗣️  Sprache: {dc.language}")
        print(f"      🏷️  Typ: {dc.type}")
        
        # Educational Metadata
        edu = extracted_data.educational
        print(f"\n   🎓 Educational Metadaten:")
        print(f"      📖 Resource Type: {edu.learning_resource_type.value}")
        print(f"      🎯 Kontext: {edu.context.value}")
        print(f"      👥 Zielgruppe: {', '.join(edu.intended_end_user_role)}")
        
        return extracted_data
        
    except Exception as e:
        print(f"❌ Fehler beim vollständigen Parsing: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Hauptfunktion für Tests"""
    print("🧪 TESTE OERSYNC-AI MIT ECHTER MBZ-DATEI: 063_PFB1.mbz")
    print("=" * 80)
    
    extraction_result = None
    extractor = None
    
    try:
        # 1. MBZ-Extraktion testen
        extraction_result, extractor = test_real_mbz_extraction()
        if not extraction_result or extraction_result == False:
            print("\n❌ MBZ-Extraktion fehlgeschlagen. Test wird abgebrochen.")
            return
        
        # 2. XML-Parsing testen
        parsing_result = test_real_xml_parsing(extraction_result)
        if not parsing_result:
            print("\n❌ XML-Parsing fehlgeschlagen.")
            return
        
        backup_info, course_info, sections_info = parsing_result
        
        # 3. Dublin Core Erstellung testen (auch ohne course_info möglich)
        dublin_core = test_dublin_core_creation(backup_info, course_info)
        
        # 4. Vollständiges Parsing testen (nur wenn course_info verfügbar)
        if course_info:
            extracted_data = test_complete_parsing(extraction_result)
        else:
            print("\n⚠️  Vollständiges Parsing übersprungen (course.xml nicht verfügbar)")
            extracted_data = None
        
        # 5. Zusammenfassung
        print("\n" + "="*60)
        print("📊 TEST-ZUSAMMENFASSUNG")
        print("="*60)
        
        total_files = len(extraction_result.activities) + len(extraction_result.sections_xml)
        if extraction_result.moodle_backup_xml:
            total_files += 1
        if extraction_result.course_xml:
            total_files += 1
        if extraction_result.files_xml:
            total_files += 1
        
        print(f"✅ MBZ-Extraktion: Erfolgreich ({total_files} wichtige Dateien)")
        print(f"✅ Backup-Info Parsing: Erfolgreich")
        print(f"{'✅' if course_info else '⚠️ '} Course-Info Parsing: {'Erfolgreich' if course_info else 'Nicht verfügbar'}")
        print(f"{'✅' if sections_info else '⚠️ '} Sections Parsing: {'Erfolgreich' if sections_info else 'Nicht verfügbar'}")
        print(f"{'✅' if dublin_core else '⚠️ '} Dublin Core Erstellung: {'Erfolgreich' if dublin_core else 'Übersprungen'}")
        print(f"{'✅' if extracted_data else '❌'} Vollständiges Parsing: {'Erfolgreich' if extracted_data else 'Fehlgeschlagen'}")
        
        if extracted_data:
            print(f"\n🎉 ALLE TESTS ERFOLGREICH!")
            print(f"   📚 Kurs '{extracted_data.course_name}' vollständig verarbeitet")
            print(f"   📊 Daten bereit für LLM-Verarbeitung")
            print(f"   🗂️  Archiv-Format: {extraction_result.archive_type.upper()}")
        else:
            print(f"\n⚠️  TESTS TEILWEISE ERFOLGREICH")
            print(f"   🔧 Einige Komponenten benötigen weitere Überarbeitung")
        
        print(f"\n🏁 Test abgeschlossen!")
        
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Bereinigung
        if extractor:
            try:
                extractor.cleanup()
                print(f"\n🧹 Temporäre Dateien bereinigt")
            except Exception as e:
                print(f"\n⚠️  Fehler beim Bereinigen: {e}")


if __name__ == "__main__":
    main() 