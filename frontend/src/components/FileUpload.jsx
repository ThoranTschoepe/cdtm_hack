import React, { useState } from 'react';

const FileUpload = ({ onUpload, isMultiple }) => {
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    
    try {
      // If multiple file upload is enabled, upload each file sequentially
      if (isMultiple) {
        const results = [];
        for (const file of files) {
          const result = await onUpload(file);
          results.push(result);
        }
        setFiles([]);
        return results;
      } else {
        // Just upload the first file
        const result = await onUpload(files[0]);
        setFiles([]);
        return result;
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload file(s)');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{ margin: '15px 0' }}>
      <input
        type="file"
        onChange={handleFileChange}
        multiple={isMultiple}
        accept="image/*"
        disabled={isUploading}
        style={{ margin: '10px 0' }}
      />
      <div>
        {files.length > 0 && (
          <div>
            <p>{files.length} file(s) selected</p>
            <button 
              onClick={handleUpload}
              disabled={isUploading || files.length === 0}
              style={{
                padding: '8px 16px',
                backgroundColor: '#4caf50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {isUploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;