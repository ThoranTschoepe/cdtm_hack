import React, { useState, useRef } from 'react';

function AudioRecorder({ sessionId, onResponse }) {
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunks = useRef([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);

    audioChunks.current = [];

    mediaRecorderRef.current.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.current.push(event.data);
      }
    };

    mediaRecorderRef.current.onstop = async () => {
      const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
      audioChunks.current = [];

      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');

      try {
        const res = await fetch(`http://localhost:8000/answer_transcribe/${sessionId}`, {
          method: 'POST',
          body: formData
        });

        const data = await res.json();
        onResponse({ text: data.message || data.text, isUser: false });
      } catch (err) {
        console.error("Upload error:", err);
        onResponse({ text: 'Error transcribing audio. Please try again.', isUser: false });
      }
    };

    mediaRecorderRef.current.start();
    setRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current.stop();
    setRecording(false);
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
          cursor: 'pointer',
          transition: 'background-color 0.3s'
        }}
      >
        🎤 {recording ? 'Stop Recording' : 'Start Voice Input'}
      </button>
    </div>
  );
}

export default AudioRecorder;
