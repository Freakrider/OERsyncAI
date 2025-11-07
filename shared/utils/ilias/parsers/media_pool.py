"""
Parser für ILIAS-Media-Pool-Komponenten.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
import logging
import os
from .base import IliasComponentParser

logger = logging.getLogger(__name__)

class MediaPoolParser(IliasComponentParser):
    """Parser für ILIAS-Media-Pools."""
    
    def _parse_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parst die XML-Daten eines ILIAS-Media-Pools.
        
        Args:
            root: XML-Root-Element
            
        Returns:
            Dict mit den extrahierten Media-Pool-Daten
        """
        media_pool_data = {}
        
        try:
            # Suche nach ExportItem/MediaPool
            export_item = self._find_element(root, './/exp:ExportItem', self.namespaces)
            if export_item is None:
                logger.warning("Kein ExportItem-Element gefunden")
                return self._extract_basic_info()
            
            # Suche nach MediaPool
            media_pool_elem = export_item.find('.//MediaPool')
            if media_pool_elem is None:
                # Versuche alternative Pfade
                media_pool_elem = root.find('.//MediaPool')
                if media_pool_elem is None:
                    logger.warning("Kein MediaPool-Element gefunden")
                    return self._extract_basic_info()
            
            # Basis-Informationen
            for field in ['Id', 'Title', 'Description', 'Owner', 'CreateDate', 'LastUpdate']:
                elem = media_pool_elem.find(field)
                if elem is not None:
                    media_pool_data[field.lower()] = self._get_text(elem)
            
            # Media-Items
            media_items = []
            media_items_elem = media_pool_elem.find('MediaItems')
            if media_items_elem is not None:
                for item_elem in media_items_elem.findall('MediaItem'):
                    item_data = {
                        'id': self._get_attribute(item_elem, 'id', ''),
                        'title': self._get_text(item_elem.find('Title') if item_elem.find('Title') is not None else None),
                        'type': self._get_attribute(item_elem, 'type', ''),
                        'format': self._get_attribute(item_elem, 'format', ''),
                        'location': self._get_text(item_elem.find('Location') if item_elem.find('Location') is not None else None)
                    }
                    
                    # Weitere Metadaten
                    for field in ['Width', 'Height', 'Duration', 'Size']:
                        elem = item_elem.find(field)
                        if elem is not None:
                            item_data[field.lower()] = self._get_text(elem)
                    
                    media_items.append(item_data)
            
            if media_items:
                media_pool_data['media_items'] = media_items
            
            # Folder-Struktur
            folders = []
            folders_elem = media_pool_elem.find('Folders')
            if folders_elem is not None:
                for folder_elem in folders_elem.findall('Folder'):
                    folder_data = {
                        'id': self._get_attribute(folder_elem, 'id', ''),
                        'title': self._get_text(folder_elem.find('Title') if folder_elem.find('Title') is not None else None)
                    }
                    folders.append(folder_data)
            
            if folders:
                media_pool_data['folders'] = folders
            
            # Wenn keine Titel gefunden wurde, nutze Basis-Info
            if 'title' not in media_pool_data or not media_pool_data['title']:
                basic_info = self._extract_basic_info()
                media_pool_data.update(basic_info)
            
            return media_pool_data
        
        except Exception as e:
            logger.error(f"Fehler beim Parsen der Media-Pool-XML: {str(e)}")
            return self._extract_basic_info()

