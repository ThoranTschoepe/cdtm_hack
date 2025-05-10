import React, { useState } from 'react';

const FileUpload = ({ onUpload, isMultiple = false }) => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (event) => {
    if (event.target.files && event.target.files.length > 0) {
      // Convert FileList to Array
      const filesArray = Array.from(event.target.files);
      setSelectedFiles(filesArray);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      // Convert FileList to Array
      const filesArray = Array.from(event.dataTransfer.files);
      
      // Filter to only image files
      const imageFiles = filesArray.filter(file => 
        file.type.startsWith('image/') || file.type === 'application/pdf'
      );
      
      if (imageFiles.length === 0) {
        alert('Please upload image or PDF files only.');
        return;
      }
      
      setSelectedFiles(imageFiles);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    
    if (selectedFiles.length === 0) {
      alert('Please select at least one file to upload.');
      return;
    }
    
    // Pass all files to the onUpload handler
    // If isMultiple is false, just pass the first file for backward compatibility
    if (isMultiple) {
      onUpload(selectedFiles);
    } else {
      onUpload(selectedFiles[0]);
    }
    
    // Clear selection after upload
    setSelectedFiles([]);
  };

  const handleSkip = () => {
    // Call onUpload with "skip" to indicate user is skipping
    onUpload("skip");
  };

  return (
    <div style={{ margin: '20px 0' }}>
      <form onSubmit={handleSubmit}>
        <div 
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${isDragging ? '#2196F3' : '#ccc'}`,
            borderRadius: '4px',
            padding: '20px',
            textAlign: 'center',
            backgroundColor: isDragging ? '#f0f8ff' : '#f9f9f9',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
          }}
        >
          <input
            type="file"
            onChange={handleFileChange}
            multiple={isMultiple}
            accept="image/*,application/pdf"
            style={{ display: 'none' }}
            id="file-input"
          />
          <label htmlFor="file-input" style={{ cursor: 'pointer', display: 'block' }}>
            {isDragging
              ? 'Drop files here'
              : 'Drag and drop files here or click to browse'}
          </label>
          
          {selectedFiles.length > 0 && (
            <div style={{ marginTop: '15px', textAlign: 'left' }}>
              <h4>Selected Files:</h4>
              <ul style={{ paddingLeft: '20px' }}>
                {selectedFiles.map((file, index) => (
                  <li key={index}>
                    {file.name} ({(file.size / 1024).toFixed(2)} KB)
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px' }}>
          <button
            type="submit"
            disabled={selectedFiles.length === 0}
            style={{
              padding: '10px 15px',
              backgroundColor: selectedFiles.length === 0 ? '#cccccc' : '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: selectedFiles.length === 0 ? 'not-allowed' : 'pointer'
            }}
          >
            {selectedFiles.length > 1 ? 'Upload Files' : 'Upload File'}
          </button>
          
          <button
            type="button"
            onClick={handleSkip}
            style={{
              padding: '10px 15px',
              backgroundColor: '#9e9e9e',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Skip
          </button>
        </div>
      </form>
    </div>
  );
};

export default FileUpload;