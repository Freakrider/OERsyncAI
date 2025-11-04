import { useState, useCallback } from 'react';

export default function useApiData() {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

  // Lädt die Ergebnisse für eine Job-ID
  const loadResults = useCallback(async (jobId) => {
    setStatus('loading');
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/extract/${jobId}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      const result = await response.json();
      setData(result);
      setStatus('success');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  }, [API_BASE_URL]);

  // Polling für Job-Status
  const pollJobStatus = useCallback(async (jobId, onComplete, onError) => {
    let attempts = 0;
    const maxAttempts = 60;
    async function check() {
      try {
        const response = await fetch(`${API_BASE_URL}/extract/${jobId}/status`);
        const data = await response.json();
        if (data.status === 'completed') {
          setStatus('success');
          onComplete && onComplete();
        } else if (data.status === 'failed') {
          setStatus('error');
          setError(data.error || 'Unbekannter Fehler');
          onError && onError(data.error);
        } else {
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(check, 1000);
          } else {
            setStatus('error');
            setError('Timeout erreicht. Bitte versuchen Sie es erneut.');
            onError && onError('Timeout erreicht');
          }
        }
      } catch {
        setStatus('error');
        setError('Fehler beim Statuscheck');
        onError && onError('Fehler beim Statuscheck');
      }
    }
    check();
  }, [API_BASE_URL]);

  return { data, status, error, loadResults, pollJobStatus };
} 