# backend/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uuid
import os
from typing import Dict, List
from pydantic import BaseModel
from models import OnboardingState, QuestionResponse, DocumentProcessResponse
from document_processor import MultiDocumentProcessor
from onboarding_agent import OnboardingAgent # Import the new agent
from voice.llm import synthesize_speech, transcribe_audio_file
import io
import hashlib

app = FastAPI(title="Medical Onboarding API")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Your React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "audio_cache"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Mount the audio folder to serve audio files
app.mount("/audio", StaticFiles(directory=AUDIO_FOLDER), name="audio")

# Initialize the document processor
document_processor = MultiDocumentProcessor()

# Initialize the agent
agent = OnboardingAgent(document_processor)

# Mock database for user sessions (in production, use a real database)
sessions: Dict[str, OnboardingState] = {}

def get_session(session_id: str) -> OnboardingState:
    """Get or create a session"""
    if session_id not in sessions:
        sessions[session_id] = OnboardingState(id=session_id)
    return sessions[session_id]

class AnswerRequest(BaseModel):
    answer: str

class EnhancedQuestionResponse(QuestionResponse):
    """Enhanced response that includes audio URL"""
    audio_url: str

# Function to generate and cache audio
def generate_audio_file(text: str) -> str:
    """Generate audio file from text and return the URL path"""
    # Create a hash of the text to use as filename (to enable caching)
    text_hash = hashlib.md5(text.encode()).hexdigest()
    audio_filename = f"{text_hash}.mp3"
    audio_path = os.path.join(AUDIO_FOLDER, audio_filename)
    
    # If audio doesn't exist yet, generate it
    if not os.path.exists(audio_path):
        audio_stream = synthesize_speech(text)
        # Save the audio stream to a file
        with open(audio_path, "wb") as f:
            f.write(audio_stream.read())
    
    # Return the URL to access the audio
    return f"/audio/{audio_filename}"

# API Endpoints
@app.post("/session")
async def create_session():
    """Create a new session"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = OnboardingState(id=session_id)
    return {"session_id": session_id}

@app.get("/questions/{session_id}", response_model=EnhancedQuestionResponse)
async def get_next_question(session_id: str, background_tasks: BackgroundTasks):
    """Get the next question with audio URL"""
    state = get_session(session_id)
    # Let the agent determine the next question/message
    response = agent.get_next_question(state)
    
    # Generate audio file and get its URL
    audio_url = generate_audio_file(response.message)
    
    # Create enhanced response with audio URL
    enhanced_response = EnhancedQuestionResponse(
        **response.model_dump(),
        audio_url=audio_url
    )
    
    return enhanced_response

@app.post("/answer/{session_id}")
async def submit_answer(session_id: str, request: AnswerRequest):
    """Submit an answer to the current question"""
    state = get_session(session_id)
    # Let the agent process the answer
    response = agent.process_answer(state, request.answer)
    # Update the session state
    sessions[session_id] = state
    
    # Generate audio for the response
    audio_url = generate_audio_file(response.message)
    
    # Create enhanced response with audio URL
    enhanced_response = EnhancedQuestionResponse(
        **response.model_dump(),
        audio_url=audio_url
    )
    
    return enhanced_response

@app.post("/answer_transcribe/{session_id}")
async def submit_transcribed_answer(
    session_id: str,
    answer: str = Form(None),
    file: UploadFile = File(None)
):
    """Submit a text or audio answer"""
    state = get_session(session_id)

    try:
        # 1. Get the answer from audio or form
        if file:
            answer = transcribe_audio_file(file)
        elif not answer:
            raise HTTPException(status_code=400, detail="No input provided.")

        # 2. Process the answer
        response = agent.process_answer(state, answer)
        sessions[session_id] = state
        
        # Generate audio for the response
        audio_url = generate_audio_file(response.message)
        
        # Create enhanced response with audio URL
        enhanced_response = EnhancedQuestionResponse(
            **response.model_dump(),
            audio_url=audio_url
        )
        
        return enhanced_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process answer: {str(e)}")

@app.post("/document/{session_id}")
async def process_document(session_id: str, files: List[UploadFile] = File(...)):
    """Process multiple uploaded documents at once"""
    state = get_session(session_id)
    
    # Process all files
    try:
        # Collect all files
        image_bytes_list = []
        filenames = []
        
        for file in files:
            # Save the file
            filename = f"{uuid.uuid4()}_{file.filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            with open(filepath, "wb") as buffer:
                file_content = await file.read()
                buffer.write(file_content)
            
            # Read the saved file
            with open(filepath, "rb") as f:
                image_bytes = f.read()
                image_bytes_list.append(image_bytes)
                filenames.append(filename)
        
        # Let the agent process all documents at once
        doc_response = agent.process_documents(state, image_bytes_list, filenames)
        
        # Get the next question to provide a message
        question_response = agent.get_next_question(state)
        
        # Generate audio for the question response message
        audio_url = generate_audio_file(question_response.message)
        
        # Create enhanced response with audio URL and document data
        enhanced_response = EnhancedQuestionResponse(
            message=question_response.message,
            awaiting_followup=question_response.awaiting_followup,
            done=question_response.done,
            current_question_index=question_response.current_question_index,
            extracted_data=doc_response.extracted_data,
            audio_url=audio_url
        )
        
        # Update the session state
        sessions[session_id] = state
        return enhanced_response
    
    except Exception as e:
        # Add better error logging
        import traceback
        print(f"Error processing documents: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")

@app.get("/state/{session_id}")
async def get_session_state(session_id: str):
    """Get the current session state"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

@app.delete("/session/{session_id}")
async def reset_session(session_id: str):
    """Reset a session"""
    if session_id in sessions:
        del sessions[session_id]
    return {"success": True}

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)