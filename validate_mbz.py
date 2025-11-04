#!/usr/bin/env python3
"""
Validiert eine erzeugte MBZ-Datei.
"""

import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def validate_mbz(mbz_path: str) -> bool:
    """
    Validiert eine MBZ-Datei.
    
    Args:
        mbz_path: Pfad zur MBZ-Datei
        
    Returns:
        True wenn valide, sonst False
    """
    mbz_path = Path(mbz_path).resolve()
    
    if not mbz_path.exists():
        logger.error(f"MBZ-Datei nicht gefunden: {mbz_path}")
        return False
    
    if not mbz_path.suffix == '.mbz':
        logger.error(f"Keine MBZ-Datei: {mbz_path}")
        return False
    
    logger.info("=" * 80)
    logger.info(f"Validiere MBZ: {mbz_path.name}")
    logger.info("=" * 80)
    
    try:
        with zipfile.ZipFile(mbz_path, 'r') as zip_ref:
            files = zip_ref.namelist()
            logger.info(f"\n✓ ZIP-Archiv erfolgreich geöffnet")
            logger.info(f"  Dateien im Archiv: {len(files)}")
            
            # 1. Prüfe Pflicht-Dateien
            logger.info("\n[1] Prüfe Pflicht-Dateien...")
            required_files = [
                'moodle_backup.xml',
                'files.xml',
            ]
            
            required_dirs = [
                'course/',
                'sections/',
            ]
            
            all_good = True
            
            for req_file in required_files:
                if req_file in files:
                    logger.info(f"  ✓ {req_file}")
                else:
                    logger.error(f"  ✗ {req_file} fehlt!")
                    all_good = False
            
            for req_dir in required_dirs:
                if any(f.startswith(req_dir) for f in files):
                    logger.info(f"  ✓ {req_dir}")
                else:
                    logger.warning(f"  ⚠ {req_dir} fehlt!")
            
            # 2. Validiere moodle_backup.xml
            logger.info("\n[2] Validiere moodle_backup.xml...")
            try:
                xml_content = zip_ref.read('moodle_backup.xml')
                root = ET.fromstring(xml_content)
                
                if root.tag != 'moodle_backup':
                    logger.error(f"  ✗ Falsches Root-Element: {root.tag}")
                    all_good = False
                else:
                    logger.info(f"  ✓ Root-Element korrekt")
                
                # Prüfe Information
                info = root.find('information')
                if info is None:
                    logger.error("  ✗ Kein 'information' Element")
                    all_good = False
                else:
                    logger.info("  ✓ Information-Element vorhanden")
                    
                    # Prüfe Course-Name
                    course_name = info.find('.//original_course_fullname')
                    if course_name is not None:
                        logger.info(f"  ✓ Kurs-Name: {course_name.text}")
                    
                    # Prüfe Contents
                    contents = info.find('contents')
                    if contents is not None:
                        activities = contents.find('activities')
                        sections = contents.find('sections')
                        
                        if activities is not None:
                            activity_list = list(activities)
                            logger.info(f"  ✓ Activities: {len(activity_list)}")
                            
                            # Zeige erste 3 Activities
                            for i, act in enumerate(activity_list[:3], 1):
                                title = act.find('title')
                                modname = act.find('modulename')
                                if title is not None and modname is not None:
                                    logger.info(f"    {i}. {title.text} ({modname.text})")
                        
                        if sections is not None:
                            section_list = list(sections)
                            logger.info(f"  ✓ Sections: {len(section_list)}")
                            
                            # Zeige erste 3 Sections
                            for i, sec in enumerate(section_list[:3], 1):
                                title = sec.find('title')
                                if title is not None:
                                    logger.info(f"    {i}. {title.text}")
                
            except ET.ParseError as e:
                logger.error(f"  ✗ XML-Parse-Fehler: {e}")
                all_good = False
            
            # 3. Prüfe Activities
            logger.info("\n[3] Prüfe Activities...")
            activity_dirs = [f for f in files if f.startswith('activities/') and f.endswith('/')]
            activity_dirs = list(set(['/'.join(f.split('/')[:2]) for f in files if f.startswith('activities/') and '/' in f[11:]]))
            
            logger.info(f"  Activity-Verzeichnisse: {len(activity_dirs)}")
            
            for act_dir in activity_dirs[:5]:  # Zeige erste 5
                act_files = [f for f in files if f.startswith(act_dir + '/')]
                has_activity_xml = any(f.endswith('activity.xml') for f in act_files)
                has_module_xml = any(f.endswith('module.xml') for f in act_files)
                
                status = "✓" if has_activity_xml and has_module_xml else "⚠"
                logger.info(f"  {status} {act_dir}: {len(act_files)} Dateien")
            
            # 4. Prüfe Sections
            logger.info("\n[4] Prüfe Sections...")
            section_dirs = list(set(['/'.join(f.split('/')[:2]) for f in files if f.startswith('sections/') and '/' in f[9:]]))
            
            logger.info(f"  Section-Verzeichnisse: {len(section_dirs)}")
            
            for sec_dir in section_dirs[:5]:  # Zeige erste 5
                sec_files = [f for f in files if f.startswith(sec_dir + '/')]
                has_section_xml = any(f.endswith('section.xml') for f in sec_files)
                
                status = "✓" if has_section_xml else "⚠"
                logger.info(f"  {status} {sec_dir}: {len(sec_files)} Dateien")
            
            # Zusammenfassung
            logger.info("\n" + "=" * 80)
            if all_good:
                logger.info("✅ MBZ-Datei ist VALIDE")
                logger.info("=" * 80)
                logger.info("\n💡 Nächste Schritte:")
                logger.info("  1. Importiere die MBZ-Datei in Moodle")
                logger.info("  2. Gehe zu: Site Administration > Courses > Restore course")
                logger.info("  3. Lade die MBZ-Datei hoch")
                logger.info("  4. Folge dem Restore-Wizard")
                return True
            else:
                logger.warning("⚠️  MBZ-Datei hat PROBLEME")
                logger.info("=" * 80)
                return False
                
    except zipfile.BadZipFile:
        logger.error("❌ Ungültige ZIP-Datei")
        return False
    except Exception as e:
        logger.error(f"❌ Fehler bei der Validierung: {e}", exc_info=True)
        return False


def main():
    """Hauptfunktion."""
    if len(sys.argv) < 2:
        print("Usage: python validate_mbz.py <mbz_file>")
        print("\nBeispiel:")
        print("  python validate_mbz.py ./output/my_course.mbz")
        sys.exit(1)
    
    mbz_path = sys.argv[1]
    success = validate_mbz(mbz_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

