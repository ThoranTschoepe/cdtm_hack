// components/UserInput.js
import React, { useState } from 'react';

const UserInput = ({ onSend, disabled }) => {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !disabled) {
      onSend(text);
      setText('');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ 
      marginBottom: '15px', 
      display: 'flex',
      alignItems: 'center',
      position: 'relative'
    }}>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type your answer..."
        disabled={disabled}
        style={{
          flex: 1,
          padding: '14px 16px',
          paddingRight: '100px', // Space for the button
          fontSize: '16px',
          borderRadius: '30px',
          border: '1px solid #e0e0e0',
          outline: 'none',
          boxShadow: '0 2px 5px rgba(0,0,0,0.05)',
          transition: 'all 0.3s ease',
          ':focus': {
            borderColor: '#1976d2',
            boxShadow: '0 2px 8px rgba(25, 118, 210, 0.25)'
          }
        }}
      />
      <button
        type="submit"
        disabled={!text.trim() || disabled}
        style={{
          position: 'absolute',
          right: '4px',
          top: '4px',
          bottom: '4px',
          padding: '0 20px',
          backgroundColor: '#1976d2',
          color: 'white',
          border: 'none',
          borderRadius: '30px',
          cursor: text.trim() && !disabled ? 'pointer' : 'not-allowed',
          opacity: text.trim() && !disabled ? 1 : 0.7,
          fontSize: '15px',
          fontWeight: '500',
          transition: 'all 0.2s ease'
        }}
      >
        Send
      </button>
    </form>
  );
};

export default UserInput;