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
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '16px'
    }}>
      {errorMessage ? (
        <div style={{ color: 'white', textAlign: 'center', padding: '20px' }}>
          <p>{errorMessage}</p>
          <button 
            onClick={handleClose}
            style={{
              padding: '10px 20px',
              backgroundColor: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              margin: '10px'
            }}
          >
            Close
          </button>
        </div>
      ) : capturedImage ? (
        // Show preview of captured image
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ 
            maxWidth: '100%', 
            maxHeight: '70vh',
            overflow: 'hidden',
            marginBottom: '20px',
            border: '2px solid white'
          }}>
            <img 
              src={capturedImage.url} 
              alt="Captured" 
              style={{ maxWidth: '100%', maxHeight: '100%' }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '10px' }}>
            <button 
              onClick={retakePicture}
              style={{
                padding: '10px 20px',
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Retake
            </button>
            <button 
              onClick={confirmCapture}
              style={{
                padding: '10px 20px',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
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
            borderRadius: '8px',
            overflow: 'hidden',
            border: '2px solid white'
          }}>
            <video 
              ref={videoRef}
              autoPlay 
              playsInline 
              style={{ width: '100%', display: isCameraReady ? 'block' : 'none' }}
              onCanPlay={() => videoRef.current.play()}
            />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            {!isCameraReady && (
              <div style={{ 
                padding: '40px', 
                color: 'white', 
                textAlign: 'center',
                backgroundColor: '#333' 
              }}>
                Loading camera...
              </div>
            )}
          </div>
          
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            padding: '20px',
            gap: '10px',
            width: '100%'
          }}>
            <button 
              onClick={handleClose}
              style={{
                padding: '10px 20px',
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
            <button 
              onClick={takePicture}
              disabled={!isCameraReady}
              style={{
                padding: '10px 20px',
                backgroundColor: '#1976d2',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: isCameraReady ? 'pointer' : 'not-allowed',
                opacity: isCameraReady ? 1 : 0.7
              }}
            >
              Take Photo
            </button>
            <button 
              onClick={switchCamera}
              disabled={!isCameraReady}
              style={{
                padding: '10px',
                backgroundColor: '#333',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: isCameraReady ? 'pointer' : 'not-allowed',
                opacity: isCameraReady ? 1 : 0.7
              }}
            >
              <span role="img" aria-label="switch camera">🔄</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CameraCapture;