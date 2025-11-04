"""
Parser für ILIAS-ItemGroup-Komponenten.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
import logging
import os
from .base import IliasComponentParser

logger = logging.getLogger(__name__)

class ItemGroupParser(IliasComponentParser):
    """Parser für ILIAS-ItemGroup-Komponenten."""
    
    def _parse_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parst die XML-Daten einer ILIAS-ItemGroup-Komponente.
        
        Args:
            root: XML-Root-Element
            
        Returns:
            Dict mit den extrahierten Daten
        """
        item_group_data = {}
        
        try:
            # Suche nach ExportItem/ItemGroup
            export_item = self._find_element(root, './/exp:ExportItem', self.namespaces)
            if export_item is None:
                logger.warning("Kein ExportItem-Element gefunden")
                return self._extract_basic_info()
            
            # Versuche zuerst DataSet-Struktur (moderne ILIAS-Exporte)
            dataset = export_item.find('.//ds:DataSet', self.namespaces)
            if dataset is not None:
                # Extrahiere ItemGroup-Daten aus DataSet (ds:Rec sind direkte Kinder!)
                for rec in dataset.findall('ds:Rec[@Entity="itgr"]', self.namespaces):
                    # Itgr kann einen eigenen Namespace haben, daher direkt durch Kinder iterieren
                    for child in rec:
                        if child.tag.endswith('Itgr'):
                            # Durchlaufe alle Kind-Elemente und extrahiere Felder
                            for elem in child:
                                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                                if tag_name in ['Id', 'Title', 'Description', 'HideTitle', 'Behaviour']:
                                    item_group_data[tag_name.lower()] = self._get_text(elem)
                            break
                
                # Extrahiere Item-Referenzen aus DataSet (ds:Rec sind direkte Kinder!)
                items = []
                for rec in dataset.findall('ds:Rec[@Entity="itgr_item"]', self.namespaces):
                    # ItgrItem kann einen eigenen Namespace haben
                    for child in rec:
                        if child.tag.endswith('ItgrItem'):
                            item_id = None
                            itgr_id = None
                            for elem in child:
                                if elem.tag.endswith('ItemId'):
                                    item_id = self._get_text(elem)
                                elif elem.tag.endswith('ItgrId'):
                                    itgr_id = self._get_text(elem)
                            
                            if item_id:
                                items.append({
                                    'item_id': item_id,
                                    'itgr_id': itgr_id,
                                    'type': 'ref'  # Referenz auf ein anderes Item
                                })
                            break
                
                if items:
                    item_group_data['items'] = items
                    logger.info(f"ItemGroup '{item_group_data.get('title', 'Unbekannt')}' mit {len(items)} Items aus DataSet geparst")
                
                return item_group_data
            
            # Fallback: Alte ItemGroup-Struktur
            item_group = export_item.find('.//ItemGroup')
            if item_group is None:
                # Versuche alternative Pfade
                item_group = root.find('.//ItemGroup')
                if item_group is None:
                    logger.warning("Kein ItemGroup-Element oder DataSet gefunden")
                    return self._extract_basic_info()
            
            # Basis-Informationen (alte Struktur)
            for field in ['Id', 'Title', 'Description', 'Owner', 'CreateDate', 'LastUpdate']:
                elem = item_group.find(field)
                if elem is not None:
                    item_group_data[field.lower()] = self._get_text(elem)
            
            # Eigenschaften
            properties_elem = item_group.find('Properties')
            if properties_elem is not None:
                properties = {}
                for prop_elem in properties_elem:
                    prop_name = prop_elem.tag
                    prop_value = self._get_text(prop_elem)
                    properties[prop_name] = prop_value
                
                if properties:
                    item_group_data['properties'] = properties
            
            # Items extrahieren (alte Struktur)
            items = []
            items_elem = item_group.find('Items')
            
            if items_elem is not None:
                for item_elem in items_elem.findall('Item'):
                    item_data = {
                        'item_id': self._get_attribute(item_elem, 'id', ''),
                        'type': self._get_attribute(item_elem, 'type', '')
                    }
                    
                    # Weitere Informationen
                    for field in ['Title', 'Description', 'Content', 'MediaObject']:
                        elem = item_elem.find(field)
                        if elem is not None:
                            item_data[field.lower()] = self._get_text(elem)
                    
                    # Metadaten
                    metadata_elem = item_elem.find('Metadata')
                    if metadata_elem is not None:
                        metadata = {}
                        for meta_elem in metadata_elem:
                            metadata[meta_elem.tag] = self._get_text(meta_elem)
                        if metadata:
                            item_data['metadata'] = metadata
                    
                    # Eigenschaften des Items
                    item_props_elem = item_elem.find('Properties')
                    if item_props_elem is not None:
                        item_props = {}
                        for prop_elem in item_props_elem:
                            prop_name = prop_elem.tag
                            prop_value = self._get_text(prop_elem)
                            item_props[prop_name] = prop_value
                        
                        if item_props:
                            item_data['properties'] = item_props
                    
                    # Medienobjekte
                    media_elem = item_elem.find('MediaObject')
                    if media_elem is not None:
                        media_data = {
                            'id': self._get_attribute(media_elem, 'id', ''),
                            'type': self._get_attribute(media_elem, 'type', '')
                        }
                        
                        # Weitere Informationen zum Medienobjekt
                        for field in ['Title', 'Description', 'Location', 'Format']:
                            elem = media_elem.find(field)
                            if elem is not None:
                                media_data[field.lower()] = self._get_text(elem)
                        
                        if media_data:
                            item_data['media_object'] = media_data
                    
                    # Inhalte
                    content_elem = item_elem.find('Content')
                    if content_elem is not None:
                        # Extrahiere den HTML-Inhalt
                        content_html = ET.tostring(content_elem, encoding='utf-8', method='html').decode('utf-8')
                        # Entferne das Content-Tag selbst
                        content_html = content_html.replace('<Content>', '').replace('</Content>', '')
                        item_data['content_html'] = content_html
                    
                    items.append(item_data)
            
            if items:
                item_group_data['items'] = items
            
            # Wenn keine Items gefunden wurden, aber ein Titel vorhanden ist
            if not items and 'title' in item_group_data:
                # Erstelle ein Dummy-Item mit dem Titel der Item-Gruppe
                item_group_data['items'] = [{
                    'item_id': 'dummy',
                    'title': item_group_data['title'],
                    'type': 'dummy',
                    'description': item_group_data.get('description', '')
                }]
            
            return item_group_data
        
        except Exception as e:
            logger.exception(f"Fehler beim Parsen der XML-Daten: {str(e)}")
            return self._extract_basic_info()
    
    def _extract_item_group_from_filesystem(self) -> Dict[str, Any]:
        """
        Extrahiert Informationen über die Item-Gruppe aus dem Dateisystem.
        
        Returns:
            Dict mit Informationen über die Item-Gruppe
        """
        item_group_data = self._extract_basic_info()
        
        # Suche nach HTML-Dateien im Komponenten-Pfad
        html_files = []
        for root, dirs, files in os.walk(self.component_path):
            for file in files:
                if file.lower().endswith('.html'):
                    html_files.append(os.path.join(root, file))
        
        # Wenn HTML-Dateien gefunden wurden, extrahiere Inhalte
        items = []
        for i, html_path in enumerate(html_files):
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                filename = os.path.basename(html_path)
                items.append({
                    'item_id': f'item_{i}',
                    'title': filename,
                    'type': 'html',
                    'content_html': content
                })
            except Exception as e:
                logger.warning(f"Fehler beim Lesen der HTML-Datei {html_path}: {str(e)}")
        
        if items:
            item_group_data['items'] = items
        
        return item_group_data 