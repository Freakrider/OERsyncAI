"""
Integration-Tests für den MoodleConverter mit StructureMapper.
"""

import os
import tempfile
import zipfile
import pytest
import xml.etree.ElementTree as ET
from pathlib import Path

# Da wir Module aus dem shared-Verzeichnis importieren
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.utils.ilias.analyzer import IliasAnalyzer
from shared.utils.ilias.moodle_converter import MoodleConverter


class TestMoodleConverterIntegration:
    """Integration-Tests für den vollständigen Konvertierungsprozess."""
    
    @pytest.fixture
    def ilias_export_dir(self):
        """Fixture für das ILIAS Export-Verzeichnis."""
        # Verwende das echte dummy_files/ilias_kurs Verzeichnis
        test_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(test_dir)
        ilias_dir = os.path.join(project_root, 'dummy_files', 'ilias_kurs')
        
        if not os.path.exists(ilias_dir):
            pytest.skip(f"ILIAS Beispielkurs nicht gefunden: {ilias_dir}")
        
        return ilias_dir
    
    @pytest.fixture
    def analyzer(self, ilias_export_dir):
        """Fixture für den IliasAnalyzer."""
        analyzer = IliasAnalyzer(ilias_export_dir)
        success = analyzer.analyze()
        
        if not success:
            pytest.skip("Fehler beim Analysieren des ILIAS-Kurses")
        
        return analyzer
    
    def test_converter_initialization(self, analyzer):
        """Testet die Initialisierung des MoodleConverters."""
        converter = MoodleConverter(analyzer)
        
        assert converter.analyzer == analyzer
        assert converter.temp_dir is not None
        assert os.path.exists(converter.temp_dir)
        assert converter.moodle_dir is not None
        assert os.path.exists(converter.moodle_dir)
        assert converter.use_structure_mapper is True
    
    def test_converter_structure_mapping(self, analyzer):
        """Testet das Structure-Mapping."""
        converter = MoodleConverter(analyzer)
        
        # Führe das Mapping durch
        if analyzer.container_structure:
            converter._map_structure()
            
            # Prüfe, dass die Moodle-Struktur erstellt wurde
            assert converter.moodle_structure is not None
            assert len(converter.moodle_structure.sections) > 0
            
            # Prüfe, dass mindestens eine Section Aktivitäten hat
            total_activities = sum(len(s.activities) for s in converter.moodle_structure.sections)
            assert total_activities > 0
            
            # Prüfe Section-Attribute
            for section in converter.moodle_structure.sections:
                assert section.section_id is not None
                assert section.name is not None
                assert section.number is not None
                assert isinstance(section.activities, list)
            
            # Prüfe Activity-Attribute
            for section in converter.moodle_structure.sections:
                for activity in section.activities:
                    assert activity.activity_id is not None
                    assert activity.module_name is not None
                    assert activity.title is not None
        else:
            pytest.skip("Keine Container-Struktur verfügbar")
    
    def test_converter_conversion_report(self, analyzer):
        """Testet die Generierung des Conversion-Reports."""
        converter = MoodleConverter(analyzer)
        
        if analyzer.container_structure:
            converter._map_structure()
            converter._generate_conversion_report()
            
            # Prüfe, dass der Report erstellt wurde
            assert converter.conversion_report is not None
            
            # Prüfe Report-Attribute
            report = converter.conversion_report
            assert hasattr(report, 'info_issues')
            assert hasattr(report, 'warning_issues')
            assert hasattr(report, 'error_issues')
            
            # Ausgabe für Debugging
            print(f"\n=== Conversion Report ===")
            print(f"Info-Issues: {len(report.info_issues)}")
            print(f"Warnungen: {len(report.warning_issues)}")
            print(f"Fehler: {len(report.error_issues)}")
        else:
            pytest.skip("Keine Container-Struktur verfügbar")
    
    def test_full_conversion(self, analyzer):
        """Testet die vollständige Konvertierung zu einer MBZ-Datei."""
        converter = MoodleConverter(analyzer)
        
        # Führe die Konvertierung durch
        mbz_path = converter.convert(generate_report=True)
        
        # Prüfe, dass die MBZ-Datei erstellt wurde
        assert mbz_path is not None
        assert os.path.exists(mbz_path)
        assert mbz_path.endswith('.mbz')
        
        # Prüfe, dass das Conversion-Report-File erstellt wurde
        if converter.conversion_report:
            report_path = mbz_path.replace('.mbz', '_conversion_report.md')
            assert os.path.exists(report_path)
        
        # Prüfe den Inhalt der MBZ-Datei
        with zipfile.ZipFile(mbz_path, 'r') as zip_ref:
            files = zip_ref.namelist()
            
            # Prüfe, dass wichtige Dateien vorhanden sind
            assert 'moodle_backup.xml' in files
            assert any(f.startswith('course/') for f in files)
            assert any(f.startswith('sections/') for f in files)
            
            # Wenn StructureMapper genutzt wurde, prüfe activities
            if converter.moodle_structure:
                assert any(f.startswith('activities/') for f in files)
        
        # Cleanup
        if os.path.exists(mbz_path):
            os.remove(mbz_path)
        if converter.conversion_report:
            report_path = mbz_path.replace('.mbz', '_conversion_report.md')
            if os.path.exists(report_path):
                os.remove(report_path)
    
    def test_moodle_backup_xml_structure(self, analyzer):
        """Testet die Struktur der generierten moodle_backup.xml."""
        converter = MoodleConverter(analyzer)
        mbz_path = converter.convert(generate_report=False)
        
        # Extrahiere und parse moodle_backup.xml
        with zipfile.ZipFile(mbz_path, 'r') as zip_ref:
            xml_content = zip_ref.read('moodle_backup.xml')
            root = ET.fromstring(xml_content)
        
        # Prüfe Haupt-Struktur
        assert root.tag == 'moodle_backup'
        
        # Prüfe Information-Element
        info = root.find('information')
        assert info is not None
        
        # Prüfe Contents
        contents = info.find('contents')
        assert contents is not None
        
        # Prüfe Activities
        activities = contents.find('activities')
        assert activities is not None
        activity_list = list(activities)
        
        if converter.moodle_structure:
            # Prüfe, dass Activities korrekt gemappt wurden
            expected_count = sum(len(s.activities) for s in converter.moodle_structure.sections)
            assert len(activity_list) == expected_count
            
            # Prüfe erste Activity im Detail
            if activity_list:
                first_activity = activity_list[0]
                assert first_activity.find('moduleid') is not None
                assert first_activity.find('sectionid') is not None
                assert first_activity.find('modulename') is not None
                assert first_activity.find('title') is not None
        
        # Prüfe Sections
        sections_elem = contents.find('sections')
        assert sections_elem is not None
        section_list = list(sections_elem)
        
        if converter.moodle_structure:
            # Prüfe, dass Sections korrekt gemappt wurden
            assert len(section_list) == len(converter.moodle_structure.sections)
            
            # Prüfe erste Section im Detail
            if section_list:
                first_section = section_list[0]
                assert first_section.find('sectionid') is not None
                assert first_section.find('title') is not None
        
        # Cleanup
        if os.path.exists(mbz_path):
            os.remove(mbz_path)
    
    def test_activity_directories_created(self, analyzer):
        """Testet, dass Activity-Verzeichnisse korrekt erstellt wurden."""
        converter = MoodleConverter(analyzer)
        mbz_path = converter.convert(generate_report=False)
        
        # Extrahiere MBZ
        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(mbz_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Prüfe, dass activities-Verzeichnis existiert
            activities_dir = os.path.join(extract_dir, 'activities')
            assert os.path.exists(activities_dir)
            
            if converter.moodle_structure:
                # Prüfe, dass für jede Activity ein Verzeichnis existiert
                for section in converter.moodle_structure.sections:
                    for activity in section.activities:
                        activity_dir = os.path.join(activities_dir, f"{activity.module_name}_{activity.activity_id}")
                        assert os.path.exists(activity_dir), f"Activity-Verzeichnis nicht gefunden: {activity_dir}"
                        
                        # Prüfe, dass activity.xml existiert
                        activity_xml = os.path.join(activity_dir, 'activity.xml')
                        assert os.path.exists(activity_xml), f"activity.xml nicht gefunden: {activity_xml}"
        
        # Cleanup
        if os.path.exists(mbz_path):
            os.remove(mbz_path)
    
    def test_section_directories_created(self, analyzer):
        """Testet, dass Section-Verzeichnisse korrekt erstellt wurden."""
        converter = MoodleConverter(analyzer)
        mbz_path = converter.convert(generate_report=False)
        
        # Extrahiere MBZ
        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(mbz_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Prüfe, dass sections-Verzeichnis existiert
            sections_dir = os.path.join(extract_dir, 'sections')
            assert os.path.exists(sections_dir)
            
            if converter.moodle_structure:
                # Prüfe, dass für jede Section ein Verzeichnis existiert
                for section in converter.moodle_structure.sections:
                    section_dir = os.path.join(sections_dir, f"section_{section.section_id}")
                    assert os.path.exists(section_dir), f"Section-Verzeichnis nicht gefunden: {section_dir}"
                    
                    # Prüfe, dass section.xml existiert
                    section_xml = os.path.join(section_dir, 'section.xml')
                    assert os.path.exists(section_xml), f"section.xml nicht gefunden: {section_xml}"
        
        # Cleanup
        if os.path.exists(mbz_path):
            os.remove(mbz_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

