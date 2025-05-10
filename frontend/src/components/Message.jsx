import React from 'react';

const Message = ({ message, isUser }) => {
  const getMessageStyle = () => {
    return {
      background: isUser ? '#e3f2fd' : '#f5f5f5',
      borderRadius: '10px',
      padding: '10px 15px',
      margin: '5px 0',
      maxWidth: '70%',
      alignSelf: isUser ? 'flex-end' : 'flex-start',
    };
  };

  return (
    <div style={getMessageStyle()}>
      <p style={{ margin: 0 }}>{message}</p>
    </div>
  );
};

export default Message;