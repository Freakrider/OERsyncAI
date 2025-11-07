"""
Parser für ILIAS-Learning-Module-Komponenten.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
import logging
import os
from .base import IliasComponentParser

logger = logging.getLogger(__name__)

class LearningModuleParser(IliasComponentParser):
    """Parser für ILIAS-Learning-Module (Lernmodule)."""
    
    def _parse_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parst die XML-Daten eines ILIAS-Learning-Moduls.
        
        Args:
            root: XML-Root-Element
            
        Returns:
            Dict mit den extrahierten Learning-Module-Daten
        """
        lm_data = {}
        
        try:
            # Suche nach ContentObject (Lernmodul)
            content_object = self._find_element(root, './/ContentObject')
            if content_object is None:
                # Alternative Suche
                content_object = self._find_element(root, './/LearningModule')
                if content_object is None:
                    logger.warning("Kein ContentObject/LearningModule-Element gefunden")
                    return self._extract_basic_info()
            
            # Basis-Informationen
            for field in ['Title', 'Description']:
                elem = content_object.find(field)
                if elem is not None:
                    lm_data[field.lower()] = self._get_text(elem)
            
            # Meta-Daten
            meta_data_elem = content_object.find('MetaData')
            if meta_data_elem is not None:
                metadata = {}
                for field in ['Language', 'Keyword', 'Coverage']:
                    elem = meta_data_elem.find(field)
                    if elem is not None:
                        metadata[field.lower()] = self._get_text(elem)
                
                if metadata:
                    lm_data['metadata'] = metadata
            
            # Struktur-Objekte (Seiten und Kapitel)
            structure_objects = []
            for struct_obj in content_object.findall('.//StructureObject'):
                struct_data = {
                    'type': self._get_attribute(struct_obj, 'Type', 'st'),
                    'title': self._get_text(struct_obj.find('Title') if struct_obj.find('Title') is not None else None)
                }
                structure_objects.append(struct_data)
            
            # Page-Objekte (Seiten mit Inhalten)
            page_objects = []
            for page_obj in content_object.findall('.//PageObject'):
                page_data = {
                    'title': self._get_text(page_obj.find('Title') if page_obj.find('Title') is not None else None),
                    'layout': self._get_attribute(page_obj, 'Layout', 'standard')
                }
                
                # MediaObject-Referenzen
                media_objects = []
                for media_obj in page_obj.findall('.//MediaObject'):
                    media_data = {
                        'alias': self._get_attribute(media_obj, 'Alias', ''),
                        'type': self._get_attribute(media_obj, 'Type', '')
                    }
                    
                    # MediaItem
                    media_item = media_obj.find('MediaItem')
                    if media_item is not None:
                        media_data['location'] = self._get_attribute(media_item, 'Location', '')
                        media_data['format'] = self._get_attribute(media_item, 'Format', '')
                    
                    media_objects.append(media_data)
                
                if media_objects:
                    page_data['media_objects'] = media_objects
                
                # Paragraph-Content
                paragraphs = []
                for para in page_obj.findall('.//Paragraph'):
                    para_data = {
                        'language': self._get_attribute(para, 'Language', 'de'),
                        'characteristic': self._get_attribute(para, 'Characteristic', 'Standard'),
                        'content': self._get_text(para)
                    }
                    paragraphs.append(para_data)
                
                if paragraphs:
                    page_data['paragraphs'] = paragraphs
                
                page_objects.append(page_data)
            
            if structure_objects:
                lm_data['structure_objects'] = structure_objects
            
            if page_objects:
                lm_data['page_objects'] = page_objects
            
            # Einstellungen
            settings_elem = content_object.find('Settings')
            if settings_elem is not None:
                settings = {}
                for field in ['DefaultLayout', 'PageHeader', 'TOC', 'NumberingEnabled', 
                            'PublicNotes', 'CleanFrames', 'HistoryUserComments']:
                    elem = settings_elem.find(field)
                    if elem is not None:
                        settings[field.lower()] = self._get_text(elem)
                
                if settings:
                    lm_data['settings'] = settings
            
            # Wenn keine Titel gefunden wurde, nutze Basis-Info
            if 'title' not in lm_data or not lm_data['title']:
                basic_info = self._extract_basic_info()
                lm_data.update(basic_info)
            
            return lm_data
        
        except Exception as e:
            logger.error(f"Fehler beim Parsen der Learning-Module-XML: {str(e)}")
            return self._extract_basic_info()

