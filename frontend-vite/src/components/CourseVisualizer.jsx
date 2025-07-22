import React from 'react';
import ActivityList from './ActivityList';

export default function CourseVisualizer({ data }) {
  if (!data) return null;
  const extracted = data.extracted_data || data;
  const sections = extracted.sections || [];
  const activities = extracted.activities || [];

  // Wenn keine Sections, aber Aktivitäten vorhanden: einfache Liste
  if ((!sections || sections.length === 0) && activities.length > 0) {
    return (
      <div className="course-visualizer">
        <h3>Kurs-Demo-Ansicht</h3>
        <div className="activity-list">
          {activities.map((act, i) => (
            <div key={act.id || i} className="activity-item" style={{ margin: '6px 0' }}>
              <span style={{ marginRight: 8 }}>📄</span>
              {act.name || act.module_name || 'Aktivität'}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Standard: mit Sections
  return (
    <div className="course-visualizer">
      <h3>Kurs-Demo-Ansicht</h3>
      <ActivityList sections={sections} activities={activities} />
    </div>
  );
} 