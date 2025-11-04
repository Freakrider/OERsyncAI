"""
Tests für den ContainerStructureParser.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path

from shared.utils.ilias.container_parser import (
    ContainerStructureParser,
    ContainerStructure,
    ContainerItem,
    parse_container_structure
)


@pytest.fixture
def temp_component_dir():
    """Erstellt ein temporäres Verzeichnis für Test-Komponenten."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_container_xml(temp_component_dir):
    """Erstellt eine Sample Container-XML-Datei."""
    # Erstelle die Verzeichnisstruktur
    container_dir = os.path.join(temp_component_dir, 'Services', 'Container', 'set_1')
    os.makedirs(container_dir, exist_ok=True)
    
    # Erstelle die XML-Datei
    xml_content = """<?xml version="1.0" encoding="utf-8"?>
<exp:Export InstallationId="13869" InstallationUrl="https://www.ilias.nrw" Entity="struct" SchemaVersion="4.1.0" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xmlns:exp="http://www.ilias.de/Services/Export/exp/4_1" 
    xmlns="https://www.ilias.de/Modules/Folder/fold/4_1">
  <exp:ExportItem Id="9094">
    <Items>
      <Item RefId="3812" Id="9094" Title="Testkurs" Type="grp" Page="1" Style="9115">
        <Timing Type="1" Visible="0" Changeable="0">
          <Start>2025-02-05 08:40:24</Start>
          <End>2025-02-05 08:40:24</End>
        </Timing>
        <Item RefId="3845" Id="9151" Title="Test 1" Type="tst" Page="" Style="0" Offline="1">
          <Timing Type="1" Visible="0" Changeable="0"/>
        </Item>
        <Item RefId="3826" Id="9124" Title="Ordner 1" Type="fold" Page="" Style="0">
          <Timing Type="1" Visible="0" Changeable="0">
            <Start>2025-02-12 14:44:16</Start>
            <End>2025-02-12 14:44:16</End>
          </Timing>
        </Item>
        <Item RefId="3827" Id="9125" Title="ItemGroup 1" Type="itgr" Page="" Style="0">
          <Timing Type="1" Visible="0" Changeable="0"/>
        </Item>
      </Item>
    </Items>
  </exp:ExportItem>
</exp:Export>
"""
    
    xml_path = os.path.join(container_dir, 'export.xml')
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    return temp_component_dir


def test_container_structure_parser_initialization(temp_component_dir):
    """Test: Parser-Initialisierung."""
    parser = ContainerStructureParser(temp_component_dir)
    assert parser.component_path == temp_component_dir
    assert parser.container_xml_path is None  # Keine XML vorhanden


def test_find_container_xml(sample_container_xml):
    """Test: Finde Container-XML."""
    parser = ContainerStructureParser(sample_container_xml)
    assert parser.container_xml_path is not None
    assert parser.container_xml_path.endswith('export.xml')
    assert os.path.exists(parser.container_xml_path)


def test_parse_container_structure(sample_container_xml):
    """Test: Parse Container-Struktur."""
    structure = parse_container_structure(sample_container_xml)
    
    assert structure is not None
    assert isinstance(structure, ContainerStructure)
    assert structure.root_item is not None
    assert structure.root_item.title == "Testkurs"
    assert structure.root_item.item_type == "grp"


def test_container_item_attributes(sample_container_xml):
    """Test: Container-Item-Attribute."""
    structure = parse_container_structure(sample_container_xml)
    root = structure.root_item
    
    # Root-Item prüfen
    assert root.ref_id == "3812"
    assert root.item_id == "9094"
    assert root.title == "Testkurs"
    assert root.item_type == "grp"
    assert root.page == "1"
    assert root.style == "9115"
    assert root.offline is False
    
    # Timing prüfen
    assert root.timing is not None
    assert 'start' in root.timing
    assert root.timing['start'] == "2025-02-05 08:40:24"


def test_container_item_children(sample_container_xml):
    """Test: Container-Item-Kinder."""
    structure = parse_container_structure(sample_container_xml)
    root = structure.root_item
    
    # Kinder prüfen
    assert len(root.children) == 3
    
    # Erstes Kind: Test
    test_item = root.children[0]
    assert test_item.title == "Test 1"
    assert test_item.item_type == "tst"
    assert test_item.ref_id == "3845"
    assert test_item.offline is True
    
    # Zweites Kind: Folder
    folder_item = root.children[1]
    assert folder_item.title == "Ordner 1"
    assert folder_item.item_type == "fold"
    
    # Drittes Kind: ItemGroup
    itgr_item = root.children[2]
    assert itgr_item.title == "ItemGroup 1"
    assert itgr_item.item_type == "itgr"


def test_container_structure_lookups(sample_container_xml):
    """Test: Container-Struktur-Lookups."""
    structure = parse_container_structure(sample_container_xml)
    
    # Lookup by RefId
    item = structure.get_by_ref_id("3845")
    assert item is not None
    assert item.title == "Test 1"
    
    # Lookup by ItemId
    item = structure.get_by_item_id("9124")
    assert item is not None
    assert item.title == "Ordner 1"
    
    # Nicht existierende IDs
    assert structure.get_by_ref_id("99999") is None
    assert structure.get_by_item_id("99999") is None


def test_get_items_by_type(sample_container_xml):
    """Test: Items nach Typ filtern."""
    structure = parse_container_structure(sample_container_xml)
    
    # Alle Tests
    tests = structure.get_items_by_type("tst")
    assert len(tests) == 1
    assert tests[0].title == "Test 1"
    
    # Alle Folders
    folders = structure.get_items_by_type("fold")
    assert len(folders) == 1
    assert folders[0].title == "Ordner 1"
    
    # Alle ItemGroups
    itgrs = structure.get_items_by_type("itgr")
    assert len(itgrs) == 1
    
    # Nicht existierender Typ
    unknown = structure.get_items_by_type("unknown")
    assert len(unknown) == 0


def test_container_item_to_dict(sample_container_xml):
    """Test: Container-Item zu Dictionary."""
    structure = parse_container_structure(sample_container_xml)
    root = structure.root_item
    
    dict_repr = root.to_dict()
    
    assert dict_repr['ref_id'] == "3812"
    assert dict_repr['title'] == "Testkurs"
    assert dict_repr['type'] == "grp"
    assert 'children' in dict_repr
    assert len(dict_repr['children']) == 3


def test_container_structure_to_dict(sample_container_xml):
    """Test: Container-Struktur zu Dictionary."""
    structure = parse_container_structure(sample_container_xml)
    dict_repr = structure.to_dict()
    
    assert 'root' in dict_repr
    assert 'total_items' in dict_repr
    assert 'types' in dict_repr
    
    # Total Items: 1 grp + 1 tst + 1 fold + 1 itgr = 4
    assert dict_repr['total_items'] == 4
    
    # Typ-Verteilung
    assert dict_repr['types']['grp'] == 1
    assert dict_repr['types']['tst'] == 1
    assert dict_repr['types']['fold'] == 1
    assert dict_repr['types']['itgr'] == 1


def test_get_all_descendants(sample_container_xml):
    """Test: Alle Nachkommen abrufen."""
    structure = parse_container_structure(sample_container_xml)
    root = structure.root_item
    
    descendants = root.get_all_descendants()
    
    # Sollte alle 3 Kinder enthalten
    assert len(descendants) == 3
    titles = [d.title for d in descendants]
    assert "Test 1" in titles
    assert "Ordner 1" in titles
    assert "ItemGroup 1" in titles


def test_parse_without_container_xml(temp_component_dir):
    """Test: Parsen ohne Container-XML."""
    structure = parse_container_structure(temp_component_dir)
    assert structure is None


def test_nested_items():
    """Test: Verschachtelte Items."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Erstelle Verzeichnisstruktur
        container_dir = os.path.join(temp_dir, 'Services', 'Container', 'set_1')
        os.makedirs(container_dir, exist_ok=True)
        
        # XML mit verschachtelten Items
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
<exp:Export xmlns:exp="http://www.ilias.de/Services/Export/exp/4_1" xmlns="https://www.ilias.de/Modules/Folder/fold/4_1">
  <exp:ExportItem Id="1">
    <Items>
      <Item RefId="1" Id="1" Title="Root" Type="grp">
        <Item RefId="2" Id="2" Title="Level 1-1" Type="fold">
          <Item RefId="3" Id="3" Title="Level 2-1" Type="file"/>
          <Item RefId="4" Id="4" Title="Level 2-2" Type="file"/>
        </Item>
        <Item RefId="5" Id="5" Title="Level 1-2" Type="tst"/>
      </Item>
    </Items>
  </exp:ExportItem>
</exp:Export>
"""
        
        xml_path = os.path.join(container_dir, 'export.xml')
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # Parse
        structure = parse_container_structure(temp_dir)
        
        assert structure is not None
        
        # Root hat 2 Kinder
        assert len(structure.root_item.children) == 2
        
        # Erstes Kind (fold) hat 2 Kinder
        folder = structure.root_item.children[0]
        assert folder.title == "Level 1-1"
        assert len(folder.children) == 2
        
        # Verschachtelte Files prüfen
        file1 = folder.children[0]
        assert file1.title == "Level 2-1"
        assert file1.item_type == "file"
        
        # Alle Nachkommen
        descendants = structure.root_item.get_all_descendants()
        assert len(descendants) == 4  # 2 direkte + 2 verschachtelte
        
        # Lookup funktioniert auch für verschachtelte Items
        item = structure.get_by_ref_id("3")
        assert item is not None
        assert item.title == "Level 2-1"
    
    finally:
        shutil.rmtree(temp_dir)


def test_real_ilias_structure():
    """Test: Echte ILIAS-Struktur aus dummy_files."""
    # Pfad zur echten ILIAS-Struktur
    ilias_path = "/Users/alexander/Repository/ai/oersynch-ai/dummy_files/ilias_kurs/set_1/1744020005__13869__grp_9094"
    
    if not os.path.exists(ilias_path):
        pytest.skip("Dummy-Dateien nicht verfügbar")
    
    structure = parse_container_structure(ilias_path)
    
    assert structure is not None
    assert structure.root_item is not None
    
    # Root sollte eine Gruppe sein
    assert structure.root_item.item_type == "grp"
    assert "Vorlage" in structure.root_item.title or "Adaptivitätsstufe" in structure.root_item.title
    
    # Sollte Kinder haben
    assert len(structure.root_item.children) > 0
    
    # Prüfe, dass verschiedene Typen vorhanden sind
    types = structure._count_types()
    assert 'grp' in types
    
    # Lookup sollte funktionieren
    assert len(structure.item_by_ref_id) > 0
    assert len(structure.item_by_item_id) > 0
    
    print(f"\n--- Echte ILIAS-Struktur ---")
    print(f"Root: {structure.root_item.title} ({structure.root_item.item_type})")
    print(f"Gesamt Items: {len(structure.item_by_item_id)}")
    print(f"Typ-Verteilung: {types}")
    print(f"Kinder des Roots: {len(structure.root_item.children)}")
    
    for child in structure.root_item.children:
        print(f"  - {child.title} ({child.item_type})")

