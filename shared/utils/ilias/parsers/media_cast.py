"""
Parser für ILIAS-MediaCast-Komponenten.
"""

from typing import Dict, Any
import xml.etree.ElementTree as ET
import logging
import os
from .base import IliasComponentParser
import mimetypes

logger = logging.getLogger(__name__)

class MediaCastParser(IliasComponentParser):
    """Parser für ILIAS-MediaCast-Komponenten."""
    
    def _parse_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parst die XML-Daten einer ILIAS-MediaCast-Komponente.
        
        Args:
            root: XML-Root-Element
            
        Returns:
            Dict mit den extrahierten Mediendaten
        """
        media_data = {}
        
        try:
            # Suche nach ExportItem/MediaCast
            export_item = self._find_element(root, './/exp:ExportItem', self.namespaces)
            if export_item is None:
                logger.warning("Kein ExportItem-Element gefunden")
                return self._extract_media_from_filesystem()
            
            # Suche nach MediaCast oder MediaItems
            media_cast = export_item.find('.//MediaCast')
            if media_cast is None:
                # Versuche alternative Pfade
                media_cast = root.find('.//MediaCast')
                if media_cast is None:
                    logger.warning("Kein MediaCast-Element gefunden")
                    return self._extract_media_from_filesystem()
            
            # Basis-Informationen
            title_elem = media_cast.find('Title')
            if title_elem is not None:
                media_data['title'] = self._get_text(title_elem)
            
            description_elem = media_cast.find('Description')
            if description_elem is not None:
                media_data['description'] = self._get_text(description_elem)
            
            # Weitere Metadaten extrahieren
            for field in ['Id', 'Owner', 'CreateDate', 'LastUpdate', 'DefaultAccess']:
                elem = media_cast.find(field)
                if elem is not None:
                    media_data[field.lower()] = self._get_text(elem)
            
            # MediaItems extrahieren
            media_items = []
            items_elem = media_cast.find('MediaItems')
            
            if items_elem is not None:
                for item_elem in items_elem.findall('MediaItem'):
                    item_data = {
                        'id': self._get_attribute(item_elem, 'id', ''),
                        'format': self._get_attribute(item_elem, 'format', '')
                    }
                    
                    # Weitere Informationen
                    for field in ['Title', 'Description', 'Location', 'Format', 'MimeType', 'Duration', 'Width', 'Height', 'Size']:
                        elem = item_elem.find(field)
                        if elem is not None:
                            item_data[field.lower()] = self._get_text(elem)
                    
                    # Lokation und Typ
                    location_elem = item_elem.find('Location')
                    if location_elem is not None:
                        item_data['location'] = self._get_text(location_elem)
                        item_data['location_type'] = self._get_attribute(location_elem, 'type', 'file')
                    
                    # Metadaten
                    metadata_elem = item_elem.find('Metadata')
                    if metadata_elem is not None:
                        metadata = {}
                        for meta_elem in metadata_elem:
                            metadata[meta_elem.tag] = self._get_text(meta_elem)
                        if metadata:
                            item_data['metadata'] = metadata
                    
                    media_items.append(item_data)
            
            if media_items:
                media_data['media_items'] = media_items
            else:
                logger.warning("Keine MediaItems gefunden")
                # Suche nach Mediendateien im Dateisystem
                filesystem_media = self._extract_media_from_filesystem()
                if 'media_items' in filesystem_media:
                    media_data['media_items'] = filesystem_media['media_items']
            
            return media_data
        
        except Exception as e:
            logger.exception(f"Fehler beim Parsen der XML-Daten: {str(e)}")
            return self._extract_media_from_filesystem()
    
    def _extract_media_from_filesystem(self) -> Dict[str, Any]:
        """
        Extrahiert Mediendateien aus dem Dateisystem.
        
        Returns:
            Dict mit Mediendaten
        """
        media_data = {}
        
        if not self.component_path:
            return media_data
        
        try:
            # Suche nach Mediendateien im Komponenten-Pfad
            media_files = []
            for root, dirs, files in os.walk(self.component_path):
                for file in files:
                    # Ignoriere XML-Dateien und versteckte Dateien
                    if file.endswith('.xml') or file.startswith('.'):
                        continue
                    
                    # Mediendateien
                    if file.lower().endswith(('.mp4', '.mp3', '.avi', '.mov', '.wmv', '.flv')):
                        media_files.append(os.path.join(root, file))
            
            if not media_files:
                logger.warning(f"Keine Mediendateien im Komponenten-Pfad gefunden: {self.component_path}")
                return media_data
            
            # Verwende den Dateinamen als Titel
            component_title = os.path.basename(media_files[0])
            media_data['title'] = component_title
            
            # Füge Mediendateien zu den Daten hinzu
            media_items = []
            for media_path in media_files:
                filename = os.path.basename(media_path)
                mime_type, encoding = mimetypes.guess_type(media_path)
                file_size = os.path.getsize(media_path)
                
                # Versuche, weitere Metadaten zu extrahieren
                duration = None
                width = None
                height = None
                
                # Für Video-Dateien versuche, Dauer, Breite und Höhe zu ermitteln
                if mime_type and mime_type.startswith('video/'):
                    try:
                        import subprocess
                        # Verwende ffprobe, falls verfügbar
                        result = subprocess.run(
                            ['ffprobe', '-v', 'error', '-show_entries', 
                             'format=duration:stream=width,height', '-of', 
                             'default=noprint_wrappers=1:nokey=1', media_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        if result.returncode == 0:
                            lines = result.stdout.strip().split('\n')
                            if len(lines) >= 3:
                                duration = lines[0]
                                width = lines[1]
                                height = lines[2]
                    except Exception as e:
                        logger.debug(f"Fehler beim Extrahieren von Video-Metadaten: {str(e)}")
                
                item_data = {
                    'title': filename,
                    'location': filename,
                    'format': mime_type or "Unbekannt",
                    'location_type': 'file',
                    'size': str(file_size)
                }
                
                if duration:
                    item_data['duration'] = duration
                if width:
                    item_data['width'] = width
                if height:
                    item_data['height'] = height
                
                media_items.append(item_data)
            
            media_data['media_items'] = media_items
            logger.info(f"Mediendaten aus Dateisystem extrahiert: {len(media_items)} Dateien gefunden")
            
            return media_data
        
        except Exception as e:
            logger.warning(f"Fehler beim Extrahieren von Mediendaten aus dem Dateisystem: {str(e)}")
            return media_data 