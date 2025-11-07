"""
Factory für ILIAS-Komponenten-Parser.
"""

import os
import logging
from typing import Optional, Dict, Type
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

logger = logging.getLogger(__name__)

class ParserFactory:
    """Factory-Klasse für die Erstellung von Parsern für verschiedene ILIAS-Komponenten."""
    
    # Mapping von Komponententypen zu Parser-Klassen
    _parsers: Dict[str, Type[IliasComponentParser]] = {
        'crs': CourseParser,
        'grp': GroupParser,
        'fold': GroupParser,  # Folder (Ordner) sind strukturell ähnlich zu Groups
        'tst': TestParser,
        'mcst': MediaCastParser,
        'mep': MediaPoolParser,
        'lm': LearningModuleParser,
        'file': FileParser,
        'itgr': ItemGroupParser
    }
    
    @classmethod
    def get_parser(cls, component_type: str, component_path: str) -> Optional[IliasComponentParser]:
        """
        Gibt einen Parser für den angegebenen Komponententyp zurück.
        
        Args:
            component_type: Typ der Komponente (z.B. 'grp', 'tst', 'mcst', 'file', 'itgr')
            component_path: Pfad zur Komponente
            
        Returns:
            Ein Parser für den angegebenen Komponententyp oder None, wenn kein passender Parser gefunden wurde
        """
        # Überprüfen, ob der Komponenten-Pfad existiert
        if not os.path.exists(component_path):
            logger.error(f"Der Komponenten-Pfad existiert nicht: {component_path}")
            return None
        
        parser_class = cls._parsers.get(component_type)
        if parser_class:
            try:
                return parser_class(component_path)
            except Exception as e:
                logger.error(f"Fehler beim Erstellen des Parsers für Komponententyp '{component_type}': {str(e)}")
                return None
        
        logger.warning(f"Kein Parser für Komponententyp '{component_type}' gefunden")
        return None
    
    @classmethod
    def register_parser(cls, component_type: str, parser_class: Type[IliasComponentParser]) -> None:
        """
        Registriert einen neuen Parser für einen Komponententyp.
        
        Args:
            component_type: Typ der Komponente
            parser_class: Parser-Klasse für den Komponententyp
        """
        cls._parsers[component_type] = parser_class
        logger.info(f"Parser für Komponententyp '{component_type}' registriert: {parser_class.__name__}")
    
    @classmethod
    def get_supported_types(cls) -> list:
        """
        Gibt eine Liste der unterstützten Komponententypen zurück.
        
        Returns:
            Liste der unterstützten Typen
        """
        return list(cls._parsers.keys()) 