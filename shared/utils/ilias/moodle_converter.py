"""
Konvertiert ILIAS-Kursdaten in ein Moodle-Backup-Format.
"""

import os
import tempfile
import zipfile
import shutil
import logging
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class MoodleConverter:
    """
    Konvertiert ILIAS-Kursdaten in ein Moodle-Backup-Format.
    """
    
    def __init__(self, analyzer):
        """
        Initialisiert den MoodleConverter.
        
        Args:
            analyzer: Eine Instanz von IliasAnalyzer mit analysierten Kursdaten
        """
        self.analyzer = analyzer
        self.temp_dir = tempfile.mkdtemp()
        self.moodle_dir = os.path.join(self.temp_dir, 'moodle_backup')
        os.makedirs(self.moodle_dir, exist_ok=True)
        
        # Neue: StructureMapper und CompatibilityChecker
        self.moodle_structure = None
        self.conversion_report = None
        self.use_structure_mapper = True  # Flag zum Aktivieren des neuen Mappings
        
    def _write_xml_file(self, tree, filepath):
        """
        Schreibt eine XML-Datei mit korrekter XML-Deklaration.
        
        Args:
            tree: ElementTree-Objekt
            filepath: Pfad, wohin die XML-Datei geschrieben werden soll
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            tree.write(f, encoding='unicode', xml_declaration=False)
        
    def convert(self, generate_report: bool = True) -> str:
        """
        Konvertiert die ILIAS-Kursdaten in ein Moodle-Backup-Format.
        
        Args:
            generate_report: Ob ein Conversion-Report generiert werden soll
            
        Returns:
            Pfad zur erstellten MBZ-Datei
        """
        logger.info(f"Starte Konvertierung zu Moodle-Backup für Kurs: {self.analyzer.course_title}")
        
        # NEU: Nutze StructureMapper wenn Container-Struktur verfügbar
        if self.use_structure_mapper and self.analyzer.container_structure:
            logger.info("Nutze StructureMapper für 1:1-Konvertierung")
            self._map_structure()
            
            # Generiere Conversion-Report
            if generate_report:
                self._generate_conversion_report()
        
        # Erstelle die Moodle-Backup-Struktur
        self._create_backup_structure()
        
        # Erstelle die Moodle-Backup-Dateien
        self._create_backup_files()
        
        # Erstelle die MBZ-Datei
        mbz_path = self._create_mbz_file()
        
        # Speichere Report wenn vorhanden
        if self.conversion_report and generate_report:
            self._save_conversion_report(mbz_path)
        
        return mbz_path
    
    def _map_structure(self):
        """Mappt ILIAS-Struktur zu Moodle-Struktur mit StructureMapper."""
        from .structure_mapper import StructureMapper
        from .itemgroup_resolver import ItemGroupResolver
        
        logger.info("Mappe ILIAS-Container-Struktur zu Moodle-Struktur")
        
        # Erstelle ItemGroupResolver
        itemgroup_resolver = ItemGroupResolver(
            container_structure=self.analyzer.container_structure,
            components=self.analyzer.components
        )
        
        # Erstelle StructureMapper
        mapper = StructureMapper(
            container_structure=self.analyzer.container_structure,
            itemgroup_resolver=itemgroup_resolver,
            components=self.analyzer.components  # NEU: Components für ItemGroup-Resolution
        )
        
        # Führe Mapping durch
        self.moodle_structure = mapper.map_to_moodle()
        
        logger.info(f"Mapping abgeschlossen: {len(self.moodle_structure.sections)} Sections, "
                   f"{sum(len(s.activities) for s in self.moodle_structure.sections)} Activities")
    
    def _generate_conversion_report(self):
        """Generiert einen Conversion-Report."""
        from .compatibility_checker import CompatibilityChecker
        
        if not self.moodle_structure:
            logger.warning("Keine Moodle-Struktur verfügbar für Report-Generierung")
            return
        
        logger.info("Generiere Conversion-Report")
        
        checker = CompatibilityChecker()
        self.conversion_report = checker.generate_report(
            self.moodle_structure,
            self.analyzer.container_structure
        )
        
        logger.info(f"Report generiert: {len(self.conversion_report.warning_issues)} Warnungen, "
                   f"{len(self.conversion_report.error_issues)} Fehler")
    
    def _save_conversion_report(self, mbz_path: str):
        """Speichert den Conversion-Report als Markdown-Datei."""
        if not self.conversion_report:
            return
        
        # Bestimme Report-Pfad (neben der MBZ-Datei)
        report_path = mbz_path.replace('.mbz', '_conversion_report.md')
        
        try:
            markdown = self.conversion_report.to_markdown()
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            logger.info(f"Conversion-Report gespeichert: {report_path}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Reports: {e}")
    
    def _create_backup_structure(self):
        """Erstellt die Verzeichnisstruktur für das Moodle-Backup."""
        # Hauptverzeichnisse
        os.makedirs(os.path.join(self.moodle_dir, 'activities'), exist_ok=True)
        os.makedirs(os.path.join(self.moodle_dir, 'course'), exist_ok=True)
        os.makedirs(os.path.join(self.moodle_dir, 'sections'), exist_ok=True)
        
        # Aktivitätsverzeichnisse für verschiedene Typen
        activity_types = ['resource', 'folder', 'page', 'url', 'forum', 'quiz', 'assign', 'wiki']
        for activity_type in activity_types:
            os.makedirs(os.path.join(self.moodle_dir, 'activities', activity_type), exist_ok=True)
    
    def _create_backup_files(self):
        """Erstellt die XML-Dateien für das Moodle-Backup."""
        # Erstelle moodle_backup.xml
        self._create_moodle_backup_xml()
        
        # Erstelle course/course.xml
        self._create_course_xml()
        
        # Erstelle course/sections.xml
        self._create_sections_xml()
        
        # Erstelle Aktivitäten-XMLs
        self._create_activity_xmls()
        
        # Erstelle files.xml
        self._create_files_xml()
        
        # Erstelle weitere erforderliche XML-Dateien
        self._create_users_xml()
        self._create_roles_xml()
        self._create_scales_xml()
        self._create_outcomes_xml()
        self._create_questions_xml()
        self._create_groups_xml()
        self._create_gradebook_xml()
        self._create_grade_history_xml()
        self._create_completion_xml()
        self._create_badges_xml()
        
        # Erstelle Abschnittsverzeichnisse und XML-Dateien
        self._create_section_files()
    
    def _create_moodle_backup_xml(self):
        """Erstellt die moodle_backup.xml-Datei."""
        root = ET.Element('moodle_backup')
        
        # Informationen
        info = ET.SubElement(root, 'information')
        
        # Name
        name = ET.SubElement(info, 'n')
        backup_name = f"backup-moodle2-course-{self.analyzer.course_title.replace(' ', '-')}-{datetime.now().strftime('%Y%m%d-%H%M')}.mbz"
        name.text = backup_name
        
        # Moodle-Version
        moodle_version = ET.SubElement(info, 'moodle_version')
        moodle_version.text = '2024100701.05'
        
        # Moodle-Release
        moodle_release = ET.SubElement(info, 'moodle_release')
        moodle_release.text = '4.5.1+ (Build: 20250109)'
        
        # Backup-Version
        backup_version = ET.SubElement(info, 'backup_version')
        backup_version.text = '2010072300'
        
        # Backup-Release
        backup_release = ET.SubElement(info, 'backup_release')
        backup_release.text = '2.0'
        
        # Backup-Datum (Unix-Timestamp)
        backup_date = ET.SubElement(info, 'backup_date')
        backup_date.text = str(int(datetime.now().timestamp()))
        
        # Weitere erforderliche Felder
        mnet_remoteusers = ET.SubElement(info, 'mnet_remoteusers')
        mnet_remoteusers.text = '0'
        
        include_files = ET.SubElement(info, 'include_files')
        include_files.text = '1'
        
        include_file_references = ET.SubElement(info, 'include_file_references_to_external_content')
        include_file_references.text = '0'
        
        original_wwwroot = ET.SubElement(info, 'original_wwwroot')
        original_wwwroot.text = self.analyzer.installation_url or 'http://ilias-export-converter'
        
        original_site_identifier_hash = ET.SubElement(info, 'original_site_identifier_hash')
        import hashlib
        site_hash = hashlib.md5(original_wwwroot.text.encode()).hexdigest()
        original_site_identifier_hash.text = site_hash
        
        original_course_id = ET.SubElement(info, 'original_course_id')
        original_course_id.text = '1'
        
        original_course_format = ET.SubElement(info, 'original_course_format')
        original_course_format.text = 'topics'
        
        original_course_fullname = ET.SubElement(info, 'original_course_fullname')
        original_course_fullname.text = self.analyzer.course_title
        
        original_course_shortname = ET.SubElement(info, 'original_course_shortname')
        original_course_shortname.text = self.analyzer.course_title[:20]
        
        # Kursstartdatum (aktuelles Datum)
        original_course_startdate = ET.SubElement(info, 'original_course_startdate')
        original_course_startdate.text = str(int(datetime.now().timestamp()))
        
        # Kursendedatum (1 Jahr später)
        original_course_enddate = ET.SubElement(info, 'original_course_enddate')
        end_date = datetime.now()
        end_date = end_date.replace(year=end_date.year + 1)
        original_course_enddate.text = str(int(end_date.timestamp()))
        
        original_course_contextid = ET.SubElement(info, 'original_course_contextid')
        original_course_contextid.text = '20'
        
        original_system_contextid = ET.SubElement(info, 'original_system_contextid')
        original_system_contextid.text = '1'
        
        # Details
        details = ET.SubElement(info, 'details')
        detail = ET.SubElement(details, 'detail')
        detail.set('backup_id', hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest())
        
        type_elem = ET.SubElement(detail, 'type')
        type_elem.text = 'course'
        
        format_elem = ET.SubElement(detail, 'format')
        format_elem.text = 'moodle2'
        
        interactive = ET.SubElement(detail, 'interactive')
        interactive.text = '1'
        
        mode = ET.SubElement(detail, 'mode')
        mode.text = '70'
        
        execution = ET.SubElement(detail, 'execution')
        execution.text = '2'
        
        executiontime = ET.SubElement(detail, 'executiontime')
        executiontime.text = '0'
        
        # Inhalte
        contents = ET.SubElement(info, 'contents')
        
        # Aktivitäten
        activities = ET.SubElement(contents, 'activities')
        
        # NEU: Nutze MoodleStructure wenn verfügbar, sonst alte Logik
        if self.moodle_structure:
            # Neue Struktur-basierte Generierung
            for section in self.moodle_structure.sections:
                for activity in section.activities:
                    act_elem = ET.SubElement(activities, 'activity')
                    
                    moduleid = ET.SubElement(act_elem, 'moduleid')
                    moduleid.text = str(activity.module_id)
                    
                    sectionid = ET.SubElement(act_elem, 'sectionid')
                    sectionid.text = str(section.section_id)
                    
                    modulename = ET.SubElement(act_elem, 'modulename')
                    modulename.text = activity.module_name
                    
                    title = ET.SubElement(act_elem, 'title')
                    title.text = activity.title
                    
                    directory = ET.SubElement(act_elem, 'directory')
                    directory.text = f"activities/{activity.module_name}_{activity.module_id}"
                    
                    insubsection = ET.SubElement(act_elem, 'insubsection')
        else:
            # ALT: Alte Logik für Fallback
            activity_id = 1
            for module_index, module in enumerate(self.analyzer.modules, 1):
                for item_index, item in enumerate(module.items, 1):
                    item_type = item.get('type', 'unknown')
                    item_title = item.get('title', 'Unbekanntes Item')
                    
                    # Bestimme den Moodle-Aktivitätstyp
                    moodle_type = self._get_moodle_type(item_type)
                    
                    activity = ET.SubElement(activities, 'activity')
                    
                    moduleid = ET.SubElement(activity, 'moduleid')
                    moduleid.text = str(activity_id)
                    
                    sectionid = ET.SubElement(activity, 'sectionid')
                    sectionid.text = str(module_index)
                    
                    modulename = ET.SubElement(activity, 'modulename')
                    modulename.text = moodle_type
                    
                    title = ET.SubElement(activity, 'title')
                    title.text = item_title
                    
                    directory = ET.SubElement(activity, 'directory')
                    directory.text = f"activities/{moodle_type}_{activity_id}"
                    
                    insubsection = ET.SubElement(activity, 'insubsection')
                    
                    activity_id += 1
        
        # Abschnitte
        sections = ET.SubElement(contents, 'sections')
        
        # NEU: Nutze MoodleStructure wenn verfügbar
        if self.moodle_structure:
            # Neue Struktur-basierte Generierung
            for moodle_section in self.moodle_structure.sections:
                section = ET.SubElement(sections, 'section')
                
                sectionid = ET.SubElement(section, 'sectionid')
                sectionid.text = str(moodle_section.section_id)
                
                title = ET.SubElement(section, 'title')
                title.text = moodle_section.name
                
                directory = ET.SubElement(section, 'directory')
                directory.text = f"sections/section_{moodle_section.section_id}"
                
                parentcmid = ET.SubElement(section, 'parentcmid')
                
                modname = ET.SubElement(section, 'modname')
        else:
            # ALT: Alte Logik für Fallback
            # Allgemeiner Abschnitt
            section = ET.SubElement(sections, 'section')
            
            sectionid = ET.SubElement(section, 'sectionid')
            sectionid.text = '0'
            
            title = ET.SubElement(section, 'title')
            title.text = '0'
            
            directory = ET.SubElement(section, 'directory')
            directory.text = 'sections/section_0'
            
            parentcmid = ET.SubElement(section, 'parentcmid')
            
            modname = ET.SubElement(section, 'modname')
            
            # Module als Abschnitte
            for i, module in enumerate(self.analyzer.modules, 1):
                section = ET.SubElement(sections, 'section')
                
                sectionid = ET.SubElement(section, 'sectionid')
                sectionid.text = str(i)
                
                title = ET.SubElement(section, 'title')
                title.text = str(i)
                
                directory = ET.SubElement(section, 'directory')
                directory.text = f"sections/section_{i}"
                
                parentcmid = ET.SubElement(section, 'parentcmid')
                
                modname = ET.SubElement(section, 'modname')
        
        # Kurs
        course = ET.SubElement(contents, 'course')
        
        courseid = ET.SubElement(course, 'courseid')
        courseid.text = '1'
        
        title = ET.SubElement(course, 'title')
        title.text = self.analyzer.course_title
        
        directory = ET.SubElement(course, 'directory')
        directory.text = 'course'
        
        # Einstellungen
        settings = ET.SubElement(info, 'settings')
        
        # Root-Einstellungen
        self._add_setting(settings, 'root', 'filename', backup_name)
        self._add_setting(settings, 'root', 'users', '1')
        self._add_setting(settings, 'root', 'anonymize', '1')
        self._add_setting(settings, 'root', 'role_assignments', '1')
        self._add_setting(settings, 'root', 'activities', '1')
        self._add_setting(settings, 'root', 'blocks', '1')
        self._add_setting(settings, 'root', 'files', '1')
        self._add_setting(settings, 'root', 'filters', '1')
        self._add_setting(settings, 'root', 'comments', '1')
        self._add_setting(settings, 'root', 'badges', '1')
        self._add_setting(settings, 'root', 'calendarevents', '1')
        self._add_setting(settings, 'root', 'userscompletion', '1')
        self._add_setting(settings, 'root', 'logs', '1')
        self._add_setting(settings, 'root', 'grade_histories', '1')
        self._add_setting(settings, 'root', 'questionbank', '1')
        self._add_setting(settings, 'root', 'groups', '1')
        self._add_setting(settings, 'root', 'competencies', '1')
        self._add_setting(settings, 'root', 'customfield', '1')
        self._add_setting(settings, 'root', 'contentbankcontent', '1')
        self._add_setting(settings, 'root', 'xapistate', '1')
        self._add_setting(settings, 'root', 'legacyfiles', '1')
        
        # NEU: Nutze MoodleStructure wenn verfügbar
        if self.moodle_structure:
            # Abschnittseinstellungen (neue Struktur)
            for moodle_section in self.moodle_structure.sections:
                section_id = moodle_section.section_id
                self._add_setting(settings, 'section', f'section_{section_id}_included', '1', f'section_{section_id}')
                self._add_setting(settings, 'section', f'section_{section_id}_userinfo', '0', f'section_{section_id}')
            
            # Aktivitätseinstellungen (neue Struktur)
            for moodle_section in self.moodle_structure.sections:
                for activity in moodle_section.activities:
                    activity_name = f"{activity.module_name}_{activity.activity_id}"
                    self._add_setting(settings, 'activity', f'{activity_name}_included', '1', activity_name)
                    self._add_setting(settings, 'activity', f'{activity_name}_userinfo', '0', activity_name)
        else:
            # ALT: Alte Logik für Fallback
            # Abschnittseinstellungen
            for i in range(len(self.analyzer.modules) + 1):
                section_id = i
                self._add_setting(settings, 'section', f'section_{section_id}_included', '1', f'section_{section_id}')
                self._add_setting(settings, 'section', f'section_{section_id}_userinfo', '1', f'section_{section_id}')
            
            # Aktivitätseinstellungen
            activity_id = 1
            for module in self.analyzer.modules:
                for item in module.items:
                    item_type = item.get('type', 'unknown')
                    moodle_type = self._get_moodle_type(item_type)
                    
                    self._add_setting(settings, 'activity', f'{moodle_type}_{activity_id}_included', '1', f'{moodle_type}_{activity_id}')
                    self._add_setting(settings, 'activity', f'{moodle_type}_{activity_id}_userinfo', '1', f'{moodle_type}_{activity_id}')
                    
                    activity_id += 1
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        
        # Manuelles Schreiben der XML-Datei mit korrekter XML-Deklaration
        xml_path = os.path.join(self.moodle_dir, 'moodle_backup.xml')
        self._write_xml_file(tree, xml_path)
    
    def _add_setting(self, parent, level, name, value, section_or_activity=None):
        """Fügt eine Einstellung zum settings-Element hinzu."""
        setting = ET.SubElement(parent, 'setting')
        
        level_elem = ET.SubElement(setting, 'level')
        level_elem.text = level
        
        if section_or_activity:
            section_or_activity_elem = ET.SubElement(setting, level)
            section_or_activity_elem.text = section_or_activity
        
        name_elem = ET.SubElement(setting, 'n')
        name_elem.text = name
        
        value_elem = ET.SubElement(setting, 'value')
        value_elem.text = value
    
    def _get_moodle_type(self, ilias_type):
        """Konvertiert einen ILIAS-Typ in einen Moodle-Typ."""
        # Aktivitäten-Mapping für die Konvertierung
        activity_mapping = {
            'file': 'resource',
            'documents': 'resource',
            'presentations': 'resource',
            'forum': 'forum',
            'test': 'quiz',
            'exercise': 'assign',
            'wiki': 'wiki',
            'mediacast': 'resource',
            'itemgroup': 'folder'
        }
        
        return activity_mapping.get(ilias_type, 'resource')
    
    def _create_course_xml(self):
        """Erstellt die course/course.xml-Datei."""
        root = ET.Element('course')
        root.set('id', '1')
        
        # Kurs-ID (simuliert)
        course_id = ET.SubElement(root, 'id')
        course_id.text = '1'
        
        # Kategorie
        category = ET.SubElement(root, 'category')
        category.text = '1'
        
        # Vollständiger Name
        fullname = ET.SubElement(root, 'fullname')
        fullname.text = self.analyzer.course_title
        
        # Kurzname
        shortname = ET.SubElement(root, 'shortname')
        shortname.text = self.analyzer.course_title[:20]  # Begrenzt auf 20 Zeichen
        
        # Zusammenfassung
        summary = ET.SubElement(root, 'summary')
        summary.text = f"Aus ILIAS importierter Kurs: {self.analyzer.course_title}"
        
        # Zusammenfassungsformat
        summaryformat = ET.SubElement(root, 'summaryformat')
        summaryformat.text = '1'
        
        # Format
        format = ET.SubElement(root, 'format')
        format.text = 'topics'
        
        # Showgrades
        showgrades = ET.SubElement(root, 'showgrades')
        showgrades.text = '1'
        
        # Newsitems
        newsitems = ET.SubElement(root, 'newsitems')
        newsitems.text = '5'
        
        # Startdate
        startdate = ET.SubElement(root, 'startdate')
        startdate.text = str(int(datetime.now().timestamp()))
        
        # Enddate
        enddate = ET.SubElement(root, 'enddate')
        end_date = datetime.now()
        end_date = end_date.replace(year=end_date.year + 1)
        enddate.text = str(int(end_date.timestamp()))
        
        # Marker
        marker = ET.SubElement(root, 'marker')
        marker.text = '0'
        
        # Maxbytes
        maxbytes = ET.SubElement(root, 'maxbytes')
        maxbytes.text = '0'
        
        # Legacyfiles
        legacyfiles = ET.SubElement(root, 'legacyfiles')
        legacyfiles.text = '0'
        
        # Showreports
        showreports = ET.SubElement(root, 'showreports')
        showreports.text = '0'
        
        # Visible
        visible = ET.SubElement(root, 'visible')
        visible.text = '1'
        
        # Groupmode
        groupmode = ET.SubElement(root, 'groupmode')
        groupmode.text = '0'
        
        # Groupmodeforce
        groupmodeforce = ET.SubElement(root, 'groupmodeforce')
        groupmodeforce.text = '0'
        
        # Defaultgroupingid
        defaultgroupingid = ET.SubElement(root, 'defaultgroupingid')
        defaultgroupingid.text = '0'
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'course', 'course.xml'))
        
        # Erstelle weitere Dateien im course-Verzeichnis
        self._create_course_additional_files()
    
    def _create_course_additional_files(self):
        """Erstellt zusätzliche XML-Dateien für den Kurs."""
        course_dir = os.path.join(self.moodle_dir, 'course')
        
        # Filters
        root = ET.Element('filters')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(course_dir, 'filters.xml'))
        
        # Comments
        root = ET.Element('comments')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(course_dir, 'comments.xml'))
        
        # Completiondefaults
        root = ET.Element('course_completion_defaults')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(course_dir, 'completiondefaults.xml'))
        
        # Contentbank
        root = ET.Element('contentbank')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(course_dir, 'contentbank.xml'))
        
        # Logstores
        root = ET.Element('logstores')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(course_dir, 'logstores.xml'))
        
        # Competencies
        root = ET.Element('competencies')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(course_dir, 'competencies.xml'))
        
        # Loglastaccess
        root = ET.Element('loglastaccesses')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(course_dir, 'loglastaccess.xml'))
        
        # Roles
        root = ET.Element('roles')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(course_dir, 'roles.xml'))
        
        # Calendar
        root = ET.Element('calendar')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(course_dir, 'calendar.xml'))
        
        # Enrolments
        root = ET.Element('enrolments')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(course_dir, 'enrolments.xml'))
        
        # Logs
        root = ET.Element('logs')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(course_dir, 'logs.xml'))
        
        # Inforef
        root = ET.Element('inforef')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(course_dir, 'inforef.xml'))
    
    def _create_sections_xml(self):
        """Erstellt die course/sections.xml-Datei."""
        root = ET.Element('sections')
        
        # NEU: Nutze MoodleStructure wenn verfügbar
        if self.moodle_structure:
            # Neue Struktur-basierte Generierung
            for moodle_section in self.moodle_structure.sections:
                section = ET.SubElement(root, 'section')
                
                section_id = ET.SubElement(section, 'id')
                section_id.text = str(moodle_section.section_id)
                
                section_number = ET.SubElement(section, 'number')
                section_number.text = str(moodle_section.number)
                
                section_name = ET.SubElement(section, 'name')
                section_name.text = moodle_section.name
                
                section_summary = ET.SubElement(section, 'summary')
                section_summary.text = moodle_section.summary
                
                # Activity-IDs als Sequence hinzufügen
                if moodle_section.activities:
                    sequence = ET.SubElement(section, 'sequence')
                    activity_ids = [str(activity.module_id) for activity in moodle_section.activities]
                    sequence.text = ','.join(activity_ids)
                else:
                    sequence = ET.SubElement(section, 'sequence')
                    sequence.text = ''
                
                visible = ET.SubElement(section, 'visible')
                visible.text = '1' if moodle_section.visible else '0'
                
                timemodified = ET.SubElement(section, 'timemodified')
                timemodified.text = str(int(datetime.now().timestamp()))
        else:
            # ALT: Alte Logik als Fallback
            # Allgemeiner Abschnitt
            section = ET.SubElement(root, 'section')
            
            section_id = ET.SubElement(section, 'id')
            section_id.text = '0'
            
            section_number = ET.SubElement(section, 'number')
            section_number.text = '0'
            
            section_name = ET.SubElement(section, 'name')
            section_name.text = 'Allgemein'
            
            section_summary = ET.SubElement(section, 'summary')
            section_summary.text = 'Allgemeiner Abschnitt'
            
            # Module als Abschnitte
            for i, module in enumerate(self.analyzer.modules, 1):
                section = ET.SubElement(root, 'section')
                
                section_id = ET.SubElement(section, 'id')
                section_id.text = str(i)
                
                section_number = ET.SubElement(section, 'number')
                section_number.text = str(i)
                
                section_name = ET.SubElement(section, 'name')
                section_name.text = module.title
                
                section_summary = ET.SubElement(section, 'summary')
                section_summary.text = getattr(module, 'description', '') or f"Abschnitt für {module.title}"
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'course', 'sections.xml'))
    
    def _create_activity_xmls(self):
        """Erstellt die XML-Dateien für die Aktivitäten."""
        # NEU: Nutze MoodleStructure wenn verfügbar
        if self.moodle_structure:
            # Neue Struktur-basierte Generierung
            for section in self.moodle_structure.sections:
                section_number = getattr(section, 'number', section.section_id)
                for activity in section.activities:
                    activity_dir_name = f"{activity.module_name}_{activity.module_id}"
                    activity_dir = os.path.join(self.moodle_dir, 'activities', activity_dir_name)
                    os.makedirs(activity_dir, exist_ok=True)

                    item = self._get_item_by_id(activity.ilias_id) if getattr(activity, 'ilias_id', None) else {}
                    title = self._resolve_activity_title(activity.title, item, activity.module_name, activity.module_id)
                    intro_text = self._resolve_activity_intro(activity.intro, item)

                    self._create_activity_xml(
                        activity_dir=activity_dir,
                        activity_id=activity.activity_id,
                        module_id=activity.module_id,
                        module_name=activity.module_name,
                        title=title,
                        section_id=section.section_id,
                        section_number=section_number,
                        visible=activity.visible,
                        intro=intro_text,
                        item=item
                    )

                    if activity.module_name == 'resource':
                        self._create_resource_xml(activity_dir, item, title, intro_text, activity.module_id, activity.activity_id, section_number, activity.visible)
                    elif activity.module_name == 'forum':
                        self._create_forum_xml(activity_dir, item, title, intro_text, activity.module_id, activity.activity_id, section_number, activity.visible)
                    elif activity.module_name == 'quiz':
                        self._create_quiz_xml(activity_dir, item, title, intro_text, activity.module_id, activity.activity_id, section_number, activity.visible)
                    elif activity.module_name == 'folder':
                        self._create_folder_xml(activity_dir, item, title, intro_text, activity.module_id, activity.activity_id, section_number, activity.visible)

                    self._create_inforef_xml(activity_dir)
                    self._create_grades_xml(activity_dir)
                    self._create_roles_xml_for_activity(activity_dir)
                    self._create_module_xml(
                        activity_dir,
                        module_id=activity.module_id,
                        module_name=activity.module_name,
                        section_id=section.section_id,
                        section_number=section_number,
                        instance_id=activity.activity_id,
                        visible=activity.visible
                    )
                    self._create_additional_activity_files(activity_dir)
        else:
            # ALT: Alte Logik für Fallback
            activity_id = 1
            
            # Für jedes Modul
            for module_index, module in enumerate(self.analyzer.modules, 1):
                # Für jedes Item im Modul
                for item_index, item in enumerate(module.items, 1):
                    item_type = item.get('type', 'unknown')
                    item_title = item.get('title', 'Unbekanntes Item')
                    
                    # Bestimme den Moodle-Aktivitätstyp
                    moodle_type = self._get_moodle_type(item_type)
                    
                    # Erstelle das Aktivitätsverzeichnis
                    activity_dir = os.path.join(self.moodle_dir, 'activities', f"{moodle_type}_{activity_id}")
                    os.makedirs(activity_dir, exist_ok=True)
                    
                    module_id = activity_id
                    section_number = module_index
                    intro_text = self._resolve_activity_intro('', item)
                    title = self._resolve_activity_title(item_title, item, moodle_type, module_id)

                    self._create_activity_xml(
                        activity_dir=activity_dir,
                        activity_id=activity_id,
                        module_id=module_id,
                        module_name=moodle_type,
                        title=title,
                        section_id=module_index,
                        section_number=section_number,
                        visible=True,
                        intro=intro_text,
                        item=item
                    )
                    
                    # Erstelle typspezifische XML-Dateien
                    if moodle_type == 'resource':
                        self._create_resource_xml(activity_dir, item, title, intro_text, module_id, activity_id, section_number, True)
                    elif moodle_type == 'forum':
                        self._create_forum_xml(activity_dir, item, title, intro_text, module_id, activity_id, section_number, True)
                    elif moodle_type == 'quiz':
                        self._create_quiz_xml(activity_dir, item, title, intro_text, module_id, activity_id, section_number, True)
                    elif moodle_type == 'folder':
                        self._create_folder_xml(activity_dir, item, title, intro_text, module_id, activity_id, section_number, True)
                    
                    # Erstelle gemeinsame XML-Dateien für alle Aktivitätstypen
                    self._create_inforef_xml(activity_dir)
                    self._create_grades_xml(activity_dir)
                    self._create_roles_xml_for_activity(activity_dir)
                    self._create_module_xml(
                        activity_dir,
                        module_id=module_id,
                        module_name=moodle_type,
                        section_id=module_index,
                        section_number=section_number,
                        instance_id=activity_id,
                        visible=True
                    )
                    self._create_additional_activity_files(activity_dir)
                    
                    # Erhöhe die Aktivitäts-ID
                    activity_id += 1
    
    def _get_item_by_id(self, item_id: str) -> Dict[str, Any]:
        """Hilfsmethode um ein Item aus den Components zu holen."""
        for component in self.analyzer.components:
            data = component.get('data', {}) if isinstance(component, dict) else {}
            component_id = component.get('id') if isinstance(component, dict) else None
            if component_id and component_id == item_id:
                return data or component

            if data.get('id') == item_id:
                result = data.copy()
                if 'type' not in result and component.get('type'):
                    result['type'] = component.get('type')
                if 'title' not in result and component.get('type'):
                    result['title'] = data.get('title') or component.get('type')
                return result
        return {}

    def _resolve_activity_title(self, fallback_title: Optional[str], item: Dict[str, Any], module_name: str, identifier: Union[int, str]) -> str:
        """Bestimmt den Titel einer Aktivität mit sinnvollen Fallbacks."""
        if fallback_title:
            return fallback_title

        if item:
            title = item.get('title') or item.get('name')
            if title:
                return title

            data = item.get('data') if isinstance(item, dict) else None
            if isinstance(data, dict):
                nested_title = data.get('title') or data.get('name')
                if nested_title:
                    return nested_title

        return f"{module_name.title()} {identifier}"

    def _resolve_activity_intro(self, fallback_intro: Optional[str], item: Dict[str, Any]) -> str:
        """Bestimmt den Intro-Text für eine Aktivität."""
        if fallback_intro:
            return fallback_intro

        metadata = item.get('metadata') if isinstance(item, dict) else None
        if isinstance(metadata, dict):
            for key in ('description', 'intro', 'summary', 'content'):
                value = metadata.get(key)
                if value:
                    return value

        for key in ('description', 'intro', 'summary'):
            value = item.get(key) if isinstance(item, dict) else None
            if value:
                return value

        return ''

    def _create_activity_xml(
        self,
        activity_dir: str,
        activity_id: int,
        module_id: int,
        module_name: str,
        title: str,
        section_id: int,
        section_number: int,
        visible: bool,
        intro: str,
        item: Dict[str, Any]
    ) -> None:
        """Erstellt die activity.xml für eine Aktivität."""
        root = ET.Element('activity')
        root.set('id', str(activity_id))
        root.set('moduleid', str(module_id))
        root.set('modulename', module_name)

        ET.SubElement(root, 'id').text = str(activity_id)
        ET.SubElement(root, 'moduleid').text = str(module_id)
        ET.SubElement(root, 'modulename').text = module_name
        ET.SubElement(root, 'title').text = title
        ET.SubElement(root, 'section').text = str(section_id)
        ET.SubElement(root, 'sectionnumber').text = str(section_number)
        ET.SubElement(root, 'visible').text = '1' if visible else '0'

        intro_elem = ET.SubElement(root, 'intro')
        intro_elem.text = intro or ''
        ET.SubElement(root, 'introformat').text = '1'

        timestamp = str(int(datetime.now().timestamp()))
        ET.SubElement(root, 'timecreated').text = timestamp
        ET.SubElement(root, 'timemodified').text = timestamp

        ET.SubElement(root, 'availability').text = '$@NULL@$'
        ET.SubElement(root, 'showdescription').text = '0'

        if item and isinstance(item, dict):
            ilias_id = item.get('id') or item.get('ref_id') or item.get('obj_id')
            if ilias_id:
                ET.SubElement(root, 'ilias_id').text = str(ilias_id)

        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'activity.xml'))

    def _create_module_xml(
        self,
        activity_dir: str,
        module_id: int,
        module_name: str,
        section_id: int,
        section_number: int,
        instance_id: int,
        visible: bool
    ) -> None:
        """Erstellt die module.xml für eine Aktivität."""
        root = ET.Element('module')
        root.set('id', str(module_id))

        ET.SubElement(root, 'modulename').text = module_name
        ET.SubElement(root, 'sectionid').text = str(section_id)
        ET.SubElement(root, 'sectionnum').text = str(section_number)
        ET.SubElement(root, 'instance').text = str(instance_id)
        ET.SubElement(root, 'idnumber').text = ''

        timestamp = str(int(datetime.now().timestamp()))
        ET.SubElement(root, 'added').text = timestamp
        ET.SubElement(root, 'score').text = '0'
        ET.SubElement(root, 'indent').text = '0'
        ET.SubElement(root, 'visible').text = '1' if visible else '0'
        ET.SubElement(root, 'visibleold').text = '1' if visible else '0'
        ET.SubElement(root, 'groupmode').text = '0'
        ET.SubElement(root, 'groupingid').text = '0'
        ET.SubElement(root, 'completion').text = '0'
        ET.SubElement(root, 'completiongradeitemnumber').text = '$@NULL@$'
        ET.SubElement(root, 'completionview').text = '0'
        ET.SubElement(root, 'completionexpected').text = '0'
        ET.SubElement(root, 'availability').text = '$@NULL@$'
        ET.SubElement(root, 'showdescription').text = '0'

        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'module.xml'))
    
    def _create_grades_xml(self, activity_dir):
        """Erstellt die grades.xml-Datei für eine Aktivität."""
        root = ET.Element('activity_gradebook')
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'grades.xml'))
    
    def _create_roles_xml_for_activity(self, activity_dir):
        """Erstellt die roles.xml-Datei für eine Aktivität."""
        root = ET.Element('roles')
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'roles.xml'))
    
    def _create_resource_xml(
        self,
        activity_dir: str,
        item: Dict[str, Any],
        title: str,
        intro: str,
        module_id: int,
        instance_id: int,
        section_number: int,
        visible: bool
    ) -> None:
        """Erstellt die resource.xml-Datei für eine Ressource."""
        root = ET.Element('activity')
        root.set('id', str(instance_id))
        root.set('moduleid', str(module_id))
        root.set('modulename', 'resource')
        root.set('contextid', '1')

        resource = ET.SubElement(root, 'resource')
        resource.set('id', str(instance_id))

        ET.SubElement(resource, 'name').text = title
        intro_elem = ET.SubElement(resource, 'intro')
        intro_elem.text = intro or ''
        ET.SubElement(resource, 'introformat').text = '1'
        ET.SubElement(resource, 'section').text = str(section_number)
        ET.SubElement(resource, 'sectionnumber').text = str(section_number)
        ET.SubElement(resource, 'visible').text = '1' if visible else '0'
        ET.SubElement(resource, 'timemodified').text = str(int(datetime.now().timestamp()))

        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'resource.xml'))

    def _create_forum_xml(
        self,
        activity_dir: str,
        item: Dict[str, Any],
        title: str,
        intro: str,
        module_id: int,
        instance_id: int,
        section_number: int,
        visible: bool
    ) -> None:
        """Erstellt die forum.xml-Datei für ein Forum."""
        root = ET.Element('activity')
        root.set('id', str(instance_id))
        root.set('moduleid', str(module_id))
        root.set('modulename', 'forum')
        root.set('contextid', '1')

        forum = ET.SubElement(root, 'forum')
        forum.set('id', str(instance_id))

        ET.SubElement(forum, 'name').text = title
        intro_elem = ET.SubElement(forum, 'intro')
        intro_elem.text = intro or ''
        ET.SubElement(forum, 'introformat').text = '1'
        ET.SubElement(forum, 'section').text = str(section_number)
        ET.SubElement(forum, 'sectionnumber').text = str(section_number)
        ET.SubElement(forum, 'visible').text = '1' if visible else '0'
        ET.SubElement(forum, 'timemodified').text = str(int(datetime.now().timestamp()))

        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'forum.xml'))

    def _create_quiz_xml(
        self,
        activity_dir: str,
        item: Dict[str, Any],
        title: str,
        intro: str,
        module_id: int,
        instance_id: int,
        section_number: int,
        visible: bool
    ) -> None:
        """Erstellt die quiz.xml-Datei für ein Quiz."""
        root = ET.Element('activity')
        root.set('id', str(instance_id))
        root.set('moduleid', str(module_id))
        root.set('modulename', 'quiz')
        root.set('contextid', '1')

        quiz = ET.SubElement(root, 'quiz')
        quiz.set('id', str(instance_id))

        ET.SubElement(quiz, 'name').text = title
        intro_elem = ET.SubElement(quiz, 'intro')
        intro_elem.text = intro or ''
        ET.SubElement(quiz, 'introformat').text = '1'
        ET.SubElement(quiz, 'section').text = str(section_number)
        ET.SubElement(quiz, 'sectionnumber').text = str(section_number)
        ET.SubElement(quiz, 'visible').text = '1' if visible else '0'
        ET.SubElement(quiz, 'timemodified').text = str(int(datetime.now().timestamp()))

        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'quiz.xml'))

    def _create_folder_xml(
        self,
        activity_dir: str,
        item: Dict[str, Any],
        title: str,
        intro: str,
        module_id: int,
        instance_id: int,
        section_number: int,
        visible: bool
    ) -> None:
        """Erstellt die folder.xml-Datei für einen Ordner."""
        root = ET.Element('activity')
        root.set('id', str(instance_id))
        root.set('moduleid', str(module_id))
        root.set('modulename', 'folder')
        root.set('contextid', '1')

        folder = ET.SubElement(root, 'folder')
        folder.set('id', str(instance_id))

        ET.SubElement(folder, 'name').text = title
        intro_elem = ET.SubElement(folder, 'intro')
        intro_elem.text = intro or ''
        ET.SubElement(folder, 'introformat').text = '1'
        ET.SubElement(folder, 'section').text = str(section_number)
        ET.SubElement(folder, 'sectionnumber').text = str(section_number)
        ET.SubElement(folder, 'visible').text = '1' if visible else '0'
        ET.SubElement(folder, 'timemodified').text = str(int(datetime.now().timestamp()))

        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'folder.xml'))
    
    def _create_files_xml(self):
        """Erstellt die files.xml-Datei."""
        root = ET.Element('files')
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'files.xml'))
    
    def _create_users_xml(self):
        """Erstellt die users.xml-Datei."""
        root = ET.Element('users')
        
        # Erstelle einen Beispielbenutzer (Admin)
        user = ET.SubElement(root, 'user')
        user.set('id', '1')
        
        # Benutzer-ID
        id_elem = ET.SubElement(user, 'id')
        id_elem.text = '1'
        
        # Benutzername
        username = ET.SubElement(user, 'username')
        username.text = 'admin'
        
        # Vorname
        firstname = ET.SubElement(user, 'firstname')
        firstname.text = 'Admin'
        
        # Nachname
        lastname = ET.SubElement(user, 'lastname')
        lastname.text = 'User'
        
        # E-Mail
        email = ET.SubElement(user, 'email')
        email.text = 'admin@example.com'
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'users.xml'))
    
    def _create_roles_xml(self):
        """Erstellt die roles.xml-Datei."""
        root = ET.Element('roles')
        
        # Rolle
        role = ET.SubElement(root, 'role')
        role.set('id', '1')
        
        # Rollen-ID
        id_elem = ET.SubElement(role, 'id')
        id_elem.text = '1'
        
        # Rollenname
        name = ET.SubElement(role, 'name')
        name.text = 'editingteacher'
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'roles.xml'))
    
    def _create_scales_xml(self):
        """Erstellt die scales.xml-Datei."""
        root = ET.Element('scales')
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'scales.xml'))
    
    def _create_outcomes_xml(self):
        """Erstellt die outcomes.xml-Datei."""
        root = ET.Element('outcomes')
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'outcomes.xml'))
    
    def _create_questions_xml(self):
        """Erstellt die questions.xml-Datei."""
        root = ET.Element('question_categories')
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'questions.xml'))
    
    def _create_groups_xml(self):
        """Erstellt die groups.xml-Datei."""
        root = ET.Element('groups')
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'groups.xml'))
    
    def _create_gradebook_xml(self):
        """Erstellt die gradebook.xml-Datei."""
        root = ET.Element('gradebook')
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'gradebook.xml'))
    
    def _create_grade_history_xml(self):
        """Erstellt die grade_history.xml-Datei."""
        root = ET.Element('grade_history')
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'grade_history.xml'))
    
    def _create_completion_xml(self):
        """Erstellt die completion.xml-Datei."""
        root = ET.Element('completions')
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'completion.xml'))
    
    def _create_badges_xml(self):
        """Erstellt die badges.xml-Datei."""
        root = ET.Element('badges')
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(self.moodle_dir, 'badges.xml'))
    
    def _create_section_files(self):
        """Erstellt die Abschnittsverzeichnisse und XML-Dateien."""
        # Erstelle Verzeichnis für Abschnitte
        sections_dir = os.path.join(self.moodle_dir, 'sections')
        os.makedirs(sections_dir, exist_ok=True)
        
        # NEU: Nutze MoodleStructure wenn verfügbar
        if self.moodle_structure:
            # Neue Struktur-basierte Generierung
            for moodle_section in self.moodle_structure.sections:
                section_dir = os.path.join(sections_dir, f'section_{moodle_section.section_id}')
                os.makedirs(section_dir, exist_ok=True)
                
                # Erstelle section.xml mit allen Details
                self._create_section_xml_detailed(
                    section_dir, 
                    moodle_section.section_id, 
                    moodle_section.name,
                    moodle_section.summary,
                    moodle_section.activities
                )
                
                # Erstelle inforef.xml
                self._create_inforef_xml(section_dir)
        else:
            # ALT: Alte Logik als Fallback
            # Erstelle Abschnitt 0 (Allgemeiner Abschnitt)
            section_dir = os.path.join(sections_dir, 'section_0')
            os.makedirs(section_dir, exist_ok=True)
            
            # Erstelle section.xml für Abschnitt 0
            self._create_section_xml(section_dir, 0, 'Allgemein')
            
            # Erstelle inforef.xml für Abschnitt 0
            self._create_inforef_xml(section_dir)
            
            # Erstelle Abschnitte für Module
            for i, module in enumerate(self.analyzer.modules, 1):
                section_dir = os.path.join(sections_dir, f'section_{i}')
                os.makedirs(section_dir, exist_ok=True)
                
                # Erstelle section.xml
                self._create_section_xml(section_dir, i, module.title)
                
                # Erstelle inforef.xml
                self._create_inforef_xml(section_dir)
    
    def _create_section_xml(self, section_dir, section_id, section_name):
        """Erstellt die section.xml für einen Abschnitt (alte Methode für Fallback)."""
        root = ET.Element('section')
        root.set('id', str(section_id))
        
        # ID
        id_elem = ET.SubElement(root, 'id')
        id_elem.text = str(section_id)
        
        # Nummer
        number = ET.SubElement(root, 'number')
        number.text = str(section_id)
        
        # Name
        name = ET.SubElement(root, 'name')
        name.text = section_name
        
        # Zusammenfassung
        summary = ET.SubElement(root, 'summary')
        summary.text = ''
        
        # Zusammenfassungsformat
        summaryformat = ET.SubElement(root, 'summaryformat')
        summaryformat.text = '1'
        
        # Sequenz
        sequence = ET.SubElement(root, 'sequence')
        sequence.text = ''
        
        # Sichtbarkeit
        visible = ET.SubElement(root, 'visible')
        visible.text = '1'
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(section_dir, 'section.xml'))
    
    def _create_section_xml_detailed(self, section_dir, section_id, section_name, section_summary, activities):
        """Erstellt die section.xml für einen Abschnitt mit vollständigen Details (neue Methode)."""
        root = ET.Element('section')
        root.set('id', str(section_id))
        
        # ID
        id_elem = ET.SubElement(root, 'id')
        id_elem.text = str(section_id)
        
        # Nummer
        number = ET.SubElement(root, 'number')
        number.text = str(section_id)
        
        # Name
        name = ET.SubElement(root, 'name')
        name.text = section_name
        
        # Zusammenfassung
        summary = ET.SubElement(root, 'summary')
        summary.text = section_summary or ''
        
        # Zusammenfassungsformat
        summaryformat = ET.SubElement(root, 'summaryformat')
        summaryformat.text = '1'
        
        # Sequenz (Activity-IDs)
        sequence = ET.SubElement(root, 'sequence')
        if activities:
            activity_ids = [str(activity.module_id) for activity in activities]
            sequence.text = ','.join(activity_ids)
        else:
            sequence.text = ''
        
        # Sichtbarkeit
        visible = ET.SubElement(root, 'visible')
        visible.text = '1'
        
        # Zeitstempel
        timemodified = ET.SubElement(root, 'timemodified')
        timemodified.text = str(int(datetime.now().timestamp()))
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(section_dir, 'section.xml'))
    
    def _create_inforef_xml(self, directory):
        """Erstellt eine inforef.xml-Datei im angegebenen Verzeichnis."""
        root = ET.Element('inforef')
        
        # Schreibe die XML-Datei
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(directory, 'inforef.xml'))
    
    def _create_additional_activity_files(self, activity_dir):
        """Erstellt zusätzliche XML-Dateien für eine Aktivität."""
        # Grading
        root = ET.Element('activity_gradebook')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'grading.xml'))
        
        # Filters
        root = ET.Element('filters')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'filters.xml'))
        
        # Comments
        root = ET.Element('comments')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'comments.xml'))
        
        # Completion
        root = ET.Element('completions')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'completion.xml'))
        
        # Logstores
        root = ET.Element('logstores')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'logstores.xml'))
        
        # Competencies
        root = ET.Element('competencies')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'competencies.xml'))
        
        # Grade history
        root = ET.Element('grade_history')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'grade_history.xml'))
        
        # Calendar
        root = ET.Element('calendar')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'calendar.xml'))
        
        # XAPIState
        root = ET.Element('xapistate')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'xapistate.xml'))
        
        # Logs
        root = ET.Element('logs')
        tree = ET.ElementTree(root)
        self._write_xml_file(tree, os.path.join(activity_dir, 'logs.xml'))
    
    def _create_mbz_file(self) -> str:
        """
        Erstellt die MBZ-Datei aus dem Moodle-Backup-Verzeichnis.
        
        Returns:
            Pfad zur erstellten MBZ-Datei
        """
        # Erstelle einen Dateinamen basierend auf dem Kurstitel
        safe_title = ''.join(c if c.isalnum() else '_' for c in self.analyzer.course_title)
        mbz_filename = f"{safe_title}_moodle_backup.mbz"
        mbz_path = os.path.join(self.temp_dir, mbz_filename)
        
        # Erstelle die ZIP-Datei
        with zipfile.ZipFile(mbz_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.moodle_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.moodle_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"Moodle-Backup erstellt: {mbz_path}")
        return mbz_path
    
    def cleanup(self):
        """Bereinigt temporäre Dateien."""
        try:
            shutil.rmtree(self.temp_dir)
            logger.info(f"Temporäres Verzeichnis gelöscht: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Fehler beim Löschen des temporären Verzeichnisses: {e}") 