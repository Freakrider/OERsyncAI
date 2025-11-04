"""
Parser für ILIAS-Wiki-Komponenten.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
import logging
import os
import glob
from .base import IliasComponentParser

logger = logging.getLogger(__name__)

class WikiParser(IliasComponentParser):
    """Parser für ILIAS-Wikis."""
    
    def _parse_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parst die XML-Daten eines ILIAS-Wikis.
        
        Args:
            root: XML-Root-Element
            
        Returns:
            Dict mit den extrahierten Wiki-Daten
        """
        wiki_data = {}
        
        try:
            # Suche nach ExportItem/Wiki
            export_item = self._find_element(root, './/exp:ExportItem', self.namespaces)
            if export_item is None:
                logger.warning("Kein ExportItem-Element gefunden")
                return self._extract_basic_info()
            
            # Suche nach Wiki
            wiki_elem = export_item.find('.//Wiki')
            if wiki_elem is None:
                # Versuche alternative Pfade
                wiki_elem = root.find('.//Wiki')
                if wiki_elem is None:
                    logger.warning("Kein Wiki-Element gefunden")
                    return self._extract_basic_info()
            
            # Basis-Informationen
            for field in ['Id', 'Title', 'Description', 'Owner', 'CreateDate', 'LastUpdate']:
                elem = wiki_elem.find(field)
                if elem is not None:
                    wiki_data[field.lower()] = self._get_text(elem)
            
            # Einstellungen
            settings_elem = wiki_elem.find('Settings')
            if settings_elem is not None:
                settings = {}
                for setting_elem in settings_elem:
                    setting_name = setting_elem.tag
                    setting_value = self._get_text(setting_elem)
                    settings[setting_name.lower()] = setting_value
                
                if settings:
                    wiki_data['settings'] = settings
            
            # Wiki-Seiten
            pages = []
            pages_elem = wiki_elem.find('Pages')
            if pages_elem is not None:
                for page_elem in pages_elem.findall('Page'):
                    page_data = {
                        'id': self._get_attribute(page_elem, 'id', ''),
                        'title': self._get_text(page_elem.find('Title')),
                        'content': self._get_text(page_elem.find('Content')),
                        'author': self._get_text(page_elem.find('Author')),
                        'create_date': self._get_text(page_elem.find('CreateDate')),
                        'last_update': self._get_text(page_elem.find('LastUpdate')),
                        'is_startpage': self._get_text(page_elem.find('IsStartpage')) == '1'
                    }
                    
                    # Versionen
                    versions = []
                    versions_elem = page_elem.find('Versions')
                    if versions_elem is not None:
                        for version_elem in versions_elem.findall('Version'):
                            version_data = {
                                'id': self._get_attribute(version_elem, 'id', ''),
                                'number': self._get_text(version_elem.find('Number')),
                                'content': self._get_text(version_elem.find('Content')),
                                'author': self._get_text(version_elem.find('Author')),
                                'create_date': self._get_text(version_elem.find('CreateDate')),
                                'comment': self._get_text(version_elem.find('Comment'))
                            }
                            versions.append(version_data)
                    
                    if versions:
                        page_data['versions'] = versions
                    
                    # Anhänge
                    attachments = []
                    attachments_elem = page_elem.find('Attachments')
                    if attachments_elem is not None:
                        for attachment_elem in attachments_elem.findall('Attachment'):
                            attachment_data = {
                                'name': self._get_text(attachment_elem.find('Name')),
                                'size': self._get_text(attachment_elem.find('Size')),
                                'type': self._get_text(attachment_elem.find('Type')),
                                'path': self._get_text(attachment_elem.find('Path'))
                            }
                            attachments.append(attachment_data)
                    
                    if attachments:
                        page_data['attachments'] = attachments
                    
                    pages.append(page_data)
            
            if pages:
                wiki_data['pages'] = pages
            else:
                # Wenn keine Seiten in der XML gefunden wurden, versuche sie aus dem Dateisystem zu extrahieren
                filesystem_pages = self._extract_pages_from_filesystem()
                if filesystem_pages:
                    wiki_data['pages'] = filesystem_pages
            
            return wiki_data
        
        except Exception as e:
            logger.exception(f"Fehler beim Parsen der XML-Daten: {str(e)}")
            return self._extract_basic_info()
    
    def _extract_pages_from_filesystem(self) -> List[Dict[str, Any]]:
        """
        Extrahiert Wiki-Seiteninformationen aus dem Dateisystem.
        
        Returns:
            Liste mit Wiki-Seiteninformationen
        """
        pages = []
        
        if not self.component_path:
            return pages
        
        try:
            # Suche nach Seitenverzeichnissen
            page_dirs = glob.glob(os.path.join(self.component_path, "page_*"))
            
            for page_dir in page_dirs:
                page_id = os.path.basename(page_dir).replace("page_", "")
                
                # Basis-Informationen aus dem Verzeichnisnamen
                page_data = {
                    'id': page_id,
                    'title': f"Seite {page_id}",
                    'content': f"Aus dem Dateisystem extrahierte Seite {page_id}"
                }
                
                # Suche nach XML-Dateien für weitere Informationen
                xml_files = glob.glob(os.path.join(page_dir, "*.xml"))
                for xml_file in xml_files:
                    try:
                        tree = ET.parse(xml_file)
                        xml_root = tree.getroot()
                        
                        # Suche nach Titel und Inhalt
                        title_elem = xml_root.find(".//Title")
                        if title_elem is not None and title_elem.text:
                            page_data['title'] = title_elem.text
                        
                        content_elem = xml_root.find(".//Content")
                        if content_elem is not None and content_elem.text:
                            page_data['content'] = content_elem.text
                        
                        # Suche nach Autor und Datum
                        author_elem = xml_root.find(".//Author")
                        if author_elem is not None and author_elem.text:
                            page_data['author'] = author_elem.text
                        
                        create_date_elem = xml_root.find(".//CreateDate")
                        if create_date_elem is not None and create_date_elem.text:
                            page_data['create_date'] = create_date_elem.text
                        
                        # Prüfe, ob es sich um die Startseite handelt
                        is_startpage_elem = xml_root.find(".//IsStartpage")
                        if is_startpage_elem is not None and is_startpage_elem.text:
                            page_data['is_startpage'] = is_startpage_elem.text == '1'
                    
                    except Exception as e:
                        logger.warning(f"Fehler beim Extrahieren von Informationen aus {xml_file}: {str(e)}")
                
                # Suche nach Versionen
                versions = []
                version_dirs = glob.glob(os.path.join(page_dir, "version_*"))
                
                for version_dir in version_dirs:
                    version_id = os.path.basename(version_dir).replace("version_", "")
                    
                    # Basis-Informationen aus dem Verzeichnisnamen
                    version_data = {
                        'id': version_id,
                        'number': version_id,
                        'content': f"Aus dem Dateisystem extrahierte Version {version_id}"
                    }
                    
                    # Suche nach XML-Dateien für weitere Informationen
                    xml_files = glob.glob(os.path.join(version_dir, "*.xml"))
                    for xml_file in xml_files:
                        try:
                            tree = ET.parse(xml_file)
                            xml_root = tree.getroot()
                            
                            # Suche nach Inhalt
                            content_elem = xml_root.find(".//Content")
                            if content_elem is not None and content_elem.text:
                                version_data['content'] = content_elem.text
                            
                            # Suche nach Autor und Datum
                            author_elem = xml_root.find(".//Author")
                            if author_elem is not None and author_elem.text:
                                version_data['author'] = author_elem.text
                            
                            create_date_elem = xml_root.find(".//CreateDate")
                            if create_date_elem is not None and create_date_elem.text:
                                version_data['create_date'] = create_date_elem.text
                            
                            # Suche nach Kommentar
                            comment_elem = xml_root.find(".//Comment")
                            if comment_elem is not None and comment_elem.text:
                                version_data['comment'] = comment_elem.text
                        
                        except Exception as e:
                            logger.warning(f"Fehler beim Extrahieren von Informationen aus {xml_file}: {str(e)}")
                    
                    versions.append(version_data)
                
                if versions:
                    page_data['versions'] = versions
                
                # Suche nach Anhängen
                attachments = []
                attachment_dir = os.path.join(page_dir, "attachments")
                if os.path.exists(attachment_dir):
                    for root, _, filenames in os.walk(attachment_dir):
                        for filename in filenames:
                            file_path = os.path.join(root, filename)
                            file_size = os.path.getsize(file_path)
                            file_type = os.path.splitext(filename)[1][1:]  # Entferne den Punkt
                            
                            attachments.append({
                                'name': filename,
                                'size': str(file_size),
                                'type': file_type,
                                'path': os.path.relpath(file_path, self.component_path)
                            })
                
                if attachments:
                    page_data['attachments'] = attachments
                
                pages.append(page_data)
        
        except Exception as e:
            logger.warning(f"Fehler beim Extrahieren von Wiki-Seiten aus dem Dateisystem: {str(e)}")
        
        return pages 