import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { X, FileText, Clock, User, Calendar } from 'lucide-react';

export default function ActivityPreview({ activity, onClose }) {
  if (!activity) return null;

  // Unterstütze sowohl alte als auch neue Struktur
  const config = activity.activity_config || activity.config;
  const module_name = activity.module_name || activity.name;
  const activity_type = activity.activity_type;

  // Hilfsfunktion zum Bereinigen von HTML-Inhalt
  const cleanHtml = (html) => {
    if (!html) return '';
    // Entferne HTML-Tags für einfache Anzeige
    return html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  };

  // Hilfsfunktion zum Formatieren von Inhalt
  const formatContent = (content) => {
    if (!content) return 'Kein Inhalt verfügbar';
    
    // Entferne HTML-Tags und formatiere
    const cleanContent = cleanHtml(content);
    if (cleanContent.length > 200) {
      return cleanContent.substring(0, 200) + '...';
    }
    return cleanContent;
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

  // Activity-Typ-spezifische Anzeige
  const renderActivityContent = () => {
    if (!config) return <p className="text-muted-foreground">Keine Details verfügbar</p>;

    // Textbasierte Activities (Page, Forum, etc.) - einheitliche Anzeige
    const textBasedActivities = ['page', 'forum', 'label', 'feedback', 'survey', 'choice'];
    if (textBasedActivities.includes(activity_type?.toLowerCase())) {
      return (
        <div className="space-y-4">
          {config.intro && (
            <div>
              <h4 className="font-medium text-foreground mb-2">Einführung</h4>
              <p className="text-sm text-muted-foreground">{formatContent(config.intro)}</p>
            </div>
          )}
          {config.content && (
            <div>
              <h4 className="font-medium text-foreground mb-2">Inhalt</h4>
              <p className="text-sm text-muted-foreground">{formatContent(config.content)}</p>
            </div>
          )}
          {config.description && (
            <div>
              <h4 className="font-medium text-foreground mb-2">Beschreibung</h4>
              <p className="text-sm text-muted-foreground">{formatContent(config.description)}</p>
            </div>
          )}
          {/* Activity-spezifische Zusatzinfos */}
          {activity_type?.toLowerCase() === 'forum' && config.forum_type && (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-foreground">Forum-Typ:</span>
              <Badge variant="outline" className="text-xs">{config.forum_type}</Badge>
            </div>
          )}
          {activity_type?.toLowerCase() === 'quiz' && config.time_limit_seconds && (
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Zeitlimit: {config.time_limit_seconds} Sekunden
              </span>
            </div>
          )}
        </div>
      );
    }

    // Spezielle Activities mit komplexer Struktur
    switch (activity_type?.toLowerCase()) {
      case 'book':
        return (
          <div className="space-y-4">
            {config.intro && (
              <div>
                <h4 className="font-medium text-foreground mb-2">Einführung</h4>
                <p className="text-sm text-muted-foreground">{formatContent(config.intro)}</p>
              </div>
            )}
            {config.chapters && config.chapters.length > 0 && (
              <div>
                <h4 className="font-medium text-foreground mb-2">
                  Kapitel ({config.chapters.length})
                </h4>
                <div className="space-y-2">
                  {config.chapters.map((chapter, index) => (
                    <div key={chapter.id || index} className="p-3 bg-muted/50 rounded-lg">
                      <h5 className="font-medium text-sm text-foreground">{chapter.title}</h5>
                      {chapter.content && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatContent(chapter.content)}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 'quiz':
        return (
          <div className="space-y-4">
            {config.intro && (
              <div>
                <h4 className="font-medium text-foreground mb-2">Einführung</h4>
                <p className="text-sm text-muted-foreground">{formatContent(config.intro)}</p>
              </div>
            )}
            <div className="space-y-2">
              {config.time_limit_seconds && (
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    Zeitlimit: {config.time_limit_seconds} Sekunden
                  </span>
                </div>
              )}
              {config.max_attempts && (
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    Max. Versuche: {config.max_attempts}
                  </span>
                </div>
              )}
              {config.grade_method && (
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    Bewertungsmethode: {config.grade_method}
                  </span>
                </div>
              )}
            </div>
          </div>
        );

      case 'url':
        return (
          <div className="space-y-4">
            {config.intro && (
              <div>
                <h4 className="font-medium text-foreground mb-2">Einführung</h4>
                <p className="text-sm text-muted-foreground">{formatContent(config.intro)}</p>
              </div>
            )}
            {config.externalurl && (
              <div>
                <h4 className="font-medium text-foreground mb-2">URL</h4>
                <a 
                  href={config.externalurl} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline break-all"
                >
                  {config.externalurl}
                </a>
              </div>
            )}
          </div>
        );

      case 'resource':
        return (
          <div className="space-y-4">
            {config.intro && (
              <div>
                <h4 className="font-medium text-foreground mb-2">Einführung</h4>
                <p className="text-sm text-muted-foreground">{formatContent(config.intro)}</p>
              </div>
            )}
            {config.reference && (
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  Referenz: {config.reference}
                </span>
              </div>
            )}
          </div>
        );

      default:
        // Fallback für unbekannte Activity-Typen
        return (
          <div className="space-y-4">
            {config.intro && (
              <div>
                <h4 className="font-medium text-foreground mb-2">Einführung</h4>
                <p className="text-sm text-muted-foreground">{formatContent(config.intro)}</p>
              </div>
            )}
            {config.content && (
              <div>
                <h4 className="font-medium text-foreground mb-2">Inhalt</h4>
                <p className="text-sm text-muted-foreground">{formatContent(config.content)}</p>
              </div>
            )}
            {config.description && (
              <div>
                <h4 className="font-medium text-foreground mb-2">Beschreibung</h4>
                <p className="text-sm text-muted-foreground">{formatContent(config.description)}</p>
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <div className="activity-preview">
      <Card className="activity-preview-content">
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-xl">{module_name}</CardTitle>
              <div className="flex items-center gap-2 mt-2">
                <Badge 
                  variant="outline" 
                  className={`text-xs ${getActivityTypeColor(activity_type)}`}
                >
                  {activity_type}
                </Badge>
                {activity.time_created && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Calendar className="w-3 h-3" />
                    {new Date(activity.time_created).toLocaleDateString('de-DE')}
                  </div>
                )}
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {renderActivityContent()}
        </CardContent>
      </Card>
    </div>
  );
} 