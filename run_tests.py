#!/usr/bin/env python3
"""
🧪 OERSync-AI Test Runner

Zentraler Test-Runner für alle OERSync-AI Tests:
- Komponenten-Tests (schnell)
- API-Tests (benötigt laufenden Service)
- Integration-Tests
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import argparse

def run_component_tests():
    """Führe Komponenten-Tests aus"""
    print("🔧 KOMPONENTEN-TESTS")
    print("="*50)

    try:
        result = subprocess.run([
            sys.executable, "tests/test_simple.py"
        ], capture_output=True, text=True, timeout=60)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ Komponenten-Tests Timeout")
        return False
    except Exception as e:
        print(f"❌ Komponenten-Tests Fehler: {e}")
        return False

def run_api_tests():
    """Führe API-Tests aus (Service muss laufen)"""
    print("\\n🌐 API-TESTS")
    print("="*50)

    try:
        result = subprocess.run([
            sys.executable, "tests/test_extractor_api.py"
        ], capture_output=True, text=True, timeout=120)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ API-Tests Timeout")
        return False
    except Exception as e:
        print(f"❌ API-Tests Fehler: {e}")
        return False

def check_service_health():
    """Prüfe ob FastAPI Service läuft"""
    try:
        import requests
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        API_BASE_URL = os.environ.get("VITE_API_URL", "http://localhost:8000")
        response = requests.get(API_BASE_URL + "/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def run_pytest_tests():
    """Führe pytest Tests aus"""
    print("\\n🧪 PYTEST-TESTS")
    print("="*50)

    try:
        # Alle Tests außer slow
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/",
            "-v", "--tb=short", "-m", "not slow"
        ], timeout=120)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ Pytest Tests Timeout")
        return False
    except Exception as e:
        print(f"❌ Pytest Tests Fehler: {e}")
        return False

def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(description='OERSync-AI Test Runner')
    parser.add_argument('--components-only', action='store_true',
                       help='Nur Komponenten-Tests ausführen')
    parser.add_argument('--api-only', action='store_true',
                       help='Nur API-Tests ausführen (Service muss laufen)')
    parser.add_argument('--pytest', action='store_true',
                       help='Nur pytest Tests ausführen')
    parser.add_argument('--all', action='store_true',
                       help='Alle Tests ausführen (Standard)')

    args = parser.parse_args()

    print("🧪 OERSYNC-AI TEST RUNNER")
    print("="*60)
    print(f"⏰ Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Entscheide welche Tests ausgeführt werden
    if args.components_only:
        results.append(("Komponenten", run_component_tests()))
    elif args.api_only:
        if check_service_health():
            results.append(("API", run_api_tests()))
        else:
            print("❌ FastAPI Service nicht erreichbar auf http://localhost:8000")
            print("💡 Starte Service mit: cd services/extractor && python main.py")
            return False
    elif args.pytest:
        results.append(("Pytest", run_pytest_tests()))
    else:
        # Standard: Alle Tests
        results.append(("Komponenten", run_component_tests()))

        if check_service_health():
            results.append(("API", run_api_tests()))
        else:
            print("\\n⚠️  FastAPI Service nicht erreichbar - API-Tests übersprungen")
            print("💡 Starte Service mit: cd services/extractor && python main.py")

    # Zusammenfassung
    print("\\n📊 TEST-ZUSAMMENFASSUNG")
    print("="*60)

    passed = 0
    for name, result in results:
        status = "✅ BESTANDEN" if result else "❌ FEHLGESCHLAGEN"
        print(f"{name:15} | {status}")
        if result:
            passed += 1

    print(f"\\n🎯 Ergebnis: {passed}/{len(results)} Test-Suites bestanden")

    if passed == len(results):
        print("🎉 Alle Tests erfolgreich!")
        return True
    else:
        print("⚠️  Einige Tests haben Probleme.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)