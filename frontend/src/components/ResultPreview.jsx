import React from 'react';

const ResultPreview = ({ extractedData }) => {
  if (!extractedData) return null;

  const renderSection = (title, data) => {
    if (!data || (Array.isArray(data) && data.length === 0)) return null;

    return (
      <div style={{ margin: '10px 0' }}>
        <h4>{title}</h4>
        {Array.isArray(data) ? (
          <ul>
            {data.map((item, index) => (
              <li key={index}>
                {typeof item === 'object' 
                  ? item.name || item.condition || JSON.stringify(item)
                  : item}
              </li>
            ))}
          </ul>
        ) : (
          <div>{JSON.stringify(data)}</div>
        )}
      </div>
    );
  };

  return (
    <div
      style={{
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        padding: '15px',
        margin: '15px 0',
        backgroundColor: '#f9f9f9'
      }}
    >
      <h3>Extracted Information</h3>
      
      {renderSection('Patient Information', extractedData.patient)}
      {renderSection('Medications', extractedData.medications)}
      {renderSection('Diagnoses', extractedData.diagnoses)}
      {renderSection('Hospital Visits', extractedData.hospital_visits)}
      {renderSection('Test Results', extractedData.test_results)}
    </div>
  );
};

export default ResultPreview;