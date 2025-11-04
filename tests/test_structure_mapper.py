"""
Tests für den StructureMapper.
"""

import os
import pytest
from shared.utils.ilias.structure_mapper import (
    StructureMapper,
    MoodleSection,
    MoodleActivity,
    MoodleStructure,
    map_ilias_to_moodle
)
from shared.utils.ilias.container_parser import parse_container_structure
from shared.utils.ilias.itemgroup_resolver import ItemGroupResolver


def test_moodle_section_creation():
    """Test: MoodleSection erstellen."""
    section = MoodleSection(
        section_id=1,
        number=1,
        name="Test Section"
    )
    
    assert section.section_id == 1
    assert section.name == "Test Section"
    assert len(section.activities) == 0


def test_moodle_activity_creation():
    """Test: MoodleActivity erstellen."""
    activity = MoodleActivity(
        activity_id=1,
        module_id=1000,
        section_id=1,
        module_name="resource",
        title="Test File"
    )
    
    assert activity.activity_id == 1
    assert activity.module_name == "resource"
    assert activity.title == "Test File"


def test_moodle_structure_creation():
    """Test: MoodleStructure erstellen."""
    structure = MoodleStructure(course_title="Test Course")
    
    assert structure.course_title == "Test Course"
    assert len(structure.sections) == 0
    assert len(structure.warnings) == 0


def test_add_section_to_structure():
    """Test: Section zu Structure hinzufügen."""
    structure = MoodleStructure(course_title="Test")
    section = MoodleSection(section_id=1, number=1, name="Section 1")
    
    structure.add_section(section)
    
    assert len(structure.sections) == 1
    assert structure.sections[0].name == "Section 1"


def test_add_warning_to_structure():
    """Test: Warning zu Structure hinzufügen."""
    structure = MoodleStructure(course_title="Test")
    
    structure.add_warning("Test warning")
    
    assert len(structure.warnings) == 1
    assert structure.warnings[0] == "Test warning"


def test_structure_mapper_initialization():
    """Test: StructureMapper initialisieren."""
    mapper = StructureMapper()
    
    assert mapper.container_structure is None
    assert mapper.next_section_id == 1
    assert mapper.next_activity_id == 1


def test_type_mapping():
    """Test: ILIAS-Typ zu Moodle-Typ Mapping."""
    mapper = StructureMapper()
    
    assert mapper.TYPE_MAPPING['file'] == 'resource'
    assert mapper.TYPE_MAPPING['tst'] == 'quiz'
    assert mapper.TYPE_MAPPING['fold'] == 'folder'
    assert mapper.TYPE_MAPPING['frm'] == 'forum'


def test_map_without_container_structure():
    """Test: Mapping ohne Container-Struktur."""
    mapper = StructureMapper()
    structure = mapper.map_to_moodle()
    
    assert structure.course_title == "Unbekannter Kurs"
    assert len(structure.warnings) == 1
    assert "Keine Container-Struktur" in structure.warnings[0]


def test_map_with_real_ilias_structure():
    """Test: Mapping mit echter ILIAS-Struktur."""
    ilias_path = "/Users/alexander/Repository/ai/oersynch-ai/dummy_files/ilias_kurs/set_1/1744020005__13869__grp_9094"
    
    if not os.path.exists(ilias_path):
        pytest.skip("Dummy-Dateien nicht verfügbar")
    
    # Parse Container-Struktur
    container_structure = parse_container_structure(ilias_path)
    
    if not container_structure:
        pytest.skip("Keine Container-Struktur verfügbar")
    
    # Mappe zu Moodle
    mapper = StructureMapper(container_structure)
    moodle_structure = mapper.map_to_moodle()
    
    # Prüfungen
    assert moodle_structure is not None
    assert "Vorlage" in moodle_structure.course_title or "Adaptivitätsstufe" in moodle_structure.course_title
    
    # Sollte mindestens die Standard-Section haben
    assert len(moodle_structure.sections) >= 1
    
    # Erste Section sollte "Allgemein" sein
    assert moodle_structure.sections[0].name == "Allgemein"
    assert moodle_structure.sections[0].number == 0
    
    print(f"\n--- Mapping-Ergebnis ---")
    print(f"Kurs: {moodle_structure.course_title}")
    print(f"Sections: {len(moodle_structure.sections)}")
    
    total_activities = sum(len(s.activities) for s in moodle_structure.sections)
    print(f"Activities: {total_activities}")
    print(f"Warnungen: {len(moodle_structure.warnings)}")
    
    # Zeige Sections
    for section in moodle_structure.sections:
        print(f"\n  Section {section.number}: {section.name}")
        print(f"    Activities: {len(section.activities)}")
        for activity in section.activities[:3]:  # Erste 3
            print(f"      - {activity.title} ({activity.module_name})")
        if len(section.activities) > 3:
            print(f"      ... und {len(section.activities) - 3} weitere")
    
    # Zeige Warnungen
    if moodle_structure.warnings:
        print(f"\n  Warnungen:")
        for warning in moodle_structure.warnings[:5]:
            print(f"    - {warning}")


def test_moodle_section_to_dict():
    """Test: MoodleSection zu Dictionary."""
    section = MoodleSection(
        section_id=1,
        number=1,
        name="Test",
        summary="Summary"
    )
    
    activity = MoodleActivity(
        activity_id=1,
        module_id=1000,
        section_id=1,
        module_name="resource",
        title="File 1"
    )
    
    section.add_activity(activity)
    
    dict_repr = section.to_dict()
    
    assert dict_repr['section_id'] == 1
    assert dict_repr['name'] == "Test"
    assert dict_repr['activity_count'] == 1
    assert len(dict_repr['activities']) == 1


def test_moodle_structure_to_dict():
    """Test: MoodleStructure zu Dictionary."""
    structure = MoodleStructure(course_title="Test")
    
    section = MoodleSection(section_id=1, number=1, name="Section 1")
    activity = MoodleActivity(
        activity_id=1,
        module_id=1000,
        section_id=1,
        module_name="quiz",
        title="Quiz 1"
    )
    section.add_activity(activity)
    structure.add_section(section)
    
    dict_repr = structure.to_dict()
    
    assert dict_repr['course_title'] == "Test"
    assert dict_repr['total_sections'] == 1
    assert dict_repr['total_activities'] == 1
    assert len(dict_repr['sections']) == 1


def test_convenience_function():
    """Test: Convenience-Funktion map_ilias_to_moodle."""
    ilias_path = "/Users/alexander/Repository/ai/oersynch-ai/dummy_files/ilias_kurs/set_1/1744020005__13869__grp_9094"
    
    if not os.path.exists(ilias_path):
        pytest.skip("Dummy-Dateien nicht verfügbar")
    
    container_structure = parse_container_structure(ilias_path)
    
    if not container_structure:
        pytest.skip("Keine Container-Struktur verfügbar")
    
    # Nutze Convenience-Funktion
    moodle_structure = map_ilias_to_moodle(container_structure)
    
    assert moodle_structure is not None
    assert len(moodle_structure.sections) >= 1


def test_get_section_by_id():
    """Test: Section anhand ID finden."""
    structure = MoodleStructure(course_title="Test")
    
    section1 = MoodleSection(section_id=1, number=1, name="Section 1")
    section2 = MoodleSection(section_id=2, number=2, name="Section 2")
    
    structure.add_section(section1)
    structure.add_section(section2)
    
    found = structure.get_section_by_id(2)
    
    assert found is not None
    assert found.name == "Section 2"
    
    not_found = structure.get_section_by_id(99)
    assert not_found is None


def test_activity_with_ilias_metadata():
    """Test: Activity mit ILIAS-Metadaten."""
    activity = MoodleActivity(
        activity_id=1,
        module_id=1000,
        section_id=1,
        module_name="quiz",
        title="Test Quiz",
        ilias_type="tst",
        ilias_id="9151",
        ilias_ref_id="3845"
    )
    
    dict_repr = activity.to_dict()
    
    assert dict_repr['ilias_type'] == "tst"
    assert dict_repr['ilias_id'] == "9151"
    assert dict_repr['ilias_ref_id'] == "3845"

