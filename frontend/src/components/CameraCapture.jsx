// components/CameraCapture.js
import React, { useRef, useState, useEffect } from 'react';

const CameraCapture = ({ onCapture, onClose }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [facingMode, setFacingMode] = useState('environment'); // 'environment' for back camera, 'user' for front

  // Initialize camera
  useEffect(() => {
    const startCamera = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: facingMode }
        });
        
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
          setStream(mediaStream);
          setIsCameraReady(true);
          setErrorMessage('');
        }
      } catch (err) {
        console.error('Error accessing camera:', err);
        setErrorMessage('Unable to access camera. Please make sure you have granted camera permissions.');
        setIsCameraReady(false);
      }
    };

    startCamera();

    // Cleanup function
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [facingMode]);

  // Switch between front and back camera
  const switchCamera = () => {
    // Stop current stream
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    
    // Toggle facing mode
    setFacingMode(facingMode === 'environment' ? 'user' : 'environment');
  };

  // Take picture from video stream
  const takePicture = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      // Set canvas dimensions to match video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      // Draw current video frame to canvas
      const context = canvas.getContext('2d');
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      // Convert canvas to blob
      canvas.toBlob(blob => {
        // Create a preview URL
        const imageUrl = URL.createObjectURL(blob);
        setCapturedImage({
          blob,
          url: imageUrl,
          name: `capture_${new Date().toISOString()}.jpg`
        });
      }, 'image/jpeg', 0.95); // JPEG at 95% quality
    }
  };

  // Use the captured image
  const confirmCapture = () => {
    if (capturedImage) {
      // Create a File object from the Blob
      const file = new File([capturedImage.blob], capturedImage.name, {
        type: 'image/jpeg',
        lastModified: new Date().getTime()
      });
      
      // Pass the file back to parent component
      onCapture(file);
      
      // Cleanup
      URL.revokeObjectURL(capturedImage.url);
      setCapturedImage(null);
      onClose();
    }
  };

  // Retake the picture
  const retakePicture = () => {
    if (capturedImage) {
      URL.revokeObjectURL(capturedImage.url);
      setCapturedImage(null);
    }
  };

  // Close camera and cleanup
  const handleClose = () => {
    if (capturedImage) {
      URL.revokeObjectURL(capturedImage.url);
    }
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    onClose();
  };

  return (
    <div className="camera-capture-container" style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      backgroundColor: 'rgba(0, 0, 0, 0.95)',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '16px'
    }}>
      {errorMessage ? (
        <div style={{ color: 'white', textAlign: 'center', padding: '20px', maxWidth: '400px' }}>
          <div style={{ 
            backgroundColor: 'rgba(244, 67, 54, 0.1)', 
            padding: '20px',
            borderRadius: '10px',
            marginBottom: '20px',
            border: '1px solid rgba(244, 67, 54, 0.3)'
          }}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#f44336" strokeWidth="2" style={{ marginBottom: '15px' }}>
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <p style={{ color: '#f44336', fontWeight: '500', fontSize: '18px' }}>Camera Error</p>
            <p style={{ color: 'white' }}>{errorMessage}</p>
          </div>
          <button 
            onClick={handleClose}
            style={{
              padding: '12px 24px',
              backgroundColor: 'white',
              color: '#333',
              border: 'none',
              borderRadius: '30px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: '500'
            }}
          >
            Close
          </button>
        </div>
      ) : capturedImage ? (
        // Show preview of captured image
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', maxWidth: '500px' }}>
          <div style={{ 
            width: '100%',
            maxHeight: '70vh',
            overflow: 'hidden',
            marginBottom: '20px',
            borderRadius: '10px',
            boxShadow: '0 0 20px rgba(0,0,0,0.5)',
            position: 'relative'
          }}>
            <img 
              src={capturedImage.url} 
              alt="Captured" 
              style={{ width: '100%', display: 'block' }}
            />
            <div style={{
              position: 'absolute',
              top: '15px',
              right: '15px',
              backgroundColor: 'rgba(0,0,0,0.5)',
              color: 'white',
              padding: '5px 10px',
              borderRadius: '20px',
              fontSize: '14px'
            }}>
              Preview
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '15px', width: '100%' }}>
            <button 
              onClick={retakePicture}
              style={{
                padding: '12px 24px',
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.4)',
                borderRadius: '30px',
                cursor: 'pointer',
                flex: 1,
                maxWidth: '150px',
                fontSize: '15px',
                transition: 'all 0.2s ease'
              }}
            >
              Retake
            </button>
            <button 
              onClick={confirmCapture}
              style={{
                padding: '12px 24px',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '30px',
                cursor: 'pointer',
                flex: 1,
                maxWidth: '150px',
                fontSize: '15px',
                fontWeight: '500',
                transition: 'all 0.2s ease'
              }}
            >
              Use Photo
            </button>
          </div>
        </div>
      ) : (
        // Show camera view
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          width: '100%',
          maxWidth: '500px' 
        }}>
          <div style={{ 
            width: '100%', 
            position: 'relative',
            borderRadius: '10px',
            overflow: 'hidden',
            boxShadow: '0 0 20px rgba(0,0,0,0.5)',
            backgroundColor: '#000'
          }}>
            <video 
              ref={videoRef}
              autoPlay 
              playsInline 
              style={{ 
                width: '100%', 
                display: isCameraReady ? 'block' : 'none',
                borderRadius: '10px'
              }}
              onCanPlay={() => videoRef.current.play()}
            />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            
            {/* Camera overlay with focus guides */}
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              pointerEvents: 'none',
              borderRadius: '10px',
              border: '2px solid rgba(255,255,255,0.3)',
              boxSizing: 'border-box'
            }}>
              <div style={{
                position: 'absolute',
                top: '15px',
                left: '15px',
                width: '50px',
                height: '50px',
                borderLeft: '2px solid rgba(255,255,255,0.6)',
                borderTop: '2px solid rgba(255,255,255,0.6)',
                borderRadius: '10px 0 0 0'
              }} />
              <div style={{
                position: 'absolute',
                top: '15px',
                right: '15px',
                width: '50px',
                height: '50px',
                borderRight: '2px solid rgba(255,255,255,0.6)',
                borderTop: '2px solid rgba(255,255,255,0.6)',
                borderRadius: '0 10px 0 0'
              }} />
              <div style={{
                position: 'absolute',
                bottom: '15px',
                left: '15px',
                width: '50px',
                height: '50px',
                borderLeft: '2px solid rgba(255,255,255,0.6)',
                borderBottom: '2px solid rgba(255,255,255,0.6)',
                borderRadius: '0 0 0 10px'
              }} />
              <div style={{
                position: 'absolute',
                bottom: '15px',
                right: '15px',
                width: '50px',
                height: '50px',
                borderRight: '2px solid rgba(255,255,255,0.6)',
                borderBottom: '2px solid rgba(255,255,255,0.6)',
                borderRadius: '0 0 10px 0'
              }} />
            </div>
            
            {!isCameraReady && (
              <div style={{ 
                padding: '60px 20px', 
                color: 'white', 
                textAlign: 'center',
              }}>
                <div className="loading-spinner" style={{
                  width: '40px',
                  height: '40px',
                  margin: '0 auto 20px',
                  border: '4px solid rgba(255,255,255,0.2)',
                  borderRadius: '50%',
                  borderTop: '4px solid white',
                  animation: 'spin 1s linear infinite'
                }}></div>
                <style>{`
                  @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                  }
                `}</style>
                Activating camera...
              </div>
            )}
          </div>
          
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            padding: '25px 0',
            gap: '15px',
            width: '100%'
          }}>
            <button 
              onClick={handleClose}
              style={{
                padding: '12px 20px',
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.4)',
                borderRadius: '30px',
                cursor: 'pointer',
                fontSize: '15px',
                minWidth: '90px'
              }}
            >
              Cancel
            </button>
            <button 
              onClick={takePicture}
              disabled={!isCameraReady}
              style={{
                padding: '12px 20px',
                backgroundColor: isCameraReady ? '#1976d2' : 'rgba(25, 118, 210, 0.3)',
                color: 'white',
                border: 'none',
                borderRadius: '30px',
                cursor: isCameraReady ? 'pointer' : 'not-allowed',
                fontSize: '15px',
                fontWeight: '500',
                minWidth: '90px',
                position: 'relative'
              }}
            >
              <div style={{
                width: '50px',
                height: '50px',
                borderRadius: '50%',
                border: '3px solid white',
                backgroundColor: isCameraReady ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.1)',
                position: 'absolute',
                left: '50%',
                top: '50%',
                transform: 'translate(-50%, -50%)'
              }}></div>
            </button>
            <button 
              onClick={switchCamera}
              disabled={!isCameraReady}
              style={{
                padding: '12px 20px',
                backgroundColor: 'rgba(0,0,0,0.4)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)',
                borderRadius: '30px',
                cursor: isCameraReady ? 'pointer' : 'not-allowed',
                fontSize: '15px',
                minWidth: '90px',
                opacity: isCameraReady ? 1 : 0.5
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CameraCapture;