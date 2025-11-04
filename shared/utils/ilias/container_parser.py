"""
Container-Struktur-Parser für ILIAS-Exporte.

Dieser Parser analysiert die Container-Struktur aus Services/Container/export.xml
und extrahiert die hierarchische Organisation der Kursinhalte.
"""

import os
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ContainerItem:
    """Repräsentiert ein Item in der Container-Struktur."""
    
    ref_id: str
    item_id: str
    title: str
    item_type: str
    page: str = ""
    start_page: str = ""
    style: str = "0"
    offline: bool = False
    timing: Optional[Dict[str, Any]] = None
    children: List['ContainerItem'] = field(default_factory=list)
    
    def add_child(self, child: 'ContainerItem') -> None:
        """Fügt ein Kind-Item hinzu."""
        self.children.append(child)
    
    def get_all_descendants(self) -> List['ContainerItem']:
        """Gibt alle Nachkommen (rekursiv) zurück."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert das Item zu einem Dictionary."""
        return {
            'ref_id': self.ref_id,
            'item_id': self.item_id,
            'title': self.title,
            'type': self.item_type,
            'page': self.page,
            'start_page': self.start_page,
            'style': self.style,
            'offline': self.offline,
            'timing': self.timing,
            'children': [child.to_dict() for child in self.children]
        }


@dataclass
class ContainerStructure:
    """Repräsentiert die komplette Container-Struktur."""
    
    root_item: ContainerItem
    item_by_ref_id: Dict[str, ContainerItem] = field(default_factory=dict)
    item_by_item_id: Dict[str, ContainerItem] = field(default_factory=dict)
    
    def __post_init__(self):
        """Erstellt die Lookup-Dictionaries nach der Initialisierung."""
        self._build_lookups(self.root_item)
    
    def _build_lookups(self, item: ContainerItem) -> None:
        """Baut die Lookup-Dictionaries rekursiv auf."""
        if item.ref_id:
            self.item_by_ref_id[item.ref_id] = item
        if item.item_id:
            self.item_by_item_id[item.item_id] = item
        
        for child in item.children:
            self._build_lookups(child)
    
    def get_by_ref_id(self, ref_id: str) -> Optional[ContainerItem]:
        """Findet ein Item anhand seiner RefId."""
        return self.item_by_ref_id.get(ref_id)
    
    def get_by_item_id(self, item_id: str) -> Optional[ContainerItem]:
        """Findet ein Item anhand seiner ItemId."""
        return self.item_by_item_id.get(item_id)
    
    def get_items_by_type(self, item_type: str) -> List[ContainerItem]:
        """Findet alle Items eines bestimmten Typs."""
        items = []
        for item in self.item_by_item_id.values():
            if item.item_type == item_type:
                items.append(item)
        return items
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert die Struktur zu einem Dictionary."""
        return {
            'root': self.root_item.to_dict(),
            'total_items': len(self.item_by_item_id),
            'types': self._count_types()
        }
    
    def _count_types(self) -> Dict[str, int]:
        """Zählt die Anzahl der Items pro Typ."""
        type_counts = {}
        for item in self.item_by_item_id.values():
            type_counts[item.item_type] = type_counts.get(item.item_type, 0) + 1
        return type_counts


class ContainerStructureParser:
    """
    Parser für die Container-Struktur aus Services/Container/export.xml.
    
    Dieser Parser extrahiert die hierarchische Organisation der Kursinhalte
    und stellt Methoden zur Abfrage der Struktur bereit.
    """
    
    def __init__(self, component_path: str):
        """
        Initialisiert den Parser.
        
        Args:
            component_path: Pfad zum Komponenten-Verzeichnis (z.B. set_1/1744020005__13869__grp_9094)
        """
        self.component_path = component_path
        self.container_xml_path = None
        self._find_container_xml()
    
    def _find_container_xml(self) -> None:
        """Sucht die Container-XML-Datei im Komponenten-Verzeichnis."""
        # Suche in Services/Container/set_*/export.xml
        container_dir = os.path.join(self.component_path, 'Services', 'Container')
        
        if not os.path.exists(container_dir):
            logger.warning(f"Container-Verzeichnis nicht gefunden: {container_dir}")
            return
        
        # Suche nach set_*-Verzeichnissen
        for item in os.listdir(container_dir):
            item_path = os.path.join(container_dir, item)
            if os.path.isdir(item_path) and item.startswith('set_'):
                export_xml = os.path.join(item_path, 'export.xml')
                if os.path.exists(export_xml):
                    self.container_xml_path = export_xml
                    logger.info(f"Container-XML gefunden: {export_xml}")
                    return
        
        logger.warning(f"Keine Container-XML gefunden in {container_dir}")
    
    def parse(self) -> Optional[ContainerStructure]:
        """
        Parst die Container-Struktur.
        
        Returns:
            ContainerStructure oder None, wenn keine Container-XML gefunden wurde
        """
        if not self.container_xml_path:
            logger.error("Keine Container-XML verfügbar zum Parsen")
            return None
        
        if not os.path.exists(self.container_xml_path):
            logger.error(f"Container-XML existiert nicht: {self.container_xml_path}")
            return None
        
        try:
            tree = ET.parse(self.container_xml_path)
            root = tree.getroot()
            
            # Finde das ExportItem
            export_item = root.find('.//{http://www.ilias.de/Services/Export/exp/4_1}ExportItem')
            if export_item is None:
                # Versuche ohne Namespace
                export_item = root.find('.//ExportItem')
            
            if export_item is None:
                logger.error("Kein ExportItem in Container-XML gefunden")
                return None
            
            # Finde das Items-Element
            items_elem = None
            for child in export_item:
                if child.tag.endswith('Items') or child.tag == 'Items':
                    items_elem = child
                    break
            
            if items_elem is None:
                logger.error("Kein Items-Element in Container-XML gefunden")
                return None
            
            # Parse das Root-Item (sollte das erste Item sein)
            root_item_elem = None
            for child in items_elem:
                if child.tag.endswith('Item') or child.tag == 'Item':
                    root_item_elem = child
                    break
            
            if root_item_elem is None:
                logger.error("Kein Root-Item in Container-XML gefunden")
                return None
            
            # Parse das Root-Item rekursiv
            root_item = self._parse_item(root_item_elem)
            
            # Erstelle die ContainerStructure
            structure = ContainerStructure(root_item=root_item)
            
            logger.info(f"Container-Struktur geparst: {len(structure.item_by_item_id)} Items gefunden")
            logger.info(f"Typ-Verteilung: {structure._count_types()}")
            
            return structure
        
        except ET.ParseError as e:
            logger.error(f"Fehler beim Parsen der Container-XML: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unerwarteter Fehler beim Parsen der Container-Struktur: {e}")
            return None
    
    def _parse_item(self, item_elem: ET.Element) -> ContainerItem:
        """
        Parst ein Item-Element rekursiv.
        
        Args:
            item_elem: XML-Element des Items
            
        Returns:
            ContainerItem mit allen Kindern
        """
        # Attribute extrahieren
        ref_id = item_elem.get('RefId', '')
        item_id = item_elem.get('Id', '')
        title = item_elem.get('Title', '')
        item_type = item_elem.get('Type', 'unknown')
        page = item_elem.get('Page', '')
        start_page = item_elem.get('StartPage', '')
        style = item_elem.get('Style', '0')
        offline = item_elem.get('Offline', '0') == '1'
        
        # Timing extrahieren, falls vorhanden
        timing = self._parse_timing(item_elem)
        
        # Erstelle das Item
        item = ContainerItem(
            ref_id=ref_id,
            item_id=item_id,
            title=title,
            item_type=item_type,
            page=page,
            start_page=start_page,
            style=style,
            offline=offline,
            timing=timing
        )
        
        # Parse Kinder rekursiv
        for child_elem in item_elem:
            if child_elem.tag.endswith('Item') or child_elem.tag == 'Item':
                child_item = self._parse_item(child_elem)
                item.add_child(child_item)
        
        return item
    
    def _parse_timing(self, item_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Extrahiert Timing-Informationen aus einem Item-Element.
        
        Args:
            item_elem: XML-Element des Items
            
        Returns:
            Dictionary mit Timing-Informationen oder None
        """
        # Suche direkt unter dem Item (nicht rekursiv)
        timing_elem = None
        for child in item_elem:
            if child.tag.endswith('Timing') or child.tag == 'Timing':
                timing_elem = child
                break
        
        if timing_elem is None:
            return None
        
        timing = {
            'type': timing_elem.get('Type', ''),
            'visible': timing_elem.get('Visible', '0') == '1',
            'changeable': timing_elem.get('Changeable', '0') == '1'
        }
        
        # Zeitpunkte extrahieren (direkte Kinder des Timing-Elements)
        for field in ['Start', 'End', 'SuggestionStart', 'SuggestionEnd']:
            elem = None
            for child in timing_elem:
                if child.tag.endswith(field) or child.tag == field:
                    elem = child
                    break
            
            if elem is not None and elem.text:
                timing[field.lower()] = elem.text
        
        return timing if len(timing) > 3 else None  # Nur wenn mehr als nur die Attribute vorhanden sind


def parse_container_structure(component_path: str) -> Optional[ContainerStructure]:
    """
    Convenience-Funktion zum Parsen einer Container-Struktur.
    
    Args:
        component_path: Pfad zum Komponenten-Verzeichnis
        
    Returns:
        ContainerStructure oder None
    """
    parser = ContainerStructureParser(component_path)
    return parser.parse()

