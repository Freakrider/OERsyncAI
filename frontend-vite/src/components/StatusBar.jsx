import React from 'react';

export default function StatusBar({ message, type }) {
  if (!message) return null;
  return (
    <div className={`status ${type}`.trim()} style={{ margin: '20px 0' }}>
      {message}
      {type === 'loading' && (
        <>
          <div className="loading-spinner" style={{ margin: '10px auto' }}></div>
          <div className="progress-bar"><div className="progress-fill" style={{ width: '100%' }}></div></div>
        </>
      )}
    </div>
  );
} 