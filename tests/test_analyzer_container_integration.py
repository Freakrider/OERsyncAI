"""
Tests für die Integration der Container-Struktur im IliasAnalyzer.
"""

import os
import pytest
from shared.utils.ilias.analyzer import IliasAnalyzer


def test_analyzer_parses_container_structure():
    """Test: Analyzer parst die Container-Struktur."""
    # Pfad zur echten ILIAS-Struktur
    ilias_path = "/Users/alexander/Repository/ai/oersynch-ai/dummy_files/ilias_kurs"
    
    if not os.path.exists(ilias_path):
        pytest.skip("Dummy-Dateien nicht verfügbar")
    
    # Analyzer erstellen und analysieren
    analyzer = IliasAnalyzer(ilias_path)
    success = analyzer.analyze()
    
    assert success, "Analyse sollte erfolgreich sein"
    
    # Container-Struktur sollte geparst worden sein
    assert analyzer.container_structure is not None, "Container-Struktur sollte vorhanden sein"
    
    # Container-Struktur prüfen
    structure = analyzer.container_structure
    assert structure.root_item is not None
    assert structure.root_item.item_type == "grp"
    assert "Vorlage" in structure.root_item.title or "Adaptivitätsstufe" in structure.root_item.title
    
    # Sollte Kinder haben
    assert len(structure.root_item.children) > 0
    
    # course_structure sollte has_container_structure=True haben
    assert analyzer.course_structure.get("has_container_structure") is True
    
    print(f"\n--- Container-Struktur im Analyzer ---")
    print(f"Root: {structure.root_item.title}")
    print(f"Anzahl Items: {len(structure.item_by_item_id)}")
    print(f"Anzahl Kinder: {len(structure.root_item.children)}")
    print(f"Typ-Verteilung: {structure._count_types()}")


def test_analyzer_without_container_structure(tmp_path):
    """Test: Analyzer funktioniert auch ohne Container-Struktur."""
    # Erstelle ein Test-Verzeichnis ohne Container-Struktur
    test_dir = tmp_path / "test_ilias"
    test_dir.mkdir()
    
    # Erstelle eine einfache Manifest-Datei
    manifest = test_dir / "manifest.xml"
    manifest.write_text("""<?xml version="1.0" encoding="utf-8"?>
<Manifest MainEntity="grp" Title="Test Kurs" InstallationId="1" InstallationUrl="http://test">
</Manifest>
""")
    
    # Analyzer erstellen und analysieren
    analyzer = IliasAnalyzer(str(test_dir))
    success = analyzer.analyze()
    
    # Sollte trotzdem erfolgreich sein
    assert success
    
    # Container-Struktur sollte None sein
    assert analyzer.container_structure is None
    
    # course_structure sollte has_container_structure=False haben
    assert analyzer.course_structure.get("has_container_structure") is False


def test_container_structure_lookup_by_ref_id():
    """Test: Lookup von Items nach RefId."""
    ilias_path = "/Users/alexander/Repository/ai/oersynch-ai/dummy_files/ilias_kurs"
    
    if not os.path.exists(ilias_path):
        pytest.skip("Dummy-Dateien nicht verfügbar")
    
    analyzer = IliasAnalyzer(ilias_path)
    analyzer.analyze()
    
    assert analyzer.container_structure is not None
    
    # Suche nach Items anhand von RefIds
    # (Die genauen RefIds müssen aus der echten Struktur kommen)
    structure = analyzer.container_structure
    
    # Sollte mehrere Items haben
    assert len(structure.item_by_ref_id) > 0
    assert len(structure.item_by_item_id) > 0
    
    # Prüfe, dass wir Items nach RefId finden können
    for ref_id, item in structure.item_by_ref_id.items():
        assert item is not None
        assert item.ref_id == ref_id
        print(f"RefId {ref_id}: {item.title} ({item.item_type})")


def test_container_structure_types():
    """Test: Container-Struktur enthält erwartete Typen."""
    ilias_path = "/Users/alexander/Repository/ai/oersynch-ai/dummy_files/ilias_kurs"
    
    if not os.path.exists(ilias_path):
        pytest.skip("Dummy-Dateien nicht verfügbar")
    
    analyzer = IliasAnalyzer(ilias_path)
    analyzer.analyze()
    
    assert analyzer.container_structure is not None
    structure = analyzer.container_structure
    
    # Erwartete Typen
    types = structure._count_types()
    
    # Sollte mindestens eine Gruppe haben
    assert 'grp' in types
    assert types['grp'] >= 1
    
    # Sollte verschiedene Typen haben
    assert len(types) > 1
    
    print(f"\n--- Gefundene Typen ---")
    for item_type, count in types.items():
        print(f"{item_type}: {count}")

