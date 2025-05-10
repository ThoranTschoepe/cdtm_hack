import React from 'react';

const ResultPreview = ({ extractedData }) => {
  if (!extractedData) return null;

  const renderSection = (title, data, icon = null) => {
    if (!data || (Array.isArray(data) && data.length === 0) || Object.keys(data).length === 0) return null;

    return (
      <div style={{ 
        margin: '10px 0', 
        padding: '12px', 
        backgroundColor: '#f5f9ff',
        borderRadius: '6px',
        borderLeft: '4px solid #3f87e5'
      }}>
        <h4 style={{ margin: '0 0 10px 0', color: '#2c5282' }}>
          {icon && <span style={{ marginRight: '8px' }}>{icon}</span>}
          {title}
        </h4>
        {Array.isArray(data) ? (
          <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
            {data.map((item, index) => (
              <li key={index} style={{ margin: '4px 0' }}>
                {typeof item === 'object' 
                  ? item.name || item.condition || JSON.stringify(item)
                  : item}
              </li>
            ))}
          </ul>
        ) : (
          <div>
            {typeof data === 'object' ? (
              <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                {Object.entries(data).map(([key, value]) => (
                  <li key={key} style={{ margin: '4px 0' }}>
                    <strong>{key.replace(/_/g, ' ').charAt(0).toUpperCase() + key.replace(/_/g, ' ').slice(1)}:</strong>{' '}
                    {typeof value === 'object' ? JSON.stringify(value) : value}
                  </li>
                ))}
              </ul>
            ) : (
              data
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      style={{
        border: '1px solid #d1e3ff',
        borderRadius: '8px',
        padding: '15px',
        margin: '15px 0',
        backgroundColor: '#f8faff',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
      }}
    >
      <h3 style={{ 
        borderBottom: '2px solid #3f87e5', 
        paddingBottom: '8px',
        color: '#2a4365'
      }}>Medical Documentation</h3>
      
      {/* Symptoms information */}
      {extractedData.current_symptoms && Object.keys(extractedData.current_symptoms).length > 0 && (
        <div style={{ 
          margin: '10px 0', 
          padding: '12px', 
          backgroundColor: '#f5f9ff',
          borderRadius: '6px',
          borderLeft: '4px solid #3f87e5'
        }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#2c5282' }}>
            <span style={{ marginRight: '8px' }}>📋</span>
            Clinical Assessment
          </h4>
          {extractedData.current_symptoms.description && (
            <p style={{ margin: '8px 0', fontSize: '15px' }}>
              <strong>Patient Presentation:</strong> {extractedData.current_symptoms.description}
            </p>
          )}
          {extractedData.current_symptoms.extracted_symptoms && extractedData.current_symptoms.extracted_symptoms.length > 0 && (
            <div style={{ marginTop: '10px' }}>
              <strong>Clinical Findings:</strong>
              <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                {extractedData.current_symptoms.extracted_symptoms.map((symptom, index) => (
                  <li key={index} style={{ margin: '4px 0' }}>{symptom}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      
      {/* Insurance information */}
      {renderSection('Insurance Details', extractedData.insurance || {}, '🏥')}
      
      {/* Medications */}
      {renderSection('Prescribed Medications', extractedData.medications || [], '💊')}
      
      {/* Health records */}
      {extractedData.health_records && (
        <>
          {renderSection('Diagnoses & Conditions', extractedData.health_records.diagnoses || [], '🩺')}
          {renderSection('Hospital Encounters', extractedData.health_records.hospital_visits || [], '🏥')}
          {renderSection('Laboratory Results', extractedData.health_records.test_results || [], '🧪')}
        </>
      )}
    </div>
  );
};

export default ResultPreview;