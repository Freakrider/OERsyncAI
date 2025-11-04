#!/usr/bin/env python3
"""
Demo-Skript für die ILIAS zu Moodle Konvertierung.

Dieses Skript demonstriert die vollständige Konvertierung eines ILIAS-Kurses
zu einem Moodle-Backup (MBZ) unter Verwendung des StructureMappers und
CompatibilityCheckers.
"""

import os
import sys
import logging
from pathlib import Path

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import der benötigten Module
from shared.utils.ilias.analyzer import IliasAnalyzer
from shared.utils.ilias.moodle_converter import MoodleConverter


def main():
    """Hauptfunktion für die Demo-Konvertierung."""
    
    # Bestimme das ILIAS Export-Verzeichnis
    project_root = Path(__file__).parent
    ilias_export_dir = project_root / 'dummy_files' / 'ilias_kurs'
    
    if not ilias_export_dir.exists():
        logger.error(f"ILIAS Export-Verzeichnis nicht gefunden: {ilias_export_dir}")
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("ILIAS zu Moodle Konvertierung - Demo")
    logger.info("=" * 80)
    
    # Schritt 1: ILIAS-Kurs analysieren
    logger.info("\n[1/4] Analysiere ILIAS-Kurs...")
    logger.info(f"Export-Verzeichnis: {ilias_export_dir}")
    
    analyzer = IliasAnalyzer(str(ilias_export_dir))
    success = analyzer.analyze()
    
    if not success:
        logger.error("Fehler beim Analysieren des ILIAS-Kurses")
        sys.exit(1)
    
    logger.info(f"✓ Kurs-Titel: {analyzer.course_title}")
    logger.info(f"✓ Komponenten gefunden: {len(analyzer.components)}")
    logger.info(f"✓ Container-Struktur: {'Ja' if analyzer.container_structure else 'Nein'}")
    
    if analyzer.container_structure:
        logger.info(f"✓ Root-Container: {analyzer.container_structure.root_item.title} ({analyzer.container_structure.root_item.item_type})")
        logger.info(f"✓ Items in Hierarchie: {len(analyzer.container_structure.item_by_item_id)}")
    
    # Schritt 2: MoodleConverter initialisieren
    logger.info("\n[2/4] Initialisiere MoodleConverter...")
    converter = MoodleConverter(analyzer)
    logger.info(f"✓ StructureMapper aktiv: {converter.use_structure_mapper}")
    
    # Schritt 3: Structure-Mapping durchführen
    if analyzer.container_structure and converter.use_structure_mapper:
        logger.info("\n[3/4] Mappe ILIAS-Struktur zu Moodle-Struktur...")
        converter._map_structure()
        
        if converter.moodle_structure:
            logger.info(f"✓ Sections erstellt: {len(converter.moodle_structure.sections)}")
            
            # Zeige Sections und Activities
            for idx, section in enumerate(converter.moodle_structure.sections, 1):
                logger.info(f"  Section {idx}: {section.name}")
                logger.info(f"    - ID: {section.section_id}")
                logger.info(f"    - Aktivitäten: {len(section.activities)}")
                
                for act in section.activities:
                    logger.info(f"      • {act.title} ({act.module_name})")
            
            total_activities = sum(len(s.activities) for s in converter.moodle_structure.sections)
            logger.info(f"✓ Gesamt-Aktivitäten: {total_activities}")
        else:
            logger.warning("! Keine Moodle-Struktur erstellt")
    else:
        logger.info("\n[3/4] Nutze Fallback-Konvertierung (keine Container-Struktur)")
    
    # Schritt 4: Vollständige Konvertierung durchführen
    logger.info("\n[4/4] Erstelle Moodle-Backup (MBZ)...")
    
    try:
        mbz_path = converter.convert(generate_report=True)
        
        logger.info(f"✓ MBZ erstellt: {mbz_path}")
        mbz_size = os.path.getsize(mbz_path) / 1024  # in KB
        logger.info(f"  Dateigröße: {mbz_size:.2f} KB")
        
        # Prüfe Conversion-Report
        if converter.conversion_report:
            report_path = mbz_path.replace('.mbz', '_conversion_report.md')
            
            if os.path.exists(report_path):
                logger.info(f"✓ Conversion-Report erstellt: {report_path}")
                
                report = converter.conversion_report
                logger.info("\n" + "=" * 80)
                logger.info("CONVERSION REPORT - ZUSAMMENFASSUNG")
                logger.info("=" * 80)
                logger.info(f"Info-Meldungen: {len(report.info_issues)}")
                logger.info(f"Warnungen: {len(report.warning_issues)}")
                logger.info(f"Fehler: {len(report.error_issues)}")
                
                if report.warning_issues or report.error_issues:
                    logger.info("\nWichtige Hinweise:")
                    
                    for issue in report.error_issues[:3]:  # Zeige max. 3 Fehler
                        logger.warning(f"  ERROR: {issue.ilias_feature} - {issue.message}")
                    
                    for issue in report.warning_issues[:3]:  # Zeige max. 3 Warnungen
                        logger.warning(f"  WARN: {issue.ilias_feature} - {issue.message}")
                    
                    if len(report.error_issues) > 3 or len(report.warning_issues) > 3:
                        logger.info(f"\n  ... siehe {report_path} für vollständige Details")
        
        logger.info("\n" + "=" * 80)
        logger.info("KONVERTIERUNG ERFOLGREICH ABGESCHLOSSEN!")
        logger.info("=" * 80)
        logger.info(f"\nErstellte Dateien:")
        logger.info(f"  • Moodle-Backup: {mbz_path}")
        
        if converter.conversion_report:
            report_path = mbz_path.replace('.mbz', '_conversion_report.md')
            if os.path.exists(report_path):
                logger.info(f"  • Conversion-Report: {report_path}")
        
    except Exception as e:
        logger.error(f"Fehler bei der Konvertierung: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

