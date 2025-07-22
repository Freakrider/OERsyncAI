import { useContext } from 'react';
import CourseContext from './CourseContext';

export function useCourse() {
  const context = useContext(CourseContext);
  if (!context) throw new Error('useCourse muss innerhalb eines CourseProvider verwendet werden');
  return context;
} 