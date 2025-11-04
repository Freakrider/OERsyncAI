"""
Parser für ILIAS-Datei-Komponenten.
"""

from typing import Dict, Any
import xml.etree.ElementTree as ET
import logging
from .base import IliasComponentParser
import os

logger = logging.getLogger(__name__)

class FileParser(IliasComponentParser):
    """Parser für ILIAS-Dateien."""
    
    def _parse_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parst die XML-Daten einer ILIAS-Datei.
        
        Args:
            root: XML-Root-Element
            
        Returns:
            Dict mit den extrahierten Dateidaten
        """
        file_data = {}
        
        try:
            # Suche nach ExportItem/File
            export_item = self._find_element(root, './/exp:ExportItem', self.namespaces)
            if export_item is None:
                logger.warning("Kein ExportItem-Element gefunden")
                return self._extract_file_info_from_filesystem()
            
            file_elem = export_item.find('.//File')
            if file_elem is None:
                logger.warning("Kein File-Element gefunden")
                return self._extract_file_info_from_filesystem()
            
            # Basis-Informationen
            file_data.update({
                'obj_id': self._get_attribute(file_elem, 'obj_id'),
                'version': self._get_attribute(file_elem, 'version'),
                'max_version': self._get_attribute(file_elem, 'max_version'),
                'size': self._get_attribute(file_elem, 'size'),
                'type': self._get_attribute(file_elem, 'type'),
                'action': self._get_attribute(file_elem, 'action')
            })
            
            # Dateiname und Titel
            for field in ['Filename', 'Title', 'Description']:
                elem = file_elem.find(field)
                if elem is not None:
                    file_data[field.lower()] = self._get_text(elem)
                else:
                    logger.debug(f"Kein {field}-Element gefunden")
            
            # Rating
            rating = file_elem.find('Rating')
            if rating is not None:
                file_data['rating'] = self._get_text(rating)
            
            # Versionen
            versions = file_elem.find('Versions')
            if versions is not None:
                version_list = []
                for version in versions.findall('Version'):
                    version_data = {
                        'version': self._get_attribute(version, 'version'),
                        'max_version': self._get_attribute(version, 'max_version'),
                        'date': self._get_attribute(version, 'date'),
                        'usr_id': self._get_attribute(version, 'usr_id'),
                        'action': self._get_attribute(version, 'action'),
                        'rollback_version': self._get_attribute(version, 'rollback_version'),
                        'rollback_user_id': self._get_attribute(version, 'rollback_user_id'),
                        'mode': self._get_attribute(version, 'mode'),
                        'path': self._get_text(version)
                    }
                    version_list.append(version_data)
                file_data['versions'] = version_list
            
            # Wenn kein Titel gefunden wurde, verwende den Dateinamen
            if 'title' not in file_data or not file_data['title']:
                if 'filename' in file_data and file_data['filename']:
                    file_data['title'] = file_data['filename']
            
            # Wenn keine Größe gefunden wurde, versuche sie aus dem Dateisystem zu ermitteln
            if 'size' not in file_data or not file_data['size'] or file_data['size'] == '0':
                filesystem_info = self._extract_file_info_from_filesystem()
                if 'size' in filesystem_info:
                    file_data['size'] = filesystem_info['size']
                if 'type' in filesystem_info and ('type' not in file_data or not file_data['type']):
                    file_data['type'] = filesystem_info['type']
            
            return file_data
        except Exception as e:
            logger.exception(f"Fehler beim Parsen der XML-Daten: {str(e)}")
            return self._extract_file_info_from_filesystem()
    
    def _extract_file_info_from_filesystem(self) -> Dict[str, Any]:
        """
        Extrahiert Dateiinformationen aus dem Dateisystem.
        
        Returns:
            Dict mit Dateiinformationen
        """
        file_data = {}
        
        if not self.component_path:
            return file_data
        
        try:
            # Suche nach Dateien im Komponenten-Pfad
            for root, dirs, files in os.walk(self.component_path):
                for file in files:
                    # Ignoriere XML-Dateien und versteckte Dateien
                    if file.endswith('.xml') or file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    
                    # Bestimme den MIME-Typ
                    import mimetypes
                    mime_type, encoding = mimetypes.guess_type(file_path)
                    
                    file_data = {
                        'filename': file,
                        'title': file,
                        'size': str(file_size),
                        'type': mime_type or 'application/octet-stream'
                    }
                    
                    logger.info(f"Dateiinformationen aus Dateisystem extrahiert: {file_data}")
                    return file_data
        
        except Exception as e:
            logger.warning(f"Fehler beim Extrahieren von Dateiinformationen aus dem Dateisystem: {str(e)}")
        
        return file_data 