import React, { useEffect, useRef } from 'react';
import Message from './Message';

const Chat = ({ messages, latestAudioUrl }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '60vh',
        overflowY: 'auto',
        padding: '15px',
        border: '1px solid #ddd',
        borderRadius: '8px',
        backgroundColor: '#fafafa'
      }}
    >
      {messages.map((msg, index) => (
        <Message key={index} message={msg.text} isUser={msg.isUser} />
      ))}

      {latestAudioUrl && (
        <div style={{ textAlign: 'center', marginTop: '10px' }}>
          <button
            onClick={() => {
              const audio = new Audio(latestAudioUrl);
              audio.play().catch(e => {
                console.warn("Playback failed:", e);
              });
            }}
            style={{
              padding: '8px 16px',
              backgroundColor: '#4caf50',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            🔊 Replay Last Response
          </button>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
};

export default Chat;
