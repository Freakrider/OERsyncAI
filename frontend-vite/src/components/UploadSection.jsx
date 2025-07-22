import React, { useRef, useState } from 'react';
import { useCourse } from '../context/useCourse';

const ACCEPTED_TYPES = ['.mbz', '.zip', '.tar.gz'];

export default function UploadSection({ onUploadSuccess, onStatusChange }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef();
  const { setCourseData } = useCourse();

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => setDragActive(false);

  async function uploadFile() {
    if (!selectedFile) {
      setError('Bitte wähle zuerst eine Datei aus.');
      return;
    }
    setUploading(true);
    setError(null);
    setProgress(0);
    onStatusChange && onStatusChange('Datei wird hochgeladen...', 'loading');
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      const response = await fetch(`${API_BASE_URL}/extract`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      onStatusChange && onStatusChange('Verarbeitung gestartet...', 'loading');
      setProgress(30);
      onUploadSuccess && onUploadSuccess(data.job_id);
    } catch (err) {
      setError('Fehler beim Upload: ' + err.message);
      onStatusChange && onStatusChange('Fehler beim Upload: ' + err.message, 'error');
    } finally {
      setUploading(false);
    }
  }

  async function quickAnalyze() {
    if (!selectedFile) {
      setError('Bitte wähle zuerst eine Datei aus.');
      return;
    }
    setUploading(true);
    setError(null);
    setProgress(0);
    onStatusChange && onStatusChange('Datei wird hochgeladen...', 'loading');
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      const response = await fetch(`${API_BASE_URL}/extract-activities`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const data = await response.json();
      setProgress(100);
      setCourseData({ activities: data.activities });
      onStatusChange && onStatusChange('Schnell-Analyse abgeschlossen!', 'success');
    } catch (err) {
      setError('Fehler bei Schnell-Analyse: ' + err.message);
      onStatusChange && onStatusChange('Fehler bei Schnell-Analyse: ' + err.message, 'error');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div
      className={`upload-section${dragActive ? ' dragover' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <h2>MBZ-Datei hochladen</h2>
      <p style={{ margin: '15px 0', color: '#64748b' }}>
        Ziehen Sie Ihre Moodle-Backup-Datei (.mbz) hierher oder wählen Sie eine Datei aus
      </p>
      <input
        type="file"
        ref={fileInputRef}
        className="file-input"
        accept={ACCEPTED_TYPES.join(',')}
        style={{ display: 'none' }}
        onChange={handleFileChange}
        disabled={uploading}
      />
      <button
        className="upload-btn"
        onClick={() => fileInputRef.current && fileInputRef.current.click()}
        disabled={uploading}
      >
        Datei auswählen
      </button>
      <button
        className="upload-btn"
        onClick={uploadFile}
        disabled={!selectedFile || uploading}
      >
        Analysieren
      </button>
      <button
        className="upload-btn"
        style={{ background: '#10b981', color: 'white', marginLeft: 8 }}
        onClick={quickAnalyze}
        disabled={!selectedFile || uploading}
      >
        Schnell-Analyse
      </button>
      {selectedFile && (
        <div id="selectedFile" style={{ marginTop: 15, color: '#64748b' }}>
          Ausgewählte Datei: <strong>{selectedFile.name}</strong> ({formatFileSize(selectedFile.size)})
        </div>
      )}
      {uploading && (
        <div className="progress-bar" style={{ marginTop: 20 }}>
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
      )}
      {error && <div className="status error">{error}</div>}
    </div>
  );
} 