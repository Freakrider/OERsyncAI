#!/usr/bin/env python3
"""
Test-Skript für die ILIAS-zu-Moodle-Konvertierung.

Testet die neue Container-Struktur-basierte Konvertierung.
"""

import sys
import os
from pathlib import Path

# Füge das Projekt-Root zum Path hinzu
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging
import json

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from shared.utils.ilias import IliasAnalyzer, MoodleConverter


def test_ilias_conversion():
    """Testet die Konvertierung eines ILIAS-Kurses."""
    
    # Pfad zum Test-ILIAS-Export
    ilias_export_path = os.path.join(project_root, 'dummy_files', 'ilias_kurs')
    
    if not os.path.exists(ilias_export_path):
        logger.error(f"ILIAS-Export-Verzeichnis nicht gefunden: {ilias_export_path}")
        return False
    
    logger.info(f"Teste ILIAS-Konvertierung mit: {ilias_export_path}")
    
    # 1. ILIAS-Analyse
    logger.info("=" * 80)
    logger.info("SCHRITT 1: ILIAS-Analyse")
    logger.info("=" * 80)
    
    analyzer = IliasAnalyzer(ilias_export_path)
    success = analyzer.analyze()
    
    if not success:
        logger.error("ILIAS-Analyse fehlgeschlagen!")
        return False
    
    logger.info(f"✓ ILIAS-Analyse erfolgreich")
    logger.info(f"  - Kurstitel: {analyzer.course_title}")
    logger.info(f"  - Module: {len(analyzer.modules)}")
    logger.info(f"  - Komponenten: {len(analyzer.components)}")
    logger.info(f"  - Container-Struktur vorhanden: {analyzer.container_structure is not None}")
    
    # Details zur Container-Struktur
    if analyzer.container_structure:
        logger.info("\n📦 Container-Struktur Details:")
        logger.info(f"  - Root-Item: {analyzer.container_structure.root_item.title}")
        logger.info(f"  - Root-Typ: {analyzer.container_structure.root_item.item_type}")
        logger.info(f"  - Anzahl Items gesamt: {len(analyzer.container_structure.item_by_item_id)}")
        logger.info(f"  - Direkte Kinder: {len(analyzer.container_structure.root_item.children)}")
        
        logger.info("\n  Kinder des Root-Items:")
        for i, child in enumerate(analyzer.container_structure.root_item.children, 1):
            logger.info(f"    {i}. {child.title} ({child.item_type}, ID={child.item_id}, RefId={child.ref_id})")
            if child.children:
                logger.info(f"       └─ {len(child.children)} Unterpunkte")
    else:
        logger.warning("⚠️  Keine Container-Struktur gefunden - alte Logik wird verwendet!")
    
    # 2. Moodle-Konvertierung
    logger.info("\n" + "=" * 80)
    logger.info("SCHRITT 2: Moodle-Konvertierung")
    logger.info("=" * 80)
    
    converter = MoodleConverter(analyzer)
    
    # Prüfe, ob neue Logik aktiviert wird
    if converter.use_structure_mapper and analyzer.container_structure:
        logger.info("✓ Neue Struktur-Mapper-Logik wird verwendet")
    else:
        logger.warning("⚠️  Alte Fallback-Logik wird verwendet")
    
    try:
        mbz_path = converter.convert(generate_report=True)
        logger.info(f"✓ MBZ-Datei erstellt: {mbz_path}")
    except Exception as e:
        logger.exception(f"✗ Konvertierung fehlgeschlagen: {e}")
        return False
    
    # 3. Überprüfung der Moodle-Struktur
    if converter.moodle_structure:
        logger.info("\n" + "=" * 80)
        logger.info("SCHRITT 3: Moodle-Struktur-Überprüfung")
        logger.info("=" * 80)
        
        structure = converter.moodle_structure
        
        logger.info(f"✓ Moodle-Struktur erstellt")
        logger.info(f"  - Kurstitel: {structure.course_title}")
        logger.info(f"  - Anzahl Sections: {len(structure.sections)}")
        logger.info(f"  - Anzahl Activities gesamt: {sum(len(s.activities) for s in structure.sections)}")
        logger.info(f"  - Warnungen: {len(structure.warnings)}")
        
        logger.info("\n📑 Sections:")
        for section in structure.sections:
            logger.info(f"\n  Section {section.section_id}: {section.name}")
            logger.info(f"    - Nummer: {section.number}")
            logger.info(f"    - Sichtbar: {section.visible}")
            logger.info(f"    - Activities: {len(section.activities)}")
            
            if section.activities:
                logger.info(f"    - Activity-Details:")
                for activity in section.activities:
                    indent_marker = "  " * activity.indent if activity.indent > 0 else ""
                    logger.info(f"      {indent_marker}└─ {activity.title} ({activity.module_name}, indent={activity.indent})")
                    if activity.ilias_type:
                        logger.info(f"         {indent_marker}   ILIAS-Typ: {activity.ilias_type}")
        
        if structure.warnings:
            logger.info("\n⚠️  Warnungen:")
            for warning in structure.warnings:
                logger.info(f"  - {warning}")
    else:
        logger.warning("⚠️  Keine Moodle-Struktur verfügbar (alte Logik)")
    
    # 4. Conversion-Report
    if converter.conversion_report:
        logger.info("\n" + "=" * 80)
        logger.info("SCHRITT 4: Conversion-Report")
        logger.info("=" * 80)
        
        report = converter.conversion_report
        logger.info(f"✓ Conversion-Report generiert")
        logger.info(f"  - Info-Meldungen: {len(report.info_issues)}")
        logger.info(f"  - Warnungen: {len(report.warning_issues)}")
        logger.info(f"  - Fehler: {len(report.error_issues)}")
        
        if report.warning_issues:
            logger.info(f"\n⚠️  Erste 5 Warnungen:")
            for issue in report.warning_issues[:5]:
                logger.info(f"  - {issue.ilias_item} ({issue.ilias_feature}): {issue.message}")
        
        if report.error_issues:
            logger.info(f"\n✗ Erste 5 Fehler:")
            for issue in report.error_issues[:5]:
                logger.info(f"  - {issue.ilias_item} ({issue.ilias_feature}): {issue.message}")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ TEST ERFOLGREICH ABGESCHLOSSEN")
    logger.info("=" * 80)
    
    return True


if __name__ == "__main__":
    success = test_ilias_conversion()
    sys.exit(0 if success else 1)

