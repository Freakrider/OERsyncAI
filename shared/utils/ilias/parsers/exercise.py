"""
Parser für ILIAS-Übungs-Komponenten.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
import logging
import os
import glob
from .base import IliasComponentParser

logger = logging.getLogger(__name__)

class ExerciseParser(IliasComponentParser):
    """Parser für ILIAS-Übungen."""
    
    def _parse_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parst die XML-Daten einer ILIAS-Übung.
        
        Args:
            root: XML-Root-Element
            
        Returns:
            Dict mit den extrahierten Übungsdaten
        """
        exercise_data = {}
        
        try:
            # Suche nach ExportItem/Exercise
            export_item = self._find_element(root, './/exp:ExportItem', self.namespaces)
            if export_item is None:
                logger.warning("Kein ExportItem-Element gefunden")
                return self._extract_basic_info()
            
            # Suche nach Exercise
            exercise_elem = export_item.find('.//Exercise')
            if exercise_elem is None:
                # Versuche alternative Pfade
                exercise_elem = root.find('.//Exercise')
                if exercise_elem is None:
                    logger.warning("Kein Exercise-Element gefunden")
                    return self._extract_basic_info()
            
            # Basis-Informationen
            for field in ['Id', 'Title', 'Description', 'Owner', 'CreateDate', 'LastUpdate', 'Instructions']:
                elem = exercise_elem.find(field)
                if elem is not None:
                    exercise_data[field.lower()] = self._get_text(elem)
            
            # Einstellungen
            settings_elem = exercise_elem.find('Settings')
            if settings_elem is not None:
                settings = {}
                for setting_elem in settings_elem:
                    setting_name = setting_elem.tag
                    setting_value = self._get_text(setting_elem)
                    settings[setting_name.lower()] = setting_value
                
                if settings:
                    exercise_data['settings'] = settings
            
            # Aufgaben
            assignments = []
            assignments_elem = exercise_elem.find('Assignments')
            if assignments_elem is not None:
                for assignment_elem in assignments_elem.findall('Assignment'):
                    assignment_data = {
                        'id': self._get_attribute(assignment_elem, 'id', ''),
                        'title': self._get_text(assignment_elem.find('Title')),
                        'description': self._get_text(assignment_elem.find('Description')),
                        'type': self._get_text(assignment_elem.find('Type')),
                    }
                    
                    # Termine
                    for date_field in ['StartDate', 'EndDate', 'SubmissionDate']:
                        date_elem = assignment_elem.find(date_field)
                        if date_elem is not None:
                            assignment_data[date_field.lower()] = self._get_text(date_elem)
                    
                    # Aufgabendetails
                    details_elem = assignment_elem.find('Details')
                    if details_elem is not None:
                        details = {}
                        for detail_elem in details_elem:
                            detail_name = detail_elem.tag
                            detail_value = self._get_text(detail_elem)
                            details[detail_name.lower()] = detail_value
                        
                        if details:
                            assignment_data['details'] = details
                    
                    # Dateien
                    files = []
                    files_elem = assignment_elem.find('Files')
                    if files_elem is not None:
                        for file_elem in files_elem.findall('File'):
                            file_data = {
                                'name': self._get_text(file_elem.find('Name')),
                                'size': self._get_text(file_elem.find('Size')),
                                'type': self._get_text(file_elem.find('Type')),
                                'path': self._get_text(file_elem.find('Path'))
                            }
                            files.append(file_data)
                    
                    if files:
                        assignment_data['files'] = files
                    
                    # Einreichungen
                    submissions = []
                    submissions_elem = assignment_elem.find('Submissions')
                    if submissions_elem is not None:
                        for submission_elem in submissions_elem.findall('Submission'):
                            submission_data = {
                                'id': self._get_attribute(submission_elem, 'id', ''),
                                'user_id': self._get_attribute(submission_elem, 'user_id', ''),
                                'date': self._get_text(submission_elem.find('Date')),
                                'status': self._get_text(submission_elem.find('Status')),
                                'feedback': self._get_text(submission_elem.find('Feedback')),
                                'grade': self._get_text(submission_elem.find('Grade'))
                            }
                            
                            # Eingereichte Dateien
                            sub_files = []
                            sub_files_elem = submission_elem.find('Files')
                            if sub_files_elem is not None:
                                for sub_file_elem in sub_files_elem.findall('File'):
                                    sub_file_data = {
                                        'name': self._get_text(sub_file_elem.find('Name')),
                                        'size': self._get_text(sub_file_elem.find('Size')),
                                        'type': self._get_text(sub_file_elem.find('Type')),
                                        'path': self._get_text(sub_file_elem.find('Path'))
                                    }
                                    sub_files.append(sub_file_data)
                            
                            if sub_files:
                                submission_data['files'] = sub_files
                            
                            submissions.append(submission_data)
                    
                    if submissions:
                        assignment_data['submissions'] = submissions
                    
                    assignments.append(assignment_data)
            
            if assignments:
                exercise_data['assignments'] = assignments
            else:
                # Wenn keine Aufgaben in der XML gefunden wurden, versuche sie aus dem Dateisystem zu extrahieren
                filesystem_assignments = self._extract_assignments_from_filesystem()
                if filesystem_assignments:
                    exercise_data['assignments'] = filesystem_assignments
            
            return exercise_data
        
        except Exception as e:
            logger.exception(f"Fehler beim Parsen der XML-Daten: {str(e)}")
            return self._extract_basic_info()
    
    def _extract_assignments_from_filesystem(self) -> List[Dict[str, Any]]:
        """
        Extrahiert Aufgabeninformationen aus dem Dateisystem.
        
        Returns:
            Liste mit Aufgabeninformationen
        """
        assignments = []
        
        if not self.component_path:
            return assignments
        
        try:
            # Suche nach Aufgabenverzeichnissen
            assignment_dirs = glob.glob(os.path.join(self.component_path, "assignment_*"))
            
            for assignment_dir in assignment_dirs:
                assignment_id = os.path.basename(assignment_dir).replace("assignment_", "")
                
                # Basis-Informationen aus dem Verzeichnisnamen
                assignment_data = {
                    'id': assignment_id,
                    'title': f"Aufgabe {assignment_id}",
                    'description': f"Aus dem Dateisystem extrahierte Aufgabe {assignment_id}"
                }
                
                # Suche nach XML-Dateien für weitere Informationen
                xml_files = glob.glob(os.path.join(assignment_dir, "*.xml"))
                for xml_file in xml_files:
                    try:
                        tree = ET.parse(xml_file)
                        xml_root = tree.getroot()
                        
                        # Suche nach Titel und Beschreibung
                        title_elem = xml_root.find(".//Title")
                        if title_elem is not None and title_elem.text:
                            assignment_data['title'] = title_elem.text
                        
                        desc_elem = xml_root.find(".//Description")
                        if desc_elem is not None and desc_elem.text:
                            assignment_data['description'] = desc_elem.text
                        
                        # Suche nach Terminen
                        for date_field in ['StartDate', 'EndDate', 'SubmissionDate']:
                            date_elem = xml_root.find(f".//{date_field}")
                            if date_elem is not None and date_elem.text:
                                assignment_data[date_field.lower()] = date_elem.text
                    
                    except Exception as e:
                        logger.warning(f"Fehler beim Extrahieren von Informationen aus {xml_file}: {str(e)}")
                
                # Suche nach Dateien
                files = []
                file_dirs = glob.glob(os.path.join(assignment_dir, "files"))
                for file_dir in file_dirs:
                    for root, _, filenames in os.walk(file_dir):
                        for filename in filenames:
                            file_path = os.path.join(root, filename)
                            file_size = os.path.getsize(file_path)
                            file_type = os.path.splitext(filename)[1][1:]  # Entferne den Punkt
                            
                            files.append({
                                'name': filename,
                                'size': str(file_size),
                                'type': file_type,
                                'path': os.path.relpath(file_path, self.component_path)
                            })
                
                if files:
                    assignment_data['files'] = files
                
                # Suche nach Einreichungen
                submissions = []
                submission_dirs = glob.glob(os.path.join(assignment_dir, "submissions", "*"))
                for submission_dir in submission_dirs:
                    user_id = os.path.basename(submission_dir)
                    
                    submission_data = {
                        'id': f"{assignment_id}_{user_id}",
                        'user_id': user_id
                    }
                    
                    # Suche nach eingereichten Dateien
                    sub_files = []
                    for root, _, filenames in os.walk(submission_dir):
                        for filename in filenames:
                            file_path = os.path.join(root, filename)
                            file_size = os.path.getsize(file_path)
                            file_type = os.path.splitext(filename)[1][1:]  # Entferne den Punkt
                            
                            sub_files.append({
                                'name': filename,
                                'size': str(file_size),
                                'type': file_type,
                                'path': os.path.relpath(file_path, self.component_path)
                            })
                    
                    if sub_files:
                        submission_data['files'] = sub_files
                    
                    submissions.append(submission_data)
                
                if submissions:
                    assignment_data['submissions'] = submissions
                
                assignments.append(assignment_data)
        
        except Exception as e:
            logger.warning(f"Fehler beim Extrahieren von Aufgaben aus dem Dateisystem: {str(e)}")
        
        return assignments 