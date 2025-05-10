import React, { useEffect, useRef } from 'react';
import Message from './Message';

const Chat = ({ messages }) => {
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
      <div ref={messagesEndRef} />
    </div>
  );
};

export default Chat;