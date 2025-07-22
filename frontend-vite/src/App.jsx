import React, { useState } from 'react';
import { CourseProvider } from './context/CourseContext';
import { useCourse } from './context/useCourse';
import UploadSection from './components/UploadSection';
import StatusBar from './components/StatusBar';
import CourseSummary from './components/CourseSummary';
import MetadataDisplay from './components/MetadataDisplay';
import CourseVisualizer from './components/CourseVisualizer';
import './App.css';

function MainApp() {
  const { courseData, setCourseData } = useCourse();
  const [statusMsg, setStatusMsg] = useState('');
  const [statusType, setStatusType] = useState('');

  // StatusBar-Callback
  function handleStatus(msg, type) {
    setStatusMsg(msg);
    setStatusType(type);
  }

  // Upload-Callback
  function handleUploadSuccess(newJobId) {
    handleStatus('Verarbeitung läuft...', 'loading');
    pollJobStatus(newJobId);
  }

  // Polling für Job-Status und Laden der Ergebnisse
  async function pollJobStatus(jobId) {
    let attempts = 0;
    const maxAttempts = 60;
    async function check() {
      try {
        const response = await fetch(`http://localhost:8000/extract/${jobId}/status`);
        const data = await response.json();
        if (data.status === 'completed') {
          handleStatus('Verarbeitung abgeschlossen!', 'success');
          fetchResults(jobId);
        } else if (data.status === 'failed') {
          handleStatus('Verarbeitung fehlgeschlagen: ' + (data.error || 'Unbekannter Fehler'), 'error');
        } else {
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(check, 1000);
          } else {
            handleStatus('Timeout erreicht. Bitte versuchen Sie es erneut.', 'error');
          }
        }
      } catch {
        handleStatus('Fehler beim Statuscheck', 'error');
      }
    }
    check();
  }

  async function fetchResults(jobId) {
    try {
      const response = await fetch(`http://localhost:8000/extract/${jobId}`);
      const data = await response.json();
      setCourseData(data);
    } catch {
      handleStatus('Fehler beim Laden der Ergebnisse', 'error');
    }
  }

  // Hilfsfunktion: Hat das courseData mehr als nur activities?
  function hasCourseMeta(data) {
    const d = data?.extracted_data || data;
    return !!(d.sections || d.course_name || d.dublin_core);
  }

  return (
    <>
      <div className="container">
        <div className="header">
          <span className="header-title">OERSync-AI</span>
          <p>Automatische Metadaten-Extraktion für Moodle-Kurse</p>
        </div>
        <div className="main-content">
          <UploadSection onUploadSuccess={handleUploadSuccess} onStatusChange={handleStatus} />
          <StatusBar message={statusMsg} type={statusType} />
          {courseData && hasCourseMeta(courseData) && <CourseSummary data={courseData} />}
          {courseData && hasCourseMeta(courseData) && <MetadataDisplay data={courseData} />}
          {courseData && <CourseVisualizer data={courseData} />}
        </div>
      </div>
      <footer className="footer">
        <div className="footer-logos">
          <img src="/moodle_nrw.png" alt="Moodle.NRW Logo" className="footer-logo" />
          <img src="/orca_nrw.png" alt="ORCA.nrw Logo" className="footer-logo orca-logo" />
        </div>
        <div className="footer-text">
          Gefördert durch das Land NRW · Partner: Moodle.NRW & ORCA.nrw
        </div>
      </footer>
    </>
  );
}

export default function App() {
  return (
    <CourseProvider>
      <MainApp />
    </CourseProvider>
  );
}
