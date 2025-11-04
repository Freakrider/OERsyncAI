"""
Basisklassen für die ILIAS-Komponenten-Parser.
"""

import os
import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class IliasComponentParser:
    """Basisklasse für alle ILIAS-Komponenten-Parser."""
    
    def __init__(self, component_path: str = None):
        """
        Initialisiert den Parser mit Standard-Namespaces und dem Pfad zur Komponente.
        
        Args:
            component_path: Pfad zur Komponente
        """
        self.namespaces = {
            'exp': 'http://www.ilias.de/Services/Export/exp/4_1',
            'ds': 'http://www.ilias.de/Services/DataSet/ds/4_3'
        }
        
        self.component_path = component_path
        if component_path and not os.path.exists(component_path):
            logger.warning(f"Der Komponenten-Pfad existiert nicht: {component_path}")
    
    def parse(self, xml_path: str = None) -> Dict[str, Any]:
        """
        Parst eine XML-Datei und gibt die extrahierten Daten zurück.
        
        Args:
            xml_path: Pfad zur XML-Datei. Wenn None, wird versucht, die Datei im Komponenten-Pfad zu finden.
            
        Returns:
            Dict mit den extrahierten Daten
        """
        # Wenn kein XML-Pfad angegeben wurde, versuche, die Datei im Komponenten-Pfad zu finden
        if xml_path is None:
            if self.component_path is None:
                logger.error("Weder XML-Pfad noch Komponenten-Pfad angegeben")
                return {}
            
            # Suche nach export.xml im Komponenten-Pfad
            export_xml_path = None
            for root, dirs, files in os.walk(self.component_path):
                if "export.xml" in files:
                    export_xml_path = os.path.join(root, "export.xml")
                    break
            
            if export_xml_path:
                xml_path = export_xml_path
                logger.info(f"Verwende export.xml: {xml_path}")
            else:
                # Suche nach XML-Dateien im Komponenten-Pfad
                xml_files = []
                for root, dirs, files in os.walk(self.component_path):
                    for file in files:
                        if file.endswith('.xml'):
                            xml_files.append(os.path.join(root, file))
                
                if not xml_files:
                    logger.warning(f"Keine XML-Dateien im Komponenten-Pfad gefunden: {self.component_path}")
                    return self._extract_basic_info()
                
                # Verwende die erste gefundene XML-Datei
                xml_path = xml_files[0]
                logger.info(f"Verwende XML-Datei: {xml_path}")
        
        if not os.path.isfile(xml_path):
            logger.warning(f"Die Datei '{xml_path}' existiert nicht.")
            # Überprüfen, ob das übergeordnete Verzeichnis existiert
            parent_dir = os.path.dirname(xml_path)
            if os.path.exists(parent_dir):
                logger.info(f"Verzeichnisinhalt von {parent_dir}: {os.listdir(parent_dir)}")
            return self._extract_basic_info()
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            data = self._parse_xml(root)
            
            # Wenn keine Titel gefunden wurde, versuche ihn aus dem Dateinamen zu extrahieren
            if "title" not in data or not data["title"]:
                data.update(self._extract_basic_info())
            
            return data
        except ET.ParseError as e:
            logger.error(f"XML-Parsing-Fehler in {xml_path}: {e}")
            return self._extract_basic_info()
        except Exception as e:
            logger.error(f"Fehler beim Parsen von {xml_path}: {e}")
            return self._extract_basic_info()
    
    def _parse_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parst ein XML-Element. Muss von abgeleiteten Klassen implementiert werden.
        
        Args:
            root: XML-Root-Element
            
        Returns:
            Dict mit den extrahierten Daten
        """
        raise NotImplementedError("Diese Methode muss von abgeleiteten Klassen implementiert werden.")
    
    def _get_text(self, element: Optional[ET.Element], default: str = "") -> str:
        """
        Extrahiert den Text aus einem XML-Element.
        
        Args:
            element: XML-Element
            default: Standardwert, falls kein Text gefunden wird
            
        Returns:
            Extrahierter Text oder Standardwert
        """
        return element.text if element is not None and element.text else default
    
    def _get_attribute(self, element: ET.Element, attr: str, default: str = "") -> str:
        """
        Extrahiert ein Attribut aus einem XML-Element.
        
        Args:
            element: XML-Element
            attr: Name des Attributs
            default: Standardwert, falls das Attribut nicht gefunden wird
            
        Returns:
            Attributwert oder Standardwert
        """
        return element.get(attr, default)
    
    def _find_element(self, root: ET.Element, path: str, namespaces: Optional[Dict[str, str]] = None) -> Optional[ET.Element]:
        """
        Sucht ein Element im XML-Baum.
        
        Args:
            root: XML-Root-Element
            path: XPath zum Element
            namespaces: Optional zu verwendende Namespaces
            
        Returns:
            Gefundenes Element oder None
        """
        ns = namespaces if namespaces is not None else self.namespaces
        try:
            return root.find(path, ns)
        except Exception as e:
            logger.error(f"Fehler beim Suchen von {path}: {e}")
            return None
    
    def _findall_elements(self, root: ET.Element, path: str, namespaces: Optional[Dict[str, str]] = None) -> list:
        """
        Sucht alle passenden Elemente im XML-Baum.
        
        Args:
            root: XML-Root-Element
            path: XPath zu den Elementen
            namespaces: Optional zu verwendende Namespaces
            
        Returns:
            Liste der gefundenen Elemente
        """
        ns = namespaces if namespaces is not None else self.namespaces
        try:
            return root.findall(path, ns)
        except Exception as e:
            logger.error(f"Fehler beim Suchen von {path}: {e}")
            return []
    
    def _extract_basic_info(self) -> Dict[str, Any]:
        """
        Extrahiert grundlegende Informationen aus dem Komponenten-Pfad.
        
        Returns:
            Dict mit grundlegenden Informationen
        """
        if not self.component_path:
            return {"title": "Unbekannt", "id": "unknown"}
        
        # Versuche, Informationen aus dem Pfad zu extrahieren
        component_name = os.path.basename(self.component_path)
        component_id = "unknown"
        component_title = "Unbekannt"
        component_type = "unknown"
        
        # Versuche, den Titel aus dem Verzeichnisnamen zu extrahieren
        if "__" in component_name:
            parts = component_name.split("__")
            if len(parts) >= 3:
                type_id_parts = parts[2].split("_")
                if len(type_id_parts) > 0:
                    component_type = type_id_parts[0]  # z.B. "grp" aus "grp_6623"
                if len(type_id_parts) > 1:
                    component_id = type_id_parts[1]
                    
                    # Suche nach einer Beschreibungsdatei im Komponenten-Pfad
                    for root, dirs, files in os.walk(self.component_path):
                        for file in files:
                            if file.lower() in ["description.txt", "title.txt", "info.txt"]:
                                try:
                                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                                        component_title = f.read().strip()
                                        logger.info(f"Titel aus {file} extrahiert: {component_title}")
                                        break
                                except Exception as e:
                                    logger.warning(f"Fehler beim Lesen von {file}: {str(e)}")
        
        # Suche nach dem Titel in Unterverzeichnissen
        if component_title == "Unbekannt" and self.component_path:
            for root, dirs, files in os.walk(self.component_path):
                for file in files:
                    if file == "export.xml":
                        try:
                            tree = ET.parse(os.path.join(root, file))
                            xml_root = tree.getroot()
                            
                            # Suche nach dem Titel in verschiedenen Formaten
                            title_elem = xml_root.find(".//Title")
                            if title_elem is not None and title_elem.text:
                                component_title = title_elem.text
                                logger.info(f"Titel aus export.xml extrahiert: {component_title}")
                                break
                            else:
                                # Alternative Suche nach dem Titel
                                for elem in xml_root.iter():
                                    if elem.tag.endswith("Title") and elem.text:
                                        component_title = elem.text
                                        logger.info(f"Titel aus alternativer Quelle extrahiert: {component_title}")
                                        break
                        except Exception as e:
                            logger.warning(f"Fehler beim Extrahieren des Titels aus export.xml: {str(e)}")
        
        # Wenn immer noch kein Titel gefunden wurde, suche nach relevanten Dateien
        if component_title == "Unbekannt" and self.component_path:
            # Suche nach Mediendateien oder anderen relevanten Dateien
            media_files = []
            document_files = []
            
            for root, dirs, files in os.walk(self.component_path):
                for file in files:
                    # Ignoriere XML-Dateien und versteckte Dateien
                    if file.endswith('.xml') or file.startswith('.'):
                        continue
                    
                    # Mediendateien
                    if file.lower().endswith(('.mp4', '.mp3', '.avi', '.mov', '.wmv', '.flv')):
                        media_files.append(os.path.join(root, file))
                    # Dokumente
                    elif file.lower().endswith(('.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt')):
                        document_files.append(os.path.join(root, file))
            
            # Verwende den Dateinamen als Titel
            if media_files:
                component_title = os.path.basename(media_files[0])
                logger.info(f"Titel aus Mediendatei extrahiert: {component_title}")
                
                # Füge Mediendateien zu den Daten hinzu
                media_items = []
                for media_path in media_files:
                    filename = os.path.basename(media_path)
                    import mimetypes
                    mime_type, encoding = mimetypes.guess_type(media_path)
                    
                    media_items.append({
                        "location": filename,
                        "format": mime_type or "Unbekannt",
                        "location_type": "file"
                    })
                
                return {
                    "id": component_id,
                    "title": component_title,
                    "type": component_type,
                    "media_items": media_items
                }
            
            elif document_files:
                component_title = os.path.basename(document_files[0])
                logger.info(f"Titel aus Dokumentdatei extrahiert: {component_title}")
                
                # Füge Dokumentinformationen zu den Daten hinzu
                file_path = document_files[0]
                file_size = os.path.getsize(file_path)
                import mimetypes
                mime_type, encoding = mimetypes.guess_type(file_path)
                
                return {
                    "id": component_id,
                    "title": component_title,
                    "type": component_type,
                    "filename": component_title,
                    "size": str(file_size),
                    "type": mime_type or "application/octet-stream"
                }
        
        return {
            "id": component_id,
            "title": component_title,
            "type": component_type
        } 