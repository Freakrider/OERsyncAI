# ILIAS-zu-Moodle-Konvertierung - Debug-Anleitung

## Bekannte Probleme und Lösungen

### ✅ Problem 1: Kurse mit `crs` (Course) statt `grp` (Group) werden nicht angezeigt

**Symptom**: Bei ILIAS-Exporten, die mit `<Manifest MainEntity="crs"...>` beginnen, wird keine Preview angezeigt.

**Ursache**: Der Analyzer behandelte nur `grp` (Group) als Hauptcontainer, nicht aber `crs` (Course).

**Lösung**: ✅ BEHOBEN - Der Code wurde angepasst, um sowohl `grp` als auch `crs` zu unterstützen.

**Betroffene Dateien**:
- `shared/utils/ilias/analyzer.py` - Container-Erkennung erweitert
- `shared/utils/ilias/structure_mapper.py` - Mapping für `crs` hinzugefügt

### Problem 2: Leerer Kurs bei MBZ-Konvertierung

Der Benutzer meldet, dass:
1. ILIAS-Preview (ohne Konvertierung) funktioniert einwandfrei
2. Bei Konvertierung zu MBZ wird ein leerer Kurs angezeigt
3. Keine Logs werden angezeigt

## Ursachenanalyse

### 1. Die Konvertierung selbst funktioniert!

Das Debug-Skript (`debug_conversion.py`) zeigt, dass die Konvertierung lokal funktioniert:
- **8 Sections** werden erstellt
- **11 Activities** werden generiert  
- MBZ-Datei ist **46.69 KB** groß und valide

### 2. Das eigentliche Problem

Das Problem liegt bei der **Integration zwischen ILIAS-Analyzer-Service und Extractor-Service**:

```python
# Im ILIAS-Analyzer-Service wird nach der Konvertierung:
# 1. Die MBZ-Datei erstellt
# 2. Die MBZ-Datei an den Extractor-Service gesendet
# 3. Auf die Analyse durch den Extractor gewartet
# 4. Die Ergebnisse vom Extractor zurückgegeben
```

Wenn einer dieser Schritte fehlschlägt:
- Der Extractor-Service läuft nicht
- Der Extractor kann nicht erreicht werden
- Der Extractor schlägt bei der Analyse fehl
- Die Kommunikation zwischen den Services schlägt fehl

→ Dann erhält das Frontend leere oder fehlerhafte Daten

### 3. Frontend-Logik

Das Frontend entscheidet basierend auf vorhandenen Daten:

```javascript
// Wenn extracted_data vorhanden → Zeige Moodle-Ansicht
if (courseData.extracted_data) {
  // CourseSummary + MetadataDisplay
}
// Wenn nur analysis_data → Zeige ILIAS-Ansicht
else if (courseData.analysis_data) {
  // IliasAnalysisView mit Logs
}
```

**Problem**: Wenn `extracted_data` existiert aber leer ist, wird die Moodle-Ansicht gezeigt, aber sie ist leer.

## Lösungen

### 1. Verbessertes Logging (✅ Implementiert)

**Backend** (`services/ilias-analyzer/main.py`):
- Mehr Logging bei Konvertierung
- Detailliertes Logging bei Extractor-Kommunikation
- Fehler-Logging mit Details

**Frontend** (`frontend-vite/src/components/IliasAnalysisView.jsx`):
- Logs werden auch bei konvertierten Dateien angezeigt
- Neuer Parameter `showOnlyLogs` für partielle Anzeige
- Logs in Browser-Console UND im UI

### 2. Debug-Skript (✅ Erstellt)

`debug_conversion.py`:
- Testet ILIAS-Analyse lokal
- Testet Konvertierung zu MBZ lokal  
- Zeigt detaillierte Struktur-Informationen
- Hilft bei der Fehlersuche

**Verwendung**:
```bash
python debug_conversion.py
```

### 3. Bessere Fehlerbehandlung (⚠️ Noch zu tun)

**Empfehlungen**:

1. **Fallback ohne Extractor**:
   Wenn Extractor nicht verfügbar, trotzdem MBZ-Datei bereitstellen:
   ```python
   if extractor_available:
       # Analyse durch Extractor
   else:
       # Nur MBZ-Download anbieten, aber ILIAS-Daten anzeigen
   ```

2. **Frontend: Leere Daten erkennen**:
   ```javascript
   // Prüfe ob extracted_data leer ist
   const hasContent = extracted_data?.sections?.length > 0 || 
                      extracted_data?.activities?.length > 0;
   
   if (!hasContent && analysis_data) {
       // Zeige ILIAS-Ansicht mit Warnung
   }
   ```

3. **Timeout-Handling**:
   - Kürzerer Timeout für Extractor-Polling
   - Bessere Fehlerme ldungen bei Timeout

## Services überprüfen

### Docker-Compose

Prüfen ob alle Services laufen:
```bash
docker-compose ps
```

Erwartete Services:
- `extractor` (Port 8001)
- `ilias-analyzer` (Port 8004)
- `gateway` (Port 8000)
- `redis` (Port 6379)

### Lokale Entwicklung

Wenn Services lokal laufen (ohne Docker):

1. **Extractor-Service starten**:
   ```bash
   cd services/extractor
   uvicorn main:app --reload --port 8001
   ```

2. **ILIAS-Analyzer-Service starten**:
   ```bash
   cd services/ilias-analyzer
   # Umgebungsvariable setzen
   export EXTRACTOR_URL=http://localhost:8001
   uvicorn main:app --reload --port 8004
   ```

3. **Frontend starten**:
   ```bash
   cd frontend-vite
   npm run dev
   ```

## Testing

### 1. Service-Verfügbarkeit prüfen

**Extractor**:
```bash
curl http://localhost:8001/health
```

**ILIAS-Analyzer**:
```bash
curl http://localhost:8004/health
```

### 2. Konvertierung testen

Mit Debug-Skript:
```bash
python debug_conversion.py
```

### 3. Integration testen

1. ILIAS-Datei hochladen
2. Haken "Nach der Analyse in Moodle-Format konvertieren" setzen
3. In Browser-Console Logs prüfen
4. Network-Tab prüfen:
   - POST `/analyze` erfolgreich?
   - GET `/analyze/{job_id}` zeigt Fortschritt?

## Nächste Schritte

1. ✅ Logging verbessert
2. ✅ Debug-Skript erstellt
3. ⚠️ **Services überprüfen** (vom Benutzer durchzuführen)
4. ⚠️ **Fallback-Logik implementieren** (optional)
5. ⚠️ **Leere Daten im Frontend abfangen** (empfohlen)

## Kontakt

Bei weiteren Problemen:
- Browser-Console-Logs prüfen
- Docker/Service-Logs prüfen: `docker-compose logs ilias-analyzer`
- Debug-Skript ausführen und Ausgabe teilen

