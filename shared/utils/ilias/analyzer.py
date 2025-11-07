"""
Hauptklasse für die Analyse von ILIAS-Exporten.
"""

import os
import logging
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from .factory import ParserFactory
from .parsers import (
    IliasComponentParser,
    GroupParser,
    TestParser,
    MediaCastParser,
    FileParser,
    ItemGroupParser,
    CourseParser,
    MediaPoolParser,
    LearningModuleParser
)
from .container_parser import ContainerStructureParser, ContainerStructure
from ..log_handler import InMemoryLogHandler, create_log_handler

logger = logging.getLogger(__name__)

class Module:
    """Repräsentiert ein Modul im ILIAS-Kurs."""
    
    def __init__(self, id: str, title: str, type: str):
        self.id = id
        self.title = title
        self.type = type
        self.items = []
    
    def add_item(self, id: str, title: str, type: str, metadata: Dict[str, Any] = None):
        """Fügt ein Item zum Modul hinzu."""
        if metadata is None:
            metadata = {}
        
        item = {
            'id': id,
            'title': title,
            'type': type,
            'metadata': metadata
        }
        self.items.append(item)
        return item

# Typ-Alias für Item-Dictionary
Item = Dict[str, Any]

class IliasAnalyzer:
    """Analysiert einen ILIAS-Export und extrahiert die Struktur und Inhalte."""
    
    def __init__(self, export_dir: str):
        """
        Initialisiert den Analyzer.
        
        Args:
            export_dir: Pfad zum ILIAS-Export-Verzeichnis
        """
        self.export_dir = export_dir
        self.course_title = ""
        self.installation_id = ""
        self.installation_url = ""
        self.modules = []
        self.components = []
        self.course_structure = {}
        self.container_structure: Optional[ContainerStructure] = None
        
        # Log-Handler für Frontend-Ausgabe
        self.log_handler: Optional[InMemoryLogHandler] = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Richtet den Log-Handler für Frontend-Ausgabe ein."""
        self.log_handler = create_log_handler(
            logger_name='shared.utils.ilias.analyzer',
            level=logging.INFO
        )
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """
        Gibt alle gesammelten Log-Nachrichten zurück.
        
        Returns:
            Liste von Log-Einträgen als Dictionaries
        """
        if self.log_handler:
            return self.log_handler.get_logs()
        return []
    
    def clear_logs(self):
        """Löscht alle gesammelten Log-Nachrichten."""
        if self.log_handler:
            self.log_handler.clear_logs()
    
    def add_module(self, id: str, title: str, type: str) -> Module:
        """Fügt ein Modul zum Kurs hinzu."""
        module = Module(id, title, type)
        self.modules.append(module)
        return module
    
    def analyze(self) -> bool:
        """
        Analysiert den ILIAS-Export und extrahiert die Struktur und Inhalte.
        
        Returns:
            bool: True, wenn die Analyse erfolgreich war, sonst False.
        """
        try:
            # Manifest-Datei suchen
            manifest_path = os.path.join(self.export_dir, "manifest.xml")
            if not os.path.exists(manifest_path):
                # Suche in Unterverzeichnissen
                manifest_found = False
                logger.info(f"Suche manifest.xml in Unterverzeichnissen von {self.export_dir}")
                for root, dirs, files in os.walk(self.export_dir):
                    if "manifest.xml" in files:
                        manifest_path = os.path.join(root, "manifest.xml")
                        manifest_found = True
                        logger.info(f"Manifest-Datei gefunden: {manifest_path}")
                        break
                
                if not manifest_found:
                    logger.error(f"Keine manifest.xml gefunden in {self.export_dir}")
                    logger.info(f"Verzeichnisinhalt: {os.listdir(self.export_dir)}")
                    return False

            # Sicherstellen, dass export_dir auf das Manifest-Verzeichnis zeigt
            manifest_dir = os.path.dirname(manifest_path)
            if os.path.normpath(manifest_dir) != os.path.normpath(self.export_dir):
                logger.info(
                    f"Passe Basis-Verzeichnis an: {manifest_dir} (vorher: {self.export_dir})"
                )
                self.export_dir = manifest_dir
            
            # Prüfen, ob die Manifest-Datei existiert
            if not os.path.exists(manifest_path):
                logger.error(f"Die Manifest-Datei existiert nicht: {manifest_path}")
                return False
            
            # Manifest-Datei parsen
            try:
                tree = ET.parse(manifest_path)
                root = tree.getroot()
            except ET.ParseError as e:
                logger.error(f"Fehler beim Parsen der Manifest-Datei: {str(e)}")
                return False
            
            # Kurs-Titel und Installation-ID extrahieren
            self.course_title = root.get("Title", "Unbekannter Kurs")
            self.installation_id = root.get("InstallationId", "")
            self.installation_url = root.get("InstallationUrl", "")
            
            logger.info(f"Analysiere Kurs: {self.course_title}")
            
            # --- START DER KORREKTUR ---
            
            # Export-Sets finden
            export_sets = []
            logger.info(f"Suche Export-Sets in {os.path.basename(manifest_path)}")

            # Parse ExportSet entries from the main manifest
            for set_elem in root.findall('ExportSet'):
                set_path = set_elem.get('Path')
                if set_path:
                    # Erstelle den vollständigen Pfad basierend auf dem export_dir
                    full_set_path = os.path.join(self.export_dir, set_path)
                    if os.path.isdir(full_set_path):
                        export_sets.append(full_set_path)
                        logger.info(f"Export-Set gefunden: {full_set_path}")
                    else:
                        logger.warning(f"Export-Set Pfad nicht gefunden: {full_set_path}")
            
            if not export_sets:
                logger.error(f"Keine ExportSet-Einträge in {os.path.basename(manifest_path)} gefunden.")
                # Fallback: Versuche, das aktuelle Verzeichnis als Export-Set zu verwenden
                # (Dies ist für den Fall, dass der Benutzer einen Unterordner hochlädt)
                logger.info(f"Verwende Fallback: Analysiere {self.export_dir} als einzelnes Set.")
                export_sets.append(self.export_dir)

            logger.info(f"Gefundene Export-Sets: {len(export_sets)}")

            # --- ENDE DER KORREKTUR ---
            
            # Komponenten in den Export-Sets analysieren
            # Jeder "Export-Set" Pfad IST ein Komponenten-Verzeichnis
            for component_path in export_sets:
                self._analyze_component(component_path)
            
            # Versuche, die Container-Struktur zu parsen (falls vorhanden)
            self._parse_container_structure(export_sets)
            
            # Kurs-Struktur erstellen
            self.course_structure = {
                "title": self.course_title,
                "installation_id": self.installation_id,
                "installation_url": self.installation_url,
                "export_sets": export_sets,
                "has_container_structure": self.container_structure is not None
            }
            
            # Module aus Komponenten erstellen
            self._create_modules_from_components()
            
            # Wenn keine Module gefunden wurden, erstelle ein Dummy-Modul
            if not self.modules:
                logger.warning("Keine Module gefunden, erstelle Dummy-Modul")
                dummy_module = self.add_module(
                    id="dummy",
                    title="Beispielmodul",
                    type="dummy"
                )
                dummy_module.add_item(
                    id="dummy_item",
                    title="Beispiel-Item",
                    type="dummy",
                    metadata={"info": "Dies ist ein Beispiel-Item, da keine echten Module gefunden wurden."}
                )
            
            return True
        
        except Exception as e:
            logger.exception(f"Fehler bei der Analyse des ILIAS-Exports: {str(e)}")
            return False
    
    def _analyze_export_set(self, set_path: str) -> None:
        """
        Analysiert ein Export-Set und extrahiert die Komponenten.
        
        Args:
            set_path: Pfad zum Export-Set
        """
        try:
            # Prüfen, ob das Export-Set existiert
            if not os.path.exists(set_path):
                logger.error(f"Das Export-Set existiert nicht: {set_path}")
                return
            
            logger.info(f"Analysiere Export-Set: {set_path}")
            
            # Suche nach Komponenten-Verzeichnissen im Export-Set
            # ILIAS-Export-Verzeichnisse haben das Format: {timestamp}__{installation_id}__{type}_{id}
            component_dirs = []
            for item in os.listdir(set_path):
                item_path = os.path.join(set_path, item)
                # Akzeptiere alle Verzeichnisse, die dem ILIAS-Export-Muster entsprechen
                if os.path.isdir(item_path) and '__' in item and '_' in item:
                    component_dirs.append(item_path)
                    logger.info(f"Komponenten-Verzeichnis gefunden: {item_path}")
            
            # Wenn Komponenten-Verzeichnisse gefunden wurden, analysiere diese
            if component_dirs:
                for component_path in component_dirs:
                    self._analyze_component(component_path)
                return
            
            # Fallback: Suche nach manifest.xml
            manifest_path = os.path.join(set_path, "manifest.xml")
            if not os.path.exists(manifest_path):
                logger.error(f"Keine manifest.xml gefunden in {set_path}")
                logger.info(f"Verzeichnisinhalt: {os.listdir(set_path)}")
                return
            
            # Manifest-Datei parsen
            try:
                tree = ET.parse(manifest_path)
                root = tree.getroot()
            except ET.ParseError as e:
                logger.error(f"Fehler beim Parsen der Manifest-Datei {manifest_path}: {str(e)}")
                return
            
            # Komponenten im Export-Set finden
            folders_found = 0
            for child in root:
                if child.tag == "Folder":
                    folders_found += 1
                    folder_path = os.path.join(set_path, child.get("path", ""))
                    logger.info(f"Folder gefunden: {folder_path}")
                    if os.path.exists(folder_path):
                        self._analyze_component(folder_path)
                    else:
                        logger.warning(f"Der Ordner existiert nicht: {folder_path}")
            
            if folders_found == 0:
                logger.warning(f"Keine Folder-Elemente im Export-Set {set_path} gefunden")
                logger.info(f"XML-Struktur: {ET.tostring(root, encoding='utf-8').decode('utf-8')[:200]}...")
                
                # Versuche, das Export-Set selbst als Komponente zu analysieren
                self._analyze_component(set_path)
        
        except Exception as e:
            logger.exception(f"Fehler bei der Analyse des Export-Sets {set_path}: {str(e)}")
    
    def _analyze_component(self, component_path: str) -> None:
        """
        Analysiert eine Komponente und extrahiert die Daten.
        
        Args:
            component_path: Pfad zur Komponente
        """
        try:
            # Prüfen, ob die Komponente existiert
            if not os.path.exists(component_path):
                logger.error(f"Die Komponente existiert nicht: {component_path}")
                return
            
            logger.info(f"Analysiere Komponente: {component_path}")
            
            # Komponententyp aus dem Pfad ermitteln
            path_component_type = None
            component_name = os.path.basename(component_path)
            component_id = "unknown"
            component_title = "Unbekannt"
            
            if "__" in component_name:
                parts = component_name.split("__")
                if len(parts) >= 3:
                    type_id = parts[2].split("_")[0]  # z.B. "grp" aus "grp_6623"
                    path_component_type = type_id
                    component_id = parts[2].split("_")[1] if len(parts[2].split("_")) > 1 else "unknown"
                    logger.info(f"Komponententyp aus Pfad ermittelt: {path_component_type}, ID: {component_id}")
            
            # Suche nach export.xml oder anderen XML-Dateien für Titel
            export_xml_path = None
            for root, dirs, files in os.walk(component_path):
                for file in files:
                    if file == "export.xml":
                        export_xml_path = os.path.join(root, file)
                        break
                if export_xml_path:
                    break
            
            # Wenn export.xml gefunden wurde, versuche den Titel zu extrahieren
            if export_xml_path and os.path.exists(export_xml_path):
                logger.info(f"Export XML gefunden: {export_xml_path}")
                try:
                    tree = ET.parse(export_xml_path)
                    root = tree.getroot()
                    
                    # Suche nach dem Titel in verschiedenen Formaten
                    title_elem = root.find(".//Title")
                    if title_elem is not None and title_elem.text:
                        component_title = title_elem.text
                        logger.info(f"Titel aus export.xml extrahiert: {component_title}")
                    else:
                        # Alternative Suche nach dem Titel
                        for elem in root.iter():
                            if elem.tag.endswith("Title") and elem.text:
                                component_title = elem.text
                                logger.info(f"Titel aus alternativer Quelle extrahiert: {component_title}")
                                break
                except Exception as e:
                    logger.warning(f"Fehler beim Extrahieren des Titels aus export.xml: {str(e)}")
            
            # Manifest-Datei der Komponente suchen
            manifest_path = os.path.join(component_path, "manifest.xml")
            if not os.path.exists(manifest_path):
                logger.warning(f"Keine manifest.xml gefunden in {component_path}")
                
                # Wenn kein Manifest gefunden wurde, aber ein Typ aus dem Pfad ermittelt werden konnte
                if path_component_type:
                    logger.info(f"Verwende Komponententyp aus Pfad: {path_component_type}")
                    
                    # Erstelle eine einfache Komponente basierend auf dem Pfad
                    # Komponente zur Liste hinzufügen
                    self.components.append({
                        "type": path_component_type,
                        "path": component_path,
                        "data": {
                            "id": component_id,
                            "title": component_title
                        }
                    })
                    
                    logger.info(f"Komponente aus Pfad erstellt: {path_component_type} - {component_title}")
                    return
                
                logger.info(f"Verzeichnisinhalt: {os.listdir(component_path)}")
                return
            
            # Manifest-Datei parsen
            try:
                tree = ET.parse(manifest_path)
                root = tree.getroot()
            except ET.ParseError as e:
                logger.error(f"Fehler beim Parsen der Manifest-Datei {manifest_path}: {str(e)}")
                return
            
            # Komponententyp ermitteln (MainEntity ist das korrekte Attribut in ILIAS-Manifesten)
            component_type = root.get("MainEntity", "unknown")
            logger.info(f"Komponententyp ermittelt: {component_type}")
            
            # Titel aus dem Manifest extrahieren, falls vorhanden
            manifest_title = root.get("Title", "")
            if manifest_title:
                component_title = manifest_title
                logger.info(f"Titel aus manifest.xml extrahiert: {component_title}")
            
            # Wenn kein Typ im Manifest gefunden wurde, aber ein Typ aus dem Pfad ermittelt werden konnte
            if component_type == "unknown" and path_component_type:
                component_type = path_component_type
                logger.info(f"Verwende Komponententyp aus Pfad: {component_type}")
            
            # Parser für den Komponententyp auswählen
            parser = ParserFactory.get_parser(component_type, component_path)
            if parser:
                # Komponente parsen
                try:
                    component_data = parser.parse()
                    
                    # Wenn der Titel in den geparsten Daten vorhanden ist, verwende diesen
                    # ABER: manifest-Titel hat Priorität, falls Parser-Titel nur ein Dateiname ist (MediaObject)
                    if "title" in component_data and component_data["title"]:
                        parser_title = component_data["title"]
                        # Wenn wir einen manifest-Titel haben und der Parser-Titel ein Dateiname ist
                        # (z.B. "reward-points.png"), behalte den manifest-Titel
                        if manifest_title and '.' in parser_title and not parser_title.startswith(manifest_title):
                            # Parser hat einen Dateinamen gefunden, verwende manifest-Titel
                            component_title = manifest_title
                            component_data["title"] = manifest_title
                        else:
                            component_title = parser_title
                    else:
                        # Füge den extrahierten Titel zu den Daten hinzu
                        component_data["title"] = component_title if component_title else manifest_title
                    
                    # Komponente zur Liste hinzufügen
                    self.components.append({
                        "type": component_type,
                        "path": component_path,
                        "data": component_data
                    })
                    
                    logger.info(f"Komponente analysiert: {component_type} - {component_data.get('title', 'Unbekannt')}")
                except Exception as e:
                    logger.exception(f"Fehler beim Parsen der Komponente {component_path}: {str(e)}")
            else:
                logger.warning(f"Kein Parser für Komponententyp '{component_type}' gefunden")
        
        except Exception as e:
            logger.exception(f"Fehler bei der Analyse der Komponente {component_path}: {str(e)}")
    
    def _parse_container_structure(self, export_sets: List[str]) -> None:
        """
        Parst die Container-Struktur aus den Export-Sets.
        
        Args:
            export_sets: Liste der Export-Set-Pfade
        """
        try:
            # Priorisiere Gruppen-Export-Sets, da diese typischerweise die Hauptcontainer sind
            grp_export_sets = []
            other_export_sets = []
            
            for export_set in export_sets:
                if "_grp_" in export_set:
                    grp_export_sets.append(export_set)
                else:
                    other_export_sets.append(export_set)
            
            # Versuche zuerst Gruppen, dann andere
            for export_set in grp_export_sets + other_export_sets:
                if not os.path.isdir(export_set):
                    continue
                
                # Versuche, die Container-Struktur zu parsen
                parser = ContainerStructureParser(export_set)
                if parser.container_xml_path:
                    logger.info(f"Versuche Container-Struktur zu parsen aus: {export_set}")
                    structure = parser.parse()
                    
                    if structure:
                        self.container_structure = structure
                        logger.info(f"Container-Struktur erfolgreich geparst: {len(structure.item_by_item_id)} Items")
                        logger.info(f"Root-Item: {structure.root_item.title} ({structure.root_item.item_type})")
                        
                        # Zeige die Struktur im Log
                        if structure.root_item.children:
                            logger.info(f"Container hat {len(structure.root_item.children)} direkte Kinder:")
                            for child in structure.root_item.children:
                                logger.info(f"  - {child.title} ({child.item_type}, RefId={child.ref_id})")
                        
                        # Wenn dies eine Gruppe oder ein Kurs ist, sind wir fertig
                        # Ansonsten könnte es noch ein besseres Export-Set geben
                        if structure.root_item.item_type in ["grp", "crs"]:
                            logger.info(f"{structure.root_item.item_type.upper()}-Container gefunden, verwende diesen als Hauptstruktur")
                            return
        
        except Exception as e:
            logger.warning(f"Fehler beim Parsen der Container-Struktur: {e}")
            # Dies ist nicht kritisch, die Analyse kann auch ohne Container-Struktur fortgesetzt werden
    
    def _create_modules_from_components(self) -> None:
        """Erstellt Module aus den analysierten Komponenten."""
        logger.info(f"Erstelle Module aus {len(self.components)} Komponenten")
        
        if not self.components:
            logger.warning("Keine Komponenten gefunden, aus denen Module erstellt werden könnten")
            return
        
        # Zuerst die Hauptgruppe/den Hauptkurs finden, falls vorhanden
        main_group = None
        for component in self.components:
            if component["type"] in ["grp", "crs"] and "Minimalst Adaptiv" in component["data"].get("title", ""):
                main_group = component
                logger.info(f"Hauptcontainer gefunden: {component['data'].get('title', 'Unbekannt')}")
                break
        
        # Wenn eine Hauptgruppe gefunden wurde, versuche die Struktur zu extrahieren
        group_structure = {}
        if main_group:
            # Versuche, die Gruppenstruktur zu extrahieren
            if "container_settings" in main_group["data"]:
                logger.info("Container-Einstellungen in der Hauptgruppe gefunden")
                container_settings = main_group["data"]["container_settings"]
                
                # Extrahiere die Referenzen zu anderen Komponenten
                if "items" in container_settings:
                    for item in container_settings["items"]:
                        if "ref_id" in item:
                            ref_id = item["ref_id"]
                            title = item.get("title", "Unbekannt")
                            item_type = item.get("type", "unknown")
                            group_structure[ref_id] = {"title": title, "type": item_type}
                            logger.info(f"Referenz gefunden: {ref_id} -> {title} ({item_type})")
        
        # Komponenten durchlaufen und Module erstellen
        for component in self.components:
            comp_type = component["type"]
            comp_data = component["data"]
            
            # Debug-Logging
            logger.info(f"Verarbeite Komponente: Typ={comp_type}, Daten={comp_data}")
            
            # Modul erstellen
            module = self.add_module(
                id=comp_data.get("id", ""),
                title=comp_data.get("title", f"{comp_type.upper()} ohne Titel"),
                type=comp_type
            )
            
            logger.info(f"Modul erstellt: {module.title} ({module.type})")
            
            # Items je nach Komponententyp hinzufügen
            if comp_type in ["grp", "crs"]:
                # Gruppeneinstellungen
                if "registration" in comp_data:
                    reg = comp_data["registration"]
                    module.add_item(
                        id="registration",
                        title="Registrierungseinstellungen",
                        type="settings",
                        metadata={
                            "type": reg.get("type", "Unbekannt"),
                            "waiting_list": reg.get("waiting_list", "Nein"),
                            "max_members": reg.get("max_members", "Unbegrenzt"),
                            "min_members": reg.get("min_members", "0")
                        }
                    )
                
                if "container_settings" in comp_data:
                    module.add_item(
                        id="container",
                        title="Container-Einstellungen",
                        type="settings",
                        metadata=comp_data["container_settings"]
                    )
                    
                    # Füge Referenzen zu anderen Komponenten hinzu
                    if "items" in comp_data["container_settings"]:
                        for i, item in enumerate(comp_data["container_settings"]["items"]):
                            module.add_item(
                                id=f"ref_{i}",
                                title=item.get("title", "Unbekannte Referenz"),
                                type="reference",
                                metadata={
                                    "ref_id": item.get("ref_id", ""),
                                    "type": item.get("type", "unknown")
                                }
                            )
            
            elif comp_type == "tst":
                # Testeinstellungen
                if "qti_metadata" in comp_data:
                    module.add_item(
                        id="qti_metadata",
                        title="Testeinstellungen",
                        type="test",
                        metadata=comp_data["qti_metadata"]
                    )
                
                if "mark_steps" in comp_data:
                    module.add_item(
                        id="mark_steps",
                        title="Bewertungsstufen",
                        type="test",
                        metadata=comp_data["mark_steps"]
                    )
                
                # Fragen hinzufügen, falls vorhanden
                if "questions" in comp_data:
                    for i, question in enumerate(comp_data["questions"]):
                        module.add_item(
                            id=f"question_{i}",
                            title=question.get("title", f"Frage {i+1}"),
                            type="question",
                            metadata=question
                        )
            
            elif comp_type == "mcst":
                # Media Cast Items
                if "media_items" in comp_data:
                    for i, item in enumerate(comp_data["media_items"]):
                        module.add_item(
                            id=f"media_{i}",
                            title=item.get("location", "Unbekanntes Medium"),
                            type="media",
                            metadata={
                                "format": item.get("format", "Unbekannt"),
                                "location": item.get("location", ""),
                                "location_type": item.get("location_type", "")
                            }
                        )
                
                # Wenn keine Media-Items gefunden wurden, aber ein Titel vorhanden ist
                elif "title" in comp_data:
                    # Suche nach Mediendateien im Komponenten-Pfad
                    media_files = []
                    component_path = component["path"]
                    for root, dirs, files in os.walk(component_path):
                        for file in files:
                            if file.lower().endswith(('.mp4', '.mp3', '.avi', '.mov', '.wmv', '.flv')):
                                media_files.append(os.path.join(root, file))
                    
                    # Füge gefundene Mediendateien als Items hinzu
                    for i, media_path in enumerate(media_files):
                        filename = os.path.basename(media_path)
                        import mimetypes
                        mime_type, encoding = mimetypes.guess_type(media_path)
                        
                        module.add_item(
                            id=f"media_{i}",
                            title=filename,
                            type="media",
                            metadata={
                                "format": mime_type or "Unbekannt",
                                "location": filename,
                                "location_type": "file"
                            }
                        )
            
            elif comp_type == "file":
                # Datei
                filename = comp_data.get("filename", "Unbekannte Datei")
                module.add_item(
                    id="file",
                    title=filename,
                    type="documents",
                    metadata={
                        "type": comp_data.get("type", "Unbekannt"),
                        "size": comp_data.get("size", "0")
                    }
                )
                
                # Wenn Versionen vorhanden sind, füge sie hinzu
                if "versions" in comp_data:
                    for i, version in enumerate(comp_data["versions"]):
                        module.add_item(
                            id=f"version_{i}",
                            title=f"Version {version.get('version', i+1)}",
                            type="file_version",
                            metadata=version
                        )
            
            elif comp_type == "itgr":
                # Items in der Item-Gruppe
                if "items" in comp_data:
                    for i, item in enumerate(comp_data["items"]):
                        module.add_item(
                            id=f"item_{i}",
                            title=item.get("title", f"Item {item.get('item_id', 'Unbekannt')}"),
                            type="item",
                            metadata=item
                        )
                
                # Wenn keine Items gefunden wurden, aber ein Titel vorhanden ist
                elif "title" in comp_data:
                    # Erstelle ein Dummy-Item mit dem Titel der Item-Gruppe
                    module.add_item(
                        id="item_dummy",
                        title=comp_data["title"],
                        type="item",
                        metadata={"info": f"Item-Gruppe: {comp_data['title']}"}
                    )
            
            # Wenn keine Items hinzugefügt wurden, füge ein Dummy-Item hinzu
            if not module.items:
                module.add_item(
                    id="dummy",
                    title=f"Inhalt von {module.title}",
                    type="info",
                    metadata={"info": f"Keine spezifischen Items für diesen {comp_type.upper()}-Typ gefunden."}
                )
    
    def generate_markdown(self) -> str:
        """
        Generiert eine Markdown-Dokumentation des analysierten ILIAS-Kurses.
        
        Returns:
            Markdown-String
        """
        markdown = []
        
        # Kurs-Titel
        if self.course_title:
            markdown.append(f"# {self.course_title}")
        else:
            markdown.append("# ILIAS-Kurs")
        
        markdown.append("")
        
        # Metadaten
        markdown.append("## Metadaten")
        markdown.append("")
        
        if self.installation_id:
            markdown.append(f"- **Installation-ID:** {self.installation_id}")
        
        if self.installation_url:
            markdown.append(f"- **Installation-URL:** {self.installation_url}")
        
        if hasattr(self, 'export_date') and self.export_date:
            markdown.append(f"- **Export-Datum:** {self.export_date}")
        
        markdown.append("")
        
        # Module
        if self.modules:
            markdown.append("## Module")
            markdown.append("")
            
            for module in self.modules:
                markdown.append(f"### {module.title}")
                
                if module.description:
                    markdown.append("")
                    markdown.append(module.description)
                
                markdown.append("")
                
                # Items im Modul
                if module.items:
                    for item in module.items:
                        markdown.append(f"#### {item.title}")
                        markdown.append("")
                        
                        if item.description:
                            markdown.append(item.description)
                            markdown.append("")
                        
                        # Spezifische Informationen je nach Komponententyp
                        if item.component_type == 'group':
                            self._append_group_info(markdown, item)
                        elif item.component_type == 'test':
                            self._append_test_info(markdown, item)
                        elif item.component_type == 'exercise':
                            self._append_exercise_info(markdown, item)
                        elif item.component_type == 'forum':
                            self._append_forum_info(markdown, item)
                        elif item.component_type == 'wiki':
                            self._append_wiki_info(markdown, item)
                        elif item.component_type == 'mediacast':
                            self._append_mediacast_info(markdown, item)
                        elif item.component_type == 'file':
                            self._append_file_info(markdown, item)
                        elif item.component_type == 'itemgroup':
                            self._append_itemgroup_info(markdown, item)
                        else:
                            # Generische Metadaten für andere Komponententypen
                            if item.metadata:
                                markdown.append("**Metadaten:**")
                                markdown.append("")
                                markdown.append("```")
                                markdown.append(json.dumps(item.metadata, indent=2, ensure_ascii=False))
                                markdown.append("```")
                                markdown.append("")
                else:
                    markdown.append("*Keine Elemente in diesem Modul*")
                    markdown.append("")
        else:
            markdown.append("## Keine Module gefunden")
            markdown.append("")
        
        return "\n".join(markdown)

    def _append_group_info(self, markdown: List[str], item: Item) -> None:
        """
        Fügt Gruppeninformationen zum Markdown hinzu.
        
        Args:
            markdown: Liste mit Markdown-Zeilen
            item: Gruppen-Item
        """
        if not item.metadata:
            return
        
        # Basis-Informationen
        if 'id' in item.metadata:
            markdown.append(f"**Gruppen-ID:** {item.metadata['id']}")
        
        if 'owner' in item.metadata:
            markdown.append(f"**Besitzer:** {item.metadata['owner']}")
        
        if 'createdate' in item.metadata:
            markdown.append(f"**Erstellt am:** {item.metadata['createdate']}")
        
        if 'lastupdate' in item.metadata:
            markdown.append(f"**Zuletzt aktualisiert:** {item.metadata['lastupdate']}")
        
        markdown.append("")
        
        # Registrierungseinstellungen
        if 'registration' in item.metadata:
            reg = item.metadata['registration']
            markdown.append("**Registrierungseinstellungen:**")
            markdown.append("")
            
            if 'type' in reg:
                markdown.append(f"- **Typ:** {reg['type']}")
            
            if 'waiting_list' in reg:
                markdown.append(f"- **Warteliste:** {'Ja' if reg['waiting_list'] else 'Nein'}")
            
            if 'max_members' in reg:
                markdown.append(f"- **Maximale Mitglieder:** {reg['max_members']}")
            
            if 'min_members' in reg:
                markdown.append(f"- **Minimale Mitglieder:** {reg['min_members']}")
            
            if 'start' in reg:
                markdown.append(f"- **Startdatum:** {reg['start']}")
            
            if 'end' in reg:
                markdown.append(f"- **Enddatum:** {reg['end']}")
            
            if 'password' in reg:
                markdown.append(f"- **Passwort erforderlich:** {'Ja' if reg['password'] else 'Nein'}")
            
            markdown.append("")
        
        # Container-Einstellungen und Items
        if 'container_settings' in item.metadata and 'items' in item.metadata['container_settings']:
            items = item.metadata['container_settings']['items']
            markdown.append("**Enthaltene Elemente:**")
            markdown.append("")
            
            for container_item in items:
                item_title = container_item.get('title', 'Unbekannter Titel')
                item_type = container_item.get('type', 'Unbekannter Typ')
                markdown.append(f"- {item_title} ({item_type})")
            
            markdown.append("")
        
        # Mitglieder
        if 'members' in item.metadata:
            members = item.metadata['members']
            markdown.append("**Mitglieder:**")
            markdown.append("")
            
            for member in members:
                member_name = f"{member.get('firstname', '')} {member.get('lastname', '')}".strip()
                if not member_name:
                    member_name = member.get('login', 'Unbekannter Benutzer')
                
                member_role = member.get('role', 'Mitglied')
                markdown.append(f"- {member_name} ({member_role})")
            
            markdown.append("")

    def _append_test_info(self, markdown: List[str], item: Item) -> None:
        """
        Fügt Testinformationen zum Markdown hinzu.
        
        Args:
            markdown: Liste mit Markdown-Zeilen
            item: Test-Item
        """
        if not item.metadata:
            return
        
        # Basis-Informationen
        if 'id' in item.metadata:
            markdown.append(f"**Test-ID:** {item.metadata['id']}")
        
        if 'owner' in item.metadata:
            markdown.append(f"**Besitzer:** {item.metadata['owner']}")
        
        if 'createdate' in item.metadata:
            markdown.append(f"**Erstellt am:** {item.metadata['createdate']}")
        
        if 'lastupdate' in item.metadata:
            markdown.append(f"**Zuletzt aktualisiert:** {item.metadata['lastupdate']}")
        
        markdown.append("")
        
        # Einstellungen
        if 'settings' in item.metadata:
            settings = item.metadata['settings']
            markdown.append("**Testeinstellungen:**")
            markdown.append("")
            
            for key, value in settings.items():
                markdown.append(f"- **{key}:** {value}")
            
            markdown.append("")
        
        # QTI-Daten
        if 'qti_data' in item.metadata:
            qti_data = item.metadata['qti_data']
            markdown.append("**QTI-Daten:**")
            markdown.append("")
            
            if 'title' in qti_data:
                markdown.append(f"- **Titel:** {qti_data['title']}")
            
            if 'description' in qti_data:
                markdown.append(f"- **Beschreibung:** {qti_data['description']}")
            
            # Fragen
            if 'questions' in qti_data:
                questions = qti_data['questions']
                markdown.append("")
                markdown.append("**Fragen:**")
                markdown.append("")
                
                for i, question in enumerate(questions, 1):
                    q_title = question.get('title', f'Frage {i}')
                    q_type = question.get('type', 'Unbekannter Typ')
                    
                    markdown.append(f"- **{q_title}** ({q_type})")
                    
                    if 'text' in question:
                        markdown.append(f"  - Text: {question['text']}")
                    
                    if 'points' in question:
                        markdown.append(f"  - Punkte: {question['points']}")
                    
                    if 'options' in question:
                        markdown.append("  - Optionen:")
                        for option in question['options']:
                            correct = option.get('correct', False)
                            option_text = option.get('text', 'Keine Angabe')
                            markdown.append(f"    - {'[x]' if correct else '[ ]'} {option_text}")
            
            markdown.append("")

    def _append_exercise_info(self, markdown: List[str], item: Item) -> None:
        """
        Fügt Übungsinformationen zum Markdown hinzu.
        
        Args:
            markdown: Liste mit Markdown-Zeilen
            item: Übungs-Item
        """
        if not item.metadata:
            return
        
        # Basis-Informationen
        if 'id' in item.metadata:
            markdown.append(f"**Übungs-ID:** {item.metadata['id']}")
        
        if 'owner' in item.metadata:
            markdown.append(f"**Besitzer:** {item.metadata['owner']}")
        
        if 'createdate' in item.metadata:
            markdown.append(f"**Erstellt am:** {item.metadata['createdate']}")
        
        if 'lastupdate' in item.metadata:
            markdown.append(f"**Zuletzt aktualisiert:** {item.metadata['lastupdate']}")
        
        if 'instructions' in item.metadata:
            markdown.append("")
            markdown.append("**Anweisungen:**")
            markdown.append("")
            markdown.append(item.metadata['instructions'])
        
        markdown.append("")
        
        # Einstellungen
        if 'settings' in item.metadata:
            settings = item.metadata['settings']
            markdown.append("**Übungseinstellungen:**")
            markdown.append("")
            
            for key, value in settings.items():
                markdown.append(f"- **{key}:** {value}")
            
            markdown.append("")
        
        # Aufgaben
        if 'assignments' in item.metadata:
            assignments = item.metadata['assignments']
            markdown.append("**Aufgaben:**")
            markdown.append("")
            
            for assignment in assignments:
                a_title = assignment.get('title', 'Unbekannte Aufgabe')
                markdown.append(f"- **{a_title}**")
                
                if 'description' in assignment:
                    markdown.append(f"  - Beschreibung: {assignment['description']}")
                
                if 'type' in assignment:
                    markdown.append(f"  - Typ: {assignment['type']}")
                
                # Termine
                for date_field in ['startdate', 'enddate', 'submissiondate']:
                    if date_field in assignment:
                        field_name = {
                            'startdate': 'Startdatum',
                            'enddate': 'Enddatum',
                            'submissiondate': 'Abgabedatum'
                        }.get(date_field, date_field)
                        
                        markdown.append(f"  - {field_name}: {assignment[date_field]}")
                
                # Dateien
                if 'files' in assignment:
                    markdown.append("  - Dateien:")
                    for file in assignment['files']:
                        file_name = file.get('name', 'Unbekannte Datei')
                        file_size = file.get('size', 'Unbekannte Größe')
                        markdown.append(f"    - {file_name} ({file_size} Bytes)")
                
                # Einreichungen
                if 'submissions' in assignment:
                    markdown.append("  - Einreichungen:")
                    for submission in assignment['submissions']:
                        user_id = submission.get('user_id', 'Unbekannter Benutzer')
                        status = submission.get('status', 'Unbekannter Status')
                        markdown.append(f"    - Benutzer {user_id}: {status}")
                        
                        if 'files' in submission:
                            markdown.append("      - Dateien:")
                            for file in submission['files']:
                                file_name = file.get('name', 'Unbekannte Datei')
                                file_size = file.get('size', 'Unbekannte Größe')
                                markdown.append(f"        - {file_name} ({file_size} Bytes)")
            
            markdown.append("")

    def _append_forum_info(self, markdown: List[str], item: Item) -> None:
        """
        Fügt Foruminformationen zum Markdown hinzu.
        
        Args:
            markdown: Liste mit Markdown-Zeilen
            item: Forum-Item
        """
        if not item.metadata:
            return
        
        # Basis-Informationen
        if 'id' in item.metadata:
            markdown.append(f"**Forum-ID:** {item.metadata['id']}")
        
        if 'owner' in item.metadata:
            markdown.append(f"**Besitzer:** {item.metadata['owner']}")
        
        if 'createdate' in item.metadata:
            markdown.append(f"**Erstellt am:** {item.metadata['createdate']}")
        
        if 'lastupdate' in item.metadata:
            markdown.append(f"**Zuletzt aktualisiert:** {item.metadata['lastupdate']}")
        
        markdown.append("")
        
        # Einstellungen
        if 'settings' in item.metadata:
            settings = item.metadata['settings']
            markdown.append("**Forumeinstellungen:**")
            markdown.append("")
            
            for key, value in settings.items():
                markdown.append(f"- **{key}:** {value}")
            
            markdown.append("")
        
        # Themen
        if 'topics' in item.metadata:
            topics = item.metadata['topics']
            markdown.append("**Themen:**")
            markdown.append("")
            
            for topic in topics:
                t_title = topic.get('title', 'Unbekanntes Thema')
                t_author = topic.get('author', 'Unbekannter Autor')
                t_date = topic.get('create_date', 'Unbekanntes Datum')
                
                markdown.append(f"- **{t_title}** (von {t_author}, {t_date})")
                
                if 'description' in topic:
                    markdown.append(f"  - Beschreibung: {topic['description']}")
                
                if 'views' in topic:
                    markdown.append(f"  - Aufrufe: {topic['views']}")
                
                if 'sticky' in topic:
                    markdown.append(f"  - Angepinnt: {'Ja' if topic['sticky'] else 'Nein'}")
                
                if 'closed' in topic:
                    markdown.append(f"  - Geschlossen: {'Ja' if topic['closed'] else 'Nein'}")
                
                # Beiträge
                if 'posts' in topic:
                    markdown.append("  - Beiträge:")
                    for post in topic['posts']:
                        p_title = post.get('title', 'Unbekannter Beitrag')
                        p_author = post.get('author', 'Unbekannter Autor')
                        p_date = post.get('create_date', 'Unbekanntes Datum')
                        
                        # Einrückung basierend auf der Tiefe
                        indent = "    "
                        if 'depth' in post:
                            try:
                                depth = int(post['depth'])
                                indent = "    " + "  " * depth
                            except (ValueError, TypeError):
                                pass
                        
                        markdown.append(f"{indent}- **{p_title}** (von {p_author}, {p_date})")
                        
                        if 'message' in post:
                            # Kürze die Nachricht, wenn sie zu lang ist
                            message = post['message']
                            if len(message) > 100:
                                message = message[:97] + "..."
                            
                            markdown.append(f"{indent}  - {message}")
                        
                        # Anhänge
                        if 'attachments' in post:
                            markdown.append(f"{indent}  - Anhänge:")
                            for attachment in post['attachments']:
                                a_name = attachment.get('name', 'Unbekannte Datei')
                                a_size = attachment.get('size', 'Unbekannte Größe')
                                markdown.append(f"{indent}    - {a_name} ({a_size} Bytes)")
            
            markdown.append("")

    def _append_wiki_info(self, markdown: List[str], item: Item) -> None:
        """
        Fügt Wiki-Informationen zum Markdown hinzu.
        
        Args:
            markdown: Liste mit Markdown-Zeilen
            item: Wiki-Item
        """
        if not item.metadata:
            return
        
        # Basis-Informationen
        if 'id' in item.metadata:
            markdown.append(f"**Wiki-ID:** {item.metadata['id']}")
        
        if 'owner' in item.metadata:
            markdown.append(f"**Besitzer:** {item.metadata['owner']}")
        
        if 'createdate' in item.metadata:
            markdown.append(f"**Erstellt am:** {item.metadata['createdate']}")
        
        if 'lastupdate' in item.metadata:
            markdown.append(f"**Zuletzt aktualisiert:** {item.metadata['lastupdate']}")
        
        markdown.append("")
        
        # Einstellungen
        if 'settings' in item.metadata:
            settings = item.metadata['settings']
            markdown.append("**Wiki-Einstellungen:**")
            markdown.append("")
            
            for key, value in settings.items():
                markdown.append(f"- **{key}:** {value}")
            
            markdown.append("")
        
        # Seiten
        if 'pages' in item.metadata:
            pages = item.metadata['pages']
            markdown.append("**Wiki-Seiten:**")
            markdown.append("")
            
            # Sortiere Seiten, Startseite zuerst
            sorted_pages = sorted(pages, key=lambda p: not p.get('is_startpage', False))
            
            for page in sorted_pages:
                p_title = page.get('title', 'Unbekannte Seite')
                p_author = page.get('author', 'Unbekannter Autor')
                p_date = page.get('create_date', 'Unbekanntes Datum')
                
                # Markiere Startseite
                start_page_marker = " (Startseite)" if page.get('is_startpage', False) else ""
                
                markdown.append(f"- **{p_title}**{start_page_marker} (von {p_author}, {p_date})")
                
                if 'content' in page:
                    # Kürze den Inhalt, wenn er zu lang ist
                    content = page['content']
                    if len(content) > 100:
                        content = content[:97] + "..."
                    
                    markdown.append(f"  - Inhalt: {content}")
                
                # Versionen
                if 'versions' in page:
                    markdown.append("  - Versionen:")
                    for version in page['versions']:
                        v_number = version.get('number', 'Unbekannte Version')
                        v_author = version.get('author', 'Unbekannter Autor')
                        v_date = version.get('create_date', 'Unbekanntes Datum')
                        
                        markdown.append(f"    - Version {v_number} (von {v_author}, {v_date})")
                        
                        if 'comment' in version:
                            markdown.append(f"      - Kommentar: {version['comment']}")
                
                # Anhänge
                if 'attachments' in page:
                    markdown.append("  - Anhänge:")
                    for attachment in page['attachments']:
                        a_name = attachment.get('name', 'Unbekannte Datei')
                        a_size = attachment.get('size', 'Unbekannte Größe')
                        markdown.append(f"    - {a_name} ({a_size} Bytes)")
            
            markdown.append("")

    def _append_mediacast_info(self, markdown: List[str], item: Item) -> None:
        """
        Fügt MediaCast-Informationen zum Markdown hinzu.
        
        Args:
            markdown: Liste mit Markdown-Zeilen
            item: MediaCast-Item
        """
        if not item.metadata:
            return
        
        # Basis-Informationen
        if 'id' in item.metadata:
            markdown.append(f"**MediaCast-ID:** {item.metadata['id']}")
        
        if 'owner' in item.metadata:
            markdown.append(f"**Besitzer:** {item.metadata['owner']}")
        
        if 'createdate' in item.metadata:
            markdown.append(f"**Erstellt am:** {item.metadata['createdate']}")
        
        if 'lastupdate' in item.metadata:
            markdown.append(f"**Zuletzt aktualisiert:** {item.metadata['lastupdate']}")
        
        markdown.append("")
        
        # Einstellungen
        if 'settings' in item.metadata:
            settings = item.metadata['settings']
            markdown.append("**MediaCast-Einstellungen:**")
            markdown.append("")
            
            for key, value in settings.items():
                markdown.append(f"- **{key}:** {value}")
            
            markdown.append("")
        
        # Medien
        if 'media' in item.metadata:
            media = item.metadata['media']
            markdown.append("**Medien:**")
            markdown.append("")
            
            for medium in media:
                m_title = medium.get('title', 'Unbekanntes Medium')
                m_type = medium.get('type', 'Unbekannter Typ')
                
                markdown.append(f"- **{m_title}** ({m_type})")
                
                if 'description' in medium:
                    markdown.append(f"  - Beschreibung: {medium['description']}")
                
                if 'duration' in medium:
                    markdown.append(f"  - Dauer: {medium['duration']}")
                
                if 'size' in medium:
                    markdown.append(f"  - Größe: {medium['size']} Bytes")
                
                if 'create_date' in medium:
                    markdown.append(f"  - Erstellt am: {medium['create_date']}")
                
                if 'path' in medium:
                    markdown.append(f"  - Pfad: {medium['path']}")
            
            markdown.append("")

    def _append_file_info(self, markdown: List[str], item: Item) -> None:
        """
        Fügt Datei-Informationen zum Markdown hinzu.
        
        Args:
            markdown: Liste mit Markdown-Zeilen
            item: Datei-Item
        """
        if not item.metadata:
            return
        
        # Basis-Informationen
        if 'id' in item.metadata:
            markdown.append(f"**Datei-ID:** {item.metadata['id']}")
        
        if 'owner' in item.metadata:
            markdown.append(f"**Besitzer:** {item.metadata['owner']}")
        
        if 'createdate' in item.metadata:
            markdown.append(f"**Erstellt am:** {item.metadata['createdate']}")
        
        if 'lastupdate' in item.metadata:
            markdown.append(f"**Zuletzt aktualisiert:** {item.metadata['lastupdate']}")
        
        markdown.append("")
        
        # Dateidetails
        if 'filename' in item.metadata:
            markdown.append(f"**Dateiname:** {item.metadata['filename']}")
        
        if 'filetype' in item.metadata:
            markdown.append(f"**Dateityp:** {item.metadata['filetype']}")
        
        if 'filesize' in item.metadata:
            markdown.append(f"**Dateigröße:** {item.metadata['filesize']} Bytes")
        
        if 'version' in item.metadata:
            markdown.append(f"**Version:** {item.metadata['version']}")
        
        if 'path' in item.metadata:
            markdown.append(f"**Pfad:** {item.metadata['path']}")
        
        markdown.append("")

    def _append_itemgroup_info(self, markdown: List[str], item: Item) -> None:
        """
        Fügt Itemgruppen-Informationen zum Markdown hinzu.
        
        Args:
            markdown: Liste mit Markdown-Zeilen
            item: Itemgruppen-Item
        """
        if not item.metadata:
            return
        
        # Basis-Informationen
        if 'id' in item.metadata:
            markdown.append(f"**Itemgruppen-ID:** {item.metadata['id']}")
        
        if 'owner' in item.metadata:
            markdown.append(f"**Besitzer:** {item.metadata['owner']}")
        
        if 'createdate' in item.metadata:
            markdown.append(f"**Erstellt am:** {item.metadata['createdate']}")
        
        if 'lastupdate' in item.metadata:
            markdown.append(f"**Zuletzt aktualisiert:** {item.metadata['lastupdate']}")
        
        markdown.append("")
        
        # Einstellungen
        if 'settings' in item.metadata:
            settings = item.metadata['settings']
            markdown.append("**Itemgruppen-Einstellungen:**")
            markdown.append("")
            
            for key, value in settings.items():
                markdown.append(f"- **{key}:** {value}")
            
            markdown.append("")
        
        # Items
        if 'items' in item.metadata:
            items = item.metadata['items']
            markdown.append("**Enthaltene Elemente:**")
            markdown.append("")
            
            for sub_item in items:
                i_title = sub_item.get('title', 'Unbekanntes Element')
                i_type = sub_item.get('type', 'Unbekannter Typ')
                
                markdown.append(f"- **{i_title}** ({i_type})")
                
                if 'description' in sub_item:
                    markdown.append(f"  - Beschreibung: {sub_item['description']}")
            
            markdown.append("") 