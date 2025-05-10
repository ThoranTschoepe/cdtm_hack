// components/AudioRecorder.js
import React, { useState, useRef } from 'react';

const AudioRecorder = ({ onResponse, sessionId }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        onResponse(audioBlob);
        
        // Stop all audio tracks
        stream.getTracks().forEach(track => track.stop());
        
        // Reset recording time
        clearInterval(timerRef.current);
        setRecordingTime(0);
      };
      
      // Start recording
      mediaRecorderRef.current.start();
      setIsRecording(true);
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Unable to access microphone. Please check your browser permissions.');
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Clear timer
      clearInterval(timerRef.current);
    }
  };
  
  // Format seconds to MM:SS
  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{
      marginBottom: '20px',
      display: 'flex',
      justifyContent: 'center'
    }}>
      <button
        onClick={isRecording ? stopRecording : startRecording}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: isRecording ? '#f44336' : '#1976d2',
          color: 'white',
          border: 'none',
          borderRadius: '30px',
          padding: '10px 20px',
          cursor: 'pointer',
          fontSize: '15px',
          fontWeight: '500',
          transition: 'all 0.2s ease',
          boxShadow: '0 2px 5px rgba(0,0,0,0.1)',
          width: isRecording ? '140px' : 'auto',
        }}
      >
        <span style={{ marginRight: '8px' }}>
          {isRecording ? '■' : '🎤'}
        </span>
        {isRecording ? `Stop (${formatTime(recordingTime)})` : "Start Voice Input"}
      </button>
    </div>
  );
};

export default AudioRecorder;