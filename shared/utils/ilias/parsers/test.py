"""
Parser für ILIAS-Test-Komponenten.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET
import logging
import os
from .base import IliasComponentParser

logger = logging.getLogger(__name__)

class TestParser(IliasComponentParser):
    """Parser für ILIAS-Tests."""
    
    def _parse_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parst die XML-Daten eines ILIAS-Tests.
        
        Args:
            root: XML-Root-Element
            
        Returns:
            Dict mit den extrahierten Testdaten
        """
        test_data = {}
        
        try:
            # Suche nach ExportItem/Test
            export_item = self._find_element(root, './/exp:ExportItem', self.namespaces)
            if export_item is None:
                logger.warning("Kein ExportItem-Element gefunden")
                return self._extract_basic_info()
            
            # Suche nach Test oder QTI-Daten
            test_elem = export_item.find('.//Test')
            if test_elem is None:
                # Versuche alternative Pfade
                test_elem = root.find('.//Test')
                if test_elem is None:
                    # Versuche QTI-Daten zu finden
                    qti_elem = root.find('.//questestinterop')
                    if qti_elem is not None:
                        return self._parse_qti(qti_elem)
                    
                    logger.warning("Kein Test-Element gefunden")
                    return self._extract_basic_info()
            
            # Basis-Informationen
            for field in ['Id', 'Title', 'Description', 'Owner', 'CreateDate', 'LastUpdate']:
                elem = test_elem.find(field)
                if elem is not None:
                    test_data[field.lower()] = self._get_text(elem)
            
            # QTI-Metadaten
            qti_metadata = {}
            metadata_elem = test_elem.find('Metadata')
            if metadata_elem is not None:
                for meta_elem in metadata_elem:
                    qti_metadata[meta_elem.tag] = self._get_text(meta_elem)
            
            if qti_metadata:
                test_data['qti_metadata'] = qti_metadata
            
            # Bewertungsstufen
            mark_steps = []
            marks_elem = test_elem.find('MarkSteps')
            if marks_elem is not None:
                for mark_elem in marks_elem.findall('MarkStep'):
                    mark_data = {
                        'short_name': self._get_attribute(mark_elem, 'short_name', ''),
                        'percentage': self._get_attribute(mark_elem, 'percentage', ''),
                        'passed': self._get_attribute(mark_elem, 'passed', '0') == '1'
                    }
                    mark_steps.append(mark_data)
            
            if mark_steps:
                test_data['mark_steps'] = mark_steps
            
            # Fragen
            questions = []
            questions_elem = test_elem.find('Questions')
            if questions_elem is not None:
                for question_elem in questions_elem.findall('Question'):
                    question_data = self._parse_question(question_elem)
                    if question_data:
                        questions.append(question_data)
            
            if questions:
                test_data['questions'] = questions
            
            # Suche nach QTI-Dateien im Komponenten-Pfad
            if not questions and self.component_path:
                qti_questions = self._extract_qti_from_filesystem()
                if qti_questions:
                    test_data['questions'] = qti_questions
            
            return test_data
        
        except Exception as e:
            logger.exception(f"Fehler beim Parsen der XML-Daten: {str(e)}")
            return self._extract_basic_info()
    
    def _parse_question(self, question_elem: ET.Element) -> Dict[str, Any]:
        """
        Parst eine Frage im Test.
        
        Args:
            question_elem: XML-Element der Frage
            
        Returns:
            Dict mit den extrahierten Fragedaten
        """
        if question_elem is None:
            return {}
        
        question_data = {
            'id': self._get_attribute(question_elem, 'id', ''),
            'type': self._get_attribute(question_elem, 'type', '')
        }
        
        # Basis-Informationen
        for field in ['Title', 'Description', 'Author', 'Points']:
            elem = question_elem.find(field)
            if elem is not None:
                question_data[field.lower()] = self._get_text(elem)
        
        # Fragetext
        question_text_elem = question_elem.find('QuestionText')
        if question_text_elem is not None:
            question_data['question_text'] = self._get_text(question_text_elem)
        
        # Antwortoptionen
        answers = []
        answers_elem = question_elem.find('Answers')
        if answers_elem is not None:
            for answer_elem in answers_elem.findall('Answer'):
                answer_data = {
                    'id': self._get_attribute(answer_elem, 'id', ''),
                    'points': self._get_attribute(answer_elem, 'points', '0'),
                    'correct': self._get_attribute(answer_elem, 'correct', '0') == '1'
                }
                
                # Antworttext
                text_elem = answer_elem.find('Text')
                if text_elem is not None:
                    answer_data['text'] = self._get_text(text_elem)
                
                answers.append(answer_data)
        
        if answers:
            question_data['answers'] = answers
        
        # Feedback
        feedback_elem = question_elem.find('Feedback')
        if feedback_elem is not None:
            question_data['feedback'] = self._get_text(feedback_elem)
        
        return question_data
    
    def _parse_qti(self, qti_elem: ET.Element) -> Dict[str, Any]:
        """
        Parst QTI-Daten.
        
        Args:
            qti_elem: XML-Element mit QTI-Daten
            
        Returns:
            Dict mit den extrahierten QTI-Daten
        """
        qti_data = {}
        
        # Assessment
        assessment_elem = qti_elem.find('.//assessment')
        if assessment_elem is not None:
            qti_data['title'] = self._get_attribute(assessment_elem, 'title', '')
            
            # Metadaten
            metadata = {}
            metadata_elem = assessment_elem.find('.//qtimetadata')
            if metadata_elem is not None:
                for field_elem in metadata_elem.findall('.//qtimetadatafield'):
                    label_elem = field_elem.find('fieldlabel')
                    entry_elem = field_elem.find('fieldentry')
                    if label_elem is not None and entry_elem is not None:
                        metadata[self._get_text(label_elem)] = self._get_text(entry_elem)
            
            if metadata:
                qti_data['qti_metadata'] = metadata
            
            # Fragen
            questions = []
            for item_elem in assessment_elem.findall('.//item'):
                question_data = {
                    'id': self._get_attribute(item_elem, 'ident', ''),
                    'title': self._get_attribute(item_elem, 'title', '')
                }
                
                # Fragetext
                presentation_elem = item_elem.find('.//presentation')
                if presentation_elem is not None:
                    material_elem = presentation_elem.find('.//material')
                    if material_elem is not None:
                        mattext_elem = material_elem.find('.//mattext')
                        if mattext_elem is not None:
                            question_data['question_text'] = self._get_text(mattext_elem)
                
                # Antwortoptionen
                answers = []
                response_elem = presentation_elem.find('.//response_lid') if presentation_elem is not None else None
                if response_elem is not None:
                    for render_choice in response_elem.findall('.//render_choice'):
                        for response_label in render_choice.findall('.//response_label'):
                            answer_data = {
                                'id': self._get_attribute(response_label, 'ident', '')
                            }
                            
                            material_elem = response_label.find('.//material')
                            if material_elem is not None:
                                mattext_elem = material_elem.find('.//mattext')
                                if mattext_elem is not None:
                                    answer_data['text'] = self._get_text(mattext_elem)
                            
                            answers.append(answer_data)
                
                if answers:
                    question_data['answers'] = answers
                
                # Richtige Antworten
                resprocessing_elem = item_elem.find('.//resprocessing')
                if resprocessing_elem is not None:
                    for respcondition in resprocessing_elem.findall('.//respcondition'):
                        varequal_elem = respcondition.find('.//varequal')
                        if varequal_elem is not None:
                            correct_answer = self._get_text(varequal_elem)
                            # Markiere die richtige Antwort
                            for answer in answers:
                                if answer.get('id') == correct_answer:
                                    answer['correct'] = True
                                else:
                                    answer['correct'] = False
                
                questions.append(question_data)
            
            if questions:
                qti_data['questions'] = questions
        
        return qti_data
    
    def _extract_qti_from_filesystem(self) -> List[Dict[str, Any]]:
        """
        Extrahiert QTI-Daten aus dem Dateisystem.
        
        Returns:
            Liste mit Fragedaten
        """
        questions = []
        
        if not self.component_path:
            return questions
        
        try:
            # Suche nach QTI-Dateien im Komponenten-Pfad
            qti_files = []
            for root, dirs, files in os.walk(self.component_path):
                for file in files:
                    if file.lower().endswith('.xml') and ('qti' in file.lower() or 'assessment' in file.lower()):
                        qti_files.append(os.path.join(root, file))
            
            # Parse QTI-Dateien
            for qti_path in qti_files:
                try:
                    tree = ET.parse(qti_path)
                    root = tree.getroot()
                    
                    # Suche nach QTI-Daten
                    qti_elem = root.find('.//questestinterop')
                    if qti_elem is not None:
                        qti_data = self._parse_qti(qti_elem)
                        if 'questions' in qti_data:
                            questions.extend(qti_data['questions'])
                except Exception as e:
                    logger.warning(f"Fehler beim Parsen der QTI-Datei {qti_path}: {str(e)}")
        
        except Exception as e:
            logger.warning(f"Fehler beim Extrahieren von QTI-Daten aus dem Dateisystem: {str(e)}")
        
        return questions 