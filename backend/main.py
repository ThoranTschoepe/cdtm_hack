# backend/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import os
from typing import Dict, List
from pydantic import BaseModel
from models import OnboardingState, QuestionResponse, DocumentProcessResponse
from document_processor import MultiDocumentProcessor
from onboarding_agent import OnboardingAgent # Import the new agent

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
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

# API Endpoints
@app.post("/session")
async def create_session():
    """Create a new session"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = OnboardingState(id=session_id)
    return {"session_id": session_id}

@app.get("/questions/{session_id}")
async def get_next_question(session_id: str):
    """Get the next question or current state"""
    state = get_session(session_id)
    # Let the agent determine the next question/message
    response = agent.get_next_question(state)
    return response

@app.post("/answer/{session_id}")
async def submit_answer(session_id: str, request: AnswerRequest):
    """Submit an answer to the current question"""
    state = get_session(session_id)
    # Let the agent process the answer
    response = agent.process_answer(state, request.answer)
    # Update the session state
    sessions[session_id] = state
    return response

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
        response = agent.process_documents(state, image_bytes_list, filenames)
        
        # Update the session state
        sessions[session_id] = state
        return response
    
    except Exception as e:
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)