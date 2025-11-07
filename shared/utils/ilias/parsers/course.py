"""
Parser für ILIAS-Kurs-Komponenten.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
import logging
import os
from .base import IliasComponentParser

logger = logging.getLogger(__name__)

class CourseParser(IliasComponentParser):
    """Parser für ILIAS-Kurse."""
    
    def _parse_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parst die XML-Daten eines ILIAS-Kurses.
        
        Args:
            root: XML-Root-Element
            
        Returns:
            Dict mit den extrahierten Kursdaten
        """
        course_data = {}
        
        try:
            # Suche nach ExportItem/Course
            export_item = self._find_element(root, './/exp:ExportItem', self.namespaces)
            if export_item is None:
                logger.warning("Kein ExportItem-Element gefunden")
                return self._extract_basic_info()
            
            # Suche nach Course
            course_elem = export_item.find('.//Course')
            if course_elem is None:
                # Versuche alternative Pfade
                course_elem = root.find('.//Course')
                if course_elem is None:
                    logger.warning("Kein Course-Element gefunden")
                    return self._extract_basic_info()
            
            # Basis-Informationen
            for field in ['Id', 'Title', 'Description', 'Owner', 'CreateDate', 'LastUpdate']:
                elem = course_elem.find(field)
                if elem is not None:
                    course_data[field.lower()] = self._get_text(elem)
            
            # Kurs-spezifische Einstellungen
            settings_elem = course_elem.find('Settings')
            if settings_elem is not None:
                settings = {}
                for field in ['Syllabus', 'ImportantInformation', 'ContactName', 
                            'ContactResponsibility', 'ContactPhone', 'ContactEmail', 
                            'ContactConsultation']:
                    elem = settings_elem.find(field)
                    if elem is not None:
                        settings[field.lower()] = self._get_text(elem)
                
                if settings:
                    course_data['settings'] = settings
            
            # Aktivierung und Zeiteinstellungen
            activation_elem = course_elem.find('Activation')
            if activation_elem is not None:
                activation = {
                    'type': self._get_attribute(activation_elem, 'type', 'unlimited'),
                    'start': self._get_text(activation_elem.find('Start') if activation_elem.find('Start') is not None else None),
                    'end': self._get_text(activation_elem.find('End') if activation_elem.find('End') is not None else None)
                }
                course_data['activation'] = activation
            
            # Container-Einstellungen
            container_elem = course_elem.find('Container')
            if container_elem is not None:
                container_settings = {
                    'view': self._get_attribute(container_elem, 'view', 'by_type'),
                    'sorting': self._get_attribute(container_elem, 'sorting', 'title')
                }
                
                # Items im Container
                items = []
                items_elem = container_elem.find('Items')
                if items_elem is not None:
                    for item_elem in items_elem.findall('Item'):
                        item_data = {
                            'ref_id': self._get_attribute(item_elem, 'ref_id', ''),
                            'type': self._get_attribute(item_elem, 'type', ''),
                            'title': self._get_text(item_elem)
                        }
                        items.append(item_data)
                
                if items:
                    container_settings['items'] = items
                
                course_data['container_settings'] = container_settings
            
            # Registrierungseinstellungen
            registration_elem = course_elem.find('Registration')
            if registration_elem is not None:
                registration = {
                    'type': self._get_attribute(registration_elem, 'type', 'direct'),
                    'waiting_list': self._get_attribute(registration_elem, 'waiting_list', '0') == '1',
                    'max_members': self._get_attribute(registration_elem, 'max_members', '0'),
                    'min_members': self._get_attribute(registration_elem, 'min_members', '0')
                }
                course_data['registration'] = registration
            
            # Mitglieder
            members = []
            members_elem = course_elem.find('Members')
            if members_elem is not None:
                for member_elem in members_elem.findall('Member'):
                    member_data = {
                        'id': self._get_attribute(member_elem, 'id', ''),
                        'login': self._get_attribute(member_elem, 'login', ''),
                        'role': self._get_attribute(member_elem, 'role', 'member')
                    }
                    members.append(member_data)
            
            if members:
                course_data['members'] = members
            
            # Wenn keine Titel gefunden wurde, nutze Basis-Info
            if 'title' not in course_data or not course_data['title']:
                basic_info = self._extract_basic_info()
                course_data.update(basic_info)
            
            return course_data
        
        except Exception as e:
            logger.error(f"Fehler beim Parsen der Kurs-XML: {str(e)}")
            return self._extract_basic_info()

