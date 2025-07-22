import React, { useState } from 'react';

// Dummy-Icon-Komponente (später ersetzen)
function ActivityIcon() {
  return <span style={{ marginRight: 8 }}>📄</span>;
}

export default function ActivityList({ sections = [], activities = [] }) {
  const [openSection, setOpenSection] = useState(null);

  // Erstelle ein Mapping von Activity-ID zu Activity-Objekt
  const activitiesById = activities.reduce((acc, act) => {
    acc[act.activity_id || act.id] = act;
    return acc;
  }, {});

  return (
    <div className="activity-list">
      {sections.map((section, idx) => (
        <div key={section.id || idx} className="section">
          <div
            className="section-header"
            onClick={() => setOpenSection(openSection === idx ? null : idx)}
            style={{ cursor: 'pointer', fontWeight: 'bold', margin: '10px 0' }}
          >
            {section.name || `Abschnitt ${idx + 1}`}
            <span style={{ float: 'right' }}>{openSection === idx ? '▼' : '▶'}</span>
          </div>
          {openSection === idx && (
            <div className="section-activities" style={{ marginLeft: 20 }}>
              {(section.activities || []).map((activityId, i) => {
                const activity = activitiesById[activityId];
                return (
                  <div key={activityId || i} className="activity-item" style={{ margin: '6px 0' }}>
                    <ActivityIcon />
                    {activity ? (activity.module_name || activity.name || 'Aktivität') : `Aktivität ${activityId}`}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ))}
    </div>
  );
} 