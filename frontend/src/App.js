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
  // Define the ref at the top level of the component
  const hasInitialized = useRef(false);

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

        // 🔊 Play audio for the question
        const audioUrl = await api.getNextQuestionAudio(session_id);
        setLatestAudioUrl(audioUrl);
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

      // 🔊 Fetch and play the audio response
      const audioUrl = await api.getNextQuestionAudio(sessionId);
      setLatestAudioUrl(audioUrl);
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
    } catch (error) {
      console.error('Error resetting session:', error);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>Medical Onboarding Assistant</h1>
  
      <Chat messages={messages} latestAudioUrl={latestAudioUrl} />
  
      {latestExtractedData && <ResultPreview extractedData={latestExtractedData} />}
  
      {!isDone ? (
        awaitingFollowup ? (
          <FileUpload onUpload={handleFileUpload} isMultiple={true} />
        ) : (
          <>
            <UserInput onSend={handleSendMessage} disabled={isLoading} />
            <AudioRecorder onTranscription={handleSendMessage} />
          </>
        )
      ) : (
        <button 
          onClick={handleReset}
          style={{
            padding: '10px 20px',
            backgroundColor: '#f44336',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            margin: '20px 0'
          }}
        >
          Start Over
        </button>
      )}
  
      {isLoading && (
        <div style={{ textAlign: 'center', margin: '10px 0' }}>
          Processing...
        </div>
      )}
    </div>
  );
}

export default App;