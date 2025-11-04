"""
Parser für ILIAS-Forum-Komponenten.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
import logging
import os
import glob
from .base import IliasComponentParser

logger = logging.getLogger(__name__)

class ForumParser(IliasComponentParser):
    """Parser für ILIAS-Foren."""
    
    def _parse_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parst die XML-Daten eines ILIAS-Forums.
        
        Args:
            root: XML-Root-Element
            
        Returns:
            Dict mit den extrahierten Forumdaten
        """
        forum_data = {}
        
        try:
            # Suche nach ExportItem/Forum
            export_item = self._find_element(root, './/exp:ExportItem', self.namespaces)
            if export_item is None:
                logger.warning("Kein ExportItem-Element gefunden")
                return self._extract_basic_info()
            
            # Suche nach Forum
            forum_elem = export_item.find('.//Forum')
            if forum_elem is None:
                # Versuche alternative Pfade
                forum_elem = root.find('.//Forum')
                if forum_elem is None:
                    logger.warning("Kein Forum-Element gefunden")
                    return self._extract_basic_info()
            
            # Basis-Informationen
            for field in ['Id', 'Title', 'Description', 'Owner', 'CreateDate', 'LastUpdate']:
                elem = forum_elem.find(field)
                if elem is not None:
                    forum_data[field.lower()] = self._get_text(elem)
            
            # Einstellungen
            settings_elem = forum_elem.find('Settings')
            if settings_elem is not None:
                settings = {}
                for setting_elem in settings_elem:
                    setting_name = setting_elem.tag
                    setting_value = self._get_text(setting_elem)
                    settings[setting_name.lower()] = setting_value
                
                if settings:
                    forum_data['settings'] = settings
            
            # Themen
            topics = []
            topics_elem = forum_elem.find('Topics')
            if topics_elem is not None:
                for topic_elem in topics_elem.findall('Topic'):
                    topic_data = {
                        'id': self._get_attribute(topic_elem, 'id', ''),
                        'title': self._get_text(topic_elem.find('Title')),
                        'description': self._get_text(topic_elem.find('Description')),
                        'author': self._get_text(topic_elem.find('Author')),
                        'create_date': self._get_text(topic_elem.find('CreateDate')),
                        'last_update': self._get_text(topic_elem.find('LastUpdate')),
                        'views': self._get_text(topic_elem.find('Views')),
                        'sticky': self._get_text(topic_elem.find('Sticky')) == '1',
                        'closed': self._get_text(topic_elem.find('Closed')) == '1'
                    }
                    
                    # Beiträge
                    posts = []
                    posts_elem = topic_elem.find('Posts')
                    if posts_elem is not None:
                        for post_elem in posts_elem.findall('Post'):
                            post_data = {
                                'id': self._get_attribute(post_elem, 'id', ''),
                                'title': self._get_text(post_elem.find('Title')),
                                'message': self._get_text(post_elem.find('Message')),
                                'author': self._get_text(post_elem.find('Author')),
                                'create_date': self._get_text(post_elem.find('CreateDate')),
                                'last_update': self._get_text(post_elem.find('LastUpdate')),
                                'parent_id': self._get_text(post_elem.find('ParentId')),
                                'depth': self._get_text(post_elem.find('Depth'))
                            }
                            
                            # Anhänge
                            attachments = []
                            attachments_elem = post_elem.find('Attachments')
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
                                post_data['attachments'] = attachments
                            
                            posts.append(post_data)
                    
                    if posts:
                        topic_data['posts'] = posts
                    
                    topics.append(topic_data)
            
            if topics:
                forum_data['topics'] = topics
            else:
                # Wenn keine Themen in der XML gefunden wurden, versuche sie aus dem Dateisystem zu extrahieren
                filesystem_topics = self._extract_topics_from_filesystem()
                if filesystem_topics:
                    forum_data['topics'] = filesystem_topics
            
            return forum_data
        
        except Exception as e:
            logger.exception(f"Fehler beim Parsen der XML-Daten: {str(e)}")
            return self._extract_basic_info()
    
    def _extract_topics_from_filesystem(self) -> List[Dict[str, Any]]:
        """
        Extrahiert Themeninformationen aus dem Dateisystem.
        
        Returns:
            Liste mit Themeninformationen
        """
        topics = []
        
        if not self.component_path:
            return topics
        
        try:
            # Suche nach Themenverzeichnissen
            topic_dirs = glob.glob(os.path.join(self.component_path, "topic_*"))
            
            for topic_dir in topic_dirs:
                topic_id = os.path.basename(topic_dir).replace("topic_", "")
                
                # Basis-Informationen aus dem Verzeichnisnamen
                topic_data = {
                    'id': topic_id,
                    'title': f"Thema {topic_id}",
                    'description': f"Aus dem Dateisystem extrahiertes Thema {topic_id}"
                }
                
                # Suche nach XML-Dateien für weitere Informationen
                xml_files = glob.glob(os.path.join(topic_dir, "*.xml"))
                for xml_file in xml_files:
                    try:
                        tree = ET.parse(xml_file)
                        xml_root = tree.getroot()
                        
                        # Suche nach Titel und Beschreibung
                        title_elem = xml_root.find(".//Title")
                        if title_elem is not None and title_elem.text:
                            topic_data['title'] = title_elem.text
                        
                        desc_elem = xml_root.find(".//Description")
                        if desc_elem is not None and desc_elem.text:
                            topic_data['description'] = desc_elem.text
                        
                        # Suche nach Autor und Datum
                        author_elem = xml_root.find(".//Author")
                        if author_elem is not None and author_elem.text:
                            topic_data['author'] = author_elem.text
                        
                        create_date_elem = xml_root.find(".//CreateDate")
                        if create_date_elem is not None and create_date_elem.text:
                            topic_data['create_date'] = create_date_elem.text
                    
                    except Exception as e:
                        logger.warning(f"Fehler beim Extrahieren von Informationen aus {xml_file}: {str(e)}")
                
                # Suche nach Beiträgen
                posts = []
                post_dirs = glob.glob(os.path.join(topic_dir, "post_*"))
                
                for post_dir in post_dirs:
                    post_id = os.path.basename(post_dir).replace("post_", "")
                    
                    # Basis-Informationen aus dem Verzeichnisnamen
                    post_data = {
                        'id': post_id,
                        'title': f"Beitrag {post_id}",
                        'message': f"Aus dem Dateisystem extrahierter Beitrag {post_id}"
                    }
                    
                    # Suche nach XML-Dateien für weitere Informationen
                    xml_files = glob.glob(os.path.join(post_dir, "*.xml"))
                    for xml_file in xml_files:
                        try:
                            tree = ET.parse(xml_file)
                            xml_root = tree.getroot()
                            
                            # Suche nach Titel und Nachricht
                            title_elem = xml_root.find(".//Title")
                            if title_elem is not None and title_elem.text:
                                post_data['title'] = title_elem.text
                            
                            message_elem = xml_root.find(".//Message")
                            if message_elem is not None and message_elem.text:
                                post_data['message'] = message_elem.text
                            
                            # Suche nach Autor und Datum
                            author_elem = xml_root.find(".//Author")
                            if author_elem is not None and author_elem.text:
                                post_data['author'] = author_elem.text
                            
                            create_date_elem = xml_root.find(".//CreateDate")
                            if create_date_elem is not None and create_date_elem.text:
                                post_data['create_date'] = create_date_elem.text
                        
                        except Exception as e:
                            logger.warning(f"Fehler beim Extrahieren von Informationen aus {xml_file}: {str(e)}")
                    
                    # Suche nach Anhängen
                    attachments = []
                    attachment_dir = os.path.join(post_dir, "attachments")
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
                        post_data['attachments'] = attachments
                    
                    posts.append(post_data)
                
                if posts:
                    topic_data['posts'] = posts
                
                topics.append(topic_data)
        
        except Exception as e:
            logger.warning(f"Fehler beim Extrahieren von Themen aus dem Dateisystem: {str(e)}")
        
        return topics 