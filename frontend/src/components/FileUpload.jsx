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
    <div className="file-upload-container" style={{ marginBottom: '20px' }}>
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
              border: `2px dashed ${isDragging ? '#1976d2' : '#ccc'}`,
              borderRadius: '8px',
              padding: '30px',
              textAlign: 'center',
              cursor: 'pointer',
              marginBottom: '15px',
              backgroundColor: isDragging ? 'rgba(25, 118, 210, 0.05)' : 'transparent',
              transition: 'all 0.2s ease'
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
            <p style={{ margin: '0 0 10px 0' }}>
              Drag & drop files here or click to browse
            </p>
            <span style={{ 
              fontSize: '40px', 
              display: 'block', 
              marginBottom: '10px' 
            }}>
              📄
            </span>
            <p style={{ margin: '0', color: '#666', fontSize: '0.9em' }}>
              {isMultiple ? 'You can upload multiple files' : 'Please upload a single file'}
            </p>
          </div>

          {/* Camera capture button */}
          {isCameraAvailable && (
            <div className="camera-option" style={{
              display: 'flex',
              justifyContent: 'center',
              marginBottom: '15px'
            }}>
              <button
                onClick={() => setShowCamera(true)}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#009688',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <span role="img" aria-label="camera">📷</span>
                Take Photo with Camera
              </button>
            </div>
          )}

          {/* File list */}
          {files.length > 0 && (
            <div className="file-list" style={{ marginBottom: '15px' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '10px' }}>Selected Files:</h3>
              <ul style={{ 
                listStyle: 'none', 
                padding: '0',
                margin: '0 0 15px 0',
                maxHeight: '200px',
                overflowY: 'auto',
                border: '1px solid #eee',
                borderRadius: '4px',
                padding: '10px'
              }}>
                {files.map((file, index) => (
                  <li key={index} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '8px',
                    borderBottom: index < files.length - 1 ? '1px solid #eee' : 'none'
                  }}>
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {file.name}
                    </span>
                    <button 
                      onClick={() => removeFile(index)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#f44336',
                        cursor: 'pointer',
                        fontSize: '1.1rem'
                      }}
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
              <button
                onClick={handleUpload}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  width: '100%'
                }}
              >
                Upload {files.length} {files.length === 1 ? 'File' : 'Files'}
              </button>
            </div>
          )}

          {/* Skip button */}
          <div style={{ textAlign: 'center', marginTop: '10px' }}>
            <button
              onClick={handleSkip}
              style={{
                padding: '8px 16px',
                backgroundColor: 'transparent',
                color: '#666',
                border: '1px solid #ccc',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Skip Document Upload
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default FileUpload;