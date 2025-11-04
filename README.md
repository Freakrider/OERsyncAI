# 🎓 OERSync-AI

Ein KI-gestütztes System zur automatischen Extraktion und Anreicherung von Metadaten aus Moodle-Kursen (MBZ-Dateien) mit Dublin Core Standards.

## 🚀 Schnellstart

### 1. Setup
```bash
# Repository klonen
git clone <repository-url>
cd OERsyncAI

# Virtual Environment erstellen und aktivieren
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -e .
```

### 2. 🎉 Projekt starten

Es gibt mehrere Möglichkeiten, das Projekt zu starten:

#### Option A: Demo-Starter (EMPFOHLEN - Ein-Befehl-Lösung)
```bash
# Komplette Demo (Backend + Frontend) mit einem Befehl
python start_demo.py
```

Das startet automatisch:
- ⚡ **Backend** auf http://localhost:8000
- 🌐 **Frontend** auf http://localhost:5173+ (modernes Vite-React-Interface, automatische Port-Erkennung)
- 🌐 **Browser** öffnet automatisch auf korrektem Port

#### Option B: Manuell (für Entwickler)
```bash
# Terminal 1: Backend starten
source venv/bin/activate
cd services/extractor
python main.py

# Terminal 2: Frontend starten
cd frontend-vite
npm install  # nur beim ersten Mal
npm run dev
```

Das startet:
- ⚡ **Backend** auf http://localhost:8000
- 🌐 **Frontend** auf http://localhost:5173 (modernes Vite-React-Interface)

#### Option C: Docker Compose
```bash
# Nur Backend mit Docker
docker-compose -f docker-compose.simple.yml up --build

# Frontend + Backend mit Docker (Development-Setup)
docker-compose -f docker-compose.dev.yml up -d

# Vollständige Services (erfordert weitere Entwicklung)
# docker-compose up --build
```

Das startet (mit `docker-compose.dev.yml`):
- ⚡ **Backend** auf http://localhost:8000 (Docker Container)
- 🌐 **Frontend** auf http://localhost:5173 (Vite Dev Server in Docker)

**Zum Testen:**
1. MBZ-Datei per Drag & Drop hochladen
2. Metadaten werden automatisch extrahiert  
3. Ergebnisse werden schön angezeigt

### 3. Tests ausführen
```bash
# Schnelltest aller Komponenten (empfohlen für ersten Check)
python run_tests.py --components-only

# Alle verfügbaren Tests
python run_tests.py
```

**Erwartete Ausgabe:**
```
🎉 Alle Tests erfolgreich!
🎯 Ergebnis: 1/1 Test-Suites bestanden
```

## 🌐 Web-Interface Features

### ✨ Drag & Drop Upload
- Ziehe MBZ-Dateien direkt in den Upload-Bereich
- Oder verwende den Datei-Auswählen Button
- Unterstützte Formate: `.mbz`, `.tar.gz`, `.zip`

### 📊 Real-time Processing
- Live-Status-Updates während der Verarbeitung
- Progress-Bar mit visueller Rückmeldung
- Automatisches Polling der Job-Status-API

### 📋 Schöne Metadaten-Anzeige
- **Kurs-Übersicht** mit Statistiken (Aktivitäten, Abschnitte, Themen)
- **Dublin Core Metadaten** strukturiert angezeigt
- **Educational Metadaten** mit Tags
- Responsive Design für alle Bildschirmgrößen

## 📁 Projekt-Struktur

```
OERsyncAI/
├── frontend-vite/          # 🌐 Modernes React-Frontend (Vite)
│   ├── src/               # React Komponenten
│   ├── package.json       # NPM Dependencies
│   └── README.md          # Frontend-Docs
├── frontend/               # 🌐 Legacy Web-Interface
│   ├── index.html         # Frontend UI
│   ├── serve.py           # HTTP Server
│   └── README.md          # Frontend-Docs
├── services/
│   ├── extractor/          # 🚀 FastAPI MBZ-Extractor Service
│   ├── gateway/            # 🌐 API Gateway (geplant)
│   └── llm-orchestrator/   # 🤖 LLM-Pipeline (geplant)
├── shared/
│   ├── models/             # 📄 Pydantic Datenmodelle
│   └── utils/              # 🔧 Gemeinsame Utilities
├── tests/                  # 🧪 Test-Suite
│   ├── test_simple.py      # ⚡ Einfache Komponenten-Tests
│   ├── test_extractor_api.py # 🌐 API-Tests
│   └── ...                 # 📋 Weitere Tests
├── docs/                   # 📚 Dokumentation
├── start_demo.py          # 🎉 Ein-Klick Demo-Starter
├── run_tests.py           # 🎯 Zentraler Test-Runner
└── 063_PFB1.mbz          # 📦 Test-MBZ-Datei (378KB)
```

## 🧪 Testing

### 🎯 Zentrale Test-Ausführung (Empfohlen)
```bash
# Alle Tests automatisch ausführen
python run_tests.py

# Nur Komponenten-Tests (schnell, ~5 Sekunden)
python run_tests.py --components-only

# Nur API-Tests (Service muss laufen)
python run_tests.py --api-only
```

### 📋 Einzelne Tests
```bash
# Basis-Komponenten testen
python tests/test_simple.py

# API-Funktionalität testen (Service muss laufen)
python tests/test_extractor_api.py

# Mit pytest (für Entwickler)
pytest tests/ -v
```

### 🔍 Was wird getestet?
- ✅ **Dublin Core Models** - Pydantic-Validierung
- ✅ **MBZ Extractor** - TAR.GZ-Extraktion mit echter MBZ-Datei
- ✅ **XML Parser** - Moodle XML-Strukturen
- ✅ **Metadata Mapper** - Language/Activity/License-Mapping
- ✅ **FastAPI Service** - Alle 6 REST-Endpoints

Siehe [Testing Guide](docs/testing_guide.md) für Details.

## 🏗️ Architektur

### 🔧 Komponenten
1. **MBZ Extractor** - Extrahiert TAR.GZ/ZIP Archive sicher
2. **XML Parser** - Parst Moodle XML-Strukturen (backup, course, sections)
3. **Metadata Mapper** - Mappt zu Dublin Core Standards + Educational Metadata
4. **FastAPI Service** - REST API mit async Job-Processing
5. **LLM Pipeline** - KI-gestützte Metadaten-Anreicherung (🔄 geplant)

### 📊 Datenfluss
```
MBZ-Datei → TAR.GZ-Extraktion → XML-Parsing → Metadata-Mapping → Dublin Core + Educational Metadata
    ↓              ↓                ↓              ↓                        ↓
  378KB         22 Dateien     Backup Info    Activity Types          JSON Response
```

### 🌐 API-Endpoints
```
POST /extract           # MBZ-Datei hochladen → Job-ID
GET  /extract/{job_id}  # Vollständige Ergebnisse abrufen
GET  /extract/{job_id}/status  # Job-Status prüfen
GET  /jobs             # Alle Jobs auflisten  
DELETE /extract/{job_id}  # Job löschen
GET  /health           # Service-Status
```

## 📊 Aktueller Status

**✅ Abgeschlossene Tasks (7/18):**
- ✅ Task 1: Projekt-Setup & Struktur
- ✅ Task 2: Dependencies & Environment
- ✅ Task 3: Dublin Core Models (Pydantic)
- ✅ Task 4: MBZ Extractor Core (TAR.GZ Support)
- ✅ Task 5: XML Parser (Moodle-Strukturen)
- ✅ Task 6: Metadata Mapper (Dublin Core Mapping)
- ✅ Task 7: FastAPI Extractor Service (6 Endpoints)

**🔄 Nächste Tasks:**
- 🔄 Task 8: LangChain Pipeline Grundstruktur
- ⏳ Task 9: LLM-Orchestrator Service
- ⏳ Task 10: API Gateway

**📈 Fortschritt:** 39% (7/18 Tasks)

## 🛠️ Entwicklung

### ⚡ Schnell-Setup für Entwickler
```bash
# Komplettes Setup
git clone <repo> && cd OERsyncAI
python -m venv venv && source venv/bin/activate
pip install -e . && python run_tests.py --components-only

# Frontend Dependencies installieren
cd frontend-vite && npm install && cd ..

# Backend starten
cd services/extractor && python main.py &

# Frontend starten
cd ../frontend-vite && npm run dev
```

### 🔍 Code-Qualität
```bash
# Linting
flake8 .

# Type Checking
mypy shared/ services/

# Tests mit Coverage
pytest tests/ --cov=shared --cov=services
```

### 🌐 API-Entwicklung
```bash
# Service im Development-Modus (auto-reload)
cd services/extractor
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Alternativer Port bei Konflikten
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 🧪 API manuell testen
```bash
# Health Check
curl http://localhost:8000/health

# MBZ-Datei hochladen
curl -X POST "http://localhost:8000/extract" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@063_PFB1.mbz"

# Ergebnis abrufen (job_id aus Upload-Response)
curl http://localhost:8000/extract/{job_id}
```

## 📚 Dokumentation

- 📋 [Testing Guide](docs/testing_guide.md) - Umfassende Test-Anleitung
- 🚀 [Task 7 Summary](docs/task7_fastapi_service_summary.md) - FastAPI Service Details
- 🌐 [API Docs](http://localhost:8000/docs) - Interactive API Documentation
- 📖 [ReDoc](http://localhost:8000/redoc) - Alternative API Documentation

## ❓ Häufige Probleme

### 🔧 Service startet nicht
```bash
# Port-Konflikt prüfen
lsof -i :8000

# Dependencies prüfen
pip list | grep fastapi

# Virtual Environment aktiviert?
which python  # sollte venv/bin/python zeigen
```

### 🧪 Tests schlagen fehl
```bash
# MBZ-Datei vorhanden?
ls -la 063_PFB1.mbz

# Korrekte Python-Pfade?
python -c "import shared.models.dublin_core; print('OK')"

# Von Projekt-Root ausführen
cd /path/to/OERsyncAI && python run_tests.py --components-only
```

### 📦 Abhängigkeiten-Probleme
```bash
# Clean Install
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## 🤝 Beitragen

1. **Fork** das Repository
2. **Feature-Branch** erstellen: `git checkout -b feature/neue-funktion`
3. **Änderungen** implementieren mit Tests
4. **Tests** ausführen: `python run_tests.py`
5. **Pull Request** erstellen

### 📝 Entwickler-Workflow
```bash
# 1. Tests vor Änderungen
python run_tests.py --components-only

# 2. Code implementieren
# ...

# 3. Tests nach Änderungen
python run_tests.py

# 4. Code-Qualität prüfen
flake8 . && mypy shared/ services/
```

## 📄 Lizenz

[Lizenz-Information hier einfügen]

---

🎓 **OERSync-AI** - Transforming Educational Metadata with AI
