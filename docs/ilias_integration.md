# ILIAS Analyzer Integration

## Übersicht

Die ILIAS Analyzer Integration ermöglicht die Analyse von ILIAS-Exporten und deren optionale Konvertierung in Moodle-MBZ-Format. Die Integration besteht aus mehreren Komponenten:

## Architektur

```
oersynch-ai/
├── services/
│   └── ilias-analyzer/          # FastAPI Microservice
│       ├── main.py              # API Endpoints
│       ├── Dockerfile
│       └── requirements.txt
├── shared/
│   └── utils/
│       └── ilias/               # Shared ILIAS utilities
│           ├── analyzer.py      # Hauptanalyse-Klasse
│           ├── factory.py       # Parser Factory
│           ├── moodle_converter.py  # ILIAS → Moodle Konverter
│           └── parsers/         # ILIAS-Komponenten-Parser
│               ├── base.py
│               ├── group.py
│               ├── test.py
│               ├── media_cast.py
│               ├── file.py
│               ├── item_group.py
│               ├── forum.py
│               ├── wiki.py
│               └── exercise.py
└── frontend-vite/
    └── src/
        ├── components/
        │   └── UploadSection.jsx   # Erweitert für ILIAS-Uploads
        └── App.jsx                  # Erweitert für ILIAS-Datenverarbeitung
```

## Komponenten

### 1. ILIAS Analyzer Service (FastAPI)

**Port:** 8004 (Host) → 8002 (Container)

**Endpoints:**

- `POST /analyze` - Analysiert ILIAS-Export
  - Query Parameter: `convert_to_moodle` (optional, boolean)
  - Returns: `AnalysisJobResponse` mit Job-ID

- `GET /analyze/{job_id}/status` - Status einer Analyse
  - Returns: `JobStatus` mit Progress-Information

- `GET /analyze/{job_id}` - Ergebnis einer Analyse
  - Returns: `AnalysisResult` mit vollständigen Analysedaten

- `GET /analyze/{job_id}/download-moodle` - Download der konvertierten MBZ-Datei
  - Nur verfügbar wenn `convert_to_moodle=true` beim Upload gesetzt wurde

- `GET /jobs` - Liste aller Analyse-Jobs

- `DELETE /analyze/{job_id}` - Löscht einen Job

- `GET /health` - Health Check

### 2. Shared ILIAS Utilities

**Location:** `shared/utils/ilias/`

#### IliasAnalyzer
Hauptklasse für die Analyse von ILIAS-Exporten.

```python
from shared.utils.ilias import IliasAnalyzer

analyzer = IliasAnalyzer("/path/to/ilias/export")
success = analyzer.analyze()

if success:
    print(f"Kurs: {analyzer.course_title}")
    print(f"Module: {len(analyzer.modules)}")
```

#### MoodleConverter
Konvertiert analysierte ILIAS-Daten in Moodle-MBZ-Format.

```python
from shared.utils.ilias import MoodleConverter

converter = MoodleConverter(analyzer)
mbz_path = converter.convert()
print(f"MBZ erstellt: {mbz_path}")
```

#### ParserFactory
Factory für ILIAS-Komponenten-Parser.

**Unterstützte Komponententypen:**
- `grp` - Gruppen
- `tst` - Tests
- `mcst` - Media Casts
- `file` - Dateien
- `itgr` - Item-Gruppen
- `frm` - Foren
- `wiki` - Wikis
- `exc` - Übungen

### 3. Frontend Integration

Das Frontend wurde erweitert um:

1. **Toggle für Moodle/ILIAS-Upload:**
   - Button zum Wechseln zwischen MBZ und ILIAS-ZIP
   - Dynamische Dateitypvalidierung
   - Angepasste Upload-Labels

2. **ILIAS-spezifische Optionen:**
   - Checkbox für Moodle-Konvertierung
   - Anzeige des Konvertierungsstatus

3. **Datenverarbeitung:**
   - Transformation von ILIAS-Daten in Moodle-kompatibles Format
   - Separate API-Endpunkte für ILIAS und Moodle
   - Einheitliche Visualisierung beider Formate

## Verwendung

### Docker Compose

Der ILIAS Analyzer Service wird automatisch mit `docker-compose up` gestartet:

```bash
docker-compose up -d
```

Services:
- `extractor` (Port 8001) - MBZ Extractor
- `llm-orchestrator` (Port 8002) - LLM Service
- `ilias-analyzer` (Port 8004) - ILIAS Analyzer
- `gateway` (Port 8000) - API Gateway

### Direkt (Entwicklung)

```bash
# Service starten
cd services/ilias-analyzer
pip install -r requirements.txt
python main.py
```

### Frontend

```bash
cd frontend-vite
npm install
npm run dev
```

**Environment Variables:**
- `VITE_API_URL` - Moodle Extractor API (default: http://localhost:8000)
- `VITE_ILIAS_API_URL` - ILIAS Analyzer API (default: http://localhost:8004)

## API Beispiele

### ILIAS-Export analysieren

```bash
curl -X POST http://localhost:8004/analyze \
  -F "file=@ilias_export.zip"
```

Response:
```json
{
  "job_id": "abc123...",
  "status": "pending",
  "message": "Job created, waiting for processing",
  "file_name": "ilias_export.zip",
  "file_size": 1024000,
  "created_at": "2025-10-31T12:00:00"
}
```

### ILIAS analysieren und zu Moodle konvertieren

```bash
curl -X POST http://localhost:8004/analyze?convert_to_moodle=true \
  -F "file=@ilias_export.zip"
```

### Status abfragen

```bash
curl http://localhost:8004/analyze/{job_id}/status
```

### Ergebnis abrufen

```bash
curl http://localhost:8004/analyze/{job_id}
```

### Moodle MBZ herunterladen

```bash
curl -O http://localhost:8004/analyze/{job_id}/download-moodle
```

## Datenstrukturen

### ILIAS Analysis Result

```json
{
  "job_id": "...",
  "status": "completed",
  "analysis_data": {
    "course_title": "Beispielkurs",
    "installation_id": "12345",
    "installation_url": "https://ilias.example.com",
    "modules_count": 5,
    "modules": [
      {
        "id": "6623",
        "title": "Modul 1",
        "type": "grp",
        "items": [
          {
            "id": "item_1",
            "title": "Test 1",
            "type": "test",
            "metadata": {...}
          }
        ]
      }
    ]
  },
  "moodle_mbz_available": true
}
```

## Entwicklung

### Neue ILIAS-Komponente hinzufügen

1. **Parser erstellen:** `shared/utils/ilias/parsers/new_component.py`

```python
from .base import IliasComponentParser

class NewComponentParser(IliasComponentParser):
    def _parse_xml(self, root):
        # XML-Parsing-Logik
        return {
            'id': '...',
            'title': '...',
            # weitere Daten
        }
```

2. **Parser registrieren:** `shared/utils/ilias/parsers/__init__.py`

```python
from .new_component import NewComponentParser

__all__ = [..., 'NewComponentParser']
```

3. **Factory aktualisieren:** `shared/utils/ilias/factory.py`

```python
_parsers: Dict[str, Type[IliasComponentParser]] = {
    # ...
    'newcomp': NewComponentParser
}
```

### Tests

```bash
# Backend testen
pytest tests/

# Frontend testen
cd frontend-vite
npm test
```

## Troubleshooting

### Service startet nicht

```bash
# Logs überprüfen
docker-compose logs ilias-analyzer

# Service neu starten
docker-compose restart ilias-analyzer
```

### Frontend kann Service nicht erreichen

1. Überprüfe Environment Variables:
   ```bash
   echo $VITE_ILIAS_API_URL
   ```

2. Teste Service direkt:
   ```bash
   curl http://localhost:8004/health
   ```

3. CORS-Probleme? Überprüfe Browser Console.

### Parser-Fehler

1. Aktiviere Debugging-Logs in `main.py`:
   ```python
   LOG_LEVEL=DEBUG python main.py
   ```

2. Überprüfe ILIAS-Export-Struktur:
   ```bash
   unzip -l ilias_export.zip
   ```

## Migration vom alten System

Das alte Flask-basierte System wurde vollständig ersetzt. Keine manuelle Migration nötig.

**Entfernte Komponenten:**
- `ilias_analyser/api.py` (Flask API)
- `ilias_analyser/static/` (HTML/JS Frontend)
- `ilias_analyser/cli.py` (CLI Interface)

**Neue Komponenten:**
- FastAPI Service mit modernem REST API
- React/Vite Frontend Integration
- Docker-basiertes Deployment

## Weitere Dokumentation

- [Environment Setup](environment_setup.md)
- [Frontend Summary](frontend_summary.md)
- [Testing Guide](testing_guide.md)
- [Media Integration](media_integration.md)

