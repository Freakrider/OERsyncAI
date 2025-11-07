#!/usr/bin/env python3
"""
Debug-Skript für ILIAS-zu-Moodle-Konvertierung.
Testet die Konvertierung lokal und zeigt detaillierte Logs.
"""

import sys
import os
import logging
import json
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.utils.ilias import IliasAnalyzer, MoodleConverter


def main():
    """Hauptfunktion zum Debuggen der Konvertierung."""
    
    # Pfad zur ILIAS-Testdatei
    ilias_path = project_root / "dummy_files" / "ilias_kurs"
    
    if not ilias_path.exists():
        logger.error(f"ILIAS-Testdatei nicht gefunden: {ilias_path}")
        return
    
    logger.info("=" * 80)
    logger.info("Starte ILIAS-Analyse und Konvertierung...")
    logger.info("=" * 80)
    
    # 1. ILIAS analysieren
    logger.info(f"\n1. Analysiere ILIAS-Export: {ilias_path}")
    analyzer = IliasAnalyzer(str(ilias_path))
    success = analyzer.analyze()
    
    if not success:
        logger.error("ILIAS-Analyse fehlgeschlagen!")
        return
    
    logger.info(f"✓ ILIAS-Analyse erfolgreich!")
    logger.info(f"  - Kurstitel: {analyzer.course_title}")
    logger.info(f"  - Module: {len(analyzer.modules)}")
    logger.info(f"  - Components: {len(analyzer.components)}")
    logger.info(f"  - Hat Container-Struktur: {analyzer.container_structure is not None}")
    
    if analyzer.container_structure:
        logger.info(f"  - Container-Items: {len(analyzer.container_structure.item_by_item_id)}")
        logger.info(f"  - Root-Item: {analyzer.container_structure.root_item.title}")
        logger.info(f"  - Item-Typen: {analyzer.container_structure._count_types()}")
    else:
        logger.warning("  ⚠️ Keine Container-Struktur gefunden!")
    
    # Zeige Module
    logger.info("\nModule:")
    for i, module in enumerate(analyzer.modules, 1):
        logger.info(f"  {i}. {module.title} ({module.type}) - {len(module.items)} Items")
        for j, item in enumerate(module.items, 1):
            logger.info(f"     {j}. {item.get('title', 'N/A')} ({item.get('type', 'N/A')})")
    
    # 2. Zu Moodle konvertieren
    logger.info("\n" + "=" * 80)
    logger.info("2. Konvertiere zu Moodle...")
    logger.info("=" * 80)
    
    try:
        converter = MoodleConverter(analyzer)
        mbz_path = converter.convert(generate_report=True)
        
        logger.info(f"✓ Konvertierung erfolgreich!")
        logger.info(f"  - MBZ-Pfad: {mbz_path}")
        logger.info(f"  - MBZ-Größe: {os.path.getsize(mbz_path) / 1024:.2f} KB")
        
        if converter.moodle_structure:
            logger.info(f"  - Sections: {len(converter.moodle_structure.sections)}")
            logger.info(f"  - Activities: {sum(len(s.activities) for s in converter.moodle_structure.sections)}")
            
            # Zeige Struktur
            logger.info("\nMoodle-Struktur:")
            for section in converter.moodle_structure.sections:
                logger.info(f"  Section {section.section_id}: {section.name}")
                logger.info(f"    - Activities: {len(section.activities)}")
                for activity in section.activities:
                    logger.info(f"      - {activity.title} ({activity.module_name})")
        else:
            logger.warning("  ⚠️ Keine Moodle-Struktur erstellt!")
        
        if converter.conversion_report:
            logger.info(f"\nConversion Report:")
            logger.info(f"  - Infos: {len(converter.conversion_report.info_issues)}")
            logger.info(f"  - Warnungen: {len(converter.conversion_report.warning_issues)}")
            logger.info(f"  - Fehler: {len(converter.conversion_report.error_issues)}")
            
            if converter.conversion_report.warning_issues:
                logger.info("\n  Erste 5 Warnungen:")
                for warning in converter.conversion_report.warning_issues[:5]:
                    logger.warning(f"    - {warning.message}")
            
            if converter.conversion_report.error_issues:
                logger.info("\n  Erste 5 Fehler:")
                for error in converter.conversion_report.error_issues[:5]:
                    logger.error(f"    - {error.message}")
        
        logger.info("\n" + "=" * 80)
        logger.info("Debug-Analyse abgeschlossen!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.exception(f"Fehler bei der Konvertierung: {e}")


if __name__ == "__main__":
    main()

