import { useState, useEffect, useRef } from 'react';
import { CourseProvider } from './context/CourseContext';
import { useCourse } from './context/useCourse';
import UploadSection from './components/UploadSection';
import StatusBar from './components/StatusBar';
import CourseSummary from './components/CourseSummary';
import MetadataDisplay from './components/MetadataDisplay';
import CourseVisualizer from './components/CourseVisualizer';
import IliasAnalysisView from './components/IliasAnalysisView';
import {
  Upload,
  BarChart3,
  BookOpen,
} from 'lucide-react';
import './App.css';

function MainApp() {
  const { courseData, setCourseData } = useCourse();
  const [statusMsg, setStatusMsg] = useState('');
  const [statusType, setStatusType] = useState('');
  const [activeTab, setActiveTab] = useState('upload');
  const [headerHeight, setHeaderHeight] = useState(0);
  const [compactHeaderFooter, setCompactHeaderFooter] = useState(false);
  const [currentFileType, setCurrentFileType] = useState('moodle'); // Track current analysis type
  const headerRef = useRef(null);
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
  const ILIAS_API_BASE_URL = import.meta.env.VITE_ILIAS_API_URL || 'http://localhost:8004';

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
  function handleUploadSuccess(newJobId, fileType = 'moodle') {
    handleStatus('Verarbeitung läuft...', 'loading');
    setCompactHeaderFooter(true); // Kompakt-Modus aktivieren
    setCurrentFileType(fileType);
    pollJobStatus(newJobId, fileType);
  }

  // Callback für Schnell-Analyse (direkt in UploadSection)
  function handleUploadStarted() {
    setCompactHeaderFooter(true);
  }

  // Polling für Job-Status und Laden der Ergebnisse
  async function pollJobStatus(jobId, fileType = 'moodle') {
    let attempts = 0;
    const maxAttempts = 60;
    const baseUrl = fileType === 'ilias' ? ILIAS_API_BASE_URL : API_BASE_URL;
    const endpoint = fileType === 'ilias' ? 'analyze' : 'extract';
    
    async function check() {
      try {
        const response = await fetch(`${baseUrl}/${endpoint}/${jobId}/status`);
        const data = await response.json();
        if (data.status === 'completed') {
          handleStatus('Verarbeitung abgeschlossen!', 'success');
          fetchResults(jobId, fileType);
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

  async function fetchResults(jobId, fileType = 'moodle') {
    try {
      const baseUrl = fileType === 'ilias' ? ILIAS_API_BASE_URL : API_BASE_URL;
      const endpoint = fileType === 'ilias' ? 'analyze' : 'extract';
      const response = await fetch(`${baseUrl}/${endpoint}/${jobId}`);
      const data = await response.json();
      
      // Just set the data directly - the view components will handle the format
      setCourseData(data);
    } catch {
      handleStatus('Fehler beim Laden der Ergebnisse', 'error');
    }
  }
  
  // Transform ILIAS data to match Moodle data structure (only for pure ILIAS analysis)
  function transformIliasData(iliasData) {
    const analysisData = iliasData.analysis_data || {};
    
    return {
      ...iliasData,
      extracted_data: {
        course_name: analysisData.course_title || 'ILIAS Kurs',
        course_summary: `ILIAS Export - ${analysisData.modules_count || 0} Module`,
        sections: analysisData.modules || [],
        activities: analysisData.modules?.flatMap(module => 
          module.items?.map(item => ({
            ...item,
            module_name: module.title,
            module_type: module.type
          })) || []
        ) || [],
        moodle_version: 'ILIAS Import',
        backup_date: iliasData.created_at
      }
    };
  }

  // Hilfsfunktion: Hat das courseData mehr als nur activities?
  function hasCourseMeta(data) {
    const d = data?.extracted_data || data;
    // Check for MBZ data OR ILIAS analysis_data
    const hasIliasData = data?.analysis_data?.course_title || data?.analysis_data?.modules;
    return !!(d.sections || d.course_name || d.dublin_core || hasIliasData);
  }

  // Tab-Konfiguration mit modernen Icons
  const tabs = [
    {
      id: 'upload',
      label: 'Upload',
      icon: Upload,
      content: (
        <div className="space-y-6">
          <UploadSection onUploadSuccess={handleUploadSuccess} onStatusChange={handleStatus} onUploadStarted={handleUploadStarted} />
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
          {/* If we have extracted_data (MBZ or ILIAS→MBZ), show normal view */}
          {courseData.extracted_data && (
            <>
              <CourseSummary data={courseData} />
              <MetadataDisplay data={courseData} />
              {/* Show ILIAS analysis logs if available (for converted files) */}
              {courseData.analysis_data && courseData.ilias_source && (
                <IliasAnalysisView data={courseData} showOnlyLogs={true} />
              )}
            </>
          )}
          {/* If we only have analysis_data (pure ILIAS), show ILIAS view */}
          {!courseData.extracted_data && courseData.analysis_data && (
            <IliasAnalysisView data={courseData} />
          )}
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
        className={`header fixed top-0 left-0 w-full z-30 transition-all duration-300${compactHeaderFooter ? ' compact' : ''}`}
        style={{
          background: '#002b44',
          borderRadius: 0,
          paddingTop: compactHeaderFooter ? '0.1rem' : '0.7rem',
          paddingBottom: compactHeaderFooter ? '0.1rem' : '0.7rem',
          boxShadow: '0 2px 12px #002b4440',
          minHeight: compactHeaderFooter ? '32px' : '48px',
        }}
      >
        <div className="header-blur-bg" style={{display: 'none'}}></div>
        {/* Kompakter Header nach Upload: alles in einer Zeile */}
        {compactHeaderFooter ? (
          <div className="w-full flex flex-row items-center justify-between px-4" style={{gap: '1.2rem', minHeight: '32px'}}>
            <h1 className="header-title" style={{color: 'white', fontWeight: 700, letterSpacing: '-1px', margin: 0, fontSize: '1.1rem', lineHeight: 1.1, minWidth: '140px', textAlign: 'left'}}>
              OERSync-AI
            </h1>
            <p className="header-subtitle" style={{color: 'white', fontSize: '0.85rem', opacity: 0.95, fontWeight: 400, margin: 0, lineHeight: 1.1, minWidth: '220px', textAlign: 'left'}}>
              Automatische Metadaten-Extraktion für Moodle-Kurse
            </p>
            <div className="flex-1 flex justify-center">
              <div className="flex space-x-2 z-20" style={{minHeight: '28px'}}>
                {tabs.map((tab) => {
                  const IconComponent = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      className={`tab-button flex items-center gap-2 px-3 py-1 transition-colors duration-150 ${
                        isActive ? 'font-bold underline' : ''
                      } ${tab.disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
                      onClick={() => !tab.disabled && setActiveTab(tab.id)}
                      disabled={tab.disabled}
                      style={{
                        color: isActive ? '#fff' : 'rgba(255,255,255,0.75)',
                        background: 'transparent',
                        border: 'none',
                        fontSize: '0.92em',
                        minHeight: '28px',
                        borderBottom: isActive ? '2.5px solid #fff' : '2.5px solid transparent',
                        borderRadius: 0,
                        outline: 'none',
                      }}
                    >
                      <IconComponent className="w-4 h-4" style={{color: isActive ? '#fff' : 'rgba(255,255,255,0.75)'}} />
                      <span>{tab.label}</span>
                      {tab.disabled && (
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-pulse" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
            <button className="header-btn" style={{
              fontSize: '0.8em',
              padding: '0.15rem 0.7rem',
              marginLeft: 'auto',
              zIndex: 10
            }}>Preview Mode</button>
          </div>
        ) : (
          <div className={`header-content w-full flex flex-col items-center text-center justify-center`} style={{padding: 0}}>
            <button className="header-btn" style={{
              position: 'absolute',
              top: '0.7rem',
              right: '2.5rem',
              fontSize: '1em',
              padding: '0.3rem 1.1rem',
              zIndex: 10
            }}>Preview Mode</button>
            <h1 className="header-title" style={{color: 'white', fontWeight: 700, letterSpacing: '-1px', margin: 0, fontSize: '1.7rem', lineHeight: 1.1}}>
              OERSync-AI
            </h1>
            <p className="header-subtitle" style={{color: 'white', fontSize: '1rem', opacity: 0.95, fontWeight: 400, margin: 0, lineHeight: 1.1, marginBottom: '0.5rem'}}>
              Automatische Metadaten-Extraktion für Moodle-Kurse
            </p>
            <div
              className="flex space-x-2 mt-2 mb-0 z-20 justify-center"
              style={{
                width: '100%',
                maxWidth: '800px',
                margin: '0 auto',
                background: 'transparent',
                borderRadius: 0,
                padding: 0,
                boxShadow: 'none',
                display: 'flex',
                alignItems: 'center',
                minHeight: '36px',
              }}
            >
              {tabs.map((tab) => {
                const IconComponent = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    className={`tab-button flex items-center gap-2 px-3 py-1 transition-colors duration-150 ${
                      isActive ? 'font-bold underline' : ''
                    } ${tab.disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
                    onClick={() => !tab.disabled && setActiveTab(tab.id)}
                    disabled={tab.disabled}
                    style={{
                      color: isActive ? '#fff' : 'rgba(255,255,255,0.75)',
                      background: 'transparent',
                      border: 'none',
                      fontSize: '1em',
                      minHeight: '36px',
                      borderBottom: isActive ? '2.5px solid #fff' : '2.5px solid transparent',
                      borderRadius: 0,
                      outline: 'none',
                    }}
                  >
                    <IconComponent className="w-4 h-4" style={{color: isActive ? '#fff' : 'rgba(255,255,255,0.75)'}} />
                    <span>{tab.label}</span>
                    {tab.disabled && (
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-pulse" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </header>

      {/* Platzhalter für festen Header (dynamisch) */}
      <div style={{height: headerHeight}}></div>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 flex-1 flex flex-col items-center
       justify-center">
        {/* Tab Content */}
        <div className="space-y-6 w-full flex flex-col items-center justify-center">
          {tabs.find(tab => tab.id === activeTab)?.content}
        </div>
      </main>

      {/* Footer */}
      <footer className={`footer relative overflow-visible mt-0${compactHeaderFooter ? ' compact' : ''}`} style={{background: '#002b44', position: 'sticky', bottom: 0, left: 0, width: '100%', minHeight: compactHeaderFooter ? '36px' : undefined, padding: compactHeaderFooter ? '0.2rem 0' : undefined, borderRadius: 0}}>
        <div className="footer-blur-bg" style={{display: 'none'}}></div>
        <div className="footer-content" style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: compactHeaderFooter ? '1.2rem' : '2.5rem'}}>
          <img src="/orca_nrw.png" alt="ORCA.nrw Logo" className="footer-logo" style={{height: compactHeaderFooter ? '22px' : '36px'}} />
          <img src="/moodle_nrw.png" alt="Moodle.NRW Logo" className="footer-logo" style={{height: compactHeaderFooter ? '22px' : '36px'}} />
          <span className="footer-text" style={{fontSize: compactHeaderFooter ? '0.8rem' : undefined}}>Gefördert durch das Land NRW · Partner: Moodle.NRW & ORCA.nrw</span>
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
