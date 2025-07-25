import React, { useState, useEffect, useRef } from 'react';
import { CourseProvider } from './context/CourseContext';
import { useCourse } from './context/useCourse';
import UploadSection from './components/UploadSection';
import StatusBar from './components/StatusBar';
import CourseSummary from './components/CourseSummary';
import MetadataDisplay from './components/MetadataDisplay';
import CourseVisualizer from './components/CourseVisualizer';
import { Card, CardContent } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { 
  Upload, 
  BarChart3, 
  BookOpen, 
  Globe,
  Award,
  Clock,
  Users,
  FileText
} from 'lucide-react';
import './App.css';

function MainApp() {
  const { courseData, setCourseData } = useCourse();
  const [statusMsg, setStatusMsg] = useState('');
  const [statusType, setStatusType] = useState('');
  const [activeTab, setActiveTab] = useState('upload');
  const [headerHeight, setHeaderHeight] = useState(0);
  const headerRef = useRef(null);

  useEffect(() => {
    function updateHeaderHeight() {
      if (headerRef.current) {
        setHeaderHeight(headerRef.current.getBoundingClientRect().height);
      }
    }
    updateHeaderHeight();
    window.addEventListener('resize', updateHeaderHeight);
    return () => window.removeEventListener('resize', updateHeaderHeight);
  }, []);

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
          // Automatisch zu den Ergebnissen wechseln
          setActiveTab('results');
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

  // Tab-Konfiguration mit modernen Icons
  const tabs = [
    {
      id: 'upload',
      label: 'Upload',
      icon: Upload,
      content: (
        <div className="space-y-6">
          <UploadSection onUploadSuccess={handleUploadSuccess} onStatusChange={handleStatus} />
          <StatusBar message={statusMsg} type={statusType} />
        </div>
      )
    },
    {
      id: 'results',
      label: 'Ergebnisse',
      icon: BarChart3,
      content: courseData && (
        <div className="space-y-6">
          {hasCourseMeta(courseData) && <CourseSummary data={courseData} />}
          {hasCourseMeta(courseData) && <MetadataDisplay data={courseData} />}
        </div>
      ),
      disabled: !courseData
    },
    {
      id: 'course',
      label: 'Kurs-Ansicht',
      icon: BookOpen,
      content: courseData && (
        <div className="space-y-6">
          <CourseVisualizer data={courseData} />
        </div>
      ),
      disabled: !courseData
    }
  ];

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Header */}
      <header
        ref={headerRef}
        className="header fixed top-0 left-0 w-full z-30 transition-all duration-300"
        style={{
          background: '#002b44',
          borderRadius: 0,
          paddingTop: '1.2rem',
          paddingBottom: '1.2rem',
          boxShadow: '0 2px 12px #002b4440',
          minHeight: '60px',
        }}
      >
        <div className="header-blur-bg" style={{display: 'none'}}></div>
        <div className="header-content flex-col items-center text-center justify-center w-full" style={{padding: 0}}>
          <h1 className="header-title w-full" style={{color: 'white', textAlign: 'center', fontWeight: 700, letterSpacing: '-1px', margin: 0, fontSize: '2rem', lineHeight: 1.1}}>
            OERSync-AI
          </h1>
          <p className="header-subtitle w-full" style={{color: 'white', textAlign: 'center', fontSize: '1.1rem', opacity: 0.95, fontWeight: 400, margin: 0, lineHeight: 1.1}}>
            Automatische Metadaten-Extraktion für Moodle-Kurse
          </p>
          <button className="header-btn mx-auto mt-2" style={{fontSize: '1em', padding: '0.4rem 1.2rem'}}>Preview Mode</button>
        </div>
      </header>

      {/* Platzhalter für festen Header (dynamisch) */}
      <div style={{height: headerHeight}}></div>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 flex-1 flex flex-col items-center justify-start">
        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-muted p-1 rounded-lg mb-8">
          {tabs.map((tab) => {
            const IconComponent = tab.icon;
            return (
              <button
                key={tab.id}
                className={`tab-button flex items-center gap-2 ${
                  activeTab === tab.id ? 'active' : ''
                } ${tab.disabled ? 'disabled' : ''}`}
                onClick={() => !tab.disabled && setActiveTab(tab.id)}
                disabled={tab.disabled}
              >
                <IconComponent className="w-4 h-4" />
                <span>{tab.label}</span>
                {tab.disabled && (
                  <div className="w-2 h-2 bg-muted-foreground rounded-full animate-pulse" />
                )}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="space-y-6 w-full flex flex-col items-center justify-center">
          {tabs.find(tab => tab.id === activeTab)?.content}
        </div>
      </main>

      {/* Footer */}
      <footer className="footer relative overflow-visible mt-0" style={{background: '#002b44', position: 'sticky', bottom: 0, left: 0, width: '100%'}}>
        <div className="footer-blur-bg" style={{display: 'none'}}></div>
        <div className="footer-content">
          <img src="/orca_nrw.png" alt="ORCA.nrw Logo" className="footer-logo" />
          <img src="/moodle_nrw.png" alt="Moodle.NRW Logo" className="footer-logo" />
          <span className="footer-text">Gefördert durch das Land NRW · Partner: Moodle.NRW & ORCA.nrw</span>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <CourseProvider>
      <MainApp />
    </CourseProvider>
  );
}
