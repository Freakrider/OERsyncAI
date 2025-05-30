# 🌐 OERSync-AI Frontend

Einfaches Web-Frontend für das OERSync-AI System zur MBZ-Metadaten-Extraktion.

## 🚀 Schnellstart

### 1. Backend starten
```bash
# Terminal 1: Backend starten
cd services/extractor
python main.py
```

### 2. Frontend starten
```bash
# Terminal 2: Frontend starten
cd frontend
python serve.py
```

Das Frontend öffnet sich automatisch im Browser: **http://localhost:3000**

## 🎯 Features

### ✨ Drag & Drop Upload
- Ziehe MBZ-Dateien direkt in den Upload-Bereich
- Oder verwende den Datei-Auswählen Button
- Unterstützte Formate: `.mbz`, `.tar.gz`, `.zip`

### 📊 Real-time Processing
- Live-Status-Updates während der Verarbeitung
- Progress-Bar mit visueller Rückmeldung
- Automatisches Polling der Job-Status-API

### 📋 Schöne Metadaten-Anzeige
- **Kurs-Übersicht** mit Statistiken
- **Dublin Core Metadaten** strukturiert angezeigt
- **Educational Metadaten** mit Tags
- Responsive Design für alle Bildschirmgrößen

## 🖥️ Screenshots

### Upload-Bereich
- Drag & Drop Zone mit Hover-Effekten
- File-Size-Anzeige und Validierung
- Intuitive Buttons mit Hover-Animationen

### Ergebnisse
- Kurs-Summary mit Aktivitäten/Abschnitte-Count
- Dublin Core Metadaten in strukturierten Karten
- Subject-Tags und Educational-Metadata-Anzeige

## ⚡ Technische Details

### Frontend-Stack
- **Vanilla JavaScript** - Keine Frameworks für maximale Kompatibilität
- **CSS3** - Gradients, Animations, Grid Layout
- **HTML5** - Semantische Struktur
- **HTTP Server** - Python SimpleHTTPServer

### API-Integration
- **REST-Client** mit Fetch API
- **CORS-Support** für Cross-Origin-Requests
- **Error-Handling** mit benutzerfreundlichen Nachrichten
- **Job-Polling** für async Processing

### Responsive Design
- Mobile-friendly Layout
- Adaptive Grid-System für Metadaten-Karten
- Touch-optimierte Upload-Area

## 🔧 Entwicklung

### Frontend lokal entwickeln
```bash
# Frontend-Server mit Auto-Reload
cd frontend
python serve.py --port 3000

# Alternativer Port falls 3000 belegt
python serve.py --port 3001
```

### Frontend ohne Browser öffnen
```bash
python serve.py --no-browser
```

### Styling anpassen
Alle Styles sind in der `index.html` in einem `<style>`-Block definiert:
- CSS-Variablen für Farben und Größen
- Flexbox/Grid für Layout
- CSS-Animations für Interaktionen

### JavaScript-Entwicklung
Alle Funktionalität in `<script>`-Tag in `index.html`:
- `uploadFile()` - Hauptfunktion für Upload
- `monitorJob()` - Status-Polling
- `displayResults()` - Ergebnis-Rendering
- Event-Listener für Drag & Drop

## 🐛 Troubleshooting

### Frontend startet nicht
```bash
# Port-Konflikt prüfen
lsof -i :3000

# Anderen Port verwenden
python serve.py --port 3001
```

### API-Verbindung fehlschlägt
- ✅ Backend läuft auf Port 8000?
- ✅ CORS ist im Backend aktiviert?
- ✅ Firewall blockiert keine Verbindungen?

### Upload funktioniert nicht
- ✅ Datei ist wirklich eine .mbz-Datei?
- ✅ Datei ist nicht zu groß (>100MB)?
- ✅ Backend zeigt Logs im Terminal?

## 📱 Browser-Kompatibilität

### ✅ Vollständig unterstützt
- **Chrome/Edge** 70+
- **Firefox** 65+
- **Safari** 12+

### ⚠️ Eingeschränkt unterstützt
- **Internet Explorer** - Nicht unterstützt (Fetch API fehlt)
- **Ältere Mobile Browser** - Drag & Drop funktioniert möglicherweise nicht

## 🎨 UI/UX Features

### Visuelle Feedback
- ✅ Hover-Effekte auf Buttons und Upload-Area
- ✅ Progress-Bar während Processing
- ✅ Status-Icons (📤, ⏳, ✅, ❌)
- ✅ Loading-Spinner-Animation

### Accessibility
- ✅ Semantische HTML-Struktur
- ✅ Keyboard-Navigation
- ✅ Screen-Reader-freundliche Labels
- ✅ Hoher Kontrast für Lesbarkeit

### Performance
- ✅ Vanilla JS ohne Framework-Overhead
- ✅ CSS-Animationen hardware-beschleunigt
- ✅ Optimierte API-Calls mit Timeout-Handling
- ✅ Lazy Loading für große Metadaten-Sets

---

🎓 **OERSync-AI Frontend** - Transforming Educational Metadata with Style 