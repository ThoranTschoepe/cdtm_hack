// components/FileUpload.js
import React, { useState, useRef } from 'react';
import CameraCapture from './CameraCapture';

const FileUpload = ({ onUpload, isMultiple = false }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState([]);
  const [showCamera, setShowCamera] = useState(false);
  const fileInputRef = useRef(null);
  
  // Check if camera is available
  const [isCameraAvailable, setIsCameraAvailable] = useState(false);
  
  React.useEffect(() => {
    // Check if the browser supports getUserMedia
    setIsCameraAvailable(
      !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
    );
  }, []);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = (fileList) => {
    const newFiles = [...files];
    
    for (let i = 0; i < fileList.length; i++) {
      newFiles.push(fileList[i]);
    }
    
    setFiles(newFiles);
  };

  const handleCameraCapture = (file) => {
    const newFiles = [...files, file];
    setFiles(newFiles);
    setShowCamera(false);
  };

  const removeFile = (index) => {
    const newFiles = [...files];
    newFiles.splice(index, 1);
    setFiles(newFiles);
  };

  const handleUpload = () => {
    if (files.length > 0) {
      onUpload(isMultiple ? files : files[0]);
      setFiles([]);
    }
  };

  const handleSkip = () => {
    onUpload("skip");
  };

  return (
    <div className="file-upload-container" style={{ marginBottom: '30px' }}>
      {showCamera ? (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={() => setShowCamera(false)}
        />
      ) : (
        <>
          <div
            className={`drop-area ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current.click()}
            style={{
              border: `2px solid ${isDragging ? '#1976d2' : '#e0e0e0'}`, // Solid border looks cleaner
              borderRadius: '12px',
              padding: '40px 20px', // More vertical padding
              textAlign: 'center',
              cursor: 'pointer',
              marginBottom: '20px',
              backgroundColor: isDragging ? 'rgba(25, 118, 210, 0.05)' : '#f9f9f9',
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 8px rgba(0,0,0,0.05)', // Subtle shadow
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '200px' // Ensure consistent height
            }}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileInputChange}
              multiple={isMultiple}
              accept="image/*,.pdf"
              style={{ display: 'none' }}
            />
            
            <div style={{ 
              width: '70px', 
              height: '70px', 
              backgroundColor: '#e3f2fd', 
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '16px'
            }}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1976d2" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="12" y1="18" x2="12" y2="12"></line>
                <line x1="9" y1="15" x2="15" y2="15"></line>
              </svg>
            </div>
            
            <h3 style={{ 
              margin: '0 0 8px 0', 
              color: '#333',
              fontSize: '18px',
              fontWeight: '500'
            }}>
              Drag & drop files here or click to browse
            </h3>
            
            <p style={{ 
              margin: '0', 
              color: '#666', 
              fontSize: '14px',
              maxWidth: '80%',
              lineHeight: '1.5'
            }}>
              {isMultiple ? 'You can upload multiple documents or photos at once' : 'Please upload a single file'}
            </p>
          </div>

          {/* Action buttons */}
          <div className="upload-actions" style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            alignItems: 'center'
          }}>
            {/* Camera capture button */}
            {isCameraAvailable && (
              <button
                onClick={() => setShowCamera(true)}
                style={{
                  padding: '12px 20px',
                  backgroundColor: '#009688',
                  color: 'white',
                  border: 'none',
                  borderRadius: '30px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  width: '100%',
                  maxWidth: '320px',
                  fontSize: '15px',
                  fontWeight: '500',
                  boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
                  transition: 'all 0.2s ease'
                }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                  <circle cx="12" cy="13" r="4"></circle>
                </svg>
                Take Photo with Camera
              </button>
            )}

            {/* Skip button */}
            <button
              onClick={handleSkip}
              style={{
                padding: '12px 20px',
                backgroundColor: 'transparent',
                color: '#666',
                border: '1px solid #ddd',
                borderRadius: '30px',
                cursor: 'pointer',
                width: '100%',
                maxWidth: '320px',
                fontSize: '15px',
                transition: 'all 0.2s ease',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
              }}
            >
              Skip Document Upload
            </button>
          </div>

          {/* File list */}
          {files.length > 0 && (
            <div className="file-list" style={{ 
              marginTop: '25px',
              backgroundColor: 'white',
              borderRadius: '10px',
              padding: '16px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
              border: '1px solid #eee',
            }}>
              <h3 style={{ 
                fontSize: '16px', 
                margin: '0 0 12px 0',
                color: '#333',
                fontWeight: '500'
              }}>
                Selected Files ({files.length})
              </h3>
              
              <ul style={{ 
                listStyle: 'none', 
                padding: '0',
                margin: '0 0 15px 0',
                maxHeight: '200px',
                overflowY: 'auto',
              }}>
                {files.map((file, index) => (
                  <li key={index} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '10px 0',
                    borderBottom: index < files.length - 1 ? '1px solid #f0f0f0' : 'none'
                  }}>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center',
                      overflow: 'hidden'
                    }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="2" style={{ marginRight: '8px', flexShrink: 0 }}>
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                      </svg>
                      <span style={{ 
                        overflow: 'hidden', 
                        textOverflow: 'ellipsis', 
                        whiteSpace: 'nowrap',
                        fontSize: '14px',
                        color: '#333'
                      }}>
                        {file.name}
                      </span>
                    </div>
                    <button 
                      onClick={() => removeFile(index)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#f44336',
                        cursor: 'pointer',
                        fontSize: '18px',
                        display: 'flex',
                        padding: '4px',
                        borderRadius: '50%',
                        transition: 'all 0.2s ease',
                        ':hover': {
                          backgroundColor: 'rgba(244, 67, 54, 0.1)'
                        }
                      }}
                      aria-label="Remove file"
                    >
                      ×
                    </button>
                  </li>
                ))}
              </ul>
              
              <button
                onClick={handleUpload}
                style={{
                  padding: '12px 20px',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '30px',
                  cursor: 'pointer',
                  width: '100%',
                  fontSize: '15px',
                  fontWeight: '500',
                  boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
                  transition: 'all 0.2s ease'
                }}
              >
                Upload {files.length} {files.length === 1 ? 'File' : 'Files'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default FileUpload;