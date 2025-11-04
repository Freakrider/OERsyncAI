"""
Tests für den ItemGroupResolver.
"""

import os
import pytest
from shared.utils.ilias.itemgroup_resolver import (
    ItemGroupResolver,
    ResolvedItem,
    resolve_itemgroup
)
from shared.utils.ilias.container_parser import parse_container_structure
from shared.utils.ilias.analyzer import IliasAnalyzer


def test_resolved_item_creation():
    """Test: ResolvedItem erstellen."""
    item = ResolvedItem(
        item_id="123",
        ref_id="456",
        title="Test Item",
        item_type="file"
    )
    
    assert item.item_id == "123"
    assert item.ref_id == "456"
    assert item.title == "Test Item"
    assert item.item_type == "file"


def test_resolved_item_to_dict():
    """Test: ResolvedItem zu Dictionary."""
    item = ResolvedItem(
        item_id="123",
        title="Test",
        item_type="file",
        metadata={"size": 1024}
    )
    
    dict_repr = item.to_dict()
    
    assert dict_repr['item_id'] == "123"
    assert dict_repr['title'] == "Test"
    assert dict_repr['type'] == "file"
    assert dict_repr['metadata']['size'] == 1024


def test_itemgroup_resolver_initialization():
    """Test: ItemGroupResolver initialisieren."""
    resolver = ItemGroupResolver()
    
    assert resolver.container_structure is None
    assert resolver.components == []
    assert len(resolver.component_by_id) == 0


def test_itemgroup_resolver_with_components():
    """Test: ItemGroupResolver mit Komponenten."""
    components = [
        {
            'type': 'file',
            'data': {'id': '123', 'title': 'Test File'},
            'path': '/test/path'
        },
        {
            'type': 'test',
            'data': {'id': '456', 'title': 'Test Quiz'},
            'path': '/test/path2'
        }
    ]
    
    resolver = ItemGroupResolver(components=components)
    
    assert len(resolver.component_by_id) == 2
    assert '123' in resolver.component_by_id
    assert '456' in resolver.component_by_id


def test_resolve_itemgroup_empty():
    """Test: Leere ItemGroup auflösen."""
    resolver = ItemGroupResolver()
    
    itemgroup_data = {
        'id': '999',
        'title': 'Empty Group',
        'items': []
    }
    
    resolved = resolver.resolve_itemgroup(itemgroup_data)
    
    assert len(resolved) == 0


def test_resolve_itemgroup_with_items():
    """Test: ItemGroup mit Items auflösen."""
    components = [
        {
            'type': 'file',
            'data': {'id': '123', 'title': 'Document.pdf'},
            'path': '/test/file'
        }
    ]
    
    resolver = ItemGroupResolver(components=components)
    
    itemgroup_data = {
        'id': '999',
        'title': 'Documents',
        'items': [
            {'item_id': '123', 'title': 'Document.pdf'}
        ]
    }
    
    resolved = resolver.resolve_itemgroup(itemgroup_data)
    
    assert len(resolved) == 1
    assert resolved[0].item_id == '123'
    assert resolved[0].title == 'Document.pdf'
    assert resolved[0].item_type == 'file'


def test_resolve_itemgroup_with_container_structure():
    """Test: ItemGroup mit Container-Struktur auflösen."""
    ilias_path = "/Users/alexander/Repository/ai/oersynch-ai/dummy_files/ilias_kurs/set_1/1744020005__13869__grp_9094"
    
    if not os.path.exists(ilias_path):
        pytest.skip("Dummy-Dateien nicht verfügbar")
    
    # Parse Container-Struktur
    structure = parse_container_structure(ilias_path)
    
    if not structure:
        pytest.skip("Keine Container-Struktur verfügbar")
    
    resolver = ItemGroupResolver(container_structure=structure)
    
    # Finde eine ItemGroup in der Struktur
    itemgroups = structure.get_items_by_type('itgr')
    
    if not itemgroups:
        pytest.skip("Keine ItemGroups in der Struktur")
    
    # Nutze die erste ItemGroup
    itemgroup = itemgroups[0]
    
    # Erstelle ItemGroup-Daten für den Resolver
    # (Normalerweise würden diese vom ItemGroupParser kommen)
    itemgroup_data = {
        'id': itemgroup.item_id,
        'title': itemgroup.title,
        'items': []  # In diesem Test haben wir keine Items-Daten
    }
    
    resolved = resolver.resolve_itemgroup(itemgroup_data)
    
    # Sollte leer sein, da wir keine Items-Daten haben
    assert isinstance(resolved, list)


def test_resolve_itemgroup_unknown_items():
    """Test: ItemGroup mit unbekannten Items."""
    resolver = ItemGroupResolver()
    
    itemgroup_data = {
        'id': '999',
        'title': 'Unknown Items',
        'items': [
            {'item_id': '123', 'title': 'Unknown Item 1'},
            {'item_id': '456', 'title': 'Unknown Item 2'}
        ]
    }
    
    resolved = resolver.resolve_itemgroup(itemgroup_data)
    
    # Sollte Fallback-Items erstellen
    assert len(resolved) == 2
    assert resolved[0].item_id == '123'
    assert resolved[0].title == 'Unknown Item 1'
    assert resolved[1].item_id == '456'


def test_resolve_multiple_itemgroups():
    """Test: Mehrere ItemGroups auflösen."""
    components = [
        {'type': 'file', 'data': {'id': '1', 'title': 'File 1'}},
        {'type': 'file', 'data': {'id': '2', 'title': 'File 2'}},
        {'type': 'test', 'data': {'id': '3', 'title': 'Test 1'}}
    ]
    
    resolver = ItemGroupResolver(components=components)
    
    itemgroups = [
        {
            'id': 'grp1',
            'title': 'Group 1',
            'items': [{'item_id': '1'}, {'item_id': '2'}]
        },
        {
            'id': 'grp2',
            'title': 'Group 2',
            'items': [{'item_id': '3'}]
        }
    ]
    
    results = resolver.resolve_all_itemgroups(itemgroups)
    
    assert 'grp1' in results
    assert 'grp2' in results
    assert len(results['grp1']) == 2
    assert len(results['grp2']) == 1


def test_get_itemgroup_summary():
    """Test: ItemGroup-Zusammenfassung erstellen."""
    components = [
        {'type': 'file', 'data': {'id': '1', 'title': 'File 1'}},
        {'type': 'file', 'data': {'id': '2', 'title': 'File 2'}},
        {'type': 'test', 'data': {'id': '3', 'title': 'Test 1'}}
    ]
    
    resolver = ItemGroupResolver(components=components)
    
    itemgroup_data = {
        'id': 'grp1',
        'title': 'Mixed Group',
        'items': [
            {'item_id': '1'},
            {'item_id': '2'},
            {'item_id': '3'}
        ]
    }
    
    summary = resolver.get_itemgroup_summary(itemgroup_data)
    
    assert summary['title'] == 'Mixed Group'
    assert summary['id'] == 'grp1'
    assert summary['total_items'] == 3
    assert 'file' in summary['type_counts']
    assert 'test' in summary['type_counts']
    assert summary['type_counts']['file'] == 2
    assert summary['type_counts']['test'] == 1


def test_convenience_function():
    """Test: Convenience-Funktion."""
    components = [
        {'type': 'file', 'data': {'id': '123', 'title': 'Test'}}
    ]
    
    itemgroup_data = {
        'id': '999',
        'items': [{'item_id': '123'}]
    }
    
    resolved = resolve_itemgroup(itemgroup_data, components=components)
    
    assert len(resolved) == 1
    assert resolved[0].item_id == '123'


def test_resolve_with_real_ilias_data():
    """Test: Auflösen mit echten ILIAS-Daten."""
    ilias_path = "/Users/alexander/Repository/ai/oersynch-ai/dummy_files/ilias_kurs"
    
    if not os.path.exists(ilias_path):
        pytest.skip("Dummy-Dateien nicht verfügbar")
    
    # Analyzer verwenden, um Komponenten zu extrahieren
    analyzer = IliasAnalyzer(ilias_path)
    success = analyzer.analyze()
    
    if not success or not analyzer.container_structure:
        pytest.skip("Analyzer konnte Kurs nicht analysieren")
    
    # Erstelle Resolver mit Analyzer-Daten
    resolver = ItemGroupResolver(
        container_structure=analyzer.container_structure,
        components=analyzer.components
    )
    
    # Finde ItemGroups
    itemgroups = [
        comp for comp in analyzer.components
        if comp['type'] == 'itgr'
    ]
    
    print(f"\n--- Gefundene ItemGroups ---")
    print(f"Anzahl: {len(itemgroups)}")
    
    if itemgroups:
        # Teste die erste ItemGroup
        itemgroup = itemgroups[0]
        itemgroup_data = itemgroup['data']
        
        print(f"ItemGroup: {itemgroup_data.get('title')}")
        print(f"Items in Daten: {len(itemgroup_data.get('items', []))}")
        
        resolved = resolver.resolve_itemgroup(itemgroup_data)
        
        print(f"Aufgelöste Items: {len(resolved)}")
        for item in resolved:
            print(f"  - {item.title} ({item.item_type})")
        
        assert isinstance(resolved, list)


def test_resolve_itemgroup_without_item_id():
    """Test: Item ohne item_id sollte übersprungen werden."""
    resolver = ItemGroupResolver()
    
    itemgroup_data = {
        'id': '999',
        'items': [
            {'title': 'Item ohne ID'},  # Kein item_id!
            {'item_id': '123', 'title': 'Item mit ID'}
        ]
    }
    
    resolved = resolver.resolve_itemgroup(itemgroup_data)
    
    # Nur ein Item sollte aufgelöst werden
    assert len(resolved) == 1
    assert resolved[0].item_id == '123'

