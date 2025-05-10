import React, { useState, useRef } from 'react';
import Recorder from 'recorder-js';

function AudioRecorder({ sessionId, onResponse }) {
  const [recording, setRecording] = useState(false);
  const recorderRef = useRef(null);
  const audioContextRef = useRef(null);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    recorderRef.current = new Recorder(audioContextRef.current, {
      // optional: specify encoding
      type: 'audio/wav'
    });

    recorderRef.current.init(stream);
    recorderRef.current.start();
    setRecording(true);
  };

  const stopRecording = async () => {
    const { blob } = await recorderRef.current.stop();
    setRecording(false);
  
    try {
      // ⬅️ Let App.js handle sending to backend + chat update
      onResponse(blob);
    } catch (err) {
      console.error("Recording failed:", err);
    }
  };

  return (
    <div style={{ marginTop: '10px' }}>
      <button
        onClick={recording ? stopRecording : startRecording}
        style={{
          padding: '12px 20px',
          backgroundColor: recording ? '#d32f2f' : '#1976d2',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          fontSize: '16px',
          cursor: 'pointer'
        }}
      >
        🎤 {recording ? 'Stop Recording' : 'Start Voice Input'}
      </button>
    </div>
  );
}

export default AudioRecorder;
