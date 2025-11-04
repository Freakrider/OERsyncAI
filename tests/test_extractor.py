#!/usr/bin/env python3
"""
Einfaches Test-Skript für OERSync-AI Komponenten
"""

import sys
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent  # Go up one level from tests/ to project root
sys.path.insert(0, str(project_root))


def test_mbz_extractor():
    """Teste MBZ Extractor (all course files)"""
    print("\\n🗂️  TESTE MBZ EXTRACTOR")
    print("="*50)

    try:
        from shared.utils.mbz_extractor import MBZExtractor

        test_dir = project_root / "tests/course_files"

        if not test_dir.exists() or not test_dir.is_dir():
            print(f"❌ Testverzeichnis nicht gefunden: {test_dir}")
            return False

        mbz_files = list(test_dir.glob("*.mbz")) + list(test_dir.glob("*.zip"))
        if not mbz_files:
            print(f"❌ Keine .mbz oder .zip Dateien im Verzeichnis: {test_dir}")
            return False

        all_passed = True

        for mbz_file in mbz_files:
            print(f"\n🔍 Teste Datei: {mbz_file.name}")
            print("-" * 50)

            try:
                extractor = MBZExtractor()
                print(f"✅ MBZ Extractor erstellt: {extractor.temp_dir}")

                archive_type = extractor.detect_archive_type(mbz_file)
                print(f"✅ Archiv-Typ erkannt: {archive_type}")

                is_valid = extractor.validate_mbz_file(mbz_file)
                print(f"✅ MBZ-Datei ist gültig: {is_valid}")

                result = extractor.extract_mbz(mbz_file)
                print(f"✅ MBZ extrahiert:")
                print(f"   Temp Dir: {result.temp_dir}")
                print(f"   Archiv Typ: {result.archive_type}")
                print(f"   Backup XML: {result.moodle_backup_xml is not None}")
                print(f"   Course XML: {result.course_xml is not None}")
                print(f"   Aktivitäten: {len(result.activities)}")
                print(f"   Abschnitte: {len(result.sections_xml)}")
                print(f"   Plugins: {result.required_plugins}")

                extractor.cleanup()
                print("✅ Cleanup erfolgreich")

            except Exception as e:
                print(f"❌ Fehler beim Testen von {mbz_file.name}: {e}")
                traceback.print_exc()
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"❌ MBZ Extractor Fehler: {e}")
        traceback.print_exc()
        return False

def main():
    """Führe alle Tests aus"""
    print("🧪 OERSYNC-AI EINFACHE KOMPONENTEN-TESTS")
    print("="*60)
    print(f"⏰ Test gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Teste Komponenten
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