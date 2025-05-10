import React, { useState, useEffect } from 'react';

const DataPreview = ({ data, sessionId }) => {
  const [expandedSections, setExpandedSections] = useState({
    current_symptoms: true,
    insurance: true,
    medications: true,
    health_records: true
  });
  
  const [rawData, setRawData] = useState(null);
  const [showRawData, setShowRawData] = useState(false);
  
  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };
  
  const toggleAllSections = () => {
    const allExpanded = Object.values(expandedSections).every(v => v !== false);
    
    if (allExpanded) {
      // Collapse all
      const collapsed = {};
      Object.keys(expandedSections).forEach(key => {
        collapsed[key] = false;
      });
      setExpandedSections(collapsed);
    } else {
      // Expand all
      const expanded = {};
      Object.keys(expandedSections).forEach(key => {
        expanded[key] = true;
      });
      setExpandedSections(expanded);
    }
  };
  
  // Function to fetch raw data
  const fetchRawData = async () => {
    if (!sessionId) return;
    
    try {
      const response = await fetch(`http://localhost:8000/json-data/${sessionId}`);
      const data = await response.json();
      setRawData(data);
      setShowRawData(true);
    } catch (error) {
      console.error('Error fetching raw data:', error);
    }
  };
  
  const renderValue = (value, depth = 0) => {
    if (value === null || value === undefined) {
      return <span className="null-value">null</span>;
    }

    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <span className="empty-array">[]</span>;
      }

      return (
        <div style={{ marginLeft: `${depth * 20}px` }}>
          [
          <div style={{ marginLeft: 20 }}>
            {value.map((item, index) => (
              <div key={index}>
                {renderValue(item, depth + 1)}
                {index < value.length - 1 && ','}
              </div>
            ))}
          </div>
          ]
        </div>
      );
    }

    if (typeof value === 'object') {
      const entries = Object.entries(value);
      if (entries.length === 0) {
        return <span className="empty-object">{'{}'}</span>;
      }

      return (
        <div style={{ marginLeft: `${depth * 20}px` }}>
          {'{'}
          <div style={{ marginLeft: 20 }}>
            {entries.map(([key, val], index) => (
              <div key={key}>
                <strong>{key}:</strong> {renderValue(val, depth + 1)}
                {index < entries.length - 1 && ','}
              </div>
            ))}
          </div>
          {'}'}
        </div>
      );
    }

    if (typeof value === 'string') {
      return <span className="string-value">"{value}"</span>;
    }

    return <span>{String(value)}</span>;
  };

  const renderSection = (title, data, sectionKey) => {
    const isExpanded = expandedSections[sectionKey] !== false;

    return (
      <div 
        style={{ 
          margin: '15px 0',
          backgroundColor: '#f8f9fa',
          border: '1px solid #dee2e6',
          borderRadius: '5px',
          overflow: 'hidden'
        }}
      >
        <div 
          onClick={() => toggleSection(sectionKey)} 
          style={{ 
            padding: '10px 15px',
            backgroundColor: '#e9ecef',
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <h3 style={{ margin: 0 }}>{title}</h3>
          <span>{isExpanded ? '▼' : '►'}</span>
        </div>
        
        {isExpanded && (
          <div style={{ padding: '15px' }}>
            {renderValue(data)}
          </div>
        )}
      </div>
    );
  };
  
  const renderRawData = () => {
    if (!rawData) return null;
    
    return (
      <div 
        style={{ 
          margin: '15px 0',
          backgroundColor: '#f8f9fa',
          border: '1px solid #dee2e6',
          borderRadius: '5px',
          overflow: 'hidden'
        }}
      >
        <div 
          onClick={() => setShowRawData(!showRawData)} 
          style={{ 
            padding: '10px 15px',
            backgroundColor: '#e9ecef',
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <h3 style={{ margin: 0 }}>Raw Document Data</h3>
          <span>{showRawData ? '▼' : '►'}</span>
        </div>
        
        {showRawData && (
          <div style={{ padding: '15px', overflowX: 'auto' }}>
            <pre style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '15px', 
              borderRadius: '5px',
              overflowX: 'auto',
              maxHeight: '500px'
            }}>
              {JSON.stringify(rawData, null, 2)}
            </pre>
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ 
      fontFamily: 'monospace', 
      backgroundColor: '#ffffff',
      padding: '20px',
      borderRadius: '8px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      fontSize: '14px',
      lineHeight: '1.5',
      margin: '20px 0'
    }}>
      <h2 style={{ marginTop: 0 }}>Medical Data Details</h2>
      
      {/* Data Sections */}
      {renderSection('Current Symptoms', data.current_symptoms, 'current_symptoms')}
      {renderSection('Insurance', data.insurance, 'insurance')}
      {renderSection('Medications', data.medications, 'medications')}
      {renderSection('Health Records', data.health_records, 'health_records')}
      {renderRawData()}
      
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '20px' }}>
        <button 
          onClick={toggleAllSections}
          style={{ 
            padding: '8px 15px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          {Object.values(expandedSections).every(v => v !== false) ? 'Collapse All' : 'Expand All'}
        </button>
        
        <button 
          onClick={fetchRawData}
          style={{ 
            padding: '8px 15px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Show Raw JSON Data
        </button>
      </div>
    </div>
  );
};

export default DataPreview; 