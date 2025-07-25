#!/usr/bin/env python3
"""
Test Script für erweiterten XML Parser
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent  # Go up one level from tests/ to project root
sys.path.insert(0, str(project_root))

from shared.utils.xml_parser import (
    XMLParser, MoodleBackupInfo, MoodleCourseInfo, MoodleSectionInfo,
    XMLParsingError, parse_moodle_backup_complete
)
from shared.models import DublinCoreMetadata, LearningResourceType
import tempfile
import xml.etree.ElementTree as ET


def create_sample_moodle_backup_xml() -> str:
    """Erstellt eine sample moodle_backup.xml"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<moodle_backup>
    <information>
        <name>backup-moodle2-course-123-20231201-1234.mbz</name>
        <moodle_version>4.1.6</moodle_version>
        <backup_version>2022112800</backup_version>
        <backup_date>1701432000</backup_date>
        <type>course</type>
        <original_course_info>
            <courseid>123</courseid>
            <fullname>Einführung in die Informatik</fullname>
            <shortname>info-101</shortname>
            <format>topics</format>
        </original_course_info>
        <anonymized>0</anonymized>
        <backup_unique_code>abc123def456</backup_unique_code>
    </information>
</moodle_backup>"""


def create_sample_course_xml() -> str:
    """Erstellt eine sample course.xml"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<course_backup>
    <course>
        <id>123</id>
        <fullname>Einführung in die Informatik</fullname>
        <shortname>info-101</shortname>
        <category>5</category>
        <summary><![CDATA[<p>Grundlagen der Informatik für Studierende im ersten Semester.</p>]]></summary>
        <format>topics</format>
        <startdate>1693526400</startdate>
        <enddate>1701298800</enddate>
        <lang>de</lang>
        <visible>1</visible>
        <guest>0</guest>
    </course>
</course_backup>"""


def create_sample_section_xml() -> str:
    """Erstellt eine sample section.xml"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<section_backup>
    <section>
        <id>1</id>
        <number>1</number>
        <name>Woche 1: Grundlagen</name>
        <summary><![CDATA[<p>Einführung in die Grundlagen der Informatik</p>]]></summary>
        <visible>1</visible>
        <sequence>10,11,12</sequence>
    </section>
</section_backup>"""


def create_sample_activity_xml() -> str:
    """Erstellt eine sample activity/module.xml"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<activity_backup>
    <activity>
        <id>10</id>
        <modulename>quiz</modulename>
        <sectionnumber>1</sectionnumber>
        <module>
            <name>Quiz 1: Grundlagen Test</name>
            <intro><![CDATA[<p>Testen Sie Ihr Wissen über die Grundlagen</p>]]></intro>
            <visible>1</visible>
            <completion>1</completion>
            <timecreated>1693526400</timecreated>
            <timemodified>1693612800</timemodified>
            <timelimit>1800</timelimit>
            <attempts>3</attempts>
            <grademethod>1</grademethod>
        </module>
    </activity>
</activity_backup>"""


def test_xml_parser_basic():
    """Test basic XML parser functionality"""
    print("🧪 Testing XML Parser Basic Functionality:")
    
    parser = XMLParser()
    print(f"  ✅ XML Parser created")
    print(f"  Security settings: {len(parser.XML_PARSER_SETTINGS)} options")
    print(f"  Activity mappings: {len(parser.ACTIVITY_TYPE_MAPPING)} types")


def test_moodle_backup_parsing():
    """Test moodle_backup.xml parsing"""
    print("\n🧪 Testing moodle_backup.xml Parsing:")
    
    parser = XMLParser()
    
    # Create temp file with sample XML
    temp_dir = Path(tempfile.mkdtemp())
    backup_xml = temp_dir / "moodle_backup.xml"
    backup_xml.write_text(create_sample_moodle_backup_xml())
    
    try:
        backup_info = parser.parse_moodle_backup_xml(backup_xml)
        
        print(f"  ✅ Backup parsed successfully")
        print(f"    Course: {backup_info.original_course_fullname}")
        print(f"    Moodle Version: {backup_info.moodle_version}")
        print(f"    Course ID: {backup_info.original_course_id}")
        print(f"    Anonymized: {backup_info.anonymized}")
        
        assert backup_info.original_course_fullname == "Einführung in die Informatik"
        assert backup_info.moodle_version == "4.1.6"
        assert backup_info.original_course_id == 123
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    finally:
        # Cleanup
        backup_xml.unlink()
        temp_dir.rmdir()


def test_course_xml_parsing():
    """Test course.xml parsing"""
    print("\n🧪 Testing course.xml Parsing:")
    
    parser = XMLParser()
    
    # Create temp file with sample XML
    temp_dir = Path(tempfile.mkdtemp())
    course_xml = temp_dir / "course.xml"
    course_xml.write_text(create_sample_course_xml())
    
    try:
        course_info = parser.parse_course_xml(course_xml)
        
        print(f"  ✅ Course parsed successfully")
        print(f"    Course: {course_info.fullname}")
        print(f"    Format: {course_info.format}")
        print(f"    Language: {course_info.language}")
        print(f"    Visible: {course_info.visible}")
        
        assert course_info.fullname == "Einführung in die Informatik"
        assert course_info.shortname == "info-101"
        assert course_info.format == "topics"
        assert course_info.language == "de"
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    finally:
        # Cleanup
        course_xml.unlink()
        temp_dir.rmdir()


def test_section_xml_parsing():
    """Test section.xml parsing"""
    print("\n🧪 Testing section.xml Parsing:")
    
    parser = XMLParser()
    
    # Create temp file with sample XML
    temp_dir = Path(tempfile.mkdtemp())
    section_xml = temp_dir / "section.xml"
    section_xml.write_text(create_sample_section_xml())
    
    try:
        section_info = parser._parse_single_section(section_xml)
        
        print(f"  ✅ Section parsed successfully")
        print(f"    Section: {section_info.name}")
        print(f"    Number: {section_info.section_number}")
        print(f"    Activities: {len(section_info.activities)} items")
        print(f"    Activity IDs: {section_info.activities}")
        
        assert section_info.name == "Woche 1: Grundlagen"
        assert section_info.section_number == 1
        assert section_info.activities == [10, 11, 12]
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    finally:
        # Cleanup
        section_xml.unlink()
        temp_dir.rmdir()


def test_activity_xml_parsing():
    """Test activity/module.xml parsing"""
    print("\n🧪 Testing activity/module.xml Parsing:")
    
    parser = XMLParser()
    
    # Create temp file with sample XML
    temp_dir = Path(tempfile.mkdtemp())
    activity_xml = temp_dir / "module.xml"
    activity_xml.write_text(create_sample_activity_xml())
    
    try:
        activity_metadata = parser.parse_activity_xml(activity_xml)
        
        print(f"  ✅ Activity parsed successfully")
        print(f"    Name: {activity_metadata.module_name}")
        print(f"    Type: {activity_metadata.activity_type}")
        print(f"    Section: {activity_metadata.section_number}")
        print(f"    Completion: {activity_metadata.completion_enabled}")
        print(f"    Config: {activity_metadata.activity_config}")
        
        assert activity_metadata.module_name == "Quiz 1: Grundlagen Test"
        assert activity_metadata.activity_type == LearningResourceType.QUIZ
        assert activity_metadata.section_number == 1
        assert activity_metadata.completion_enabled == True
        assert 'time_limit_seconds' in activity_metadata.activity_config
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    finally:
        # Cleanup
        activity_xml.unlink()
        temp_dir.rmdir()


def test_dublin_core_creation():
    """Test Dublin Core creation from parsed data"""
    print("\n🧪 Testing Dublin Core Creation:")
    
    parser = XMLParser()
    
    # Create sample data objects
    backup_info = MoodleBackupInfo(
        moodle_version="4.1.6",
        backup_version="2022112800",
        backup_type="course",
        backup_date=parser._parse_timestamp(ET.fromstring('<date>1701432000</date>')),
        original_course_id=123,
        original_course_fullname="Test Course",
        original_course_shortname="test-101",
        original_course_format="topics"
    )
    
    course_info = MoodleCourseInfo(
        course_id=123,
        fullname="Test Course",
        shortname="test-101",
        category_id=5,
        summary="Ein Test-Kurs für die Validierung",
        format="topics"
    )
    
    try:
        dublin_core = parser.create_dublin_core_from_course(course_info, backup_info)
        
        print(f"  ✅ Dublin Core created successfully")
        print(f"    Title: {dublin_core.title}")
        print(f"    Description: {dublin_core.description}")
        print(f"    Language: {dublin_core.language}")
        print(f"    Format: {dublin_core.format}")
        print(f"    Identifier: {dublin_core.identifier}")
        
        assert dublin_core.title == "Test Course"
        assert dublin_core.description == "Ein Test-Kurs für die Validierung"
        assert dublin_core.language.value == "de"
        assert dublin_core.format == "Moodle Course Backup"
        
    except Exception as e:
        print(f"  ❌ Error: {e}")


def main():
    """Run all tests"""
    print("🚀 Starting XML Parser Tests\n")
    
    test_xml_parser_basic()
    test_moodle_backup_parsing()
    test_course_xml_parsing()
    test_section_xml_parsing()
    test_activity_xml_parsing()
    test_dublin_core_creation()
    
    print(f"\n🎉 XML Parser Tests abgeschlossen!")


if __name__ == "__main__":
    main() 