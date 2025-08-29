import React, { useState, useRef } from 'react';
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
  const exportRef = useRef();
  
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

  // Exportfunktion für HTML
  const exportAsHtml = () => {
    const content = exportRef.current.innerHTML;
    const css = `*,:before,:after{--tw-border-spacing-x: 0;--tw-border-spacing-y: 0;--tw-translate-x: 0;--tw-translate-y: 0;--tw-rotate: 0;--tw-skew-x: 0;--tw-skew-y: 0;--tw-scale-x: 1;--tw-scale-y: 1;--tw-pan-x: ;--tw-pan-y: ;--tw-pinch-zoom: ;--tw-scroll-snap-strictness: proximity;--tw-gradient-from-position: ;--tw-gradient-via-position: ;--tw-gradient-to-position: ;--tw-ordinal: ;--tw-slashed-zero: ;--tw-numeric-figure: ;--tw-numeric-spacing: ;--tw-numeric-fraction: ;--tw-ring-inset: ;--tw-ring-offset-width: 0px;--tw-ring-offset-color: #fff;--tw-ring-color: rgb(59 130 246 / .5);--tw-ring-offset-shadow: 0 0 #0000;--tw-ring-shadow: 0 0 #0000;--tw-shadow: 0 0 #0000;--tw-shadow-colored: 0 0 #0000;--tw-blur: ;--tw-brightness: ;--tw-contrast: ;--tw-grayscale: ;--tw-hue-rotate: ;--tw-invert: ;--tw-saturate: ;--tw-sepia: ;--tw-drop-shadow: ;--tw-backdrop-blur: ;--tw-backdrop-brightness: ;--tw-backdrop-contrast: ;--tw-backdrop-grayscale: ;--tw-backdrop-hue-rotate: ;--tw-backdrop-invert: ;--tw-backdrop-opacity: ;--tw-backdrop-saturate: ;--tw-backdrop-sepia: ;--tw-contain-size: ;--tw-contain-layout: ;--tw-contain-paint: ;--tw-contain-style: }::backdrop{--tw-border-spacing-x: 0;--tw-border-spacing-y: 0;--tw-translate-x: 0;--tw-translate-y: 0;--tw-rotate: 0;--tw-skew-x: 0;--tw-skew-y: 0;--tw-scale-x: 1;--tw-scale-y: 1;--tw-pan-x: ;--tw-pan-y: ;--tw-pinch-zoom: ;--tw-scroll-snap-strictness: proximity;--tw-gradient-from-position: ;--tw-gradient-via-position: ;--tw-gradient-to-position: ;--tw-ordinal: ;--tw-slashed-zero: ;--tw-numeric-figure: ;--tw-numeric-spacing: ;--tw-numeric-fraction: ;--tw-ring-inset: ;--tw-ring-offset-width: 0px;--tw-ring-offset-color: #fff;--tw-ring-color: rgb(59 130 246 / .5);--tw-ring-offset-shadow: 0 0 #0000;--tw-ring-shadow: 0 0 #0000;--tw-shadow: 0 0 #0000;--tw-shadow-colored: 0 0 #0000;--tw-blur: ;--tw-brightness: ;--tw-contrast: ;--tw-grayscale: ;--tw-hue-rotate: ;--tw-invert: ;--tw-saturate: ;--tw-sepia: ;--tw-drop-shadow: ;--tw-backdrop-blur: ;--tw-backdrop-brightness: ;--tw-backdrop-contrast: ;--tw-backdrop-grayscale: ;--tw-backdrop-hue-rotate: ;--tw-backdrop-invert: ;--tw-backdrop-opacity: ;--tw-backdrop-saturate: ;--tw-backdrop-sepia: ;--tw-contain-size: ;--tw-contain-layout: ;--tw-contain-paint: ;--tw-contain-style: }*,:before,:after{box-sizing:border-box;border-width:0;border-style:solid;border-color:#e5e7eb}:before,:after{--tw-content: ""}html,:host{line-height:1.5;-webkit-text-size-adjust:100%;-moz-tab-size:4;-o-tab-size:4;tab-size:4;font-family:ui-sans-serif,system-ui,sans-serif,"Apple Color Emoji","Segoe UI Emoji",Segoe UI Symbol,"Noto Color Emoji";font-feature-settings:normal;font-variation-settings:normal;-webkit-tap-highlight-color:transparent}body{margin:0;line-height:inherit}hr{height:0;color:inherit;border-top-width:1px}abbr:where([title]){-webkit-text-decoration:underline dotted;text-decoration:underline dotted}h1,h2,h3,h4,h5,h6{font-size:inherit;font-weight:inherit}a{color:inherit;text-decoration:inherit}b,strong{font-weight:bolder}code,kbd,samp,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,Liberation Mono,Courier New,monospace;font-feature-settings:normal;font-variation-settings:normal;font-size:1em}small{font-size:80%}sub,sup{font-size:75%;line-height:0;position:relative;vertical-align:baseline}sub{bottom:-.25em}sup{top:-.5em}table{text-indent:0;border-color:inherit;border-collapse:collapse}button,input,optgroup,select,textarea{font-family:inherit;font-feature-settings:inherit;font-variation-settings:inherit;font-size:100%;font-weight:inherit;line-height:inherit;letter-spacing:inherit;color:inherit;margin:0;padding:0}button,select{text-transform:none}button,input:where([type=button]),input:where([type=reset]),input:where([type=submit]){-webkit-appearance:button;background-color:transparent;background-image:none}:-moz-focusring{outline:auto}:-moz-ui-invalid{box-shadow:none}progress{vertical-align:baseline}::-webkit-inner-spin-button,::-webkit-outer-spin-button{height:auto}[type=search]{-webkit-appearance:textfield;outline-offset:-2px}::-webkit-search-decoration{-webkit-appearance:none}::-webkit-file-upload-button{-webkit-appearance:button;font:inherit}summary{display:list-item}blockquote,dl,dd,h1,h2,h3,h4,h5,h6,hr,figure,p,pre{margin:0}fieldset{margin:0;padding:0}legend{padding:0}ol,ul,menu{list-style:none;margin:0;padding:0}dialog{padding:0}textarea{resize:vertical}input::-moz-placeholder,textarea::-moz-placeholder{opacity:1;color:#9ca3af}input::placeholder,textarea::placeholder{opacity:1;color:#9ca3af}button,[role=button]{cursor:pointer}:disabled{cursor:default}img,svg,video,canvas,audio,iframe,embed,object{display:block;vertical-align:middle}img,video{max-width:100%;height:auto}[hidden]:where(:not([hidden=until-found])){display:none}:root{--background: 0 0% 100%;--foreground: 222.2 84% 4.9%;--card: 0 0% 100%;--card-foreground: 222.2 84% 4.9%;--popover: 0 0% 100%;--popover-foreground: 222.2 84% 4.9%;--primary: 221.2 83.2% 53.3%;--primary-foreground: 210 40% 98%;--secondary: 210 40% 96%;--secondary-foreground: 222.2 47.4% 11.2%;--muted: 210 40% 96%;--muted-foreground: 215.4 16.3% 46.9%;--accent: 210 40% 96%;--accent-foreground: 222.2 47.4% 11.2%;--destructive: 0 84.2% 60.2%;--destructive-foreground: 210 40% 98%;--border: 214.3 31.8% 91.4%;--input: 214.3 31.8% 91.4%;--ring: 221.2 83.2% 53.3%;--radius: .5rem}*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial,sans-serif;background:linear-gradient(135deg,#fbfcfd,#f4f7fb);min-height:100vh;color:#2c3e50;line-height:1.6;position:relative;overflow-x:hidden}body:before{content:"";position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle at 20% 50%,rgba(41,68,102,.03) 0%,transparent 50%),radial-gradient(circle at 80% 20%,rgba(41,68,102,.03) 0%,transparent 50%),radial-gradient(circle at 40% 80%,rgba(41,68,102,.02) 0%,transparent 50%);pointer-events:none;z-index:-1}*{border-color:hsl(var(--border))}body{background-color:hsl(var(--background));color:hsl(var(--foreground))}html{scroll-behavior:smooth}::-webkit-scrollbar{width:8px}::-webkit-scrollbar-track{background:#f1f5f980}::-webkit-scrollbar-thumb{background:#2944664d;border-radius:4px}::-webkit-scrollbar-thumb:hover{background:#29446680}.container{width:100%}@media (min-width: 640px){.container{max-width:640px}}@media (min-width: 768px){.container{max-width:768px}}@media (min-width: 1024px){.container{max-width:1024px}}@media (min-width: 1280px){.container{max-width:1280px}}@media (min-width: 1536px){.container{max-width:1536px}}.container{max-width:900px;margin:40px auto;background:#ffffffd9;-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border-radius:16px;box-shadow:0 8px 32px #2944661f,0 2px 8px #29446614;overflow:hidden;border:1px solid rgba(255,255,255,.2);animation:slideInUp .6s ease-out}@keyframes slideInUp{0%{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}.header{background:linear-gradient(135deg,#294466,#1e3248);color:#fff;padding:50px 40px;text-align:center;position:relative;overflow:hidden}.header:before{content:"";position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(45deg,transparent 30%,rgba(255,255,255,.1) 50%,transparent 70%);transform:translate(-100%);animation:shimmer 3s ease-in-out infinite}@keyframes shimmer{0%{transform:translate(-100%)}50%{transform:translate(100%)}to{transform:translate(100%)}}.header h1{font-size:2.4em;font-weight:200;margin-bottom:12px;letter-spacing:-.8px;position:relative;z-index:1;text-shadow:0 2px 4px rgba(0,0,0,.1)}.header p{font-size:1.1em;opacity:.9;font-weight:300;position:relative;z-index:1}.tab-button{display:inline-flex;align-items:center;justify-content:center;white-space:nowrap;border-radius:calc(var(--radius) - 2px);padding:.375rem .75rem;font-size:.875rem;line-height:1.25rem;font-weight:500;--tw-ring-offset-color: hsl(var(--background));transition-property:all;transition-timing-function:cubic-bezier(.4,0,.2,1);transition-duration:.15s}.tab-button:focus-visible{outline:2px solid transparent;outline-offset:2px;--tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color);--tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(2px + var(--tw-ring-offset-width)) var(--tw-ring-color);box-shadow:var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow, 0 0 #0000);--tw-ring-color: hsl(var(--ring));--tw-ring-offset-width: 2px}.tab-button:disabled{pointer-events:none;opacity:.5}.tab-button.active{background-color:hsl(var(--primary));color:hsl(var(--primary-foreground));--tw-shadow: 0 1px 2px 0 rgb(0 0 0 / .05);--tw-shadow-colored: 0 1px 2px 0 var(--tw-shadow-color);box-shadow:var(--tw-ring-offset-shadow, 0 0 #0000),var(--tw-ring-shadow, 0 0 #0000),var(--tw-shadow)}.tab-button:not(.active){background-color:transparent;color:hsl(var(--muted-foreground))}.tab-button:not(.active):hover{background-color:hsl(var(--accent));color:hsl(var(--accent-foreground))}.activity-card{display:flex;cursor:pointer;align-items:center;gap:1rem;border-radius:var(--radius);border-width:1px;padding:1rem;transition-property:color,background-color,border-color,text-decoration-color,fill,stroke;transition-timing-function:cubic-bezier(.4,0,.2,1);transition-duration:.15s}.activity-card:hover{background-color:hsl(var(--accent) / .5)}.section-header{display:flex;cursor:pointer;align-items:center;justify-content:space-between;padding:1rem;transition-property:color,background-color,border-color,text-decoration-color,fill,stroke;transition-timing-function:cubic-bezier(.4,0,.2,1);transition-duration:.15s}.section-header:hover{background-color:hsl(var(--accent) / .5)}.activity-preview{position:fixed;top:0;right:0;bottom:0;left:0;z-index:50;display:flex;align-items:center;justify-content:center;background-color:#00000080}.activity-preview-content{position:relative;max-height:80vh;max-width:42rem;overflow:auto;border-radius:var(--radius);background-color:hsl(var(--background));padding:1.5rem;--tw-shadow: 0 10px 15px -3px rgb(0 0 0 / .1), 0 4px 6px -4px rgb(0 0 0 / .1);--tw-shadow-colored: 0 10px 15px -3px var(--tw-shadow-color), 0 4px 6px -4px var(--tw-shadow-color);box-shadow:var(--tw-ring-offset-shadow, 0 0 #0000),var(--tw-ring-shadow, 0 0 #0000),var(--tw-shadow)}.upload-section{background:linear-gradient(135deg,#f8f9fbcc,#f1f5f999);border:2px dashed rgba(41,68,102,.2);border-radius:12px;padding:60px 40px;text-align:center;margin-bottom:50px;transition:all .3s cubic-bezier(.4,0,.2,1);-webkit-backdrop-filter:blur(5px);backdrop-filter:blur(5px);position:relative;overflow:hidden}.upload-section:before{content:"";position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(135deg,rgba(41,68,102,.05) 0%,transparent 100%);opacity:0;transition:opacity .3s ease}.upload-section:hover:before{opacity:1}.upload-section:hover{border-color:#29446666;transform:translateY(-2px);box-shadow:0 12px 28px #29446626}.upload-section.dragover{border-color:#294466;background:linear-gradient(135deg,#29446614,#2944660a);transform:scale(1.01);box-shadow:0 8px 25px #29446633}.upload-section h2{color:#294466;font-size:1.5em;font-weight:300;margin-bottom:15px;position:relative;z-index:1}.upload-section p{color:#64748b;margin-bottom:30px;font-size:1em;position:relative;z-index:1}.upload-btn{background:linear-gradient(135deg,#294466,#1e3248);color:#fff;border:none;padding:14px 28px;border-radius:8px;cursor:pointer;font-size:.95em;font-weight:500;transition:all .3s cubic-bezier(.4,0,.2,1);margin:0 10px;min-width:150px;position:relative;overflow:hidden;z-index:1}.upload-btn:before{content:"";position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(135deg,rgba(255,255,255,.1) 0%,transparent 100%);opacity:0;transition:opacity .3s ease}.upload-btn:hover:before{opacity:1}.upload-btn:hover{transform:translateY(-2px);box-shadow:0 8px 20px #2944664d}.upload-btn:active{transform:translateY(0)}.upload-btn:disabled{background:linear-gradient(135deg,#cbd5e1,#94a3b8);cursor:not-allowed;transform:none;box-shadow:none}.status{padding:24px;border-radius:8px;margin:40px 0;font-weight:400;border-left:4px solid;-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);animation:slideInLeft .4s ease-out}@keyframes slideInLeft{0%{opacity:0;transform:translate(-20px)}to{opacity:1;transform:translate(0)}}.status.loading{background:linear-gradient(135deg,#fef3cde6,#fde68ab3);border-color:#f59e0b;color:#92400e}.status.success{background:linear-gradient(135deg,#d1fae5e6,#a7f3d0b3);border-color:#10b981;color:#065f46}.status.error{background:linear-gradient(135deg,#fee2e2e6,#fca5a5b3);border-color:#ef4444;color:#991b1b}.course-summary{background:linear-gradient(135deg,#294466,#1e3248);color:#fff;border-radius:12px;padding:40px;margin:30px 0;position:relative;overflow:hidden;box-shadow:0 8px 32px #2944664d}.course-summary:before{content:"";position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(45deg,transparent 30%,rgba(255,255,255,.1) 50%,transparent 70%);transform:translate(-100%);animation:courseSummaryShimmer 4s ease-in-out infinite}@keyframes courseSummaryShimmer{0%,90%,to{transform:translate(-100%)}45%{transform:translate(100%)}}.course-summary h2{margin-bottom:20px;font-size:1.7em;font-weight:300;letter-spacing:-.4px;position:relative;z-index:1;text-shadow:0 2px 4px rgba(0,0,0,.1)}.course-summary p{opacity:.9;margin-bottom:10px;font-size:.95em;position:relative;z-index:1}.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:30px;margin-top:35px}.stat-card{background:#ffffff26;-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border-radius:8px;padding:30px 25px;text-align:center;border:1px solid rgba(255,255,255,.2);transition:all .3s cubic-bezier(.4,0,.2,1);position:relative;z-index:1}.stat-card:hover{transform:translateY(-3px);background:#fff3;box-shadow:0 8px 16px #0000001a}.stat-number{font-size:2em;font-weight:200;margin-bottom:10px;letter-spacing:-.8px;display:block;animation:countUp .8s ease-out}@keyframes countUp{0%{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}.stat-label{opacity:.9;font-size:.85em;font-weight:400}.metadata-card{background:#ffffffb3;-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border:1px solid rgba(229,231,235,.5);border-radius:12px;padding:35px;margin:30px 0;border-left:4px solid #294466;transition:all .3s cubic-bezier(.4,0,.2,1);position:relative;overflow:hidden}.metadata-card:before{content:"";position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(135deg,rgba(41,68,102,.02) 0%,transparent 100%);opacity:0;transition:opacity .3s ease}.metadata-card:hover:before{opacity:1}.metadata-card:hover{transform:translateY(-3px);box-shadow:0 12px 28px #29446626}.metadata-card h3{color:#294466;margin-bottom:25px;font-size:1.3em;font-weight:400;position:relative;z-index:1}.metadata-item{display:grid;grid-template-columns:220px 1fr;gap:25px;padding:15px 0;border-bottom:1px solid rgba(241,245,249,.8);transition:all .2s ease}.metadata-item:hover{background:#f8fafc80;margin:0 -15px;padding:15px;border-radius:6px}.metadata-item:last-child{border-bottom:none}.metadata-label{font-weight:500;color:#64748b;font-size:.9em}.metadata-value{color:#1e293b;font-size:.95em}.metadata-value code{background:#2944660d;padding:2px 6px;border-radius:4px;font-family:Monaco,Menlo,Ubuntu Mono,monospace;font-size:.85em;color:#294466;border:1px solid rgba(41,68,102,.1)}.metadata-value .tag{display:inline-block;background:linear-gradient(135deg,#294466,#3c5aa6);color:#fff;padding:2px 8px;border-radius:12px;font-size:.8em;margin:2px 4px 2px 0;box-shadow:0 2px 4px #29446633;transition:all .2s ease}.metadata-value .tag:hover{transform:translateY(-1px);box-shadow:0 4px 8px #2944664d}.moodle-launch-section{margin-top:25px;padding-top:20px;border-top:1px solid rgba(41,68,102,.1);text-align:center}.moodle-launch-btn{background:linear-gradient(135deg,#294466,#3c5aa6);color:#fff;border:none;padding:14px 28px;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;transition:all .3s ease;display:inline-flex;align-items:center;gap:10px;box-shadow:0 4px 12px #2944664d;position:relative;overflow:hidden}.moodle-launch-btn:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 6px 20px #29446666}.moodle-launch-btn:active:not(:disabled){transform:translateY(0)}.moodle-launch-btn:disabled{opacity:.7;cursor:not-allowed;transform:none}.moodle-launch-btn:before{content:"";position:absolute;top:0;left:-100%;width:100%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.2),transparent);transition:left .5s ease}.moodle-launch-btn:hover:before{left:100%}.moodle-launch-description{margin-top:8px;color:#64748b;font-size:.9rem}.moodle-success-info{margin-top:15px;padding:15px;background:linear-gradient(135deg,#10b9811a,#10b9810d);border:1px solid rgba(16,185,129,.2);border-radius:8px;text-align:left}.moodle-success-info p{margin:5px 0;font-size:.9rem}.moodle-success-info code{background:#10b9811a;padding:2px 6px;border-radius:4px;font-family:Monaco,Menlo,Ubuntu Mono,monospace;font-size:.8em}.loading-spinner{border:3px solid rgba(243,244,246,.8);border-top:3px solid #294466;border-radius:50%;width:28px;height:28px;animation:spin 1s linear infinite;margin:20px auto 0}@keyframes spin{0%{transform:rotate(0)}to{transform:rotate(360deg)}}.tag{display:inline-block;background:linear-gradient(135deg,#294466,#1e3248);color:#fff;padding:6px 12px;border-radius:6px;font-size:.8em;margin:3px 6px 3px 0;font-weight:400;transition:all .2s ease;cursor:default}.tag:hover{transform:translateY(-1px);box-shadow:0 4px 8px #29446633}.progress-bar{width:100%;height:4px;background:#e5e7ebcc;border-radius:2px;overflow:hidden;margin:16px 0 0}.progress-fill{height:100%;background:linear-gradient(90deg,#294466,#1e3248);width:0%;transition:width .4s cubic-bezier(.4,0,.2,1);position:relative}.progress-fill:after{content:"";position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(90deg,transparent 0%,rgba(255,255,255,.3) 50%,transparent 100%);animation:progressShimmer 1.5s ease-in-out infinite}@keyframes progressShimmer{0%{transform:translate(-100%)}to{transform:translate(100%)}}@keyframes fadeInUp{0%{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}.results{display:grid;gap:20px;max-height:70vh;overflow-y:auto;padding-right:10px}.results::-webkit-scrollbar{width:6px}.results::-webkit-scrollbar-track{background:#2944660d;border-radius:3px}.results::-webkit-scrollbar-thumb{background:#29446633;border-radius:3px;-webkit-transition:background .2s ease;transition:background .2s ease}.results::-webkit-scrollbar-thumb:hover{background:#29446666}@media (max-width: 768px){.container{margin:20px;border-radius:12px}.main-content{padding:40px 30px}.metadata-item{grid-template-columns:1fr;gap:10px}.metadata-label{font-weight:600}.upload-section{padding:40px 25px}.header{padding:40px 30px}.upload-btn{margin:5px;min-width:120px}.stats-grid{grid-template-columns:repeat(2,1fr)}}.header{background:radial-gradient(circle at 60% 40%,#3b82f6,#1e3a8a);box-shadow:0 8px 32px #3b82f626,0 2px 8px #1e3a8a14;border-radius:2rem;position:relative;overflow:visible;animation:fadeInDown .8s cubic-bezier(.4,0,.2,1);margin-bottom:2.5rem}.header-blur-bg{position:absolute;top:0;right:0;bottom:0;left:0;z-index:0;background:radial-gradient(circle at 80% 20%,#60a5fa44 0%,transparent 70%);filter:blur(32px);pointer-events:none}@keyframes logoPulse{0%{filter:drop-shadow(0 0 8px #3b82f6cc)}to{filter:drop-shadow(0 0 24px #60a5fa)}}.header-title{text-shadow:0 2px 8px #1e3a8a33;color:#0ea5e9;font-weight:700;letter-spacing:-1px}@keyframes fadeInDown{0%{opacity:0;transform:translateY(-30px)}to{opacity:1;transform:translateY(0)}}.header-content{position:relative;z-index:1;display:flex;align-items:center;gap:1.5rem;padding:2.5rem 2rem}.header-subtitle{color:#334155;font-size:1.1em;opacity:.9;font-weight:400}.header-btn{margin-left:auto;background:#e0edff;color:#2563eb;padding:.5rem 1.5rem;border-radius:9999px;font-weight:600;box-shadow:0 2px 8px #3b82f633;transition:background .2s,color .2s,box-shadow .2s;border:none;cursor:pointer}.header-btn:hover{background:#dbeafe;color:#1d4ed8;box-shadow:0 4px 16px #60a5fa55}.footer{background:linear-gradient(90deg,#1e3a8a,#2563eb);color:#e0e6ed;box-shadow:0 -8px 32px #1e3a8a33;border-radius:1.5rem 1.5rem 0 0;position:relative;overflow:visible;animation:fadeInUp .8s cubic-bezier(.4,0,.2,1);margin-top:3rem;padding:2rem 0 1.2rem}.footer-blur-bg{position:absolute;top:0;right:0;bottom:0;left:0;z-index:0;background:radial-gradient(circle at 20% 80%,#60a5fa44 0%,transparent 70%);filter:blur(32px);pointer-events:none}.footer-content{position:relative;z-index:1;display:flex;align-items:center;gap:1.5rem;justify-content:center}.footer-logo{filter:drop-shadow(0 0 8px #3b82f6cc);transition:filter .3s;height:40px;max-width:160px;-o-object-fit:contain;object-fit:contain;background:transparent;border-radius:6px;box-shadow:none}.footer-logo:hover{filter:drop-shadow(0 0 24px #60a5fa)}.footer-text{color:#e0e6ed;font-size:1em;margin-left:.5rem}@keyframes fadeInUp{0%{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}.visible{visibility:visible}.fixed{position:fixed}.absolute{position:absolute}.relative{position:relative}.sticky{position:sticky}.inset-0{top:0;right:0;bottom:0;left:0}.bottom-0{bottom:0}.left-0{left:0}.top-0{top:0}.z-20{z-index:20}.z-30{z-index:30}.mx-auto{margin-left:auto;margin-right:auto}.mb-0{margin-bottom:0}.mb-2{margin-bottom:.5rem}.mb-4{margin-bottom:1rem}.mb-6{margin-bottom:1.5rem}.ml-8{margin-left:2rem}.mt-0{margin-top:0}.mt-1{margin-top:.25rem}.mt-2{margin-top:.5rem}.block{display:block}.inline-block{display:inline-block}.flex{display:flex}.inline-flex{display:inline-flex}.h-10{height:2.5rem}.h-11{height:2.75rem}.h-2{height:.5rem}.h-3{height:.75rem}.h-4{height:1rem}.h-48{height:12rem}.h-5{height:1.25rem}.h-8{height:2rem}.h-9{height:2.25rem}.min-h-screen{min-height:100vh}.w-10{width:2.5rem}.w-2{width:.5rem}.w-3{width:.75rem}.w-4{width:1rem}.w-5{width:1.25rem}.w-8{width:2rem}.w-80{width:20rem}.w-9{width:2.25rem}.w-full{width:100%}.min-w-0{min-width:0px}.max-w-7xl{max-width:80rem}.flex-1{flex:1 1 0%}.flex-shrink-0{flex-shrink:0}@keyframes pulse{50%{opacity:.5}}.animate-pulse{animation:pulse 2s cubic-bezier(.4,0,.6,1) infinite}.cursor-not-allowed{cursor:not-allowed}.cursor-pointer{cursor:pointer}.resize{resize:both}.flex-row{flex-direction:row}.flex-col{flex-direction:column}.items-start{align-items:flex-start}.items-center{align-items:center}.justify-start{justify-content:flex-start}.justify-end{justify-content:flex-end}.justify-center{justify-content:center}.justify-between{justify-content:space-between}.gap-1{gap:.25rem}.gap-2{gap:.5rem}.gap-3{gap:.75rem}.gap-6{gap:1.5rem}.space-x-2>:not([hidden])~:not([hidden]){--tw-space-x-reverse: 0;margin-right:calc(.5rem * var(--tw-space-x-reverse));margin-left:calc(.5rem * calc(1 - var(--tw-space-x-reverse)))}.space-y-1>:not([hidden])~:not([hidden]){--tw-space-y-reverse: 0;margin-top:calc(.25rem * calc(1 - var(--tw-space-y-reverse)));margin-bottom:calc(.25rem * var(--tw-space-y-reverse))}.space-y-1\.5>:not([hidden])~:not([hidden]){--tw-space-y-reverse: 0;margin-top:calc(.375rem * calc(1 - var(--tw-space-y-reverse)));margin-bottom:calc(.375rem * var(--tw-space-y-reverse))}.space-y-2>:not([hidden])~:not([hidden]){--tw-space-y-reverse: 0;margin-top:calc(.5rem * calc(1 - var(--tw-space-y-reverse)));margin-bottom:calc(.5rem * var(--tw-space-y-reverse))}.space-y-3>:not([hidden])~:not([hidden]){--tw-space-y-reverse: 0;margin-top:calc(.75rem * calc(1 - var(--tw-space-y-reverse)));margin-bottom:calc(.75rem * var(--tw-space-y-reverse))}.space-y-4>:not([hidden])~:not([hidden]){--tw-space-y-reverse: 0;margin-top:calc(1rem * calc(1 - var(--tw-space-y-reverse)));margin-bottom:calc(1rem * var(--tw-space-y-reverse))}.space-y-6>:not([hidden])~:not([hidden]){--tw-space-y-reverse: 0;margin-top:calc(1.5rem * calc(1 - var(--tw-space-y-reverse)));margin-bottom:calc(1.5rem * var(--tw-space-y-reverse))}.overflow-hidden{overflow:hidden}.overflow-visible{overflow:visible}.truncate{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.whitespace-nowrap{white-space:nowrap}.break-all{word-break:break-all}.rounded{border-radius:.25rem}.rounded-full{border-radius:9999px}.rounded-lg{border-radius:var(--radius)}.rounded-md{border-radius:calc(var(--radius) - 2px)}.border{border-width:1px}.border-b{border-bottom-width:1px}.border-t{border-top-width:1px}.border-amber-200{--tw-border-opacity: 1;border-color:rgb(253 230 138 / var(--tw-border-opacity, 1))}.border-blue-200{--tw-border-opacity: 1;border-color:rgb(191 219 254 / var(--tw-border-opacity, 1))}.border-cyan-200{--tw-border-opacity: 1;border-color:rgb(165 243 252 / var(--tw-border-opacity, 1))}.border-emerald-200{--tw-border-opacity: 1;border-color:rgb(167 243 208 / var(--tw-border-opacity, 1))}.border-fuchsia-200{--tw-border-opacity: 1;border-color:rgb(245 208 254 / var(--tw-border-opacity, 1))}.border-gray-200{--tw-border-opacity: 1;border-color:rgb(229 231 235 / var(--tw-border-opacity, 1))}.border-green-200{--tw-border-opacity: 1;border-color:rgb(187 247 208 / var(--tw-border-opacity, 1))}.border-indigo-200{--tw-border-opacity: 1;border-color:rgb(199 210 254 / var(--tw-border-opacity, 1))}.border-input{border-color:hsl(var(--input))}.border-lime-200{--tw-border-opacity: 1;border-color:rgb(217 249 157 / var(--tw-border-opacity, 1))}.border-neutral-200{--tw-border-opacity: 1;border-color:rgb(229 229 229 / var(--tw-border-opacity, 1))}.border-orange-200{--tw-border-opacity: 1;border-color:rgb(254 215 170 / var(--tw-border-opacity, 1))}.border-pink-200{--tw-border-opacity: 1;border-color:rgb(251 207 232 / var(--tw-border-opacity, 1))}.border-purple-200{--tw-border-opacity: 1;border-color:rgb(233 213 255 / var(--tw-border-opacity, 1))}.border-red-200{--tw-border-opacity: 1;border-color:rgb(254 202 202 / var(--tw-border-opacity, 1))}.border-rose-200{--tw-border-opacity: 1;border-color:rgb(254 205 211 / var(--tw-border-opacity, 1))}.border-slate-200{--tw-border-opacity: 1;border-color:rgb(226 232 240 / var(--tw-border-opacity, 1))}.border-teal-200{--tw-border-opacity: 1;border-color:rgb(153 246 228 / var(--tw-border-opacity, 1))}.border-violet-200{--tw-border-opacity: 1;border-color:rgb(221 214 254 / var(--tw-border-opacity, 1))}.border-yellow-200{--tw-border-opacity: 1;border-color:rgb(254 240 138 / var(--tw-border-opacity, 1))}.bg-amber-100{--tw-bg-opacity: 1;background-color:rgb(254 243 199 / var(--tw-bg-opacity, 1))}.bg-background{background-color:hsl(var(--background))}.bg-blue-100{--tw-bg-opacity: 1;background-color:rgb(219 234 254 / var(--tw-bg-opacity, 1))}.bg-blue-600{--tw-bg-opacity: 1;background-color:rgb(37 99 235 / var(--tw-bg-opacity, 1))}.bg-card{background-color:hsl(var(--card))}.bg-cyan-100{--tw-bg-opacity: 1;background-color:rgb(207 250 254 / var(--tw-bg-opacity, 1))}.bg-destructive{background-color:hsl(var(--destructive))}.bg-emerald-100{--tw-bg-opacity: 1;background-color:rgb(209 250 229 / var(--tw-bg-opacity, 1))}.bg-fuchsia-100{--tw-bg-opacity: 1;background-color:rgb(250 232 255 / var(--tw-bg-opacity, 1))}.bg-gray-100{--tw-bg-opacity: 1;background-color:rgb(243 244 246 / var(--tw-bg-opacity, 1))}.bg-green-100{--tw-bg-opacity: 1;background-color:rgb(220 252 231 / var(--tw-bg-opacity, 1))}.bg-indigo-100{--tw-bg-opacity: 1;background-color:rgb(224 231 255 / var(--tw-bg-opacity, 1))}.bg-lime-100{--tw-bg-opacity: 1;background-color:rgb(236 252 203 / var(--tw-bg-opacity, 1))}.bg-muted-foreground{background-color:hsl(var(--muted-foreground))}.bg-muted\/30{background-color:hsl(var(--muted) / .3)}.bg-muted\/50{background-color:hsl(var(--muted) / .5)}.bg-neutral-100{--tw-bg-opacity: 1;background-color:rgb(245 245 245 / var(--tw-bg-opacity, 1))}.bg-orange-100{--tw-bg-opacity: 1;background-color:rgb(255 237 213 / var(--tw-bg-opacity, 1))}.bg-pink-100{--tw-bg-opacity: 1;background-color:rgb(252 231 243 / var(--tw-bg-opacity, 1))}.bg-primary{background-color:hsl(var(--primary))}.bg-primary\/10{background-color:hsl(var(--primary) / .1)}.bg-purple-100{--tw-bg-opacity: 1;background-color:rgb(243 232 255 / var(--tw-bg-opacity, 1))}.bg-red-100{--tw-bg-opacity: 1;background-color:rgb(254 226 226 / var(--tw-bg-opacity, 1))}.bg-rose-100{--tw-bg-opacity: 1;background-color:rgb(255 228 230 / var(--tw-bg-opacity, 1))}.bg-secondary{background-color:hsl(var(--secondary))}.bg-slate-100{--tw-bg-opacity: 1;background-color:rgb(241 245 249 / var(--tw-bg-opacity, 1))}.bg-teal-100{--tw-bg-opacity: 1;background-color:rgb(204 251 241 / var(--tw-bg-opacity, 1))}.bg-violet-100{--tw-bg-opacity: 1;background-color:rgb(237 233 254 / var(--tw-bg-opacity, 1))}.bg-white{--tw-bg-opacity: 1;background-color:rgb(255 255 255 / var(--tw-bg-opacity, 1))}.bg-yellow-100{--tw-bg-opacity: 1;background-color:rgb(254 249 195 / var(--tw-bg-opacity, 1))}.bg-gradient-to-t{background-image:linear-gradient(to top,var(--tw-gradient-stops))}.from-black\/60{--tw-gradient-from: rgb(0 0 0 / .6) var(--tw-gradient-from-position);--tw-gradient-to: rgb(0 0 0 / 0) var(--tw-gradient-to-position);--tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to)}.to-transparent{--tw-gradient-to: transparent var(--tw-gradient-to-position)}.bg-cover{background-size:cover}.bg-center{background-position:center}.p-0{padding:0}.p-3{padding:.75rem}.p-4{padding:1rem}.p-6{padding:1.5rem}.px-2{padding-left:.5rem;padding-right:.5rem}.px-2\.5{padding-left:.625rem;padding-right:.625rem}.px-3{padding-left:.75rem;padding-right:.75rem}.px-4{padding-left:1rem;padding-right:1rem}.px-8{padding-left:2rem;padding-right:2rem}.py-0\.5{padding-top:.125rem;padding-bottom:.125rem}.py-1{padding-top:.25rem;padding-bottom:.25rem}.py-2{padding-top:.5rem;padding-bottom:.5rem}.py-8{padding-top:2rem;padding-bottom:2rem}.pb-4{padding-bottom:1rem}.pt-0{padding-top:0}.text-center{text-align:center}.text-2xl{font-size:1.5rem;line-height:2rem}.text-3xl{font-size:1.875rem;line-height:2.25rem}.text-base{font-size:1rem;line-height:1.5rem}.text-lg{font-size:1.125rem;line-height:1.75rem}.text-sm{font-size:.875rem;line-height:1.25rem}.text-xl{font-size:1.25rem;line-height:1.75rem}.text-xs{font-size:.75rem;line-height:1rem}.font-bold{font-weight:700}.font-medium{font-weight:500}.font-semibold{font-weight:600}.leading-none{line-height:1}.tracking-tight{letter-spacing:-.025em}.text-amber-800{--tw-text-opacity: 1;color:rgb(146 64 14 / var(--tw-text-opacity, 1))}.text-blue-600{--tw-text-opacity: 1;color:rgb(37 99 235 / var(--tw-text-opacity, 1))}.text-blue-800{--tw-text-opacity: 1;color:rgb(30 64 175 / var(--tw-text-opacity, 1))}.text-card-foreground{color:hsl(var(--card-foreground))}.text-cyan-800{--tw-text-opacity: 1;color:rgb(21 94 117 / var(--tw-text-opacity, 1))}.text-destructive-foreground{color:hsl(var(--destructive-foreground))}.text-emerald-800{--tw-text-opacity: 1;color:rgb(6 95 70 / var(--tw-text-opacity, 1))}.text-foreground{color:hsl(var(--foreground))}.text-fuchsia-800{--tw-text-opacity: 1;color:rgb(134 25 143 / var(--tw-text-opacity, 1))}.text-gray-200{--tw-text-opacity: 1;color:rgb(229 231 235 / var(--tw-text-opacity, 1))}.text-gray-400{--tw-text-opacity: 1;color:rgb(156 163 175 / var(--tw-text-opacity, 1))}.text-gray-500{--tw-text-opacity: 1;color:rgb(107 114 128 / var(--tw-text-opacity, 1))}.text-gray-600{--tw-text-opacity: 1;color:rgb(75 85 99 / var(--tw-text-opacity, 1))}.text-gray-800{--tw-text-opacity: 1;color:rgb(31 41 55 / var(--tw-text-opacity, 1))}.text-gray-900{--tw-text-opacity: 1;color:rgb(17 24 39 / var(--tw-text-opacity, 1))}.text-green-600{--tw-text-opacity: 1;color:rgb(22 163 74 / var(--tw-text-opacity, 1))}.text-green-800{--tw-text-opacity: 1;color:rgb(22 101 52 / var(--tw-text-opacity, 1))}.text-indigo-800{--tw-text-opacity: 1;color:rgb(55 48 163 / var(--tw-text-opacity, 1))}.text-lime-800{--tw-text-opacity: 1;color:rgb(63 98 18 / var(--tw-text-opacity, 1))}.text-muted-foreground{color:hsl(var(--muted-foreground))}.text-neutral-800{--tw-text-opacity: 1;color:rgb(38 38 38 / var(--tw-text-opacity, 1))}.text-orange-800{--tw-text-opacity: 1;color:rgb(154 52 18 / var(--tw-text-opacity, 1))}.text-pink-800{--tw-text-opacity: 1;color:rgb(157 23 77 / var(--tw-text-opacity, 1))}.text-primary{color:hsl(var(--primary))}.text-primary-foreground{color:hsl(var(--primary-foreground))}.text-purple-800{--tw-text-opacity: 1;color:rgb(107 33 168 / var(--tw-text-opacity, 1))}.text-red-800{--tw-text-opacity: 1;color:rgb(153 27 27 / var(--tw-text-opacity, 1))}.text-rose-800{--tw-text-opacity: 1;color:rgb(159 18 57 / var(--tw-text-opacity, 1))}.text-secondary-foreground{color:hsl(var(--secondary-foreground))}.text-slate-800{--tw-text-opacity: 1;color:rgb(30 41 59 / var(--tw-text-opacity, 1))}.text-teal-800{--tw-text-opacity: 1;color:rgb(17 94 89 / var(--tw-text-opacity, 1))}.text-violet-800{--tw-text-opacity: 1;color:rgb(91 33 182 / var(--tw-text-opacity, 1))}.text-white{--tw-text-opacity: 1;color:rgb(255 255 255 / var(--tw-text-opacity, 1))}.text-yellow-800{--tw-text-opacity: 1;color:rgb(133 77 14 / var(--tw-text-opacity, 1))}.underline{text-decoration-line:underline}.underline-offset-4{text-underline-offset:4px}.opacity-0{opacity:0}.opacity-60{opacity:.6}.shadow{--tw-shadow: 0 1px 3px 0 rgb(0 0 0 / .1), 0 1px 2px -1px rgb(0 0 0 / .1);--tw-shadow-colored: 0 1px 3px 0 var(--tw-shadow-color), 0 1px 2px -1px var(--tw-shadow-color);box-shadow:var(--tw-ring-offset-shadow, 0 0 #0000),var(--tw-ring-shadow, 0 0 #0000),var(--tw-shadow)}.shadow-lg{--tw-shadow: 0 10px 15px -3px rgb(0 0 0 / .1), 0 4px 6px -4px rgb(0 0 0 / .1);--tw-shadow-colored: 0 10px 15px -3px var(--tw-shadow-color), 0 4px 6px -4px var(--tw-shadow-color);box-shadow:var(--tw-ring-offset-shadow, 0 0 #0000),var(--tw-ring-shadow, 0 0 #0000),var(--tw-shadow)}.shadow-sm{--tw-shadow: 0 1px 2px 0 rgb(0 0 0 / .05);--tw-shadow-colored: 0 1px 2px 0 var(--tw-shadow-color);box-shadow:var(--tw-ring-offset-shadow, 0 0 #0000),var(--tw-ring-shadow, 0 0 #0000),var(--tw-shadow)}.outline{outline-style:solid}.ring-offset-background{--tw-ring-offset-color: hsl(var(--background))}.filter{filter:var(--tw-blur) var(--tw-brightness) var(--tw-contrast) var(--tw-grayscale) var(--tw-hue-rotate) var(--tw-invert) var(--tw-saturate) var(--tw-sepia) var(--tw-drop-shadow)}.transition{transition-property:color,background-color,border-color,text-decoration-color,fill,stroke,opacity,box-shadow,transform,filter,-webkit-backdrop-filter;transition-property:color,background-color,border-color,text-decoration-color,fill,stroke,opacity,box-shadow,transform,filter,backdrop-filter;transition-property:color,background-color,border-color,text-decoration-color,fill,stroke,opacity,box-shadow,transform,filter,backdrop-filter,-webkit-backdrop-filter;transition-timing-function:cubic-bezier(.4,0,.2,1);transition-duration:.15s}.transition-all{transition-property:all;transition-timing-function:cubic-bezier(.4,0,.2,1);transition-duration:.15s}.transition-colors{transition-property:color,background-color,border-color,text-decoration-color,fill,stroke;transition-timing-function:cubic-bezier(.4,0,.2,1);transition-duration:.15s}.duration-150{transition-duration:.15s}.duration-300{transition-duration:.3s}.hover\:bg-accent:hover{background-color:hsl(var(--accent))}.hover\:bg-blue-50:hover{--tw-bg-opacity: 1;background-color:rgb(239 246 255 / var(--tw-bg-opacity, 1))}.hover\:bg-blue-700:hover{--tw-bg-opacity: 1;background-color:rgb(29 78 216 / var(--tw-bg-opacity, 1))}.hover\:bg-destructive\/80:hover{background-color:hsl(var(--destructive) / .8)}.hover\:bg-destructive\/90:hover{background-color:hsl(var(--destructive) / .9)}.hover\:bg-gray-100:hover{--tw-bg-opacity: 1;background-color:rgb(243 244 246 / var(--tw-bg-opacity, 1))}.hover\:bg-gray-50:hover{--tw-bg-opacity: 1;background-color:rgb(249 250 251 / var(--tw-bg-opacity, 1))}.hover\:bg-primary\/80:hover{background-color:hsl(var(--primary) / .8)}.hover\:bg-primary\/90:hover{background-color:hsl(var(--primary) / .9)}.hover\:bg-secondary\/80:hover{background-color:hsl(var(--secondary) / .8)}.hover\:text-accent-foreground:hover{color:hsl(var(--accent-foreground))}.hover\:text-gray-900:hover{--tw-text-opacity: 1;color:rgb(17 24 39 / var(--tw-text-opacity, 1))}.hover\:underline:hover{text-decoration-line:underline}.focus\:outline-none:focus{outline:2px solid transparent;outline-offset:2px}.focus\:ring-2:focus{--tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color);--tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(2px + var(--tw-ring-offset-width)) var(--tw-ring-color);box-shadow:var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow, 0 0 #0000)}.focus\:ring-ring:focus{--tw-ring-color: hsl(var(--ring))}.focus\:ring-offset-2:focus{--tw-ring-offset-width: 2px}.focus-visible\:outline-none:focus-visible{outline:2px solid transparent;outline-offset:2px}.focus-visible\:ring-2:focus-visible{--tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color);--tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(2px + var(--tw-ring-offset-width)) var(--tw-ring-color);box-shadow:var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow, 0 0 #0000)}.focus-visible\:ring-ring:focus-visible{--tw-ring-color: hsl(var(--ring))}.focus-visible\:ring-offset-2:focus-visible{--tw-ring-offset-width: 2px}.disabled\:pointer-events-none:disabled{pointer-events:none}.disabled\:opacity-50:disabled{opacity:.5}.group:hover .group-hover\:bg-blue-200{--tw-bg-opacity: 1;background-color:rgb(191 219 254 / var(--tw-bg-opacity, 1))}.group:hover .group-hover\:text-blue-600{--tw-text-opacity: 1;color:rgb(37 99 235 / var(--tw-text-opacity, 1))}.group:hover .group-hover\:opacity-100{opacity:1}`;
    const fullHtml = `\n      <!DOCTYPE html>\n      <html>\n        <head>\n          <meta charset=\"UTF-8\" />\n          <title>Kurs Export</title>\n          <style>\n            ${css}\n          </style>\n        </head>\n        <body>\n          ${content}\n        </body>\n      </html>\n    `;
    const blob = new Blob([fullHtml], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'kurs-export.html';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex gap-6 max-w-7xl mx-auto">
      {/* Main Content */}
      <div className="flex-1">
        {/* Export-Button */}
        <div className="mb-4 flex justify-end">
          <button
            onClick={exportAsHtml}
            className="px-4 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700 transition"
          >
            Als HTML exportieren
          </button>
        </div>
        {/* Exportierbarer Bereich */}
        <div ref={exportRef}>
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
        </div> {/* Ende exportRef */}
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
                    <p className="text-xs text-gray-500">TODO: Being able to create new content and ideas using digital tools</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-blue-100 rounded flex items-center justify-center flex-shrink-0">
                    <Globe className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium">Cultural</h4>
                    <p className="text-xs text-gray-500">TODO: Understanding digital communication in different contexts</p>
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