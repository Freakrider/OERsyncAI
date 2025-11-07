"""
StructureMapper für ILIAS zu Moodle Konvertierung.

Mappt die ILIAS Container-Struktur 1:1 zu einer Moodle-Kursstruktur.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MoodleSection:
    """Repräsentiert eine Moodle-Section."""
    
    section_id: int
    number: int
    name: str
    summary: str = ""
    visible: bool = True
    activities: List['MoodleActivity'] = field(default_factory=list)
    
    def add_activity(self, activity: 'MoodleActivity') -> None:
        """Fügt eine Activity zur Section hinzu."""
        self.activities.append(activity)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            'section_id': self.section_id,
            'number': self.number,
            'name': self.name,
            'summary': self.summary,
            'visible': self.visible,
            'activity_count': len(self.activities),
            'activities': [act.to_dict() for act in self.activities]
        }


@dataclass
class MoodleActivity:
    """Repräsentiert eine Moodle-Activity."""
    
    activity_id: int
    module_id: int
    section_id: int
    module_name: str  # resource, quiz, forum, etc.
    title: str
    intro: str = ""
    visible: bool = True
    indent: int = 0
    
    # Original ILIAS-Daten für Referenz
    ilias_type: Optional[str] = None
    ilias_id: Optional[str] = None
    ilias_ref_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            'activity_id': self.activity_id,
            'module_id': self.module_id,
            'section_id': self.section_id,
            'module_name': self.module_name,
            'title': self.title,
            'intro': self.intro,
            'visible': self.visible,
            'indent': self.indent,
            'ilias_type': self.ilias_type,
            'ilias_id': self.ilias_id,
            'ilias_ref_id': self.ilias_ref_id
        }


@dataclass
class MoodleStructure:
    """Repräsentiert die komplette Moodle-Kursstruktur."""
    
    course_title: str
    sections: List[MoodleSection] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_section(self, section: MoodleSection) -> None:
        """Fügt eine Section hinzu."""
        self.sections.append(section)
    
    def add_warning(self, warning: str) -> None:
        """Fügt eine Warnung hinzu."""
        self.warnings.append(warning)
        logger.warning(f"Conversion Warning: {warning}")
    
    def get_section_by_id(self, section_id: int) -> Optional[MoodleSection]:
        """Findet eine Section anhand ihrer ID."""
        for section in self.sections:
            if section.section_id == section_id:
                return section
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            'course_title': self.course_title,
            'total_sections': len(self.sections),
            'total_activities': sum(len(s.activities) for s in self.sections),
            'sections': [s.to_dict() for s in self.sections],
            'warnings': self.warnings
        }


class StructureMapper:
    """
    Mappt ILIAS Container-Struktur zu Moodle-Struktur.
    
    Führt ein 1:1-Mapping durch und sammelt Kompatibilitäts-Warnungen.
    """
    
    # Mapping von ILIAS-Typen zu Moodle-Modulen
    TYPE_MAPPING = {
        'file': 'resource',
        'fold': 'folder',
        'tst': 'quiz',
        'excex': 'assign',  # Exercise
        'frm': 'forum',
        'wiki': 'wiki',
        'mcst': 'resource',  # MediaCast als Resource
        'webr': 'url',  # Weblink
        'sahs': 'scorm',  # SCORM
        'lm': 'book',  # Learning Module
        'htlm': 'page',  # HTML Learning Module
        'glo': 'glossary',
        'svy': 'feedback',  # Survey
        'poll': 'choice',
    }
    
    def __init__(self, container_structure=None, itemgroup_resolver=None, components=None):
        """
        Initialisiert den Mapper.
        
        Args:
            container_structure: ContainerStructure aus dem Parser
            itemgroup_resolver: ItemGroupResolver für ItemGroup-Auflösung
            components: Liste der ILIAS Components (für ItemGroup-Resolution)
        """
        self.container_structure = container_structure
        self.itemgroup_resolver = itemgroup_resolver
        self.components = components or []
        
        # Zähler für IDs
        self.next_section_id = 1
        self.next_activity_id = 1
        # Modul-IDs und Activity-IDs sollen identisch bleiben, damit
        # spätere Moodle-Parser eine eindeutige Zuordnung herstellen können.
        self.next_module_id = 1
    
    def map_to_moodle(self) -> MoodleStructure:
        """
        Mappt die Container-Struktur zu einer Moodle-Struktur.
        
        Verwendet "Methode 2: Visuelle Hierarchie durch Einrücken" aus dem Konvertierungs-Konzept:
        - Hauptordner (Ebene 1) → Moodle Section
        - Unterordner (Ebene 2+) → Label mit Einrückung
        - Activities → Einrückung entsprechend Hierarchie-Ebene
        
        Returns:
            MoodleStructure mit Sections und Activities
        """
        if not self.container_structure:
            logger.error("Keine Container-Struktur verfügbar")
            return MoodleStructure(
                course_title="Unbekannter Kurs",
                warnings=["Keine Container-Struktur zum Mappen verfügbar"]
            )
        
        root = self.container_structure.root_item
        structure = MoodleStructure(course_title=root.title)
        
        logger.info(f"Mappe ILIAS-Kurs zu Moodle mit Hierarchie-Erhaltung: {root.title}")
        
        # Erstelle Standard-Section 0 (Allgemein)
        general_section = MoodleSection(
            section_id=0,
            number=0,
            name="Allgemein",
            summary="Allgemeiner Abschnitt"
        )
        structure.add_section(general_section)
        
        # Verarbeite die Kinder des Root-Items mit Hierarchie-Level
        for child in root.children:
            self._process_item_hierarchical(child, structure, level=1)
        
        logger.info(f"Mapping abgeschlossen: {len(structure.sections)} Sections, "
                   f"{sum(len(s.activities) for s in structure.sections)} Activities")
        
        return structure
    
    def _process_item_hierarchical(self, item, structure: MoodleStructure, 
                                   level: int = 1, current_section: Optional[MoodleSection] = None) -> None:
        """
        Verarbeitet ein Container-Item rekursiv mit Hierarchie-Ebenen (NEU).
        
        Strategie "Methode 2: Visuelle Hierarchie durch Einrücken":
        - Level 1: Ordner → Neue Section
        - Level 2+: Ordner → Label (Textfeld) mit Einrückung (level-1)
        - Activities → Einrückung (level-1)
        
        Args:
            item: ContainerItem
            structure: MoodleStructure
            level: Hierarchie-Ebene (1 = direkt unter Root)
            current_section: Aktuelle Section für Activities
        """
        item_type = item.item_type
        indent = max(0, level - 1)  # Ebene 1 = keine Einrückung, Ebene 2 = 1x einrücken, usw.
        
        logger.debug(f"Verarbeite Item hierarchisch: {item.title} ({item_type}) auf Level {level}, Indent {indent}")
        
        # Level 1: Hauptordner werden zu Sections
        if level == 1 and item_type == 'fold':
            section = MoodleSection(
                section_id=self.next_section_id,
                number=self.next_section_id,
                name=item.title,
                summary=f"Aus ILIAS-Folder '{item.title}'",
                visible=not item.offline
            )
            self.next_section_id += 1
            structure.add_section(section)
            
            logger.info(f"Level {level} Folder → Section: {item.title}")
            
            # Verarbeite Kinder in dieser Section (Level 2)
            for child in item.children:
                self._process_item_hierarchical(child, structure, level=2, current_section=section)
            return
        
        # Level 2+: Unterordner werden zu Labels mit Einrückung
        if level >= 2 and item_type == 'fold':
            if not current_section:
                logger.warning(f"Unterordner '{item.title}' ohne Section - erstelle neue Section")
                current_section = MoodleSection(
                    section_id=self.next_section_id,
                    number=self.next_section_id,
                    name=item.title,
                    summary=f"Aus verschachteltem ILIAS-Folder"
                )
                self.next_section_id += 1
                structure.add_section(current_section)
            
            # Erstelle Label für Unterordner
            label_activity = MoodleActivity(
                activity_id=self.next_activity_id,
                module_id=self.next_module_id,
                section_id=current_section.section_id,
                module_name='label',  # Moodle-Label (Textfeld)
                title=f"--- {item.title} ---",
                intro=f"Unterbereich: {item.title}",
                visible=not item.offline,
                indent=indent,
                ilias_type=item_type,
                ilias_id=item.item_id,
                ilias_ref_id=item.ref_id
            )
            self.next_activity_id += 1
            self.next_module_id += 1
            current_section.add_activity(label_activity)
            
            logger.info(f"Level {level} Unterordner → Label mit Indent {indent}: {item.title}")
            
            # Verarbeite Kinder mit erhöhter Einrückung
            for child in item.children:
                self._process_item_hierarchical(child, structure, level=level+1, current_section=current_section)
            return
        
        # ItemGroups: Werden zu Labels + ihre Items als Activities
        if item_type == 'itgr':
            if level == 1:
                # Ebene 1: ItemGroup als Section
                section = MoodleSection(
                    section_id=self.next_section_id,
                    number=self.next_section_id,
                    name=item.title,
                    summary=f"Aus ILIAS-ItemGroup '{item.title}'",
                    visible=not item.offline
                )
                self.next_section_id += 1
                structure.add_section(section)
                current_section = section
                logger.info(f"Level {level} ItemGroup → Section: {item.title}")
            else:
                # Ebene 2+: ItemGroup als Label
                if not current_section:
                    current_section = structure.sections[-1] if structure.sections else structure.sections[0]
                
                label_activity = MoodleActivity(
                    activity_id=self.next_activity_id,
                    module_id=self.next_module_id,
                    section_id=current_section.section_id,
                    module_name='label',
                    title=f"--- {item.title} ---",
                    intro=f"ItemGroup: {item.title}",
                    visible=not item.offline,
                    indent=indent,
                    ilias_type=item_type,
                    ilias_id=item.item_id,
                    ilias_ref_id=item.ref_id
                )
                self.next_activity_id += 1
                self.next_module_id += 1
                current_section.add_activity(label_activity)
                logger.info(f"Level {level} ItemGroup → Label mit Indent {indent}: {item.title}")
            
            # ItemGroup-Items auflösen und als Activities hinzufügen
            if self.itemgroup_resolver and current_section:
                try:
                    # Hole ItemGroup-Daten aus den Components (FIXED: component['data']['id'])
                    itemgroup_data = None
                    for component in self.components:
                        comp_id = component.get('data', {}).get('id')
                        comp_type = component.get('type')
                        if comp_id == item.item_id and comp_type == 'itgr':
                            itemgroup_data = component.get('data')  # FIXED: Übergebe nur die 'data'
                            break
                    
                    if itemgroup_data:
                        # Resolve die ItemGroup
                        resolved_items = self.itemgroup_resolver.resolve_itemgroup(itemgroup_data)
                        logger.info(f"ItemGroup '{item.title}' aufgelöst: {len(resolved_items)} Items gefunden")
                        
                        # Füge jedes aufgelöste Item als Activity hinzu
                        for resolved_item in resolved_items:
                            # Suche das Item in der Container-Struktur
                            container_item = self.container_structure.item_by_item_id.get(resolved_item.item_id)
                            if container_item and container_item.item_type in self.TYPE_MAPPING:
                                activity = self._create_activity(container_item, current_section, indent=indent+1)
                                current_section.add_activity(activity)
                                logger.info(f"  ↳ ItemGroup-Item hinzugefügt: {container_item.title} ({container_item.item_type})")
                            else:
                                # FALLBACK: Erstelle eine Dummy-Activity für nicht-auflösbare Items
                                logger.warning(f"  ↳ ItemGroup-Item nicht gefunden in Container-Struktur: {resolved_item.item_id}, erstelle Fallback-Activity")
                                fallback_activity = MoodleActivity(
                                    activity_id=self.next_activity_id,
                                    module_id=self.next_module_id,
                                    section_id=current_section.section_id,
                                    module_name='url',  # Als Link/URL-Resource
                                    title=resolved_item.title or f"Item {resolved_item.item_id}",
                                    intro=f"Referenziertes Item aus ItemGroup (Typ: {resolved_item.item_type})",
                                    visible=True,
                                    indent=indent+1,
                                    ilias_type=resolved_item.item_type,
                                    ilias_id=resolved_item.item_id
                                )
                                self.next_activity_id += 1
                                self.next_module_id += 1
                                current_section.add_activity(fallback_activity)
                                logger.info(f"  ↳ Fallback-Activity erstellt: {fallback_activity.title}")
                    else:
                        logger.warning(f"ItemGroup-Daten nicht gefunden für: {item.title} (ID: {item.item_id})")
                except Exception as e:
                    logger.error(f"Fehler beim Auflösen von ItemGroup '{item.title}': {e}")
                    structure.add_warning(f"ItemGroup '{item.title}' konnte nicht aufgelöst werden: {e}")
            
            # Verarbeite auch direkte Kinder (falls vorhanden)
            for child in item.children:
                self._process_item_hierarchical(child, structure, level=level+1, current_section=current_section)
            return
        
        # Alle anderen Typen (Tests, Files, etc.) → Activities mit Einrückung
        if item_type in self.TYPE_MAPPING:
            if not current_section:
                logger.warning(f"Activity '{item.title}' ohne Section - erstelle neue Section")
                current_section = MoodleSection(
                    section_id=self.next_section_id,
                    number=self.next_section_id,
                    name="Weitere Inhalte",
                    summary="Weitere Kursinhalte"
                )
                self.next_section_id += 1
                structure.add_section(current_section)
            
            activity = self._create_activity(item, current_section, indent=indent)
            current_section.add_activity(activity)
            logger.info(f"Level {level} Activity mit Indent {indent}: {item.title} ({item_type} → {activity.module_name})")
        
        # MediaObjects ignorieren (sind keine Sections!)
        elif item_type == 'mob':
            logger.debug(f"MediaObject '{item.title}' übersprungen (keine eigenständige Section)")
        
        # Unbekannte Typen
        else:
            structure.add_warning(f"Unbekannter ILIAS-Typ '{item_type}' für Item '{item.title}' auf Level {level}")
    
    def _process_item(self, item, structure: MoodleStructure, 
                     parent_section: Optional[MoodleSection] = None) -> None:
        """
        Verarbeitet ein Container-Item rekursiv.
        
        Args:
            item: ContainerItem
            structure: MoodleStructure zum Hinzufügen
            parent_section: Übergeordnete Section (optional)
        """
        item_type = item.item_type
        
        logger.debug(f"Verarbeite Item: {item.title} ({item_type})")
        
        # Strategie basierend auf Typ
        if item_type == 'fold':
            # Folder → Neue Section
            self._process_folder(item, structure)
        
        elif item_type == 'itgr':
            # ItemGroup → Section mit Activities (wenn Items vorhanden)
            self._process_itemgroup(item, structure)
        
        elif item_type in ['tst', 'file', 'excex', 'frm', 'wiki', 'mcst', 'webr', 'sahs', 'lm', 'htlm']:
            # Test/File/etc → Activity
            if parent_section:
                self._add_activity_to_section(item, parent_section, structure)
            else:
                # Wenn keine Parent-Section, erstelle eine
                section = self._create_section_for_item(item, structure)
                self._add_activity_to_section(item, section, structure)
        
        elif item_type in ['grp', 'crs']:
            # Group/Course (sollte nur Root sein) → Verarbeite Kinder
            structure.add_warning(f"{item_type.upper()} '{item.title}' als Kind gefunden - wird übersprungen")
        
        else:
            # Unbekannter Typ → Warnung
            structure.add_warning(f"Unbekannter ILIAS-Typ '{item_type}' für Item '{item.title}'")
    
    def _process_folder(self, folder_item, structure: MoodleStructure) -> MoodleSection:
        """
        Verarbeitet einen ILIAS-Folder zu einer Moodle-Section.
        
        Args:
            folder_item: ContainerItem vom Typ 'fold'
            structure: MoodleStructure
            
        Returns:
            Erstellte MoodleSection
        """
        section = MoodleSection(
            section_id=self.next_section_id,
            number=self.next_section_id,
            name=folder_item.title,
            summary=f"Aus ILIAS-Folder '{folder_item.title}'",
            visible=not folder_item.offline
        )
        
        self.next_section_id += 1
        structure.add_section(section)
        
        logger.info(f"Folder → Section: {folder_item.title}")
        
        # Verarbeite Kinder als Activities in dieser Section
        for child in folder_item.children:
            if child.item_type in self.TYPE_MAPPING:
                self._add_activity_to_section(child, section, structure)
            else:
                self._process_item(child, structure, section)
        
        return section
    
    def _process_itemgroup(self, itemgroup_item, structure: MoodleStructure) -> Optional[MoodleSection]:
        """
        Verarbeitet eine ILIAS-ItemGroup zu einer Moodle-Section mit Activities.
        
        Args:
            itemgroup_item: ContainerItem vom Typ 'itgr'
            structure: MoodleStructure
            
        Returns:
            Erstellte MoodleSection oder None
        """
        # Erstelle Section für die ItemGroup
        section = MoodleSection(
            section_id=self.next_section_id,
            number=self.next_section_id,
            name=itemgroup_item.title,
            summary=f"Aus ILIAS-ItemGroup '{itemgroup_item.title}'",
            visible=not itemgroup_item.offline
        )
        
        self.next_section_id += 1
        
        logger.info(f"ItemGroup → Section: {itemgroup_item.title}")
        
        # Wenn ItemGroupResolver verfügbar, versuche Items aufzulösen
        if self.itemgroup_resolver:
            # Wir bräuchten hier die ItemGroup-Daten vom Parser
            # Für jetzt: Verarbeite Kinder direkt
            pass
        
        # Verarbeite Kinder als Activities
        for child in itemgroup_item.children:
            if child.item_type in self.TYPE_MAPPING:
                self._add_activity_to_section(child, section, structure)
            else:
                structure.add_warning(
                    f"Item '{child.title}' (Typ: {child.item_type}) in ItemGroup "
                    f"'{itemgroup_item.title}' kann nicht als Activity konvertiert werden"
                )
        
        # Nur Section hinzufügen, wenn sie Activities hat
        if section.activities or itemgroup_item.children:
            structure.add_section(section)
            return section
        else:
            logger.warning(f"ItemGroup '{itemgroup_item.title}' hat keine Activities - wird übersprungen")
            return None
    
    def _create_section_for_item(self, item, structure: MoodleStructure) -> MoodleSection:
        """
        Erstellt eine neue Section für ein einzelnes Item.
        
        Args:
            item: ContainerItem
            structure: MoodleStructure
            
        Returns:
            Erstellte MoodleSection
        """
        section = MoodleSection(
            section_id=self.next_section_id,
            number=self.next_section_id,
            name=item.title,
            summary=f"Section für {item.item_type}: {item.title}"
        )
        
        self.next_section_id += 1
        structure.add_section(section)
        
        return section
    
    def _create_activity(self, item, section: MoodleSection, indent: int = 0) -> MoodleActivity:
        """
        Erstellt eine MoodleActivity aus einem ILIAS-Item (NEU mit indent-Support).
        
        Args:
            item: ContainerItem
            section: MoodleSection
            indent: Einrückungstiefe (0 = keine, 1 = eine Ebene, usw.)
            
        Returns:
            Erstellte MoodleActivity
        """
        # Bestimme Moodle-Modultyp
        moodle_type = self.TYPE_MAPPING.get(item.item_type, 'resource')
        
        # Erstelle Activity
        activity = MoodleActivity(
            activity_id=self.next_activity_id,
            module_id=self.next_module_id,
            section_id=section.section_id,
            module_name=moodle_type,
            title=item.title,
            intro=f"Konvertiert von ILIAS {item.item_type}",
            visible=not item.offline,
            indent=indent,  # NEU: Einrückung
            ilias_type=item.item_type,
            ilias_id=item.item_id,
            ilias_ref_id=item.ref_id
        )
        
        self.next_activity_id += 1
        self.next_module_id += 1
        
        return activity
    
    def _add_activity_to_section(self, item, section: MoodleSection, 
                                 structure: MoodleStructure) -> MoodleActivity:
        """
        Fügt ein Item als Activity zu einer Section hinzu (alte Methode, für Kompatibilität).
        
        Args:
            item: ContainerItem
            section: MoodleSection
            structure: MoodleStructure für Warnungen
            
        Returns:
            Erstellte MoodleActivity
        """
        if item.item_type not in self.TYPE_MAPPING:
            structure.add_warning(
                f"ILIAS-Typ '{item.item_type}' nicht im Mapping - "
                f"verwende 'resource' als Fallback für '{item.title}'"
            )
        
        activity = self._create_activity(item, section, indent=0)
        section.add_activity(activity)
        
        logger.debug(f"Activity erstellt: {item.title} ({item.item_type} → {activity.module_name})")
        
        return activity
    
    def get_mapping_summary(self) -> Dict[str, Any]:
        """
        Erstellt eine Zusammenfassung des Mappings.
        
        Returns:
            Dictionary mit Statistiken
        """
        return {
            'supported_types': list(self.TYPE_MAPPING.keys()),
            'total_type_mappings': len(self.TYPE_MAPPING),
            'next_section_id': self.next_section_id,
            'next_activity_id': self.next_activity_id
        }


def map_ilias_to_moodle(container_structure, itemgroup_resolver=None) -> MoodleStructure:
    """
    Convenience-Funktion für das Mapping.
    
    Args:
        container_structure: ContainerStructure
        itemgroup_resolver: Optional ItemGroupResolver
        
    Returns:
        MoodleStructure
    """
    mapper = StructureMapper(container_structure, itemgroup_resolver)
    return mapper.map_to_moodle()

