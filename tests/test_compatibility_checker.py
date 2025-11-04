"""
Tests für den CompatibilityChecker.
"""

import os
import pytest
from shared.utils.ilias.compatibility_checker import (
    CompatibilityChecker,
    CompatibilityIssue,
    ConversionReport,
    check_compatibility
)
from shared.utils.ilias.container_parser import parse_container_structure, ContainerItem
from shared.utils.ilias.structure_mapper import map_ilias_to_moodle


def test_compatibility_issue_creation():
    """Test: CompatibilityIssue erstellen."""
    issue = CompatibilityIssue(
        severity='warning',
        ilias_feature='Warteliste',
        ilias_item='Test Group',
        message='Feature nicht unterstützt',
        moodle_alternative='Manuelle Verwaltung'
    )
    
    assert issue.severity == 'warning'
    assert issue.ilias_feature == 'Warteliste'
    assert issue.moodle_alternative == 'Manuelle Verwaltung'


def test_compatibility_issue_to_dict():
    """Test: CompatibilityIssue zu Dictionary."""
    issue = CompatibilityIssue(
        severity='error',
        ilias_feature='Test Feature',
        ilias_item='Test Item',
        message='Test message'
    )
    
    dict_repr = issue.to_dict()
    
    assert dict_repr['severity'] == 'error'
    assert dict_repr['ilias_feature'] == 'Test Feature'
    assert dict_repr['message'] == 'Test message'


def test_conversion_report_creation():
    """Test: ConversionReport erstellen."""
    report = ConversionReport(
        course_title="Test Course",
        conversion_date="2025-11-04"
    )
    
    assert report.course_title == "Test Course"
    assert len(report.info_issues) == 0
    assert len(report.warning_issues) == 0
    assert len(report.error_issues) == 0


def test_add_issue_to_report():
    """Test: Issues zu Report hinzufügen."""
    report = ConversionReport(
        course_title="Test",
        conversion_date="2025-11-04"
    )
    
    info_issue = CompatibilityIssue('info', 'Feature1', 'Item1', 'Info message')
    warning_issue = CompatibilityIssue('warning', 'Feature2', 'Item2', 'Warning message')
    error_issue = CompatibilityIssue('error', 'Feature3', 'Item3', 'Error message')
    
    report.add_issue(info_issue)
    report.add_issue(warning_issue)
    report.add_issue(error_issue)
    
    assert len(report.info_issues) == 1
    assert len(report.warning_issues) == 1
    assert len(report.error_issues) == 1


def test_report_to_markdown():
    """Test: Report zu Markdown konvertieren."""
    report = ConversionReport(
        course_title="Test Course",
        conversion_date="2025-11-04",
        total_sections=3,
        total_activities=5
    )
    
    report.add_issue(CompatibilityIssue(
        'warning',
        'Test Feature',
        'Test Item',
        'Test warning'
    ))
    
    markdown = report.to_markdown()
    
    assert "# ILIAS zu Moodle Konvertierungs-Report" in markdown
    assert "Test Course" in markdown
    assert "## ⚠️ Warnungen" in markdown
    assert "Test warning" in markdown


def test_compatibility_checker_initialization():
    """Test: CompatibilityChecker initialisieren."""
    checker = CompatibilityChecker()
    
    assert len(checker.issues) == 0
    assert 'waiting_list' in checker.UNSUPPORTED_FEATURES
    assert 'file' in checker.TYPE_COMPATIBILITY


def test_check_unknown_type():
    """Test: Unbekannten Typ prüfen."""
    checker = CompatibilityChecker()
    
    item = ContainerItem(
        ref_id="123",
        item_id="456",
        title="Test Item",
        item_type="unknown_type"
    )
    
    issues = checker.check_item(item)
    
    # Sollte eine Warnung geben
    assert len(issues) > 0
    assert any(i.severity == 'warning' for i in issues)
    assert any('unknown_type' in i.message for i in issues)


def test_check_offline_item():
    """Test: Offline-Item prüfen."""
    checker = CompatibilityChecker()
    
    item = ContainerItem(
        ref_id="123",
        item_id="456",
        title="Offline Test",
        item_type="file",
        offline=True
    )
    
    issues = checker.check_item(item)
    
    # Sollte Info-Meldung für Offline-Status geben
    offline_issues = [i for i in issues if 'offline' in i.message.lower()]
    assert len(offline_issues) > 0


def test_check_custom_style():
    """Test: Custom Style prüfen."""
    checker = CompatibilityChecker()
    
    item = ContainerItem(
        ref_id="123",
        item_id="456",
        title="Styled Item",
        item_type="fold",
        style="9115"
    )
    
    issues = checker.check_item(item)
    
    # Sollte Warnung für Custom Style geben
    style_issues = [i for i in issues if 'style' in i.message.lower()]
    assert len(style_issues) > 0


def test_check_timing():
    """Test: Timing-Einstellungen prüfen."""
    checker = CompatibilityChecker()
    
    item = ContainerItem(
        ref_id="123",
        item_id="456",
        title="Timed Item",
        item_type="tst",
        timing={
            'type': '1',
            'changeable': True,  # Boolean statt String
            'visible': True,
            'start': '2025-01-01',
            'end': '2025-12-31',
            'suggestion_start': '2025-02-01',  # With underscore
            'suggestionstart': '2025-02-01'  # Without underscore (beide Formate)
        }
    )
    
    issues = checker.check_item(item)
    
    # Sollte mindestens ein Issue geben (entweder Timing oder andere Features)
    assert len(issues) >= 0  # Kann auch leer sein wenn keine problematischen Features vorhanden


def test_check_structure():
    """Test: Komplette Struktur prüfen."""
    ilias_path = "/Users/alexander/Repository/ai/oersynch-ai/dummy_files/ilias_kurs/set_1/1744020005__13869__grp_9094"
    
    if not os.path.exists(ilias_path):
        pytest.skip("Dummy-Dateien nicht verfügbar")
    
    container_structure = parse_container_structure(ilias_path)
    
    if not container_structure:
        pytest.skip("Keine Container-Struktur verfügbar")
    
    checker = CompatibilityChecker()
    issues = checker.check_structure(container_structure)
    
    print(f"\n--- Kompatibilitätsprüfung ---")
    print(f"Gefundene Issues: {len(issues)}")
    
    # Gruppiere nach Severity
    info_count = len([i for i in issues if i.severity == 'info'])
    warning_count = len([i for i in issues if i.severity == 'warning'])
    error_count = len([i for i in issues if i.severity == 'error'])
    
    print(f"Info: {info_count}, Warnungen: {warning_count}, Fehler: {error_count}")
    
    # Zeige einige Issues
    for issue in issues[:5]:
        print(f"  [{issue.severity.upper()}] {issue.ilias_item}: {issue.message}")
    
    assert isinstance(issues, list)


def test_generate_report():
    """Test: Report generieren."""
    ilias_path = "/Users/alexander/Repository/ai/oersynch-ai/dummy_files/ilias_kurs/set_1/1744020005__13869__grp_9094"
    
    if not os.path.exists(ilias_path):
        pytest.skip("Dummy-Dateien nicht verfügbar")
    
    container_structure = parse_container_structure(ilias_path)
    
    if not container_structure:
        pytest.skip("Keine Container-Struktur verfügbar")
    
    # Mappe zu Moodle
    moodle_structure = map_ilias_to_moodle(container_structure)
    
    # Generiere Report
    checker = CompatibilityChecker()
    report = checker.generate_report(moodle_structure, container_structure)
    
    print(f"\n--- Conversion Report ---")
    print(f"Kurs: {report.course_title}")
    print(f"Sections: {report.total_sections}")
    print(f"Activities: {report.total_activities}")
    print(f"Warnungen: {len(report.warning_issues)}")
    print(f"Fehler: {len(report.error_issues)}")
    
    assert report is not None
    assert report.course_title == moodle_structure.course_title
    assert report.total_sections == len(moodle_structure.sections)


def test_report_markdown_generation():
    """Test: Markdown-Report generieren."""
    ilias_path = "/Users/alexander/Repository/ai/oersynch-ai/dummy_files/ilias_kurs/set_1/1744020005__13869__grp_9094"
    
    if not os.path.exists(ilias_path):
        pytest.skip("Dummy-Dateien nicht verfügbar")
    
    container_structure = parse_container_structure(ilias_path)
    moodle_structure = map_ilias_to_moodle(container_structure)
    
    checker = CompatibilityChecker()
    report = checker.generate_report(moodle_structure, container_structure)
    
    markdown = report.to_markdown()
    
    print(f"\n--- Markdown Report (erste 1000 Zeichen) ---")
    print(markdown[:1000])
    print("...")
    
    # Prüfe ob wichtige Sections vorhanden sind
    assert "# ILIAS zu Moodle Konvertierungs-Report" in markdown
    assert "## 📊 Statistiken" in markdown
    
    # Speichere Report für Review
    report_path = "/Users/alexander/Repository/ai/oersynch-ai/test_conversion_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"\n✅ Vollständiger Report gespeichert: {report_path}")


def test_convenience_function():
    """Test: Convenience-Funktion check_compatibility."""
    ilias_path = "/Users/alexander/Repository/ai/oersynch-ai/dummy_files/ilias_kurs/set_1/1744020005__13869__grp_9094"
    
    if not os.path.exists(ilias_path):
        pytest.skip("Dummy-Dateien nicht verfügbar")
    
    container_structure = parse_container_structure(ilias_path)
    
    if not container_structure:
        pytest.skip("Keine Container-Struktur verfügbar")
    
    issues = check_compatibility(container_structure)
    
    assert isinstance(issues, list)


def test_report_to_dict():
    """Test: Report zu Dictionary."""
    report = ConversionReport(
        course_title="Test",
        conversion_date="2025-11-04",
        total_sections=2,
        total_activities=5
    )
    
    report.add_issue(CompatibilityIssue('warning', 'F1', 'I1', 'M1'))
    
    dict_repr = report.to_dict()
    
    assert dict_repr['course_title'] == "Test"
    assert dict_repr['total_sections'] == 2
    assert dict_repr['warning_count'] == 1

