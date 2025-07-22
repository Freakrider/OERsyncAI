# Environment Setup für OERSync-AI

## Übersicht

OERSync-AI nutzt Environment-Variablen für die Konfiguration, insbesondere für die Gitpod-Integration zum automatischen Starten von Moodle-Instanzen.

## Setup-Schritte

### 1. .env Datei erstellen

```bash
cp .env.example .env
```

### 2. Gitpod-Credentials konfigurieren

Du benötigst drei Werte von Gitpod:

#### Gitpod Personal Access Token
1. Gehe zu https://gitpod.io/user/tokens
2. Erstelle einen neuen Token mit den Bereichen:
   - `read:user`
   - `read:workspace`
   - `write:workspace`
3. Kopiere den Token und setze ihn in der .env:
   ```
   GITPOD_TOKEN=gitpod_pat_1.xxxxxxxxxxxxx
   ```

#### Gitpod Organization ID
1. Gehe zu https://gitpod.io/settings/organizations
2. Wähle deine Organisation aus
3. Die Organization ID findest du in der URL oder in den Settings
4. Setze sie in der .env:
   ```
   GITPOD_ORG_ID=your-organization-id
   ```

#### Gitpod Owner ID
1. Gehe zu https://gitpod.io/settings/account
2. Deine User ID findest du in den Account-Settings
3. Oder nutze die Gitpod API: `curl -H "Authorization: Bearer <token>" https://api.gitpod.io/gitpod.v1.UserService/GetAuthenticatedUser`
4. Setze sie in der .env:
   ```
   GITPOD_OWNER_ID=your-user-id
   ```

### 3. Vollständige .env Beispiel

```bash
# Gitpod Integration
GITPOD_TOKEN=gitpod_pat_1.ABCDEFGHIJKLMNOPQRSTUVWXYZ
GITPOD_ORG_ID=12345678-abcd-1234-efgh-123456789abc
GITPOD_OWNER_ID=87654321-dcba-4321-hgfe-cba987654321

# Backend Configuration
API_BASE_URL=http://localhost:8000
FRONTEND_PORT=3000

# Development Settings
DEBUG=true
LOG_LEVEL=info
```

## Verwendung

Nach dem Setup kannst du:

1. **Frontend starten**: `python start_demo.py`
2. **MBZ-Datei hochladen** über das Web-Interface
3. **Moodle-Instanz starten** mit einem Klick auf "Moodle-Instanz starten"

Das System erkennt automatisch die Moodle-Version aus der MBZ-Datei und startet die passende Gitpod-Instanz mit dem richtigen Branch.

## Troubleshooting

### Gitpod-Instanz startet nicht automatisch
- Prüfe, ob alle drei Environment-Variablen gesetzt sind
- Überprüfe die Gültigkeit deines Personal Access Tokens
- Stelle sicher, dass dein Token die richtigen Bereiche hat

### Fallback-Modus
Wenn die automatische Erstellung fehlschlägt, zeigt das Frontend eine manuelle URL an, die du direkt öffnen kannst.

## Security

- Die `.env` Datei ist in `.gitignore` enthalten
- Teile niemals deine Gitpod-Tokens öffentlich
- Rotiere deine Tokens regelmäßig 