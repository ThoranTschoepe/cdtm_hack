import React, { useState } from 'react';

const UserInput = ({ onSend, disabled }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSend(input);
      setInput('');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', margin: '15px 0' }}>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={disabled}
        placeholder="Type your answer..."
        style={{
          flexGrow: 1,
          padding: '10px',
          borderRadius: '4px',
          border: '1px solid #ddd',
          marginRight: '10px'
        }}
      />
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        style={{
          padding: '10px 20px',
          backgroundColor: '#2196f3',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: disabled || !input.trim() ? 'not-allowed' : 'pointer'
        }}
      >
        Send
      </button>
    </form>
  );
};

export default UserInput;