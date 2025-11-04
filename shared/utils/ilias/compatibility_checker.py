"""
CompatibilityChecker für ILIAS zu Moodle Konvertierung.

Prüft ILIAS-Features auf Moodle-Kompatibilität und generiert Reports.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CompatibilityIssue:
    """Repräsentiert ein Kompatibilitätsproblem."""
    
    severity: str  # 'info', 'warning', 'error'
    ilias_feature: str
    ilias_item: str
    message: str
    moodle_alternative: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            'severity': self.severity,
            'ilias_feature': self.ilias_feature,
            'ilias_item': self.ilias_item,
            'message': self.message,
            'moodle_alternative': self.moodle_alternative
        }


@dataclass
class ConversionReport:
    """Report über die Konvertierung."""
    
    course_title: str
    conversion_date: str
    
    # Statistiken
    total_sections: int = 0
    total_activities: int = 0
    
    # Nach Severity gruppierte Issues
    info_issues: List[CompatibilityIssue] = field(default_factory=list)
    warning_issues: List[CompatibilityIssue] = field(default_factory=list)
    error_issues: List[CompatibilityIssue] = field(default_factory=list)
    
    # Typ-Statistiken
    type_conversions: Dict[str, int] = field(default_factory=dict)
    
    def add_issue(self, issue: CompatibilityIssue) -> None:
        """Fügt ein Issue hinzu."""
        if issue.severity == 'info':
            self.info_issues.append(issue)
        elif issue.severity == 'warning':
            self.warning_issues.append(issue)
        elif issue.severity == 'error':
            self.error_issues.append(issue)
    
    def to_markdown(self) -> str:
        """Generiert Markdown-Report."""
        lines = []
        
        # Header
        lines.append(f"# ILIAS zu Moodle Konvertierungs-Report")
        lines.append("")
        lines.append(f"**Kurs**: {self.course_title}")
        lines.append(f"**Konvertierungsdatum**: {self.conversion_date}")
        lines.append("")
        
        # Statistiken
        lines.append("## 📊 Statistiken")
        lines.append("")
        lines.append(f"- **Sections**: {self.total_sections}")
        lines.append(f"- **Activities**: {self.total_activities}")
        lines.append(f"- **Info-Meldungen**: {len(self.info_issues)}")
        lines.append(f"- **Warnungen**: {len(self.warning_issues)}")
        lines.append(f"- **Fehler**: {len(self.error_issues)}")
        lines.append("")
        
        # Typ-Konvertierungen
        if self.type_conversions:
            lines.append("## 🔄 Typ-Konvertierungen")
            lines.append("")
            for ilias_type, count in sorted(self.type_conversions.items()):
                lines.append(f"- `{ilias_type}`: {count}x")
            lines.append("")
        
        # Errors
        if self.error_issues:
            lines.append("## ❌ Fehler")
            lines.append("")
            lines.append("Diese Features konnten nicht konvertiert werden:")
            lines.append("")
            for issue in self.error_issues:
                lines.append(f"### {issue.ilias_item}")
                lines.append(f"- **Feature**: {issue.ilias_feature}")
                lines.append(f"- **Problem**: {issue.message}")
                if issue.moodle_alternative:
                    lines.append(f"- **Alternative**: {issue.moodle_alternative}")
                lines.append("")
        
        # Warnings
        if self.warning_issues:
            lines.append("## ⚠️ Warnungen")
            lines.append("")
            lines.append("Diese Features wurden mit Einschränkungen konvertiert:")
            lines.append("")
            for issue in self.warning_issues:
                lines.append(f"### {issue.ilias_item}")
                lines.append(f"- **Feature**: {issue.ilias_feature}")
                lines.append(f"- **Hinweis**: {issue.message}")
                if issue.moodle_alternative:
                    lines.append(f"- **Moodle**: {issue.moodle_alternative}")
                lines.append("")
        
        # Info
        if self.info_issues:
            lines.append("## ℹ️ Informationen")
            lines.append("")
            for issue in self.info_issues:
                lines.append(f"- **{issue.ilias_item}**: {issue.message}")
            lines.append("")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            'course_title': self.course_title,
            'conversion_date': self.conversion_date,
            'total_sections': self.total_sections,
            'total_activities': self.total_activities,
            'info_count': len(self.info_issues),
            'warning_count': len(self.warning_issues),
            'error_count': len(self.error_issues),
            'info_issues': [i.to_dict() for i in self.info_issues],
            'warning_issues': [i.to_dict() for i in self.warning_issues],
            'error_issues': [i.to_dict() for i in self.error_issues],
            'type_conversions': self.type_conversions
        }


class CompatibilityChecker:
    """
    Prüft ILIAS-Features auf Moodle-Kompatibilität.
    """
    
    # Features, die nicht in Moodle verfügbar sind
    UNSUPPORTED_FEATURES = {
        'waiting_list': {
            'moodle_alternative': 'Manuelle Verwaltung erforderlich',
            'message': 'ILIAS Wartelisten-Feature wird nicht unterstützt'
        },
        'view_mode': {
            'moodle_alternative': 'Standard Moodle-Ansicht',
            'message': 'ILIAS ViewMode-Einstellungen können nicht übertragen werden'
        },
        'style': {
            'moodle_alternative': 'Moodle Theme-System',
            'message': 'ILIAS Custom Styles müssen im Moodle-Theme neu erstellt werden'
        },
        'timing_changeable': {
            'moodle_alternative': 'Feste Verfügbarkeitszeiten',
            'message': 'Moodle unterstützt keine änderbare Verfügbarkeit durch Teilnehmer'
        },
        'session_limit': {
            'moodle_alternative': None,
            'message': 'Session-Limits werden nicht unterstützt'
        }
    }
    
    # Typ-Mapping-Informationen
    TYPE_COMPATIBILITY = {
        'file': {'supported': True, 'moodle_type': 'resource', 'notes': 'Vollständig unterstützt'},
        'fold': {'supported': True, 'moodle_type': 'folder', 'notes': 'Als Folder oder Section'},
        'tst': {'supported': True, 'moodle_type': 'quiz', 'notes': 'Fragetypen können variieren'},
        'excex': {'supported': True, 'moodle_type': 'assign', 'notes': 'Grundfunktionen unterstützt'},
        'frm': {'supported': True, 'moodle_type': 'forum', 'notes': 'Vollständig unterstützt'},
        'wiki': {'supported': True, 'moodle_type': 'wiki', 'notes': 'Vollständig unterstützt'},
        'mcst': {'supported': True, 'moodle_type': 'resource', 'notes': 'Als Datei-Resource'},
        'webr': {'supported': True, 'moodle_type': 'url', 'notes': 'Vollständig unterstützt'},
        'sahs': {'supported': True, 'moodle_type': 'scorm', 'notes': 'SCORM-kompatibel'},
        'lm': {'supported': True, 'moodle_type': 'book', 'notes': 'Als Buch-Modul'},
        'htlm': {'supported': True, 'moodle_type': 'page', 'notes': 'Als Textseite'},
        'glo': {'supported': True, 'moodle_type': 'glossary', 'notes': 'Vollständig unterstützt'},
        'svy': {'supported': True, 'moodle_type': 'feedback', 'notes': 'Als Feedback-Activity'},
        'poll': {'supported': True, 'moodle_type': 'choice', 'notes': 'Als Abstimmung'},
        'itgr': {'supported': True, 'moodle_type': 'section', 'notes': 'Items werden zu Activities'},
        'grp': {'supported': True, 'moodle_type': 'course', 'notes': 'Wird zum Moodle-Kurs'},
    }
    
    def __init__(self):
        """Initialisiert den Checker."""
        self.issues: List[CompatibilityIssue] = []
    
    def check_item(self, item, item_type_override: Optional[str] = None) -> List[CompatibilityIssue]:
        """
        Prüft ein Container-Item auf Kompatibilität.
        
        Args:
            item: ContainerItem
            item_type_override: Optional überschriebener Typ
            
        Returns:
            Liste von CompatibilityIssues
        """
        issues = []
        item_type = item_type_override or item.item_type
        
        # Prüfe Typ-Kompatibilität
        if item_type not in self.TYPE_COMPATIBILITY:
            issues.append(CompatibilityIssue(
                severity='warning',
                ilias_feature='Objekttyp',
                ilias_item=item.title,
                message=f"Unbekannter ILIAS-Typ '{item_type}' - wird als 'resource' konvertiert",
                moodle_alternative='resource'
            ))
        
        # Prüfe Timing
        if item.timing:
            timing_issues = self._check_timing(item)
            issues.extend(timing_issues)
        
        # Prüfe Offline-Status
        if item.offline:
            issues.append(CompatibilityIssue(
                severity='info',
                ilias_feature='Offline-Modus',
                ilias_item=item.title,
                message='Item ist in ILIAS offline - wird in Moodle als unsichtbar markiert',
                moodle_alternative='visible=false'
            ))
        
        # Prüfe Style (wenn vorhanden)
        if item.style and item.style != '0':
            issues.append(CompatibilityIssue(
                severity='warning',
                ilias_feature='Custom Style',
                ilias_item=item.title,
                message=f"ILIAS Custom Style (ID: {item.style}) kann nicht übertragen werden",
                moodle_alternative='Moodle Theme-System verwenden'
            ))
        
        return issues
    
    def _check_timing(self, item) -> List[CompatibilityIssue]:
        """Prüft Timing-Einstellungen."""
        issues = []
        timing = item.timing
        
        # Changeable-Flag
        if timing.get('changeable'):
            issues.append(CompatibilityIssue(
                severity='warning',
                ilias_feature='Changeable Timing',
                ilias_item=item.title,
                message='ILIAS erlaubt Teilnehmern, Zeitangaben zu ändern - '
                       'in Moodle nur feste Zeiten möglich',
                moodle_alternative='Feste Verfügbarkeitszeiten'
            ))
        
        # Suggestion-Zeiten (optional in ILIAS)
        if timing.get('suggestion_start') or timing.get('suggestion_end'):
            issues.append(CompatibilityIssue(
                severity='info',
                ilias_feature='Suggestion Times',
                ilias_item=item.title,
                message='ILIAS Vorschlags-Zeiträume werden nicht übertragen',
                moodle_alternative='Nutzung von Start/End-Zeiten'
            ))
        
        return issues
    
    def check_structure(self, container_structure) -> List[CompatibilityIssue]:
        """
        Prüft eine komplette Container-Struktur.
        
        Args:
            container_structure: ContainerStructure
            
        Returns:
            Liste von CompatibilityIssues
        """
        all_issues = []
        
        # Prüfe alle Items
        for item in container_structure.item_by_item_id.values():
            issues = self.check_item(item)
            all_issues.extend(issues)
        
        return all_issues
    
    def generate_report(self, moodle_structure, container_structure=None) -> ConversionReport:
        """
        Generiert einen Conversion-Report.
        
        Args:
            moodle_structure: MoodleStructure aus dem Mapper
            container_structure: Optional ContainerStructure für erweiterte Prüfungen
            
        Returns:
            ConversionReport
        """
        report = ConversionReport(
            course_title=moodle_structure.course_title,
            conversion_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_sections=len(moodle_structure.sections),
            total_activities=sum(len(s.activities) for s in moodle_structure.sections)
        )
        
        # Zähle Typ-Konvertierungen
        for section in moodle_structure.sections:
            for activity in section.activities:
                ilias_type = activity.ilias_type or 'unknown'
                report.type_conversions[ilias_type] = report.type_conversions.get(ilias_type, 0) + 1
        
        # Füge Warnungen aus dem Mapping hinzu
        for warning in moodle_structure.warnings:
            report.add_issue(CompatibilityIssue(
                severity='warning',
                ilias_feature='Mapping',
                ilias_item='Verschiedene Items',
                message=warning
            ))
        
        # Erweiterte Prüfungen wenn Container-Struktur verfügbar
        if container_structure:
            issues = self.check_structure(container_structure)
            for issue in issues:
                report.add_issue(issue)
        
        logger.info(f"Report generiert: {len(report.warning_issues)} Warnungen, "
                   f"{len(report.error_issues)} Fehler")
        
        return report


def check_compatibility(container_structure) -> List[CompatibilityIssue]:
    """
    Convenience-Funktion für Kompatibilitätsprüfung.
    
    Args:
        container_structure: ContainerStructure
        
    Returns:
        Liste von CompatibilityIssues
    """
    checker = CompatibilityChecker()
    return checker.check_structure(container_structure)

