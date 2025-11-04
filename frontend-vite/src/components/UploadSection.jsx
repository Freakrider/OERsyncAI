import { useRef, useState } from 'react';

const ACCEPTED_TYPES = {
  moodle: ['.mbz', '.zip', '.tar.gz'],
  ilias: ['.zip']
};

export default function UploadSection({ onUploadSuccess, onStatusChange }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [fileType, setFileType] = useState('moodle'); // 'moodle' or 'ilias'
  const [convertToMoodle, setConvertToMoodle] = useState(false); // For ILIAS conversion
  const fileInputRef = useRef();

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
  const ILIAS_API_BASE_URL = import.meta.env.VITE_ILIAS_API_URL || 'http://localhost:8004';

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

  const handleFileTypeChange = (type) => {
    setFileType(type);
    setSelectedFile(null); // Reset file when switching types
    setError(null);
    setConvertToMoodle(false);
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
    
    const uploadTypeLabel = fileType === 'ilias' ? 'ILIAS-Export' : 'MBZ-Datei';
    onStatusChange && onStatusChange(`${uploadTypeLabel} wird hochgeladen...`, 'loading');
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      // Use different API endpoints based on file type
      const apiUrl = fileType === 'ilias' 
        ? `${ILIAS_API_BASE_URL}/analyze${convertToMoodle ? '?convert_to_moodle=true' : ''}`
        : `${API_BASE_URL}/extract`;
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });

      const isJson = response.headers.get('content-type')?.includes('application/json');
      const data = isJson ? await response.json() : null;

      if (!response.ok) {
        const error = new Error(data?.message || `HTTP ${response.status}: ${response.statusText}`);
        error.data = data;
        throw error;
      }

      onStatusChange && onStatusChange('Verarbeitung gestartet...', 'loading');
      setProgress(30);
      onUploadSuccess && onUploadSuccess(data.job_id, fileType); // Pass fileType to parent
    } catch (err) {
      const detailedMessage = err?.data?.message || err.message || 'Unbekannter Fehler beim Upload.';
      setError('Fehler beim Upload: ' + detailedMessage);
      onStatusChange && onStatusChange('Fehler beim Upload: ' + detailedMessage, 'error');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      {/* File Type Selector - OUTSIDE drag area */}
      <div style={{ 
        marginBottom: '20px', 
        display: 'flex', 
        gap: '10px', 
        justifyContent: 'center', 
        alignItems: 'center',
        position: 'relative',
        zIndex: 10
      }}>
        <button
          onClick={() => handleFileTypeChange('moodle')}
          style={{
            padding: '10px 20px',
            background: fileType === 'moodle' ? '#002b44' : '#f1f5f9',
            color: fileType === 'moodle' ? 'white' : '#64748b',
            border: fileType === 'moodle' ? '2px solid #002b44' : '2px solid #e2e8f0',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: fileType === 'moodle' ? 'bold' : 'normal',
            transition: 'all 0.2s',
            pointerEvents: uploading ? 'none' : 'auto'
          }}
          disabled={uploading}
        >
          📦 Moodle MBZ
        </button>
        <button
          onClick={() => handleFileTypeChange('ilias')}
          style={{
            padding: '10px 20px',
            background: fileType === 'ilias' ? '#002b44' : '#f1f5f9',
            color: fileType === 'ilias' ? 'white' : '#64748b',
            border: fileType === 'ilias' ? '2px solid #002b44' : '2px solid #e2e8f0',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: fileType === 'ilias' ? 'bold' : 'normal',
            transition: 'all 0.2s',
            pointerEvents: uploading ? 'none' : 'auto'
          }}
          disabled={uploading}
        >
          📚 ILIAS Export
        </button>
      </div>

      {/* ILIAS-specific option: Convert to Moodle - OUTSIDE drag area */}
      {fileType === 'ilias' && (
        <div style={{ 
          margin: '0 0 20px 0', 
          padding: '12px 16px', 
          background: '#f8fafc', 
          borderRadius: '8px', 
          border: '1px solid #e2e8f0',
          position: 'relative',
          zIndex: 10
        }}>
          <label style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '10px', 
            cursor: 'pointer', 
            color: '#475569',
            userSelect: 'none'
          }}>
            <input
              type="checkbox"
              checked={convertToMoodle}
              onChange={(e) => setConvertToMoodle(e.target.checked)}
              disabled={uploading}
              style={{ 
                cursor: 'pointer',
                width: '18px',
                height: '18px',
                accentColor: '#002b44'
              }}
            />
            <span style={{ fontSize: '14px', fontWeight: 500 }}>
              Nach der Analyse in Moodle-Format (MBZ) konvertieren
            </span>
          </label>
        </div>
      )}

      {/* Upload Section with Drag & Drop */}
      <div
        className={`upload-section${dragActive ? ' dragover' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >

      <h2>{fileType === 'ilias' ? 'ILIAS-Export hochladen' : 'MBZ-Datei hochladen'}</h2>
      <p style={{ margin: '15px 0', color: '#64748b' }}>
        {fileType === 'ilias' 
          ? 'Ziehen Sie Ihren ILIAS-Export (.zip) hierher oder wählen Sie eine Datei aus'
          : 'Ziehen Sie Ihre Moodle-Backup-Datei (.mbz) hierher oder wählen Sie eine Datei aus'
        }
      </p>

      <input
        type="file"
        ref={fileInputRef}
        className="file-input"
        accept={ACCEPTED_TYPES[fileType].join(',')}
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
        style={{ background: '#10b981', color: 'white', marginLeft: 8 }}
        onClick={uploadFile}
        disabled={!selectedFile || uploading}
      >
        Analysieren
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
    </div>
  );
}