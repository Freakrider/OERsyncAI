import { Badge } from './ui/badge';

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
      {/* Plugin-Details */}
      <MetadataCard title="Plugin-Details">
        <div className="metadata-item"><div className="metadata-label">Activities:</div><div className="metadata-value">
            {extractedData.required_plugins.activities?.length ? extractedData.required_plugins.activities.map((plugin, i) => (<Badge key={i}>{plugin}</Badge>)) : 'Keine'}
        </div></div>
        <div className="metadata-item"><div className="metadata-label">Blocks:</div><div className="metadata-value">
            {extractedData.required_plugins.blocks?.length ? extractedData.required_plugins.blocks.map((plugin, i) => (<Badge key={i}>{plugin}</Badge>)) : 'Keine'}
        </div></div>
        <div className="metadata-item"><div className="metadata-label">Contentbank:</div><div className="metadata-value">
            {extractedData.required_plugins.contentbank?.length ? extractedData.required_plugins.contentbank.map((plugin, i) => (<Badge key={i}>{plugin}</Badge>)) : 'Keine'}
        </div></div>
      </MetadataCard>
      {/* Dublin Core Metadaten */}
      <MetadataCard title="Dublin Core Metadaten">
        <div className="metadata-item"><div className="metadata-label">Titel:</div><div className="metadata-value">{dublin.title || 'N/A'}</div></div>
        <div className="metadata-item"><div className="metadata-label">Ersteller:</div><div className="metadata-value">{Array.isArray(dublin.creator) ? dublin.creator.map((c, i) => <span className="tag" key={i}>{c}</span>) : (dublin.creator || 'N/A')}</div></div>
        <div className="metadata-item"><div className="metadata-label">Beschreibung:</div>
            <div className="metadata-value">
                <div
                    className="moodle-html prose prose-invert max-w-none mt-2"
                    dangerouslySetInnerHTML={{
                        __html: dublin.description,
                    }}
                />
            </div>
        </div>
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
      {/* KI generated data */}
      <MetadataCard title="KI generierte Daten">
        <div className="metadata-item">
            <div className="metadata-label">Passende Kurstags:</div>
            <div className="metadata-value">
            {Array.isArray(extractedData.ai_results.tags) && extractedData.ai_results.tags.length
                ? extractedData.ai_results.tags.map((label, i) => (<Badge key={i}>{label}</Badge>))
                : 'Keine'}
            </div>
        </div>
        <div className="metadata-item">
            <div className="metadata-label">Didaktische Analyse:</div>
            <div className="metadata-value prose max-w-none">
                {extractedData.ai_results.didactical_evaluation
                ? extractedData.ai_results.didactical_evaluation
                    .split(/\n\s*\n/)  // split on blank lines
                    .map((para, i) => <p key={i}>{para.trim()}</p>)
                : 'Keine Analyse verfügbar'}
            </div>
        </div>
        <div className="metadata-item">
            <div className="metadata-label">Änderungsvorschlag:</div>
            <div className="metadata-value prose max-w-none">
                {extractedData.ai_results.restructuring_suggestions
                ? extractedData.ai_results.restructuring_suggestions
                    .split(/\n\s*\n/)  // split on blank lines
                    .map((para, i) => <p key={i}>{para.trim()}</p>)
                : 'Keine Analyse verfügbar'}
            </div>
        </div>
      </MetadataCard>
      {Array.isArray(extractedData.ai_results.user_timeline) && extractedData.ai_results.user_timeline.length > 0 && (
        <MetadataCard title="Empfohlene Zeitleiste">
            <div className="relative pl-10 mt-4">
                {/* SVG Arrow Line */}
                <svg
                    className="absolute left-3 top-0 bottom-0 w-6 h-[calc(100%-20px)] overflow-visible"
                    width="24"
                    viewBox="0 0 24 1000"
                    preserveAspectRatio="none"
                >
                    <defs>
                        <marker
                            id="arrowhead"
                            markerWidth="10"
                            markerHeight="7"
                            refX="3"
                            refY="3.5"
                            orient="auto"
                        >
                            <polygon points="0 0, 10 3.5, 0 7" fill="#9CA3AF" />
                        </marker>
                    </defs>
                    <line
                        x1="12"
                        y1="0"
                        x2="12"
                        y2="1000"
                        stroke="#9CA3AF"
                        strokeWidth="2"
                        strokeDasharray="5,5"
                        markerEnd="url(#arrowhead)"
                    />
                </svg>


                {/* Start Marker */}
                <div className="relative mb-6">
                    <div className="absolute -left-2 top-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white shadow" />
                    <div className="text-m text-gray-600 pl-4 italic">Start der Kurszeitleiste</div>
                </div>

                {/* Timeline Items */}
                {extractedData.ai_results.user_timeline.map((item, i) => (
                    <div key={i} className="relative group mb-6">
                        <div className="absolute -left-2 top-1 w-4 h-4 bg-blue-600 rounded-full border-2 border-white shadow-md group-hover:scale-110 transition-transform" />
                        <div className="bg-white shadow-sm rounded-xl p-4 border border-gray-100 hover:border-blue-300 transition">
                            <div className="flex justify-between items-center mb-1">
                                <h4 className="font-semibold text-gray-800">{item.name}</h4>
                                <span className="text-sm text-gray-500">{item.estimated_duration}</span>
                            </div>
                            {item.notes && <p className="text-sm text-gray-600">{item.notes}</p>}
                        </div>
                    </div>
                ))}


                {/* End Marker */}
                <div className="relative flex items-center space-x-2">
                <div className="text-m text-gray-600 pl-4 italic">🏁 Kurs abgeschlossen</div>
                </div>
            </div>
        </MetadataCard>
        )}
    </div>
  );
}