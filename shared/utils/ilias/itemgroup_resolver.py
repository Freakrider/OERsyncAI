"""
ItemGroup-Resolver für ILIAS-Exporte.

Dieser Resolver löst ItemGroups zu ihren tatsächlichen Items auf und
ermöglicht die Zuordnung von ItemGroup-Items zu echten Komponenten.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ResolvedItem:
    """Repräsentiert ein aufgelöstes Item aus einer ItemGroup."""
    
    item_id: str
    ref_id: Optional[str] = None
    title: str = ""
    item_type: str = "unknown"
    component_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert das Item zu einem Dictionary."""
        return {
            'item_id': self.item_id,
            'ref_id': self.ref_id,
            'title': self.title,
            'type': self.item_type,
            'component_path': self.component_path,
            'metadata': self.metadata or {}
        }


class ItemGroupResolver:
    """
    Resolver für ItemGroups in ILIAS-Exporten.
    
    Dieser Resolver nimmt eine ItemGroup und die Container-Struktur
    und löst die ItemGroup-Items zu ihren tatsächlichen Komponenten auf.
    """
    
    def __init__(self, container_structure=None, components: List[Dict[str, Any]] = None):
        """
        Initialisiert den Resolver.
        
        Args:
            container_structure: ContainerStructure mit der Hierarchie
            components: Liste der analysierten Komponenten
        """
        self.container_structure = container_structure
        self.components = components or []
        
        # Erstelle Lookup-Dictionaries für schnellen Zugriff
        self.component_by_id: Dict[str, Dict[str, Any]] = {}
        self._build_component_lookup()
    
    def _build_component_lookup(self) -> None:
        """Baut Lookup-Dictionaries für Komponenten auf."""
        for component in self.components:
            comp_id = component.get('data', {}).get('id')
            if comp_id:
                self.component_by_id[comp_id] = component
    
    def resolve_itemgroup(self, itemgroup_data: Dict[str, Any]) -> List[ResolvedItem]:
        """
        Löst eine ItemGroup zu ihren Items auf.
        
        Args:
            itemgroup_data: Dictionary mit ItemGroup-Daten (aus dem Parser)
            
        Returns:
            Liste von ResolvedItem-Objekten
        """
        resolved_items = []
        
        # Extrahiere die Items aus der ItemGroup
        items = itemgroup_data.get('items', [])
        
        if not items:
            logger.warning(f"ItemGroup hat keine Items: {itemgroup_data.get('title', 'Unbekannt')}")
            return resolved_items
        
        logger.info(f"Löse ItemGroup auf: {itemgroup_data.get('title')} mit {len(items)} Items")
        
        for item in items:
            # Item-ID extrahieren
            item_id = item.get('item_id')
            if not item_id:
                logger.warning(f"Item hat keine item_id: {item}")
                continue
            
            # Versuche, das Item aufzulösen
            resolved_item = self._resolve_single_item(item_id, item)
            
            if resolved_item:
                resolved_items.append(resolved_item)
            else:
                # Fallback: Erstelle ein ResolvedItem mit den verfügbaren Daten
                resolved_items.append(ResolvedItem(
                    item_id=item_id,
                    title=item.get('title', f'Item {item_id}'),
                    item_type='unknown',
                    metadata=item
                ))
        
        logger.info(f"ItemGroup aufgelöst: {len(resolved_items)} Items gefunden")
        return resolved_items
    
    def _resolve_single_item(self, item_id: str, item_data: Dict[str, Any]) -> Optional[ResolvedItem]:
        """
        Löst ein einzelnes Item auf.
        
        Args:
            item_id: Die Item-ID
            item_data: Zusätzliche Item-Daten aus der ItemGroup
            
        Returns:
            ResolvedItem oder None
        """
        # 1. Versuche über Container-Struktur
        if self.container_structure:
            container_item = self.container_structure.get_by_item_id(item_id)
            if container_item:
                logger.debug(f"Item {item_id} über Container-Struktur gefunden: {container_item.title}")
                return ResolvedItem(
                    item_id=item_id,
                    ref_id=container_item.ref_id,
                    title=container_item.title,
                    item_type=container_item.item_type,
                    metadata={'from_container': True}
                )
        
        # 2. Versuche über Komponenten-Liste
        component = self.component_by_id.get(item_id)
        if component:
            comp_data = component.get('data', {})
            logger.debug(f"Item {item_id} über Komponenten-Liste gefunden: {comp_data.get('title')}")
            return ResolvedItem(
                item_id=item_id,
                title=comp_data.get('title', ''),
                item_type=component.get('type', 'unknown'),
                component_path=component.get('path'),
                metadata=comp_data
            )
        
        # 3. Nutze Informationen aus item_data
        if item_data.get('title'):
            logger.debug(f"Item {item_id} konnte nicht vollständig aufgelöst werden, nutze item_data")
            return ResolvedItem(
                item_id=item_id,
                title=item_data.get('title', f'Item {item_id}'),
                item_type=item_data.get('type', 'unknown'),
                metadata=item_data
            )
        
        logger.warning(f"Item {item_id} konnte nicht aufgelöst werden")
        return None
    
    def resolve_all_itemgroups(self, itemgroups: List[Dict[str, Any]]) -> Dict[str, List[ResolvedItem]]:
        """
        Löst mehrere ItemGroups auf.
        
        Args:
            itemgroups: Liste von ItemGroup-Dictionaries
            
        Returns:
            Dictionary mit ItemGroup-ID als Key und Liste von ResolvedItems als Value
        """
        results = {}
        
        for itemgroup in itemgroups:
            itemgroup_id = itemgroup.get('id') or itemgroup.get('data', {}).get('id')
            if not itemgroup_id:
                logger.warning(f"ItemGroup hat keine ID: {itemgroup}")
                continue
            
            # Extrahiere die ItemGroup-Daten
            if 'data' in itemgroup:
                itemgroup_data = itemgroup['data']
            else:
                itemgroup_data = itemgroup
            
            resolved_items = self.resolve_itemgroup(itemgroup_data)
            results[itemgroup_id] = resolved_items
        
        return results
    
    def get_itemgroup_summary(self, itemgroup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Erstellt eine Zusammenfassung einer aufgelösten ItemGroup.
        
        Args:
            itemgroup_data: ItemGroup-Daten
            
        Returns:
            Dictionary mit Zusammenfassung
        """
        resolved_items = self.resolve_itemgroup(itemgroup_data)
        
        # Zähle Typen
        type_counts = {}
        for item in resolved_items:
            type_counts[item.item_type] = type_counts.get(item.item_type, 0) + 1
        
        return {
            'title': itemgroup_data.get('title', 'Unbekannt'),
            'id': itemgroup_data.get('id', ''),
            'total_items': len(resolved_items),
            'resolved_items': [item.to_dict() for item in resolved_items],
            'type_counts': type_counts,
            'types': list(type_counts.keys())
        }


def resolve_itemgroup(itemgroup_data: Dict[str, Any], 
                     container_structure=None,
                     components: List[Dict[str, Any]] = None) -> List[ResolvedItem]:
    """
    Convenience-Funktion zum Auflösen einer ItemGroup.
    
    Args:
        itemgroup_data: ItemGroup-Daten
        container_structure: Optional ContainerStructure
        components: Optional Liste von Komponenten
        
    Returns:
        Liste von ResolvedItem-Objekten
    """
    resolver = ItemGroupResolver(container_structure, components)
    return resolver.resolve_itemgroup(itemgroup_data)

