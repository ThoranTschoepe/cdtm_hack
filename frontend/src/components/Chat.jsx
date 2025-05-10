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
      height: '500px', // Increased height for better readability
      overflowY: 'auto',
      border: '1px solid #e0e0e0', // Lighter border
      borderRadius: '12px', // Increased border radius
      padding: '20px',
      marginBottom: '20px',
      position: 'relative',
      boxShadow: '0 2px 10px rgba(0,0,0,0.05)', // Subtle shadow
      background: '#f9f9f9' // Light background to differentiate from the page
    }}>
      {/* AudioPlayer component handles autoplay */}
      <AudioPlayer audioUrl={latestAudioUrl} autoPlay={true} />
      
      {messages.map((message, index) => (
        <div 
          key={index}
          style={{
            display: 'flex',
            justifyContent: message.isUser ? 'flex-end' : 'flex-start',
            marginBottom: '16px',
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
              maxWidth: '75%',
              padding: '12px 16px',
              paddingLeft: !message.isUser && index === messages.length - 1 ? '30px' : '16px',
              borderRadius: '18px',
              backgroundColor: message.isUser ? '#1976d2' : 'white', // White background for assistant messages
              color: message.isUser ? 'white' : '#333', // Darker text for better readability
              boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
              border: message.isUser ? 'none' : '1px solid #e0e0e0', // Border for assistant messages
              fontSize: '15px', // Slightly larger font
              lineHeight: '1.5' // Better line spacing
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