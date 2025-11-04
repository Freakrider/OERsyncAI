import { useState } from 'react';

export default function CourseSummary({ data }) {
  const [moodleStatus, setMoodleStatus] = useState('');
  const [moodleBtnText, setMoodleBtnText] = useState('Moodle-Instanz starten');
  const [moodleBtnDisabled, setMoodleBtnDisabled] = useState(false);
  const [workspaceUrl, setWorkspaceUrl] = useState(null);
  const [workspaceInfo, setWorkspaceInfo] = useState(null);

  if (!data) return null;
  const extracted = data.extracted_data || data;
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
  const ILIAS_API_BASE_URL = import.meta.env.VITE_ILIAS_API_URL || 'http://localhost:8004';
  const isFromIlias = data.ilias_source && data.moodle_mbz_available;

  async function startMoodleInstance() {
    setMoodleBtnText('Starte Moodle-Instanz...');
    setMoodleBtnDisabled(true);
    setMoodleStatus('');
    try {
      const response = await fetch(`${API_BASE_URL}/start-moodle-instance/${data.job_id}`, { method: 'POST' });
      const result = await response.json();
      if (result.success && result.workspace_url) {
        setMoodleStatus('Moodle-Instanz erfolgreich gestartet!');
        setWorkspaceUrl(result.workspace_url);
        setWorkspaceInfo(result);
        setMoodleBtnText('Zu Gitpod wechseln');
        setMoodleBtnDisabled(false);
      } else if (result.manual_start) {
        setMoodleStatus(result.message);
        setWorkspaceUrl(result.context_url);
        setMoodleBtnText('Manuell in Gitpod öffnen');
        setMoodleBtnDisabled(false);
      } else {
        setMoodleStatus('Fehler: ' + (result.error || 'Unbekannter Fehler'));
        setMoodleBtnText('Moodle-Instanz starten');
        setMoodleBtnDisabled(false);
      }
    } catch {
      setMoodleStatus('Fehler beim Starten der Moodle-Instanz');
      setMoodleBtnText('Moodle-Instanz starten');
      setMoodleBtnDisabled(false);
    }
  }

  function downloadExtractedData() {
    const json = JSON.stringify(extracted, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `${extracted.course_short_name || 'course-data'}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  async function downloadMBZ() {
    try {
      const response = await fetch(`${ILIAS_API_BASE_URL}/analyze/${data.job_id}/download-moodle`);
      if (!response.ok) {
        throw new Error('Download fehlgeschlagen');
      }
      
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'ilias_converted.mbz';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      alert('Fehler beim Download: ' + error.message);
    }
  }

  return (
    <div className="course-summary">
      <h2>{extracted.course_name || 'Unbekannter Kurs'}</h2>
      <p><strong>Kurzname:</strong>
        {extracted.course_short_name || 'N/A'}
        (Originale Kurs-ID: {extracted.course_id})
      </p>
      <p><strong>Moodle Version:</strong> {extracted.moodle_version || 'N/A'}</p>
      {extracted.course_summary && (
        <div>
            <strong>Beschreibung:</strong>
            <div
                className="moodle-html prose prose-invert max-w-none mt-2"
                dangerouslySetInnerHTML={{
                    __html: extracted.course_summary,
                }}
            />
        </div>
        )}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{extracted.activities_count || 0}</div>
          <div className="stat-label">Aktivitäten</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{extracted.sections_count || 0}</div>
          <div className="stat-label">Abschnitte</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{extracted.dublin_core?.subject ? extracted.dublin_core.subject.length : 0}</div>
          <div className="stat-label">Themen</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{data.processing_time_seconds ? Math.round(data.processing_time_seconds * 1000) : 'N/A'}</div>
          <div className="stat-label">ms Verarbeitung</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{extracted.required_plugins?.plugincounter || 0}</div>
          <div className="stat-label">Plugins</div>
        </div>
      </div>
      <div className="moodle-launch-section">
        <button className="moodle-launch-btn" onClick={() => workspaceUrl ? window.open(workspaceUrl, '_blank') : startMoodleInstance()} disabled={moodleBtnDisabled}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"></circle>
            <polygon points="10,8 16,12 10,16 10,8"></polygon>
          </svg>
          {moodleBtnText}
        </button>
        <p className="moodle-launch-description">
          Startet eine vorkonfigurierte Moodle {extracted.moodle_version || '4.x'} Instanz in Gitpod
        </p>
        {moodleStatus && <div className="moodle-success-info"><p>{moodleStatus}</p>
          {workspaceInfo && workspaceInfo.workspace_id && (
            <>
              <p><strong>Version:</strong> Moodle {workspaceInfo.moodle_version} ({workspaceInfo.branch})</p>
              <p><strong>Workspace-ID:</strong> <code>{workspaceInfo.workspace_id}</code></p>
              <p><small>Die Moodle-Instanz wird in wenigen Minuten bereit sein.</small></p>
            </>
          )}
        </div>}
      </div>
      <div className="download-json-section">
        {isFromIlias && (
          <button className="download-btn" onClick={downloadMBZ} style={{ 
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            marginBottom: '10px'
          }}>
            📦 Konvertiertes MBZ herunterladen
          </button>
        )}
        <button className="download-btn" onClick={downloadExtractedData}>
            📥 Daten als JSON herunterladen
        </button>
      </div>
    </div>
  );
}