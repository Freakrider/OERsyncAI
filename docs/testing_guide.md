# 🧪 OERSync-AI Test-Anleitung

Diese Anleitung zeigt dir verschiedene Möglichkeiten, das OERSync-AI System zu testen.

## 📋 Voraussetzungen

1. **Python Virtual Environment aktivieren:**
   ```bash
   source venv/bin/activate
   ```

2. **MBZ-Test-Datei:**
   - Stelle sicher, dass `063_PFB1.mbz` im Projekt-Root liegt
   - Größe: ~378KB, Moodle 2017 Backup

## 🚀 Test-Optionen

### 1. 🎯 Zentraler Test-Runner (Empfohlen)

**Alle verfügbaren Tests ausführen:**
```bash
python run_tests.py
```

**Nur Komponenten-Tests (schnell):**
```bash
python run_tests.py --components-only
```

**Nur API-Tests (Service muss laufen):**
```bash
python run_tests.py --api-only
```

### 2. 🔧 Einzelne Komponenten testen

**Schnelltest aller Komponenten:**
```bash
python tests/test_simple.py
```

**Erweiterte Komponenten-Tests:**
```bash
python tests/test_components.py
```

**Erwartete Ausgabe:**
```
🧪 OERSYNC-AI EINFACHE KOMPONENTEN-TESTS
============================================================
✅ Dublin Core Models   | BESTANDEN
✅ Metadata Mapper      | BESTANDEN  
✅ MBZ Extractor        | BESTANDEN
🎯 Ergebnis: 3/3 Tests bestanden
🎉 Alle Komponenten funktionieren korrekt!
```

### 3. 🌐 FastAPI Service testen

**Service starten:**
```bash
cd services/extractor
python main.py
```

**Service läuft auf:** `http://localhost:8000`

**Automatisierter API-Test:**
```bash
# In einem neuen Terminal (mit venv aktiviert):
python tests/test_extractor_api.py
```

**API-Dokumentation öffnen:**
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 4. 🧪 Pytest-Tests

**Alle Tests mit pytest:**
```bash
pytest tests/ -v
```

**Nur schnelle Tests:**
```bash
pytest tests/ -v -m "not slow"
```

**Nur API-Tests (Service muss laufen):**
```bash
pytest tests/test_extractor_api.py -v
```

### 5. 🔍 Manuelle API-Tests

**Health Check:**
```bash
curl http://localhost:8000/health
```

**MBZ-Datei hochladen:**
```bash
curl -X POST "http://localhost:8000/extract" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@063_PFB1.mbz"
```

**Job-Status prüfen:**
```bash
curl http://localhost:8000/extract/{JOB_ID}/status
```

**Ergebnisse abrufen:**
```bash
curl http://localhost:8000/extract/{JOB_ID}
```

### 6. 📊 Vollständige Pipeline testen

**Komplette Extraktion mit Metadata-Mapping:**
```bash
python -c "
import sys; sys.path.insert(0, '.')
from shared.utils.mbz_extractor import MBZExtractor
from shared.utils.metadata_mapper import create_complete_extracted_data
import json

# MBZ extrahieren
extractor = MBZExtractor()
result = extractor.extract_mbz('063_PFB1.mbz')

# XML parsen
from shared.utils.xml_parser import parse_moodle_backup_xml, parse_course_xml
backup_info = parse_moodle_backup_xml(result.moodle_backup_xml)
course_info = parse_course_xml(result.course_xml) if result.course_xml else None

# Metadaten mappen
extracted_data = create_complete_extracted_data(backup_info, course_info, [], [])

# Ausgabe
print('✅ Pipeline erfolgreich!')
print(f'Kurs: {extracted_data.course_name}')
print(f'Dublin Core Titel: {extracted_data.dublin_core.title}')
print(f'Educational Typ: {extracted_data.educational.learning_resource_type}')

# Cleanup
extractor.cleanup()
"
```

## 📁 Test-Struktur

Die Tests sind jetzt sauber im `tests/` Ordner organisiert:

```
tests/
├── __init__.py                 # Test-Package
├── conftest.py                # pytest Konfiguration
├── test_simple.py             # Einfache Komponenten-Tests
├── test_components.py         # Erweiterte Komponenten-Tests
├── test_extractor_api.py      # FastAPI Service Tests
├── test_metadata_mapper.py    # Metadata Mapping Tests
├── test_real_mbz.py          # Tests mit echter MBZ-Datei
└── test_xml_parser.py        # XML Parser Tests
```

**Projekt-Root:**
```
run_tests.py                   # Zentraler Test-Runner
```

## 📈 Test-Ergebnisse verstehen

### ✅ Erfolgreiche Tests zeigen:

**Dublin Core Models:**
- ✅ Pydantic-Modelle funktionieren
- ✅ JSON-Serialisierung works
- ✅ Enum-Validierung aktiv

**Metadata Mapper:**
- ✅ Language Mapping (de→de, en_us→en)
- ✅ Activity Mapping (quiz→quiz, page→resource)
- ✅ License Detection (CC BY, Copyright, etc.)

**MBZ Extractor:**
- ✅ TAR.GZ Format-Erkennung
- ✅ Sichere Extraktion (22 Aktivitäten, 11 Abschnitte)
- ✅ XML-Dateien gefunden (backup, course)
- ✅ Automatisches Cleanup

**FastAPI Service:**
- ✅ Asynchrone Job-Verarbeitung
- ✅ Vollständige Metadaten-Extraktion in ~0.07s
- ✅ Strukturierte JSON-Antworten
- ✅ Fehlerbehandlung für ungültige Dateien

### 📊 Erwartete Extraktions-Metriken:

```json
{
  "course_id": 3,
  "course_name": "Python for Beginners 1 - Python Language Basics",
  "course_short_name": "PFB1",
  "moodle_version": "2017051500.1",
  "processing_time_seconds": 0.07,
  "sections_count": 11,
  "activities_count": 22,
  "dublin_core": {
    "title": "Python for Beginners 1 - Python Language Basics",
    "subject": ["Basics", "Language", "Python", "PFB1", "Beginners"],
    "type": "InteractiveResource",
    "language": "de"
  },
  "educational": {
    "learning_resource_type": "course",
    "difficulty": "intermediate",
    "context": "other"
  }
}
```

## 🚨 Fehlerdiagnose

### Häufige Probleme:

**1. MBZ-Datei nicht gefunden:**
```
❌ MBZ-Datei 063_PFB1.mbz nicht gefunden
```
**Lösung:** Stelle sicher, dass die MBZ-Datei im Projekt-Root liegt.

**2. Service nicht erreichbar:**
```
❌ HTTPConnectionPool(host='localhost', port=8000): Connection refused
```
**Lösung:** Starte den FastAPI Service: `cd services/extractor && python main.py`

**3. Import-Fehler:**
```
❌ ModuleNotFoundError: No module named 'shared'
```
**Lösung:** Aktiviere die virtuelle Umgebung: `source venv/bin/activate`

**4. Archiv-Format nicht unterstützt:**
```
❌ Unbekanntes Archiv-Format
```
**Lösung:** Nur .mbz Dateien sind unterstützt (ZIP oder TAR.GZ)

### Debug-Informationen:

**Strukturiertes Logging aktivieren:**
```bash
export STRUCTLOG_LEVEL=DEBUG
python tests/test_simple.py
```

**Detaillierte Fehler-Ausgabe:**
```python
import traceback
try:
    # Test-Code hier
except Exception as e:
    traceback.print_exc()
```

## 🔄 Kontinuierliches Testen

**Alle Tests automatisch ausführen:**
```bash
# Komponenten-Tests
python tests/test_simple.py && echo "✅ Komponenten OK"

# API-Tests (Service muss laufen)
python tests/test_extractor_api.py && echo "✅ API OK"
```

**Test-Pipeline für CI/CD:**
```bash
#!/bin/bash
set -e

echo "🔄 Starte OERSync-AI Test-Pipeline..."

# 1. Komponenten testen
echo "📦 Teste Komponenten..."
python tests/test_simple.py

# 2. Service starten
echo "🚀 Starte API Service..."
cd services/extractor
python main.py &
SERVICE_PID=$!
cd ../..

# 3. Warte auf Service
sleep 5

# 4. API testen
echo "🌐 Teste API..."
python test_extractor_api.py

# 5. Service stoppen
echo "🛑 Stoppe Service..."
kill $SERVICE_PID

echo "✅ Alle Tests erfolgreich!"
```

## 📚 Weiterführende Tests

**Mit eigenen MBZ-Dateien testen:**
1. Ersetze `063_PFB1.mbz` durch deine MBZ-Datei
2. Führe Tests aus: `python test_simple.py`
3. Prüfe Extraktion: `python test_extractor_api.py`

**Performance-Tests:**
```python
import time
start = time.time()
# Test-Code hier
duration = time.time() - start
print(f"⏱️  Test dauerte: {duration:.2f}s")
```

**Stress-Tests:**
```bash
# Mehrere gleichzeitige Uploads
for i in {1..5}; do
  curl -X POST "http://localhost:8000/extract" \
       -F "file=@063_PFB1.mbz" &
done
wait
```

---

🎯 **Ziel:** Alle Komponenten sollten erfolgreich getestet werden, bevor du mit der Entwicklung fortfährst oder das System produktiv einsetzt. 