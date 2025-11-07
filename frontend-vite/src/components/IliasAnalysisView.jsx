import React from 'react';
import { BookOpen, Layers, FileText, Download, CheckCircle, AlertTriangle, Info, XCircle } from 'lucide-react';

export default function IliasAnalysisView({ data }) {
  const analysisData = data?.analysis_data;
  const analysisLogs = data?.analysis_logs;
  const ILIAS_API_BASE_URL = import.meta.env.VITE_ILIAS_API_URL || 'http://localhost:8004';
  
  // Debug: Log die gesamten Daten
  React.useEffect(() => {
    console.log('🔍 IliasAnalysisView data:', data);
    console.log('🔍 analysis_logs:', analysisLogs);
  }, [data, analysisLogs]);
  
  // Log die Analyse-Logs ins Browser-Console
  React.useEffect(() => {
    if (analysisLogs && analysisLogs.length > 0) {
      console.group('📋 ILIAS Analysis Logs');
      analysisLogs.forEach(log => {
        const style = `color: ${
          log.level === 'ERROR' ? '#ef4444' :
          log.level === 'WARNING' ? '#f59e0b' :
          log.level === 'INFO' ? '#3b82f6' :
          '#6b7280'
        }; font-weight: ${log.level === 'ERROR' || log.level === 'WARNING' ? 'bold' : 'normal'}`;
        
        console.log(
          `%c[${log.level}] ${log.timestamp} - ${log.message}`,
          style
        );
      });
      console.groupEnd();
    } else {
      console.warn('⚠️ Keine analysis_logs gefunden oder leeres Array');
    }
  }, [analysisLogs]);
  
  if (!analysisData) {
    return <div>Keine ILIAS-Daten verfügbar</div>;
  }

  const downloadMBZ = async () => {
    try {
      const response = await fetch(`${ILIAS_API_BASE_URL}/analyze/${data.job_id}/download-moodle`);
      if (!response.ok) {
        throw new Error('Download fehlgeschlagen');
      }
      
      // Get filename from Content-Disposition header or use default
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
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #002b44 0%, #004d7a 100%)',
        borderRadius: '12px',
        padding: '24px',
        color: 'white',
        boxShadow: '0 4px 12px rgba(0, 43, 68, 0.2)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <BookOpen size={32} />
          <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>
            {analysisData.course_title || 'ILIAS Kurs'}
          </h2>
        </div>
        {analysisData.installation_url && (
          <p style={{ margin: '4px 0 0 0', opacity: 0.9, fontSize: '14px' }}>
            📍 {analysisData.installation_url}
          </p>
        )}
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px'
      }}>
        <div className="stat-card">
          <div className="stat-number">{analysisData.modules_count || 0}</div>
          <div className="stat-label">Module</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">
            {analysisData.modules?.reduce((sum, m) => sum + (m.items?.length || 0), 0) || 0}
          </div>
          <div className="stat-label">Gesamt Items</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{data.file_size ? (data.file_size / 1024 / 1024).toFixed(1) : 'N/A'}</div>
          <div className="stat-label">MB Dateigröße</div>
        </div>
      </div>

      {/* Modules */}
      <div>
        <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={20} />
          Module und Inhalte
        </h3>
        
        <div className="space-y-4">
          {analysisData.modules?.map((module, idx) => (
            <div 
              key={module.id || idx}
              style={{
                background: 'white',
                borderRadius: '8px',
                padding: '20px',
                border: '1px solid #e2e8f0',
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
              }}
            >
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px',
                marginBottom: '12px',
                paddingBottom: '12px',
                borderBottom: '2px solid #f1f5f9'
              }}>
                <div style={{
                  background: '#002b44',
                  color: 'white',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  textTransform: 'uppercase'
                }}>
                  {module.type || 'Module'}
                </div>
                <h4 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#1e293b' }}>
                  {module.title}
                </h4>
              </div>

              {/* Items */}
              {module.items && module.items.length > 0 ? (
                <div style={{ marginTop: '12px' }}>
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px', fontWeight: 500 }}>
                    {module.items.length} Item{module.items.length !== 1 ? 's' : ''}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {module.items.map((item, itemIdx) => (
                      <div
                        key={item.id || itemIdx}
                        style={{
                          background: '#f8fafc',
                          padding: '12px 16px',
                          borderRadius: '6px',
                          border: '1px solid #e2e8f0',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px'
                        }}
                      >
                        <FileText size={16} style={{ color: '#64748b', flexShrink: 0 }} />
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 500, color: '#334155' }}>
                            {item.title}
                          </div>
                          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                            Typ: {item.type}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ 
                  color: '#94a3b8', 
                  fontSize: '14px', 
                  fontStyle: 'italic',
                  padding: '12px',
                  background: '#f8fafc',
                  borderRadius: '6px'
                }}>
                  Keine Items in diesem Modul
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Moodle Structure - nur wenn verfügbar */}
      {data.moodle_structure && (
        <div>
          <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={20} color="#10b981" />
            Moodle-Struktur
          </h3>
          
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
              gap: '16px',
              marginBottom: '20px'
            }}>
              <div style={{ textAlign: 'center', padding: '12px', background: '#f0f9ff', borderRadius: '8px' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#0284c7' }}>
                  {data.moodle_structure.sections_count}
                </div>
                <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>Sections</div>
              </div>
              <div style={{ textAlign: 'center', padding: '12px', background: '#f0fdf4', borderRadius: '8px' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#16a34a' }}>
                  {data.moodle_structure.activities_count}
                </div>
                <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>Activities</div>
              </div>
            </div>
            
            {data.moodle_structure.sections && (
              <div style={{ marginTop: '16px' }}>
                <div style={{ 
                  fontSize: '14px', 
                  fontWeight: 600, 
                  color: '#475569', 
                  marginBottom: '12px' 
                }}>
                  Sections:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {data.moodle_structure.sections.map((section, idx) => (
                    <div 
                      key={section.id || idx}
                      style={{
                        background: '#f8fafc',
                        padding: '12px',
                        borderRadius: '6px',
                        borderLeft: '3px solid #3b82f6',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <span style={{ fontWeight: 500, color: '#334155' }}>
                        {section.name}
                      </span>
                      <span style={{ 
                        fontSize: '12px', 
                        color: '#64748b',
                        background: 'white',
                        padding: '4px 8px',
                        borderRadius: '4px'
                      }}>
                        {section.activities_count} Activities
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Conversion Report - nur wenn verfügbar */}
      {data.conversion_report && (
        <div>
          <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Info size={20} color="#8b5cf6" />
            Conversion Report
          </h3>
          
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '20px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}>
            {/* Summary */}
            <div style={{ 
              display: 'flex', 
              gap: '12px', 
              marginBottom: '20px',
              flexWrap: 'wrap'
            }}>
              <div style={{ 
                flex: 1, 
                minWidth: '100px',
                padding: '12px',
                background: '#eff6ff',
                borderRadius: '8px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3b82f6' }}>
                  {data.conversion_report.info_count}
                </div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Info</div>
              </div>
              <div style={{ 
                flex: 1, 
                minWidth: '100px',
                padding: '12px',
                background: '#fefce8',
                borderRadius: '8px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#eab308' }}>
                  {data.conversion_report.warning_count}
                </div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Warnungen</div>
              </div>
              <div style={{ 
                flex: 1, 
                minWidth: '100px',
                padding: '12px',
                background: '#fef2f2',
                borderRadius: '8px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>
                  {data.conversion_report.error_count}
                </div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Fehler</div>
              </div>
            </div>

            {/* Warnings */}
            {data.conversion_report.warnings && data.conversion_report.warnings.length > 0 && (
              <div style={{ marginBottom: '16px' }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  marginBottom: '12px',
                  fontSize: '14px',
                  fontWeight: 600,
                  color: '#475569'
                }}>
                  <AlertTriangle size={16} color="#eab308" />
                  Warnungen
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {data.conversion_report.warnings.map((warning, idx) => (
                    <div 
                      key={idx}
                      style={{
                        background: '#fefce8',
                        padding: '12px',
                        borderRadius: '6px',
                        borderLeft: '3px solid #eab308',
                        fontSize: '13px'
                      }}
                    >
                      <div style={{ fontWeight: 600, color: '#854d0e', marginBottom: '4px' }}>
                        {warning.item}
                      </div>
                      <div style={{ color: '#a16207' }}>
                        {warning.message}
                      </div>
                      {warning.alternative && (
                        <div style={{ color: '#65a30d', fontSize: '12px', marginTop: '4px', fontStyle: 'italic' }}>
                          💡 Alternative: {warning.alternative}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Errors */}
            {data.conversion_report.errors && data.conversion_report.errors.length > 0 && (
              <div>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  marginBottom: '12px',
                  fontSize: '14px',
                  fontWeight: 600,
                  color: '#475569'
                }}>
                  <XCircle size={16} color="#ef4444" />
                  Fehler
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {data.conversion_report.errors.map((error, idx) => (
                    <div 
                      key={idx}
                      style={{
                        background: '#fef2f2',
                        padding: '12px',
                        borderRadius: '6px',
                        borderLeft: '3px solid #ef4444',
                        fontSize: '13px'
                      }}
                    >
                      <div style={{ fontWeight: 600, color: '#991b1b', marginBottom: '4px' }}>
                        {error.item}
                      </div>
                      <div style={{ color: '#dc2626' }}>
                        {error.message}
                      </div>
                      {error.alternative && (
                        <div style={{ color: '#65a30d', fontSize: '12px', marginTop: '4px', fontStyle: 'italic' }}>
                          💡 Alternative: {error.alternative}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No Issues */}
            {(!data.conversion_report.warnings || data.conversion_report.warnings.length === 0) && 
             (!data.conversion_report.errors || data.conversion_report.errors.length === 0) && (
              <div style={{
                textAlign: 'center',
                padding: '24px',
                color: '#10b981',
                fontSize: '14px'
              }}>
                <CheckCircle size={32} style={{ margin: '0 auto 8px' }} />
                <div style={{ fontWeight: 600 }}>Keine Probleme gefunden!</div>
                <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                  Die Konvertierung wurde ohne Warnungen oder Fehler abgeschlossen.
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MBZ Download Button - nur wenn verfügbar */}
      {data.moodle_mbz_available && (
        <div style={{
          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
          borderRadius: '12px',
          padding: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 4px 12px rgba(16, 185, 129, 0.2)'
        }}>
          <div style={{ color: 'white' }}>
            <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px' }}>
              ✅ Moodle-Konvertierung erfolgreich!
            </div>
            <div style={{ fontSize: '14px', opacity: 0.9 }}>
              Das konvertierte MBZ-File kann jetzt heruntergeladen werden.
            </div>
          </div>
          <button
            onClick={downloadMBZ}
            style={{
              background: 'white',
              color: '#059669',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              transition: 'transform 0.2s, box-shadow 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
            }}
          >
            <Download size={20} />
            MBZ herunterladen
          </button>
        </div>
      )}

      {/* Info Box */}
      <div style={{
        background: '#fffbeb',
        border: '1px solid #fde047',
        borderRadius: '8px',
        padding: '16px',
        display: 'flex',
        gap: '12px'
      }}>
        <div style={{ color: '#ca8a04', fontSize: '20px' }}>ℹ️</div>
        <div>
          <div style={{ fontWeight: 600, color: '#854d0e', marginBottom: '4px' }}>
            Hinweis
          </div>
          <div style={{ fontSize: '14px', color: '#a16207' }}>
            Dies ist eine vereinfachte ILIAS-Analyse. Für vollständige Metadaten und Dublin Core Informationen,
            aktivieren Sie die Option "In Moodle-Format (MBZ) konvertieren" beim Upload.
          </div>
        </div>
      </div>
    </div>
  );
}

