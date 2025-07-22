import React from 'react';

function MetadataCard({ title, children }) {
  return (
    <div className="metadata-card">
      <h3>{title}</h3>
      {children}
    </div>
  );
}

export default function MetadataDisplay({ data }) {
  if (!data) return null;
  const extractedData = data.extracted_data || data;
  const dublin = extractedData.dublin_core || {};
  const edu = extractedData.educational || {};
  return (
    <div className="results">
      {/* Backup & Technische Details */}
      <MetadataCard title="Backup & Technische Details">
        <div className="metadata-item"><div className="metadata-label">Job ID:</div><div className="metadata-value"><code>{data.job_id || 'N/A'}</code></div></div>
        <div className="metadata-item"><div className="metadata-label">Dateiname:</div><div className="metadata-value">{data.file_name || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Dateigröße:</div><div className="metadata-value">{data.file_size ? (data.file_size / 1024).toFixed(1) + ' KB' : 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Backup-Datum:</div><div className="metadata-value">{extractedData.backup_date ? new Date(extractedData.backup_date).toLocaleString('de-DE') : 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Backup-Version:</div><div className="metadata-value">{extractedData.backup_version || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Verarbeitung gestartet:</div><div className="metadata-value">{data.created_at ? new Date(data.created_at).toLocaleString('de-DE') : 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Verarbeitung abgeschlossen:</div><div className="metadata-value">{data.completed_at ? new Date(data.completed_at).toLocaleString('de-DE') : 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Verarbeitungszeit:</div><div className="metadata-value">{data.processing_time_seconds ? `${(data.processing_time_seconds * 1000).toFixed(0)} ms` : 'N/A'}</div></div>
      </MetadataCard>
      {/* Kurs-Details */}
      <MetadataCard title="Kurs-Details">
        <div className="metadata-item"><div className="metadata-label">Kurs-ID:</div><div className="metadata-value">{extractedData.course_id || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Format:</div><div className="metadata-value">{extractedData.course_format || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Sprache:</div><div className="metadata-value">{extractedData.course_language || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Startdatum:</div><div className="metadata-value">{extractedData.course_start_date ? new Date(extractedData.course_start_date).toLocaleDateString('de-DE') : 'Nicht gesetzt'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Enddatum:</div><div className="metadata-value">{extractedData.course_end_date ? new Date(extractedData.course_end_date).toLocaleDateString('de-DE') : 'Nicht gesetzt'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Sichtbarkeit:</div><div className="metadata-value">{extractedData.course_visible ? 'Sichtbar' : 'Versteckt'}</div></div>
      </MetadataCard>
      {/* Dublin Core Metadaten */}
      <MetadataCard title="Dublin Core Metadaten">
        <div className="metadata-item"><div className="metadata-label">Titel:</div><div className="metadata-value">{dublin.title || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Ersteller:</div><div className="metadata-value">{Array.isArray(dublin.creator) ? dublin.creator.map((c, i) => <span className="tag" key={i}>{c}</span>) : (dublin.creator || 'N/A')}</div></div>
        <div className="metadata-item"><div className="metadata-label">Beschreibung:</div><div className="metadata-value">{dublin.description || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Herausgeber:</div><div className="metadata-value">{dublin.publisher || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Mitwirkende:</div><div className="metadata-value">{Array.isArray(dublin.contributor) && dublin.contributor.length ? dublin.contributor.map((c, i) => <span className="tag" key={i}>{c}</span>) : 'Keine'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Datum:</div><div className="metadata-value">{dublin.date ? new Date(dublin.date).toLocaleDateString('de-DE') : 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Typ:</div><div className="metadata-value">{dublin.type || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Format:</div><div className="metadata-value">{dublin.format || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Identifikator:</div><div className="metadata-value"><code>{dublin.identifier || 'N/A'}</code></div></div>
        <div className="metadata-item"><div className="metadata-label">Quelle:</div><div className="metadata-value">{dublin.source || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Sprache:</div><div className="metadata-value">{dublin.language || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Beziehungen:</div><div className="metadata-value">{Array.isArray(dublin.relation) && dublin.relation.length ? dublin.relation.map((r, i) => <span className="tag" key={i}>{r}</span>) : 'Keine'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Abdeckung:</div><div className="metadata-value">{dublin.coverage || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Rechte:</div><div className="metadata-value">{dublin.rights || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Themen:</div><div className="metadata-value">{Array.isArray(dublin.subject) ? dublin.subject.map((s, i) => <span className="tag" key={i}>{s}</span>) : (dublin.subject || 'N/A')}</div></div>
      </MetadataCard>
      {/* Educational Metadaten */}
      {edu && (
        <MetadataCard title="Educational Metadaten">
          <div className="metadata-item"><div className="metadata-label">Lernressourcentyp:</div><div className="metadata-value">{edu.learning_resource_type || 'N/A'}</div></div>
          <div className="metadata-item"><div className="metadata-label">Kontext:</div><div className="metadata-value">{edu.context || 'N/A'}</div></div>
          <div className="metadata-item"><div className="metadata-label">Schwierigkeit:</div><div className="metadata-value">{edu.difficulty || 'N/A'}</div></div>
          <div className="metadata-item"><div className="metadata-label">Zielgruppe:</div><div className="metadata-value">{Array.isArray(edu.intended_end_user_role) ? edu.intended_end_user_role.map((r, i) => <span className="tag" key={i}>{r}</span>) : (edu.intended_end_user_role || 'N/A')}</div></div>
          {edu.typical_age_range && <div className="metadata-item"><div className="metadata-label">Typische Altersgruppe:</div><div className="metadata-value">{edu.typical_age_range}</div></div>}
          {edu.typical_learning_time && <div className="metadata-item"><div className="metadata-label">Typische Lernzeit:</div><div className="metadata-value">{edu.typical_learning_time}</div></div>}
          {edu.language && <div className="metadata-item"><div className="metadata-label">Unterrichtssprache:</div><div className="metadata-value">{edu.language}</div></div>}
        </MetadataCard>
      )}
      {/* Verarbeitungsstatus */}
      <MetadataCard title="Verarbeitungsstatus">
        <div className="metadata-item"><div className="metadata-label">Status:</div><div className="metadata-value"><span className="tag" style={{ background: '#10b981' }}>{data.status || 'N/A'}</span></div></div>
        <div className="metadata-item"><div className="metadata-label">Job erstellt:</div><div className="metadata-value">{data.created_at ? new Date(data.created_at).toLocaleString('de-DE') : 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Abgeschlossen:</div><div className="metadata-value">{data.completed_at ? new Date(data.completed_at).toLocaleString('de-DE') : 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Performance:</div><div className="metadata-value">{data.processing_time_seconds && data.file_size ? `${(data.file_size / 1024 / data.processing_time_seconds).toFixed(0)} KB/s` : 'N/A'}</div></div>
      </MetadataCard>
    </div>
  );
} 