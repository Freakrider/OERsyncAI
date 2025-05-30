"""
pytest Konfiguration für OERSync-AI Test Suite
"""

import sys
from pathlib import Path

# Add project root to Python path für pytest
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Pytest-Optionen
pytest_plugins = []

def pytest_configure(config):
    """Konfiguration für pytest"""
    config.addinivalue_line(
        "markers", 
        "slow: Markiere Tests als langsam (z.B. API-Tests)"
    )
    config.addinivalue_line(
        "markers",
        "integration: Markiere Tests als Integration-Tests"
    )

def pytest_collection_modifyitems(config, items):
    """Modifiziere gesammelte Test-Items"""
    # Füge automatisch 'slow' Marker zu API-Tests hinzu
    for item in items:
        if "api" in item.name.lower() or "extractor_api" in str(item.fspath):
            item.add_marker("slow") 