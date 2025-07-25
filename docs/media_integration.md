# Medienintegration in OERSync-AI

## Übersicht

Die erweiterte Medienintegration in OERSync-AI ermöglicht eine umfassende Verarbeitung und Verwaltung von Mediendateien aus Moodle-Backups. Das System extrahiert automatisch alle Dateien aus der `files.xml` und kategorisiert sie nach Medientypen.

## Features

### 1. Automatische Dateiextraktion
- Parsing der `files.xml` aus Moodle-Backups
- Extraktion von Metadaten (contenthash, filename, filepath, mimetype, etc.)
- Automatische Klassifizierung nach Medientypen

### 2. Medientyp-Klassifizierung
- **Bilder**: JPEG, PNG, GIF, BMP, SVG, WebP
- **Videos**: MP4, AVI, MOV, WMV, FLV, WebM
- **Audio**: MP3, WAV, OGG, AAC, FLAC
- **Dokumente**: PDF, TXT, HTML, DOC, DOCX
- **Präsentationen**: PPT, PPTX
- **Tabellen**: XLS, XLSX
- **Archive**: ZIP, RAR, 7Z, TAR, GZ
- **Code**: PY, JS, HTML, CSS, Java, C++, PHP, SQL

### 3. Erweiterte Metadaten
- Dublin Core Metadaten für jede Datei
- Verwendungskontext (Aktivitäten, Abschnitte)
- Technische Details (Größe, Format, Auflösung)
- Zeitstempel (Erstellung, Änderung)

### 4. Mediensammlungen
- Automatische Gruppierung nach Medientypen
- Kursweite und typ-spezifische Sammlungen
- Statistiken und Übersichten

## API-Endpunkte

### Basis-Extraktion
```http
POST /extract
```
Extrahiert MBZ-Datei mit erweiterter Medienintegration.

### Medienendpunkte

#### Alle Mediendateien abrufen
```http
GET /extract/{job_id}/media
```
Gibt alle extrahierten Mediendateien für einen Job zurück.

**Response:**
```json
[
  {
    "file_id": "a1b2c3d4e5f6...",
    "original_filename": "example.jpg",
    "filepath": "/course_files/images/",
    "mimetype": "image/jpeg",
    "filesize": 1024000,
    "media_type": "image",
    "file_extension": ".jpg",
    "is_image": true,
    "is_video": false,
    "is_document": false,
    "is_audio": false,
    "title": "example.jpg",
    "description": null,
    "author": null,
    "timecreated": "2024-01-15T10:30:00",
    "timemodified": "2024-01-15T10:30:00"
  }
]
```

#### Spezifische Mediendatei abrufen
```http
GET /extract/{job_id}/media/{file_id}
```
Gibt Metadaten für eine spezifische Mediendatei zurück.

#### Mediendatei herunterladen
```http
GET /extract/{job_id}/media/{file_id}/download
```
Lädt eine spezifische Mediendatei direkt herunter.

#### Mediendateien nach Typ filtern
```http
GET /extract/{job_id}/media/type/{media_type}
```
Gibt nur Mediendateien eines bestimmten Typs zurück.

**Gültige Medientypen:**
- `image` - Bilddateien
- `video` - Videodateien
- `audio` - Audiodateien
- `document` - Dokumente
- `presentation` - Präsentationen
- `spreadsheet` - Tabellen
- `archive` - Archive
- `code` - Code-Dateien
- `other` - Sonstige Dateien

#### Mediensammlungen abrufen
```http
GET /extract/{job_id}/media/collections
```
Gibt alle Mediensammlungen für einen Job zurück.

**Response:**
```json
[
  {
    "collection_id": "course_123_media",
    "name": "Medien für Beispielkurs",
    "description": "Alle Medien des Kurses",
    "total_files": 25,
    "total_size": 52428800,
    "images_count": 15,
    "videos_count": 5,
    "documents_count": 3,
    "audio_count": 1,
    "other_count": 1
  }
]
```

#### Dateistatistiken abrufen
```http
GET /extract/{job_id}/media/statistics
```
Gibt detaillierte Statistiken über alle Mediendateien zurück.

**Response:**
```json
{
  "total_files": 25,
  "total_size": 52428800,
  "by_type": {
    "image": {
      "count": 15,
      "total_size": 31457280
    },
    "video": {
      "count": 5,
      "total_size": 15728640
    }
  },
  "by_extension": {
    ".jpg": {
      "count": 10,
      "total_size": 20971520
    },
    ".png": {
      "count": 5,
      "total_size": 10485760
    }
  },
  "largest_files": [
    {
      "file_id": "a1b2c3d4e5f6...",
      "filename": "large_video.mp4",
      "size": 10485760,
      "media_type": "video"
    }
  ]
}
```

## Datenmodelle

### FileMetadata
```python
class FileMetadata(BaseModel):
    file_id: str                    # contenthash
    original_filename: str          # Ursprünglicher Dateiname
    filepath: str                   # Pfad innerhalb des Kurses
    mimetype: str                   # MIME-Type
    filesize: int                   # Dateigröße in Bytes
    media_type: MediaType           # Klassifizierter Medientyp
    file_extension: str             # Dateiendung
    title: Optional[str]            # Titel der Datei
    description: Optional[str]      # Beschreibung
    author: Optional[str]           # Autor
    license: Optional[LicenseType]  # Lizenz
    is_image: bool                  # Ist es ein Bild?
    is_video: bool                  # Ist es ein Video?
    is_document: bool               # Ist es ein Dokument?
    is_audio: bool                  # Ist es eine Audiodatei?
    timecreated: Optional[datetime] # Erstellungszeitpunkt
    timemodified: Optional[datetime] # Letzte Änderung
    used_in_activities: List[str]   # Verwendet in Aktivitäten
    used_in_sections: List[str]     # Verwendet in Abschnitten
```

### MediaCollection
```python
class MediaCollection(BaseModel):
    collection_id: str              # Eindeutige ID
    name: str                       # Name der Sammlung
    description: Optional[str]      # Beschreibung
    total_files: int                # Gesamtanzahl Dateien
    total_size: int                 # Gesamtgröße in Bytes
    images: List[FileMetadata]      # Bilddateien
    videos: List[FileMetadata]      # Videodateien
    documents: List[FileMetadata]   # Dokumente
    audio_files: List[FileMetadata] # Audiodateien
    other_files: List[FileMetadata] # Sonstige Dateien
    course_id: Optional[int]        # Zugehörige Kurs-ID
    section_id: Optional[int]       # Zugehörige Abschnitt-ID
    activity_id: Optional[int]      # Zugehörige Aktivitäts-ID
```

## Verwendung im Frontend

### 1. Medienübersicht anzeigen
```javascript
// Alle Medien abrufen
const response = await fetch(`/extract/${jobId}/media`);
const mediaFiles = await response.json();

// Nach Typ filtern
const images = mediaFiles.filter(file => file.media_type === 'image');
const videos = mediaFiles.filter(file => file.media_type === 'video');
```

### 2. Medienvorschau
```javascript
// Bildvorschau
const imageFiles = await fetch(`/extract/${jobId}/media/type/image`);
const images = await imageFiles.json();

// Video-Liste
const videoFiles = await fetch(`/extract/${jobId}/media/type/video`);
const videos = await videoFiles.json();
```

### 3. Mediendownload
```javascript
// Datei herunterladen
const downloadUrl = `/extract/${jobId}/media/${fileId}/download`;
window.open(downloadUrl, '_blank');
```

### 4. Statistiken anzeigen
```javascript
// Statistiken abrufen
const stats = await fetch(`/extract/${jobId}/media/statistics`);
const statistics = await stats.json();

console.log(`Gesamt: ${statistics.total_files} Dateien`);
console.log(`Größe: ${formatBytes(statistics.total_size)}`);
```

## Erweiterte Features

### 1. Automatische Bildanalyse
Das System kann erweitert werden um:
- Bildgröße und Auflösung zu extrahieren
- Automatische Bildbeschreibung zu generieren
- Ähnlichkeitserkennung zwischen Bildern

### 2. Video-Metadaten
Für Videodateien können extrahiert werden:
- Videolänge
- Auflösung
- Codec-Informationen
- Thumbnail-Generierung

### 3. Dokumentenanalyse
Für Dokumente können analysiert werden:
- Seitenanzahl
- Text-Extraktion
- Struktur-Erkennung

### 4. Verwendungskontext
Das System kann erweitert werden um:
- Automatische Verknüpfung von Dateien mit Aktivitäten
- Nutzungsanalyse
- Abhängigkeitserkennung

## Sicherheitsaspekte

### 1. Dateizugriff
- Nur authentifizierte Benutzer können auf Mediendateien zugreifen
- Dateipfade werden validiert um Path-Traversal zu verhindern
- MIME-Type-Validierung für Uploads

### 2. Speicherung
- Temporäre Dateien werden automatisch bereinigt
- In Produktion sollten Dateien in einem sicheren Speicher gesichert werden
- Backup-Strategien für wichtige Medien

### 3. Performance
- Streaming für große Dateien
- Caching für häufig abgerufene Medien
- Komprimierung für Web-Delivery

## Beispiel-Integration

### React-Komponente für Medienübersicht
```jsx
import React, { useState, useEffect } from 'react';

const MediaOverview = ({ jobId }) => {
  const [mediaFiles, setMediaFiles] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMedia = async () => {
      try {
        const [filesRes, statsRes] = await Promise.all([
          fetch(`/extract/${jobId}/media`),
          fetch(`/extract/${jobId}/media/statistics`)
        ]);
        
        const files = await filesRes.json();
        const stats = await statsRes.json();
        
        setMediaFiles(files);
        setStatistics(stats);
      } catch (error) {
        console.error('Fehler beim Laden der Medien:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMedia();
  }, [jobId]);

  if (loading) return <div>Lade Medien...</div>;

  return (
    <div className="media-overview">
      <h2>Medienübersicht</h2>
      
      {statistics && (
        <div className="statistics">
          <p>Gesamt: {statistics.total_files} Dateien ({formatBytes(statistics.total_size)})</p>
          <div className="type-breakdown">
            {Object.entries(statistics.by_type).map(([type, data]) => (
              <span key={type} className="type-badge">
                {type}: {data.count}
              </span>
            ))}
          </div>
        </div>
      )}
      
      <div className="media-grid">
        {mediaFiles.map(file => (
          <div key={file.file_id} className="media-item">
            {file.is_image && (
              <img 
                src={`/extract/${jobId}/media/${file.file_id}/download`}
                alt={file.original_filename}
                className="media-preview"
              />
            )}
            <div className="media-info">
              <h4>{file.original_filename}</h4>
              <p>{formatBytes(file.filesize)} • {file.media_type}</p>
              <a 
                href={`/extract/${jobId}/media/${file.file_id}/download`}
                download
                className="download-btn"
              >
                Herunterladen
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export default MediaOverview;
```

## Fazit

Die erweiterte Medienintegration in OERSync-AI bietet eine umfassende Lösung für die Verwaltung von Mediendateien aus Moodle-Backups. Durch die automatische Klassifizierung, detaillierte Metadaten und flexible API-Endpunkte können Frontend-Anwendungen eine reichhaltige Medienübersicht und -verwaltung implementieren.

Die Architektur ist erweiterbar und kann um zusätzliche Features wie automatische Bildanalyse, Video-Metadaten-Extraktion und erweiterte Verwendungskontext-Analyse erweitert werden. 