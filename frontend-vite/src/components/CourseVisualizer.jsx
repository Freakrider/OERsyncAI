import React, { useState } from 'react';
import { 
  BookOpen, 
  MessageSquare, 
  FileText, 
  Video, 
  Users, 
  Award, 
  CheckCircle, 
  Clock,
  Globe,
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
  ChevronRight,
  ChevronDown,
  Layers,
  Info,
  PlayCircle,
  BookMarked,
  GraduationCap,
  Eye,
  EyeOff
} from 'lucide-react';

// Activity Icon Mapping
const activityIcons = {
  forum: MessageSquare,
  choice: BarChart3,
  survey: CheckCircle,
  data: Database,
  bigbluebuttonbn: Video,
  page: FileText,
  resource: Download,
  book: BookOpen,
  glossary: BookMarked,
  h5pactivity: PlayCircle,
  quiz: CheckCircle,
  wiki: Users,
  assign: PenTool,
  scorm: PlayCircle,
  workshop: Users,
  url: ExternalLink,
  lesson: GraduationCap,
  feedback: MessageSquare,
  label: Info,
  folder: File,
  activity: Layers // Default for generic activities
};

// Activity names in German
const activityNames = {
  forum: 'Forum',
  choice: 'Abstimmung',
  survey: 'Umfrage',
  data: 'Datenbank',
  bigbluebuttonbn: 'BigBlueButton',
  page: 'Textseite',
  resource: 'Datei',
  book: 'Buch',
  glossary: 'Glossar',
  h5pactivity: 'H5P',
  quiz: 'Test',
  wiki: 'Wiki',
  assign: 'Aufgabe',
  scorm: 'Lernpaket',
  workshop: 'Gegenseitige Beurteilung',
  url: 'Link/URL',
  lesson: 'Lektion',
  feedback: 'Feedback',
  label: 'Textfeld',
  activity: 'Aktivität'
};

// Main Component
export default function CourseVisualizer({ data }) {
  const [expandedSections, setExpandedSections] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Use provided data
  const courseData = data?.extracted_data || data || {};
  const sections = courseData.sections || [];
  const activities = courseData.activities || [];
  
  // Map activities from the JSON format to a more usable format
  const getMappedSections = () => {
    if (activities.length === 0) return [];
    
    // Group activities by section
    const sectionMap = {};
    activities.forEach(activity => {
      const sectionNum = activity.section_number || 0;
      if (!sectionMap[sectionNum]) {
        sectionMap[sectionNum] = {
          id: sectionNum,
          name: sections[sectionNum]?.name || `Abschnitt ${sectionNum}`,
          activities: []
        };
      }
      
      // Extract activity type from activity_type field
      let activityType = 'activity';
      if (activity.activity_type) {
        activityType = activity.activity_type.replace('activity', '').trim() || 'activity';
      }
      
      sectionMap[sectionNum].activities.push({
        id: activity.activity_id,
        name: activity.module_name,
        type: activityType,
        visible: activity.visible !== false
      });
    });
    
    return Object.values(sectionMap);
  };
  
  const mappedSections = sections.length > 0 ? sections : getMappedSections();
  
  const toggleSection = (sectionId) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  // Format dates
  const formatDate = (dateStr) => {
    if (!dateStr) return null;
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('de-DE', { year: 'numeric', month: 'long', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="flex gap-6 max-w-7xl mx-auto">
      {/* Main Content */}
      <div className="flex-1">
        {/* Course Header */}
        <div className="bg-white rounded-lg shadow-lg mb-6 overflow-hidden">
          <div 
            className="h-48 bg-cover bg-center relative"
            style={{
              backgroundImage: 'url(https://images.unsplash.com/photo-1488190211105-8b0e65b80b4e?w=800&h=400&fit=crop)',
              backgroundColor: '#f0f0f0'
            }}
          >
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
            <div className="absolute bottom-0 left-0 p-6 text-white">
              <span className="inline-block mb-2 px-3 py-1 bg-blue-600 text-white text-sm rounded-full">
                Preview Mode
              </span>
              <h1 className="text-3xl font-bold mb-2">
                {courseData.course_name || 'Digital Literacy'}
              </h1>
              <p className="text-gray-200">
                {courseData.course_summary || 'Introducing the concept of Digital Literacy. Optimised for mobile.'}
              </p>
            </div>
          </div>
          <div className="p-6">
            <div className="flex gap-6 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>Start: {formatDate(courseData.course_start_date) || 'February 26, 2022'}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>End: {formatDate(courseData.course_end_date) || 'November 23, 2023'}</span>
              </div>
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4" />
                <span>{courseData.activities_count || activities.length} Activities</span>
              </div>
            </div>
          </div>
        </div>

        {/* Course Sections */}
        <div className="space-y-4">
          {mappedSections.map((section, idx) => {
            const isExpanded = expandedSections[section.id] !== false; // Default expanded
            const sectionActivities = section.activities || [];
            
            return (
              <div key={section.id || idx} className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div 
                  className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => toggleSection(section.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {isExpanded ? 
                        <ChevronDown className="w-5 h-5 text-gray-500" /> : 
                        <ChevronRight className="w-5 h-5 text-gray-500" />
                      }
                      <h3 className="text-lg font-semibold text-gray-900">
                        {section.name || `Abschnitt ${idx + 1}`}
                      </h3>
                    </div>
                    <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                      {sectionActivities.length} activities
                    </span>
                  </div>
                </div>
                
                {isExpanded && (
                  <div className="px-4 pb-4">
                    <div className="space-y-2 ml-8">
                      {sectionActivities.map((activity, actIdx) => {
                        const IconComponent = activityIcons[activity.type] || activityIcons.activity;
                        const activityTypeName = activityNames[activity.type] || activityNames.activity;
                        
                        return (
                          <div 
                            key={activity.id || actIdx}
                            className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors group"
                          >
                            <div className="flex-shrink-0">
                              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                                <IconComponent className="w-5 h-5 text-blue-600" />
                              </div>
                            </div>
                            <div className="flex-1">
                              <h4 className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                                {activity.name || 'Untitled Activity'}
                              </h4>
                              <p className="text-sm text-gray-500">{activityTypeName}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              {activity.visible ? (
                                <Eye className="w-4 h-4 text-gray-400" />
                              ) : (
                                <EyeOff className="w-4 h-4 text-gray-400" />
                              )}
                              <button className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded opacity-0 group-hover:opacity-100 transition-all">
                                View
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Sidebar */}
      {sidebarOpen && (
        <div className="w-80 space-y-4">
          {/* Course Sections Navigation */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-base font-semibold text-gray-900">Course Sections</h3>
            </div>
            <div className="p-4">
              <nav className="space-y-1">
                <a href="#" className="block px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded">About this course</a>
                <a href="#" className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded">Background reading</a>
                <a href="#" className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded">Group work and assessment</a>
                <a href="#" className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded">Extra resources</a>
                <a href="#" className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded">Self-reflection</a>
              </nav>
            </div>
          </div>

          {/* Key Elements Preview */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-base font-semibold text-gray-900">Key Elements Preview</h3>
              <p className="text-xs text-gray-500 mt-1">Core concepts from the course</p>
            </div>
            <div className="p-4">
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-green-100 rounded flex items-center justify-center flex-shrink-0">
                    <Lightbulb className="w-4 h-4 text-green-600" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium">Creative</h4>
                    <p className="text-xs text-gray-500">Being able to create new content and ideas using digital tools</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-blue-100 rounded flex items-center justify-center flex-shrink-0">
                    <Globe className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium">Cultural</h4>
                    <p className="text-xs text-gray-500">Understanding digital communication in different contexts</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}