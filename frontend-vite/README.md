# 🌐 OERSync-AI React Frontend (Vite)

Dies ist die neue, moderne React-Frontend-App für OERSync-AI, entwickelt mit [Vite](https://vitejs.dev/).

## 🚀 Schnellstart

### 1. Backend starten
```bash
cd ../services/extractor
python main.py
```

### 2. Frontend starten
```bash
npm install
npm run dev
```

Das Frontend öffnet sich automatisch im Browser: **http://localhost:5173**

## 🎯 Features

- Drag & Drop Upload für MBZ-Dateien
- Live-Status-Updates und Progress-Bar
- Schöne Metadaten-Anzeige (Kurs, Dublin Core, Educational, Technisch)
- Responsive Design, Accessibility, deutsche UI
- Integration mit OERSync-AI Backend (Port 8000)
- **Kurs-Visualisierung:** Demo-Nachbau des Kurses (Abschnitte, Aktivitäten, Icons, Accordion/Tree)
- **Erweiterbar:**
  - 📊 Charts (Aktivitätenverteilung)
  - 🎯 Learning Path (Skill-Fortschritt)
  - 📈 Progress Tracking
  - 🔍 Suche/Filter
  - 📤 Export (PDF, JSON, LTI)

## 🧩 Projektstruktur (Best Practice)

```
frontend-vite/
├── src/
│   ├── components/
│   ├── hooks/
│   ├── context/
│   ├── App.jsx
│   └── main.jsx
├── public/
├── package.json
├── vite.config.js
└── ...
```

## 🐛 Troubleshooting

- Backend läuft auf Port 8000?
- CORS im Backend aktiviert?
- Datei ist .mbz/.zip und nicht zu groß?

## 📱 Browser-Kompatibilität

- Chrome, Firefox, Edge, Safari (modern)
- Kein Internet Explorer

---

🎓 **OERSync-AI React Frontend (Vite)** – Modern, schnell, barrierefrei, zukunftssicher
