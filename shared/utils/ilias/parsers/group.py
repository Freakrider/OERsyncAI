"""
Parser für ILIAS-Gruppen-Komponenten.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
import logging
import os
from .base import IliasComponentParser

logger = logging.getLogger(__name__)

class GroupParser(IliasComponentParser):
    """Parser für ILIAS-Gruppen."""
    
    def _parse_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parst die XML-Daten einer ILIAS-Gruppe.
        
        Args:
            root: XML-Root-Element
            
        Returns:
            Dict mit den extrahierten Gruppendaten
        """
        group_data = {}
        
        try:
            # Suche nach ExportItem/Group
            export_item = self._find_element(root, './/exp:ExportItem', self.namespaces)
            if export_item is None:
                logger.warning("Kein ExportItem-Element gefunden")
                return self._extract_basic_info()
            
            # Suche nach Group
            group_elem = export_item.find('.//Group')
            if group_elem is None:
                # Versuche alternative Pfade
                group_elem = root.find('.//Group')
                if group_elem is None:
                    logger.warning("Kein Group-Element gefunden")
                    return self._extract_basic_info()
            
            # Basis-Informationen
            for field in ['Id', 'Title', 'Description', 'Owner', 'CreateDate', 'LastUpdate']:
                elem = group_elem.find(field)
                if elem is not None:
                    group_data[field.lower()] = self._get_text(elem)
            
            # Registrierungseinstellungen
            registration_elem = group_elem.find('Registration')
            if registration_elem is not None:
                registration = {
                    'type': self._get_attribute(registration_elem, 'type', 'direct'),
                    'waiting_list': self._get_attribute(registration_elem, 'waiting_list', '0') == '1',
                    'max_members': self._get_attribute(registration_elem, 'max_members', '0'),
                    'min_members': self._get_attribute(registration_elem, 'min_members', '0')
                }
                
                # Weitere Registrierungsdetails
                for field in ['Start', 'End', 'Password']:
                    elem = registration_elem.find(field)
                    if elem is not None:
                        registration[field.lower()] = self._get_text(elem)
                
                group_data['registration'] = registration
            
            # Container-Einstellungen
            container_elem = group_elem.find('Container')
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
                
                group_data['container_settings'] = container_settings
            
            # Mitglieder
            members = []
            members_elem = group_elem.find('Members')
            if members_elem is not None:
                for member_elem in members_elem.findall('Member'):
                    member_data = {
                        'id': self._get_attribute(member_elem, 'id', ''),
                        'login': self._get_attribute(member_elem, 'login', ''),
                        'role': self._get_attribute(member_elem, 'role', 'member')
                    }
                    
                    # Weitere Mitgliederdetails
                    for field in ['Firstname', 'Lastname', 'Email']:
                        elem = member_elem.find(field)
                        if elem is not None:
                            member_data[field.lower()] = self._get_text(elem)
                    
                    members.append(member_data)
            
            if members:
                group_data['members'] = members
            
            # Einstellungen
            settings_elem = group_elem.find('Settings')
            if settings_elem is not None:
                settings = {}
                for setting_elem in settings_elem:
                    setting_name = setting_elem.tag
                    setting_value = self._get_text(setting_elem)
                    settings[setting_name] = setting_value
                
                if settings:
                    group_data['settings'] = settings
            
            return group_data
        
        except Exception as e:
            logger.exception(f"Fehler beim Parsen der XML-Daten: {str(e)}")
            return self._extract_basic_info()
    
    def _extract_group_structure_from_filesystem(self) -> Dict[str, Any]:
        """
        Extrahiert die Gruppenstruktur aus dem Dateisystem.
        
        Returns:
            Dict mit Informationen über die Gruppenstruktur
        """
        group_data = self._extract_basic_info()
        
        if not self.component_path:
            return group_data
        
        try:
            # Suche nach Unterverzeichnissen, die Komponenten enthalten könnten
            container_items = []
            for root, dirs, files in os.walk(self.component_path):
                for dir_name in dirs:
                    if "__" in dir_name:
                        # Versuche, den Typ aus dem Verzeichnisnamen zu extrahieren
                        parts = dir_name.split("__")
                        if len(parts) >= 3:
                            type_id_parts = parts[2].split("_")
                            if len(type_id_parts) > 0:
                                item_type = type_id_parts[0]  # z.B. "grp" aus "grp_6623"
                                item_id = type_id_parts[1] if len(type_id_parts) > 1 else "unknown"
                                
                                # Versuche, den Titel zu extrahieren
                                item_title = dir_name
                                item_path = os.path.join(root, dir_name)
                                
                                # Suche nach export.xml oder manifest.xml für den Titel
                                for xml_file in ['export.xml', 'manifest.xml']:
                                    xml_path = os.path.join(item_path, xml_file)
                                    if os.path.exists(xml_path):
                                        try:
                                            tree = ET.parse(xml_path)
                                            xml_root = tree.getroot()
                                            
                                            # Suche nach dem Titel
                                            title_elem = xml_root.find(".//Title")
                                            if title_elem is not None and title_elem.text:
                                                item_title = title_elem.text
                                                break
                                        except Exception as e:
                                            logger.warning(f"Fehler beim Extrahieren des Titels aus {xml_path}: {str(e)}")
                                
                                container_items.append({
                                    'ref_id': item_id,
                                    'type': item_type,
                                    'title': item_title
                                })
            
            if container_items:
                if 'container_settings' not in group_data:
                    group_data['container_settings'] = {}
                
                group_data['container_settings']['items'] = container_items
        
        except Exception as e:
            logger.warning(f"Fehler beim Extrahieren der Gruppenstruktur aus dem Dateisystem: {str(e)}")
        
        return group_data 