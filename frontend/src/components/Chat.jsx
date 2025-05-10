// components/Chat.js
import React, { useRef, useEffect } from 'react';
import AudioPlayer from './AudioPlayer';

const Chat = ({ messages, latestAudioUrl }) => {
  const messagesEndRef = useRef(null);

  // Auto-scroll to the most recent message
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div className="chat-container" style={{ 
      height: '400px', 
      overflowY: 'auto',
      border: '1px solid #ddd',
      borderRadius: '8px',
      padding: '16px',
      marginBottom: '20px',
      position: 'relative'
    }}>
      {/* AudioPlayer component handles autoplay */}
      <AudioPlayer audioUrl={latestAudioUrl} autoPlay={true} />
      
      {messages.map((message, index) => (
        <div 
          key={index}
          style={{
            display: 'flex',
            justifyContent: message.isUser ? 'flex-end' : 'flex-start',
            marginBottom: '10px',
            position: 'relative'
          }}
        >
          {!message.isUser && index === messages.length - 1 && (
            <div 
              style={{
                position: 'absolute',
                top: '-2px',
                left: '-2px',
                fontSize: '16px',
                opacity: '0.7'
              }}
              title="This message will be spoken"
            >
              🔊
            </div>
          )}
          <div 
            style={{
              maxWidth: '70%',
              padding: '10px 15px',
              paddingLeft: !message.isUser && index === messages.length - 1 ? '25px' : '15px',
              borderRadius: '18px',
              backgroundColor: message.isUser ? '#1976d2' : '#f1f1f1',
              color: message.isUser ? 'white' : 'black',
              boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
            }}
          >
            {message.text}
          </div>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default Chat;