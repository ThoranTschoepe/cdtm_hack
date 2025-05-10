import React, { useState, useEffect, useRef } from 'react';
import Chat from './components/Chat';
import UserInput from './components/UserInput';
import FileUpload from './components/FileUpload';
import ResultPreview from './components/ResultPreview';
import AudioRecorder from './components/AudioRecorder'; 
import api from './services/api';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [awaitingFollowup, setAwaitingFollowup] = useState(false);
  const [latestExtractedData, setLatestExtractedData] = useState(null);
  const [latestAudioUrl, setLatestAudioUrl] = useState(null);
  const [isDone, setIsDone] = useState(false);
  const hasInitialized = useRef(false);

  // Mobile viewport adjustment for camera usage
  useEffect(() => {
    const setResponsiveMetaTag = () => {
      let metaViewport = document.querySelector('meta[name="viewport"]');
      if (!metaViewport) {
        metaViewport = document.createElement('meta');
        metaViewport.name = 'viewport';
        document.head.appendChild(metaViewport);
      }
      metaViewport.content = 'width=device-width, initial-scale=1, maximum-scale=1';
    };
    
    setResponsiveMetaTag();
    
    // Add some global styles
    const style = document.createElement('style');
    style.textContent = `
      body {
        font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
        background-color: #fafafa;
        color: #333;
        line-height: 1.6;
      }
      
      * {
        box-sizing: border-box;
      }
      
      #root {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
      }
    `;
    document.head.appendChild(style);
  }, []);

  // Initialize session
  useEffect(() => {
    const initializeSession = async () => {
      // Skip if already initialized
      if (hasInitialized.current) return;
      hasInitialized.current = true;
      
      try {
        setIsLoading(true);
        const { session_id } = await api.createSession();
        setSessionId(session_id);
        const questionData = await api.getNextQuestion(session_id);
        
        setMessages([{ text: questionData.message, isUser: false }]);
        setAwaitingFollowup(questionData.awaiting_followup);
        setIsDone(questionData.done);

        // Set audio URL directly from the response
        if (questionData.audio_url) {
          const fullAudioUrl = `http://localhost:8000${questionData.audio_url}`;
          setLatestAudioUrl(fullAudioUrl);
        }
      } catch (error) {
        console.error('Failed to initialize session:', error);
        setMessages([{ text: 'Failed to start the session. Please refresh the page.', isUser: false }]);
      } finally {
        setIsLoading(false);
      }
    };

    initializeSession();
  }, []);

  // Handle text input submission
  const handleSendMessage = async (text) => {
    if (!sessionId || isLoading) return;

    // Add user message to chat
    setMessages(prev => [...prev, { text, isUser: true }]);
    setIsLoading(true);

    try {
      const response = await api.submitAnswer(sessionId, text);
      
      setMessages(prev => [...prev, { text: response.message, isUser: false }]);
      setAwaitingFollowup(response.awaiting_followup);
      setIsDone(response.done);

      // Set audio URL directly from the response
      if (response.audio_url) {
        const fullAudioUrl = `http://localhost:8000${response.audio_url}`;
        setLatestAudioUrl(fullAudioUrl);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { 
        text: 'An error occurred while processing your message. Please try again.', 
        isUser: false 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle file upload for multiple files
  const handleFileUpload = async (files) => {
    if (!sessionId || isLoading) return;

    setIsLoading(true);
    
    if (files === "skip") {
      try {
        const response = await api.submitAnswer(sessionId, "skip");
        setMessages(prev => [...prev, { text: response.message, isUser: false }]);
        setAwaitingFollowup(response.awaiting_followup);
        setIsDone(response.done);
        
        // Set audio URL directly from the response
        if (response.audio_url) {
          const fullAudioUrl = `http://localhost:8000${response.audio_url}`;
          setLatestAudioUrl(fullAudioUrl);
        }
      } catch (error) {
        console.error('Error skipping document upload:', error);
        setMessages(prev => [...prev, { 
          text: 'An error occurred while processing your request.', 
          isUser: false 
        }]);
      } finally {
        setIsLoading(false);
      }
      return;
    }
    
    // If single file is passed, convert to array
    const fileArray = Array.isArray(files) ? files : [files];
    
    // Show message about uploading multiple files
    setMessages(prev => [...prev, { 
      text: `Uploading ${fileArray.length} file(s)`, 
      isUser: true 
    }]);

    try {
      const response = await api.uploadDocuments(sessionId, fileArray);
      
      // Show uploaded file info and extracted data
      setLatestExtractedData(response.extracted_data);
      
      setMessages(prev => [...prev, { 
        text: `${fileArray.length} File(s) processed successfully.`, 
        isUser: false 
      }]);

      // Get the next question
      const nextQuestion = await api.getNextQuestion(sessionId);
      setMessages(prev => [...prev, { text: nextQuestion.message, isUser: false }]);
      setAwaitingFollowup(nextQuestion.awaiting_followup);
      setIsDone(nextQuestion.done);

      // Set audio URL directly from the response
      if (nextQuestion.audio_url) {
        const fullAudioUrl = `http://localhost:8000${nextQuestion.audio_url}`;
        setLatestAudioUrl(fullAudioUrl);
      }
    } catch (error) {
      console.error('Error uploading files:', error);
      setMessages(prev => [...prev, { 
        text: 'An error occurred while processing the files. Please try again.', 
        isUser: false 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle voice response
  const handleVoiceResponse = async (fileBlob) => {
    setMessages(prev => [...prev, { text: '🎤 Voice input sent...', isUser: true }]);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', fileBlob, 'recording.wav');

      const res = await fetch(`http://localhost:8000/answer_transcribe/${sessionId}`, {
        method: 'POST',
        body: formData,
      });

      const response = await res.json();
      console.log("Voice response from backend:", response);

      const msgText = response.message || response.text || response || "🤖 No message";
      setMessages(prev => [...prev, { text: msgText, isUser: false }]);

      setAwaitingFollowup(response.awaiting_followup);
      setIsDone(response.done);

      // Set audio URL directly from the response
      if (response.audio_url) {
        const fullAudioUrl = `http://localhost:8000${response.audio_url}`;
        setLatestAudioUrl(fullAudioUrl);
      }
    } catch (error) {
      console.error('Error processing voice input:', error);
      setMessages(prev => [...prev, {
        text: 'Something went wrong after transcribing audio.',
        isUser: false,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Reset the session
  const handleReset = async () => {
    if (!sessionId) return;
    
    try {
      await api.resetSession(sessionId);
      
      // Create a new session
      const { session_id } = await api.createSession();
      setSessionId(session_id);
      
      // Get the first question
      const questionData = await api.getNextQuestion(session_id);
      
      // Reset states
      setMessages([{ text: questionData.message, isUser: false }]);
      setAwaitingFollowup(questionData.awaiting_followup);
      setIsDone(questionData.done);
      setLatestExtractedData(null);
      
      // Set audio URL directly from the response
      if (questionData.audio_url) {
        const fullAudioUrl = `http://localhost:8000${questionData.audio_url}`;
        setLatestAudioUrl(fullAudioUrl);
      }
    } catch (error) {
      console.error('Error resetting session:', error);
    }
  };

  // Calculate dynamic styling based on current state
  const getMainContainerStyle = () => {
    return {
      maxWidth: '800px',
      width: '100%',
      margin: '0 auto',
      padding: '20px',
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
      backgroundColor: 'white',
      boxShadow: '0 0 20px rgba(0,0,0,0.05)'
    };
  };

  return (
    <div style={getMainContainerStyle()}>
      <div style={{ 
        textAlign: 'center', 
        marginBottom: '30px',
        marginTop: '10px'
      }}>
        <img 
          src="/logo.png" 
          alt="Medimate" 
          style={{ 
            maxWidth: '150px', 
            width: '60%',
            height: 'auto',
            objectFit: 'contain',
            transition: 'all 0.3s ease',
            marginBottom: '10px'
          }} 
        />
      </div>
  
      <Chat messages={messages} latestAudioUrl={latestAudioUrl} />
  
      {latestExtractedData && (
        <div style={{ 
          marginBottom: '20px', 
          padding: '15px',
          backgroundColor: '#f0f8ff',
          borderRadius: '8px',
          border: '1px solid #e0e0e0'
        }}>
          <ResultPreview extractedData={latestExtractedData} />
        </div>
      )}
  
      {!isDone ? (
        awaitingFollowup ? (
          <FileUpload onUpload={handleFileUpload} isMultiple={true} />
        ) : (
          <div style={{ marginTop: 'auto' }}>
            <UserInput onSend={handleSendMessage} disabled={isLoading} />
            <AudioRecorder onResponse={handleVoiceResponse} sessionId={sessionId} />
          </div>
        )
      ) : (
        <div style={{ 
          display: 'flex',
          justifyContent: 'center',
          marginTop: '20px'
        }}>
          <button 
            onClick={handleReset}
            style={{
              padding: '12px 24px',
              backgroundColor: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '30px',
              cursor: 'pointer',
              fontSize: '16px',
              boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
              transition: 'all 0.2s ease'
            }}
          >
            Start Over
          </button>
        </div>
      )}
  
      {isLoading && (
        <div style={{ 
          position: 'fixed',
          bottom: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '10px 20px',
          borderRadius: '20px',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <div className="spinner" style={{
            width: '20px',
            height: '20px',
            border: '3px solid rgba(255,255,255,0.3)',
            borderRadius: '50%',
            borderTop: '3px solid white',
            animation: 'spin 1s linear infinite'
          }}></div>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
          Processing...
        </div>
      )}
    </div>
  );
}

export default App;