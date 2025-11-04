#!/usr/bin/env python3
"""
Interaktiver Test für eigene ILIAS-Kurse.
"""

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from shared.utils.ilias.analyzer import IliasAnalyzer
from shared.utils.ilias.moodle_converter import MoodleConverter


def test_ilias_export(export_path: str, output_dir: str = None):
    """
    Testet die Konvertierung eines ILIAS-Exports.
    
    Args:
        export_path: Pfad zum ILIAS Export-Verzeichnis
        output_dir: Optional - Ausgabeverzeichnis für die MBZ-Datei
    """
    export_path = Path(export_path).resolve()
    
    if not export_path.exists():
        logger.error(f"Export-Verzeichnis nicht gefunden: {export_path}")
        return False
    
    logger.info("=" * 80)
    logger.info(f"Teste ILIAS-Export: {export_path.name}")
    logger.info("=" * 80)
    
    # 1. Analyse
    logger.info("\n[1/3] Analysiere ILIAS-Export...")
    analyzer = IliasAnalyzer(str(export_path))
    
    if not analyzer.analyze():
        logger.error("❌ Fehler bei der Analyse")
        return False
    
    logger.info(f"✓ Kurs: {analyzer.course_title}")
    logger.info(f"✓ Komponenten: {len(analyzer.components)}")
    logger.info(f"✓ Container-Struktur: {'Ja' if analyzer.container_structure else 'Nein'}")
    
    if analyzer.container_structure:
        logger.info(f"  - Root: {analyzer.container_structure.root_item.title}")
        logger.info(f"  - Items: {len(analyzer.container_structure.item_by_item_id)}")
        logger.info(f"  - Typen: {analyzer.container_structure.type_count}")
    
    # 2. Konvertierung
    logger.info("\n[2/3] Konvertiere zu Moodle...")
    converter = MoodleConverter(analyzer)
    
    try:
        mbz_path = converter.convert(generate_report=True)
        logger.info(f"✓ MBZ erstellt: {mbz_path}")
        
        # Verschiebe MBZ wenn output_dir angegeben
        if output_dir:
            output_dir = Path(output_dir).resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
            
            import shutil
            mbz_name = Path(mbz_path).name
            new_mbz_path = output_dir / mbz_name
            shutil.move(mbz_path, new_mbz_path)
            logger.info(f"✓ MBZ verschoben nach: {new_mbz_path}")
            
            # Verschiebe Report
            report_path = str(mbz_path).replace('.mbz', '_conversion_report.md')
            if os.path.exists(report_path):
                new_report_path = output_dir / Path(report_path).name
                shutil.move(report_path, new_report_path)
                logger.info(f"✓ Report verschoben nach: {new_report_path}")
            
            mbz_path = new_mbz_path
        
        # 3. Report-Zusammenfassung
        if converter.conversion_report:
            logger.info("\n[3/3] Conversion-Report:")
            report = converter.conversion_report
            logger.info(f"  Info: {len(report.info_issues)}")
            logger.info(f"  Warnungen: {len(report.warning_issues)}")
            logger.info(f"  Fehler: {len(report.error_issues)}")
            
            if report.error_issues:
                logger.warning("\n⚠️  Kritische Fehler:")
                for issue in report.error_issues[:5]:
                    logger.warning(f"  - {issue.ilias_item}: {issue.message}")
            
            if report.warning_issues:
                logger.info("\nℹ️  Wichtige Warnungen:")
                for issue in report.warning_issues[:5]:
                    logger.info(f"  - {issue.ilias_item}: {issue.message}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ KONVERTIERUNG ERFOLGREICH")
        logger.info("=" * 80)
        logger.info(f"\nMBZ-Datei: {mbz_path}")
        logger.info(f"Größe: {os.path.getsize(mbz_path) / 1024:.2f} KB")
        
        if converter.moodle_structure:
            logger.info(f"\nStruktur:")
            logger.info(f"  - {len(converter.moodle_structure.sections)} Sections")
            total_acts = sum(len(s.activities) for s in converter.moodle_structure.sections)
            logger.info(f"  - {total_acts} Activities")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler bei der Konvertierung: {e}", exc_info=True)
        return False


def main():
    """Hauptfunktion."""
    if len(sys.argv) < 2:
        print("Usage: python test_own_course.py <ilias_export_dir> [output_dir]")
        print("\nBeispiel:")
        print("  python test_own_course.py ./my_ilias_export")
        print("  python test_own_course.py ./my_ilias_export ./output")
        sys.exit(1)
    
    export_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = test_ilias_export(export_path, output_dir)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

