// App.js
import React, { useState, useEffect } from 'react';
import './App.css';
import ChatContainer from './components/ChatContainer';
import DocumentList from './components/DocumentList';
import { createSession, getNextQuestion, submitAnswer, uploadDocument } from './services/api';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [currentMessage, setCurrentMessage] = useState('');
  const [awaitingFollowup, setAwaitingFollowup] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [extractedDocuments, setExtractedDocuments] = useState([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Initialize session when component mounts
    initializeSession();
  }, []);

  const initializeSession = async () => {
    try {
      setLoading(true);
      const response = await createSession();
      setSessionId(response.session_id);
      
      // Get the first question
      const questionResponse = await getNextQuestion(response.session_id);
      setCurrentMessage(questionResponse.message);
      setAwaitingFollowup(questionResponse.awaiting_followup);
      setIsDone(questionResponse.done);
      setQuestionIndex(questionResponse.current_question_index);
      
      setLoading(false);
    } catch (error) {
      console.error('Error initializing session:', error);
      setLoading(false);
    }
  };

  const handleAnswer = async (answer) => {
    if (!sessionId) return;
    
    try {
      setLoading(true);
      
      // Add user's response to conversation history
      setConversationHistory(prev => [
        ...prev, 
        { role: 'user', content: answer }
      ]);
      
      const response = await submitAnswer(sessionId, answer);
      
      // Add bot's response to conversation history
      setConversationHistory(prev => [
        ...prev, 
        { role: 'bot', content: response.message }
      ]);
      
      setCurrentMessage(response.message);
      setAwaitingFollowup(response.awaiting_followup);
      setIsDone(response.done);
      setQuestionIndex(response.current_question_index);
      
      setLoading(false);
    } catch (error) {
      console.error('Error submitting answer:', error);
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    if (!sessionId) return;
    
    try {
      setLoading(true);
      
      // Add document upload to conversation history
      setConversationHistory(prev => [
        ...prev, 
        { role: 'user', content: `Uploaded document: ${file.name}` }
      ]);
      
      const response = await uploadDocument(sessionId, file);
      
      if (response.success) {
        // Add document details to the list
        setExtractedDocuments(prev => [
          ...prev,
          {
            filename: response.filename,
            data: response.extracted_data,
            document_types: response.document_types
          }
        ]);
        
        // Get next question
        const nextQuestion = await getNextQuestion(sessionId);
        
        // Add bot's response to conversation history
        setConversationHistory(prev => [
          ...prev, 
          { 
            role: 'bot', 
            content: `Document processed. Document type: ${response.document_types.join(', ')}`,
            extractedData: response.extracted_data 
          },
          {
            role: 'bot',
            content: nextQuestion.message
          }
        ]);
        
        setCurrentMessage(nextQuestion.message);
        setAwaitingFollowup(nextQuestion.awaiting_followup);
        setIsDone(nextQuestion.done);
        setQuestionIndex(nextQuestion.current_question_index);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error uploading document:', error);
      setLoading(false);
    }
  };

  const resetSession = () => {
    setConversationHistory([]);
    setExtractedDocuments([]);
    initializeSession();
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Medical Onboarding App</h1>
      </header>
      
      <div className="app-container">
        <div className="main-content">
          <ChatContainer 
            currentMessage={currentMessage}
            awaitingFollowup={awaitingFollowup}
            isDone={isDone}
            onAnswer={handleAnswer}
            onFileUpload={handleFileUpload}
            history={conversationHistory}
            loading={loading}
            onReset={resetSession}
          />
        </div>
        
        <div className="sidebar">
          <DocumentList documents={extractedDocuments} />
        </div>
      </div>
    </div>
  );
}

export default App;


// components/ChatContainer.js
import React, { useState, useRef, useEffect } from 'react';
import './ChatContainer.css';
import ChatMessage from './ChatMessage';
import FileUploadForm from './FileUploadForm';

function ChatContainer({ 
  currentMessage, 
  awaitingFollowup, 
  isDone, 
  onAnswer, 
  onFileUpload, 
  history,
  loading,
  onReset
}) {
  const [userInput, setUserInput] = useState('');
  const chatEndRef = useRef(null);

  useEffect(() => {
    // Scroll to bottom whenever history changes
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (userInput.trim() === '') return;
    
    onAnswer(userInput);
    setUserInput('');
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {/* Initial bot message if no history */}
        {history.length === 0 && (
          <ChatMessage role="bot" content={currentMessage} />
        )}
        
        {/* Display conversation history */}
        {history.map((message, index) => (
          <ChatMessage 
            key={index} 
            role={message.role} 
            content={message.content} 
            extractedData={message.extractedData}
          />
        ))}
        
        {loading && <div className="loading-indicator">Processing...</div>}
        
        <div ref={chatEndRef} />
      </div>
      
      <div className="chat-input">
        {!isDone ? (
          <>
            {awaitingFollowup ? (
              <FileUploadForm onFileUpload={onFileUpload} />
            ) : (
              <form onSubmit={handleSubmit}>
                <input 
                  type="text" 
                  value={userInput} 
                  onChange={(e) => setUserInput(e.target.value)} 
                  placeholder="Type your answer..."
                  disabled={loading}
                />
                <button type="submit" disabled={loading}>Send</button>
              </form>
            )}
          </>
        ) : (
          <div className="chat-complete">
            <p>Onboarding complete!</p>
            <button onClick={onReset}>Start Over</button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatContainer;


// components/ChatMessage.js
import React, { useState } from 'react';
import './ChatMessage.css';

function ChatMessage({ role, content, extractedData }) {
  const [showDetails, setShowDetails] = useState(false);
  
  const toggleDetails = () => {
    setShowDetails(!showDetails);
  };
  
  return (
    <div className={`chat-message ${role}`}>
      <div className="message-header">
        <strong>{role === 'bot' ? 'Bot' : 'You'}</strong>
      </div>
      <div className="message-content">
        {content}
        
        {extractedData && (
          <div className="extracted-data">
            <button 
              className="details-toggle" 
              onClick={toggleDetails}
            >
              {showDetails ? 'Hide' : 'Show'} Extracted Data
            </button>
            
            {showDetails && (
              <div className="data-details">
                {extractedData.medications && extractedData.medications.length > 0 && (
                  <div className="data-section">
                    <h4>Medications</h4>
                    <ul>
                      {extractedData.medications.map((med, idx) => (
                        <li key={idx}>
                          {med.name} {med.dosage && `- ${med.dosage}`} 
                          {med.frequency && `(${med.frequency})`}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {extractedData.diagnoses && extractedData.diagnoses.length > 0 && (
                  <div className="data-section">
                    <h4>Diagnoses</h4>
                    <ul>
                      {extractedData.diagnoses.map((diag, idx) => (
                        <li key={idx}>
                          {diag.condition} 
                          {diag.date && `- ${diag.date}`}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {extractedData.hospital_visits && extractedData.hospital_visits.length > 0 && (
                  <div className="data-section">
                    <h4>Hospital Visits</h4>
                    <ul>
                      {extractedData.hospital_visits.map((visit, idx) => (
                        <li key={idx}>
                          {visit.name} 
                          {visit.date && `- ${visit.date}`}
                          {visit.reason && `(${visit.reason})`}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {extractedData.test_results && extractedData.test_results.length > 0 && (
                  <div className="data-section">
                    <h4>Test Results</h4>
                    <ul>
                      {extractedData.test_results.map((test, idx) => (
                        <li key={idx}>
                          {test.name}: {test.value} 
                          {test.reference_range && `(Ref: ${test.reference_range})`}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {extractedData.patient && (
                  <div className="data-section">
                    <h4>Patient Information</h4>
                    <p>Name: {extractedData.patient.name || 'Not specified'}</p>
                    {extractedData.patient.dob && <p>DOB: {extractedData.patient.dob}</p>}
                    {extractedData.patient.id && <p>ID: {extractedData.patient.id}</p>}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;


// components/DocumentList.js
import React from 'react';
import './DocumentList.css';

function DocumentList({ documents }) {
  if (documents.length === 0) {
    return (
      <div className="document-list">
        <h3>Processed Documents</h3>
        <p className="no-documents">No documents processed yet</p>
      </div>
    );
  }
  
  return (
    <div className="document-list">
      <h3>Processed Documents</h3>
      
      {documents.map((doc, index) => (
        <div key={index} className="document-item">
          <div className="document-header">
            <h4>{doc.filename}</h4>
            <span className="document-type">
              {doc.document_types.join(', ')}
            </span>
          </div>
          
          <div className="document-summary">
            {doc.data.medications && (
              <p>Medications: {doc.data.medications.length}</p>
            )}
            
            {doc.data.diagnoses && (
              <p>Diagnoses: {doc.data.diagnoses.length}</p>
            )}
            
            {doc.data.hospital_visits && (
              <p>Hospital Records: {doc.data.hospital_visits.length}</p>
            )}
            
            {doc.data.test_results && (
              <p>Test Results: {doc.data.test_results.length}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default DocumentList;


// components/FileUploadForm.js
import React, { useState } from 'react';
import './FileUploadForm.css';

function FileUploadForm({ onFileUpload }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setSelectedFile(file);
    
    // Create preview for images
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    } else {
      setPreview(null);
    }
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedFile) return;
    
    onFileUpload(selectedFile);
    setSelectedFile(null);
    setPreview(null);
  };
  
  return (
    <form className="file-upload-form" onSubmit={handleSubmit}>
      <div className="file-input-container">
        <input 
          type="file" 
          id="file-upload" 
          accept="image/*,.pdf" 
          onChange={handleFileChange} 
          className="file-input"
        />
        <label htmlFor="file-upload" className="file-label">
          Choose Document
        </label>
        
        <span className="selected-file-name">
          {selectedFile ? selectedFile.name : 'No file selected'}
        </span>
      </div>
      
      {preview && (
        <div className="file-preview">
          <img src={preview} alt="Preview" />
        </div>
      )}
      
      <button 
        type="submit" 
        className="upload-button" 
        disabled={!selectedFile}
      >
        Upload & Process
      </button>
    </form>
  );
}

export default FileUploadForm;


// services/api.js
const API_BASE_URL = 'http://localhost:8000';

export const createSession = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/session`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API error creating session:', error);
    throw error;
  }
};

export const getNextQuestion = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/questions/${sessionId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API error getting question:', error);
    throw error;
  }
};

export const submitAnswer = async (sessionId, answer) => {
  try {
    const response = await fetch(`${API_BASE_URL}/answer/${sessionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ answer }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API error submitting answer:', error);
    throw error;
  }
};

export const uploadDocument = async (sessionId, file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/document/${sessionId}`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API error uploading document:', error);
    throw error;
  }
};

export const getSessionState = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/state/${sessionId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API error getting session state:', error);
    throw error;
  }
};

export const resetSession = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/session/${sessionId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API error resetting session:', error);
    throw error;
  }
};