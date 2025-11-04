"""
ILIAS Export Analyzer Utilities

Shared utilities for analyzing and converting ILIAS exports.
"""

from .analyzer import IliasAnalyzer, Module
from .factory import ParserFactory
from .moodle_converter import MoodleConverter
from .container_parser import (
    ContainerStructureParser,
    ContainerStructure,
    ContainerItem,
    parse_container_structure
)
from .itemgroup_resolver import (
    ItemGroupResolver,
    ResolvedItem,
    resolve_itemgroup
)
from .structure_mapper import (
    StructureMapper,
    MoodleSection,
    MoodleActivity,
    MoodleStructure,
    map_ilias_to_moodle
)
from .compatibility_checker import (
    CompatibilityChecker,
    CompatibilityIssue,
    ConversionReport,
    check_compatibility
)

__version__ = '1.0.0'

__all__ = [
    'IliasAnalyzer',
    'Module',
    'ParserFactory',
    'MoodleConverter',
    'ContainerStructureParser',
    'ContainerStructure',
    'ContainerItem',
    'parse_container_structure',
    'ItemGroupResolver',
    'ResolvedItem',
    'resolve_itemgroup',
    'StructureMapper',
    'MoodleSection',
    'MoodleActivity',
    'MoodleStructure',
    'map_ilias_to_moodle',
    'CompatibilityChecker',
    'CompatibilityIssue',
    'ConversionReport',
    'check_compatibility'
]

