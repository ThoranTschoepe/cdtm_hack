# backend/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import os
from typing import Dict
from pydantic import BaseModel
from models import OnboardingState, QuestionResponse, DocumentProcessResponse
from document_processor import MultiDocumentProcessor
from onboarding_agent import GeminiOnboardingAgent  # Import the enhanced Gemini agent
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global instances for services
document_processor = None
agent = None
sessions = {}

# Initialization context
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize services on startup
    global document_processor, agent, sessions
    
    document_processor = MultiDocumentProcessor()
    
    # Initialize the Gemini-powered agent
    try:
        agent = GeminiOnboardingAgent(
            document_processor=document_processor
        )
        logger.info("Gemini onboarding agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini agent: {e}")
        # Fallback to basic agent if Gemini initialization fails
        from onboarding_agent import OnboardingAgent
        agent = OnboardingAgent(document_processor)
        logger.info("Fallback to basic onboarding agent")
    
    # Mock database for user sessions (in production, use a real database)
    sessions = {}
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down application")

# Initialize FastAPI app
app = FastAPI(
    title="Medical Onboarding API",
    description="API for medical onboarding process with intelligent document processing",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get session
def get_session(session_id: str) -> OnboardingState:
    """Get or create a session"""
    global sessions
    if session_id not in sessions:
        sessions[session_id] = OnboardingState(id=session_id)
    return sessions[session_id]

# Request models
class AnswerRequest(BaseModel):
    answer: str

# API Endpoints
@app.post("/session")
async def create_session():
    """Create a new session"""
    global sessions
    session_id = str(uuid.uuid4())
    sessions[session_id] = OnboardingState(id=session_id)
    return {"session_id": session_id}

@app.get("/questions/{session_id}")
async def get_next_question(session_id: str, state: OnboardingState = Depends(get_session)):
    """Get the next question or current state"""
    global agent
    # Let the agent determine the next question/message
    try:
        response = agent.get_next_question(state)
        return response
    except Exception as e:
        logger.error(f"Error getting next question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting next question: {str(e)}")

@app.post("/answer/{session_id}")
async def submit_answer(session_id: str, request: AnswerRequest, state: OnboardingState = Depends(get_session)):
    """Submit an answer to the current question"""
    global agent
    try:
        # Let the agent process the answer
        response = agent.process_answer(state, request.answer)
        return response
    except Exception as e:
        logger.error(f"Error processing answer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing answer: {str(e)}")

@app.post("/document/{session_id}")
async def process_document(
    session_id: str, 
    file: UploadFile = File(...), 
    state: OnboardingState = Depends(get_session)
):
    """Process an uploaded document"""
    global agent
    # Save the file
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        with open(filepath, "wb") as buffer:
            buffer.write(await file.read())
            
        # Process the document
        with open(filepath, "rb") as f:
            image_bytes = f.read()
            
        # Let the agent process the document
        response = agent.process_document(state, image_bytes, filename)
        return response
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    finally:
        # Ensure file cleanup happens even if an error occurs
        if os.path.exists(filepath):
            try:
                # Keep files for now (in production, consider cleanup strategy)
                pass
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up file {filepath}: {cleanup_error}")

@app.get("/state/{session_id}")
async def get_session_state(session_id: str):
    """Get the current session state"""
    global sessions
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

@app.delete("/session/{session_id}")
async def reset_session(session_id: str):
    """Reset a session"""
    global sessions
    if session_id in sessions:
        del sessions[session_id]
    return {"success": True}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)