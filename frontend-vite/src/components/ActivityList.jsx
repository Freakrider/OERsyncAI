import React, { useState } from 'react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { 
  ChevronDown, 
  ChevronRight,
  MessageSquare, 
  FileText, 
  Video, 
  Users, 
  CheckCircle, 
  Download,
  ExternalLink,
  HelpCircle,
  PenTool,
  BarChart3,
  Lightbulb,
  File,
  Image,
  Music,
  Presentation,
  Database,
  Settings,
  Calendar,
  Star,
  Zap,
  BookOpen
} from 'lucide-react';
import ActivityPreview from './ActivityPreview';

// Activity Icon Mapping mit Lucide Icons
const activityIcons = {
  forum: MessageSquare,
  choice: BarChart3,
  survey: FileText,
  data: Database,
  bigbluebuttonbn: Video,
  page: FileText,
  resource: Download,
  book: BookOpen,
  glossary: FileText,
  h5pactivity: HelpCircle,
  quiz: CheckCircle,
  wiki: Users,
  assign: PenTool,
  scorm: Video,
  workshop: Users,
  url: ExternalLink,
  lesson: Lightbulb,
  feedback: MessageSquare,
  label: FileText,
  folder: File,
  image: Image,
  audio: Music,
  presentation: Presentation,
  settings: Settings,
  calendar: Calendar,
  star: Star,
  zap: Zap
};

// Activity Type Color Mapping
const getActivityTypeColor = (type) => {
  const colors = {
    forum: 'bg-blue-100 text-blue-800 border-blue-200',
    choice: 'bg-green-100 text-green-800 border-green-200',
    survey: 'bg-purple-100 text-purple-800 border-purple-200',
    data: 'bg-orange-100 text-orange-800 border-orange-200',
    bigbluebuttonbn: 'bg-red-100 text-red-800 border-red-200',
    page: 'bg-indigo-100 text-indigo-800 border-indigo-200',
    resource: 'bg-gray-100 text-gray-800 border-gray-200',
    book: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    glossary: 'bg-pink-100 text-pink-800 border-pink-200',
    h5pactivity: 'bg-cyan-100 text-cyan-800 border-cyan-200',
    quiz: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    wiki: 'bg-violet-100 text-violet-800 border-violet-200',
    assign: 'bg-rose-100 text-rose-800 border-rose-200',
    scorm: 'bg-amber-100 text-amber-800 border-amber-200',
    workshop: 'bg-teal-100 text-teal-800 border-teal-200',
    url: 'bg-slate-100 text-slate-800 border-slate-200',
    lesson: 'bg-lime-100 text-lime-800 border-lime-200',
    feedback: 'bg-fuchsia-100 text-fuchsia-800 border-fuchsia-200',
    label: 'bg-neutral-100 text-neutral-800 border-neutral-200'
  };
  return colors[type] || 'bg-gray-100 text-gray-800 border-gray-200';
};

export default function ActivityList({ sections = [], activities = [] }) {
  const [openSection, setOpenSection] = useState(null);
  const [selectedActivity, setSelectedActivity] = useState(null);

  // Erstelle ein Mapping von Activity-ID zu Activity-Objekt
  const activitiesById = activities.reduce((acc, act) => {
    // Unterstütze sowohl alte als auch neue Struktur
    const activityId = act.activity_id || act.id;
    acc[activityId] = act;
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      {sections.map((section, idx) => {
        const sectionActivities = (section.activities || []).map(id => activitiesById[id]).filter(Boolean);
        const activityCount = sectionActivities.length;
        const isOpen = openSection === idx;
        
        return (
          <div key={section.id || idx} className="border rounded-lg bg-card">
            <div
              className="section-header"
              onClick={() => setOpenSection(isOpen ? null : idx)}
            >
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                    <BookOpen className="w-4 h-4 text-primary" />
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-foreground">
                    {section.name || `Abschnitt ${idx + 1}`}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {activityCount} Aktivität{activityCount !== 1 ? 'en' : ''}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">
                  {activityCount}
                </Badge>
                {isOpen ? (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                )}
              </div>
            </div>
            
            {isOpen && (
              <div className="border-t bg-muted/30">
                <div className="p-4 space-y-3">
                  {sectionActivities.map((activity, i) => {
                    const IconComponent = activityIcons[activity.activity_type] || FileText;
                    return (
                      <div 
                        key={activity.activity_id || activity.id || i} 
                        className="activity-card"
                        onClick={() => setSelectedActivity(activity)}
                      >
                        <div className="flex-shrink-0">
                          <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <IconComponent className="w-5 h-5 text-primary" />
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-foreground truncate">
                            {activity.module_name || activity.name || 'Aktivität'}
                          </h4>
                          {activity.activity_type && (
                            <div className="mt-1">
                              <Badge 
                                variant="outline" 
                                className={`text-xs ${getActivityTypeColor(activity.activity_type)}`}
                              >
                                {activity.activity_type}
                              </Badge>
                            </div>
                          )}
                        </div>
                        <Button variant="ghost" size="sm">
                          <ExternalLink className="w-4 h-4" />
                        </Button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        );
      })}
      
      {selectedActivity && (
        <ActivityPreview 
          activity={selectedActivity} 
          onClose={() => setSelectedActivity(null)} 
        />
      )}
    </div>
  );
} 