// components/AudioIndicator.js
import React, { useState, useEffect } from 'react';

const AudioIndicator = ({ isPlaying }) => {
  const [visible, setVisible] = useState(false);
  
  useEffect(() => {
    if (isPlaying) {
      setVisible(true);
      // Hide after 3 seconds
      const timer = setTimeout(() => {
        setVisible(false);
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [isPlaying]);
  
  if (!visible) return null;
  
  return (
    <div 
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        backgroundColor: 'rgba(25, 118, 210, 0.8)',
        color: 'white',
        padding: '8px 16px',
        borderRadius: '20px',
        display: 'flex',
        alignItems: 'center',
        boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
        zIndex: 1000,
        animation: 'fadeIn 0.3s ease-in-out'
      }}
    >
      <span style={{ marginRight: '8px' }}>🔊</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
        {[1, 2, 3].map(i => (
          <div 
            key={i}
            style={{
              width: '4px',
              height: '10px',
              backgroundColor: 'white',
              borderRadius: '2px',
              animation: `soundWave 0.8s infinite ${i * 0.2}s`,
            }}
          />
        ))}
      </div>
      <style jsx>{`
        @keyframes soundWave {
          0% { height: 4px; }
          50% { height: 16px; }
          100% { height: 4px; }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default AudioIndicator;