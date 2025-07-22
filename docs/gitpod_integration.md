# Gitpod-Integration für Moodle-Instanzen

Diese Dokumentation beschreibt die Integration von OERSync-AI mit Gitpod zum automatischen Starten von Moodle-Entwicklungsinstanzen.

## Überblick

Nach der Extraktion von Metadaten aus einer MBZ-Datei kann OERSync-AI automatisch eine passende Moodle-Instanz in Gitpod starten. Die Instanz wird basierend auf der erkannten Moodle-Version konfiguriert.

## Funktionen

### 🚀 Automatischer Start
- **Ein-Klick-Start** direkt aus dem Frontend
- **Versionserkennung** basierend auf MBZ-Metadaten
- **Branch-Auswahl** passend zur Moodle-Version
- **Workspace-URL** wird automatisch geöffnet

### 🔧 Konfiguration
- **Automatisch**: Mit konfigurierten Gitpod-Credentials
- **Manuell**: Fallback mit direkter URL zum Kopieren

## Setup

### 1. Gitpod-Credentials konfigurieren

Erstelle ein Personal Access Token in Gitpod und setze die Umgebungsvariablen:

```bash
# In .env Datei
GITPOD_TOKEN="gitpod_pat_xxxxxxxxxxxxxx"
GITPOD_ORG_ID="your-org-id"
GITPOD_OWNER_ID="your-user-id"
```

### 2. Dependencies installieren

```bash
pip install requests
```

### 3. Script ausführbar machen

```bash
chmod +x start_gitpod.py
```

## Verwendung

### Frontend-Integration

1. **MBZ-Datei hochladen** und Metadaten extrahieren
2. **"Moodle-Instanz starten"** Button klicken
3. **Gitpod-Workspace** wird automatisch geöffnet

### CLI-Usage

```bash
# Direkte Verwendung des Gitpod-Scripts
python start_gitpod.py "https://gitpod.io/#MOODLE_REPOSITORY=https://github.com/moodlehq/moodle.git,MOODLE_BRANCH=MOODLE_401_STABLE/https://github.com/moodlehq/moodle-docker"
```

## Moodle-Version-Mapping

| Erkannte Version | Gitpod Branch | Repository |
|------------------|---------------|------------|
| 4.x | MOODLE_401_STABLE | moodlehq/moodle |
| 3.x | MOODLE_311_STABLE | moodlehq/moodle |
| Andere | main | moodlehq/moodle |

## API-Endpoint

### POST `/start-moodle-instance/{job_id}`

Startet eine Moodle-Instanz basierend auf den extrahierten Metadaten.

**Parameter:**
- `job_id`: ID des abgeschlossenen Extraktionsjobs

**Response (Erfolg):**
```json
{
  "success": true,
  "workspace_url": "https://gitpod.io/#workspace/xxx",
  "workspace_id": "workspace-id",
  "context_url": "https://gitpod.io/#MOODLE_...",
  "moodle_version": "4.1",
  "branch": "MOODLE_401_STABLE",
  "message": "Moodle-Instanz erfolgreich gestartet!"
}
```

**Response (Manueller Start):**
```json
{
  "context_url": "https://gitpod.io/#MOODLE_...",
  "manual_start": true,
  "message": "Gitpod-Credentials nicht konfiguriert. Bitte manuell starten.",
  "instructions": "Öffne diese URL: ..."
}
```

## Frontend-Features

### Button-Verhalten

1. **Initial**: "Moodle-Instanz starten" mit Play-Icon
2. **Loading**: Spinner-Animation "Starte Moodle-Instanz..."
3. **Erfolg**: "Zu Gitpod wechseln" mit externer Link-Icon
4. **Fallback**: "Manuell in Gitpod öffnen"

### Success-Anzeige

Nach erfolgreichem Start wird zusätzliche Information angezeigt:
- ✅ Workspace gestartet
- Moodle-Version und Branch
- Workspace-ID
- Hinweis zur Bereitstellungszeit

## Troubleshooting

### Häufige Probleme

**"Gitpod-Credentials nicht konfiguriert"**
- Setze `GITPOD_TOKEN`, `GITPOD_ORG_ID`, `GITPOD_OWNER_ID`
- Prüfe Gültigkeit des Access Tokens

**"Timeout beim Starten"**
- Gitpod-API möglicherweise überlastet
- Versuche manuellen Start mit der angezeigten URL

**"Automatischer Start fehlgeschlagen"**
- Prüfe Internetverbindung
- Validiere Gitpod-Credentials
- Nutze Fallback-URL

### Logs prüfen

```bash
# Backend-Logs anzeigen
tail -f logs/extractor.log

# Gitpod-Script direkt testen
python start_gitpod.py --help
```

## Erweiterte Konfiguration

### Custom Repositories

Für spezielle Moodle-Setups kann die Context-URL angepasst werden:

```python
# Beispiel für eigenes Repository
base_url = "https://gitpod.io/#MOODLE_REPOSITORY=https://github.com/your-org/moodle.git"
```

### Workspace-Klassen

```bash
# Größere Instanz verwenden
python start_gitpod.py --workspace-class="g1-large" "context-url"
```

### Editor-Auswahl

```bash
# Mit IntelliJ statt VS Code
python start_gitpod.py --editor-name="intellij" "context-url"
```

## Sicherheit

- **Access Tokens** niemals in Git committen
- **Environment-Variablen** für alle Credentials verwenden
- **Token-Scope** minimal halten (nur Workspace-Erstellung)
- **Regelmäßige Rotation** der Access Tokens

## Integration mit CI/CD

Die Gitpod-Integration kann auch in automatisierten Workflows verwendet werden:

```yaml
# GitHub Actions Beispiel
- name: Start Moodle Test Instance
  run: |
    python start_gitpod.py "$CONTEXT_URL"
  env:
    GITPOD_TOKEN: ${{ secrets.GITPOD_TOKEN }}
    GITPOD_ORG_ID: ${{ secrets.GITPOD_ORG_ID }}
    GITPOD_OWNER_ID: ${{ secrets.GITPOD_OWNER_ID }}
``` 