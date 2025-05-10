# backend/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Body
import uuid
import os
from typing import Dict, List, Optional

from pydantic import BaseModel
from models import OnboardingState, QuestionResponse, DocumentProcessResponse
from document_processor import MultiDocumentProcessor

app = FastAPI(title="Medical Onboarding API")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize the document processor
document_processor = MultiDocumentProcessor()

# Mock database for user sessions (in production, use a real database)
sessions: Dict[str, OnboardingState] = {}

# Questions list
QUESTIONS = [
    "Do you take any medication?", 
    "Have you been to the hospital?", 
    "Do you have any chronic diseases"
]

# Helper functions
def get_session(session_id: str) -> OnboardingState:
    """Get or create a session"""
    if session_id not in sessions:
        sessions[session_id] = OnboardingState(id=session_id)
    return sessions[session_id]

def extract_relevant_info(result):
    """Extract relevant information from OCR result based on document type"""
    extracted_info = {}
    
    for doc_type, group in result.document_groups.items():
        if not group.combined_data:
            continue
            
        data = group.combined_data
        
        # Process based on document type
        if doc_type == "MedicationBox" or doc_type == "Prescription":
            medications = data.get("medications", [])
            if "medications" not in extracted_info:
                extracted_info["medications"] = []
            extracted_info["medications"].extend(medications)
            
        elif doc_type == "HospitalLetter" or doc_type == "DoctorLetter":
            # Extract diagnosis and hospital/clinic info
            if "diagnoses" in data:
                extracted_info["diagnoses"] = data.get("diagnoses", [])
            if "hospital" in data:
                extracted_info["hospital_visits"] = [data.get("hospital", {})]
                
        elif doc_type == "LabReport":
            if "test_results" in data:
                extracted_info["test_results"] = data.get("test_results", [])
                
        # Add patient info from any document type
        if "patient" in data:
            extracted_info["patient"] = data.get("patient", {})
    
    return extracted_info

def is_positive(text: str) -> bool:
    """Check if user response is positive"""
    return "yes" in text.lower()

def check_extracted_data_for_answer(question, extracted_data):
    """Check if the extracted data can answer the current question"""
    question_lower = question.lower()
    
    if "medication" in question_lower and extracted_data.get("medications"):
        return "yes - found in document: " + ", ".join(m.get("name", "") for m in extracted_data.get("medications", [])[:3])
        
    if "hospital" in question_lower and extracted_data.get("hospital_visits"):
        return "yes - found in document: " + extracted_data.get("hospital_visits", [{}])[0].get("name", "Hospital visit confirmed")
        
    if "chronic" in question_lower and "disease" in question_lower and extracted_data.get("diagnoses"):
        return "yes - found in document: " + ", ".join(d.get("condition", "") for d in extracted_data.get("diagnoses", [])[:3])
        
    return None

def update_state(state: OnboardingState, question=None, answer=None, followup_file=None):
    """Update session state with new question/answer"""
    state.previous_questions.append({
        "question": question,
        "answer": answer,
        "followup": followup_file
    })
    return state

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
    message = ""
    done = False
    
    if state.current_question_index >= len(QUESTIONS):
        message = "Thank you for completing the onboarding process."
        done = True
    elif not state.awaiting_followup:
        message = QUESTIONS[state.current_question_index]
    else:
        # Awaiting document upload
        current_q = QUESTIONS[state.current_question_index]
        message = f"Do you have a report for the question: {current_q}?"
    
    return QuestionResponse(
        message=message,
        awaiting_followup=state.awaiting_followup,
        done=done,
        current_question_index=state.current_question_index,
        extracted_data_preview=None
    )

class AnswerRequest(BaseModel):
    answer: str


@app.post("/answer/{session_id}")
async def submit_answer(session_id: str, request: AnswerRequest):
    answer = request.answer
    """Submit an answer to the current question"""
    state = get_session(session_id)
    message = ""
    
    current_q = QUESTIONS[state.current_question_index]
    
    if is_positive(answer):
        message = f"Do you have a report for the question: {current_q}?"
        state.awaiting_followup = True
        state.last_question = current_q
    else:
        update_state(state, current_q, "no", None)
        state.current_question_index += 1
        
        if state.current_question_index >= len(QUESTIONS):
            message = "Thank you for completing the onboarding process."
            done = True
        else:
            message = QUESTIONS[state.current_question_index]
            done = False
    
    sessions[session_id] = state
    
    return QuestionResponse(
        message=message,
        awaiting_followup=state.awaiting_followup,
        done=state.current_question_index >= len(QUESTIONS),
        current_question_index=state.current_question_index,
        extracted_data_preview=None
    )

@app.post("/document/{session_id}")
async def process_document(session_id: str, file: UploadFile = File(...)):
    """Process an uploaded document"""
    state = get_session(session_id)
    
    # Save the file
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())
    
    # Process the document
    try:
        with open(filepath, "rb") as f:
            image_bytes = f.read()
            
        # Process single image
        result = document_processor.process_pages([image_bytes])
        
        # Extract relevant information based on document type
        extracted_data = extract_relevant_info(result)
        
        # Check if extracted data answers the current question
        current_q = QUESTIONS[state.current_question_index]
        auto_answer = check_extracted_data_for_answer(current_q, extracted_data)
        
        # Update state with the answer and document
        update_state(state, current_q, auto_answer or "yes", filename)
        
        # Add extracted data to state
        if not hasattr(state, "extracted_documents"):
            state.extracted_documents = []
            
        state.extracted_documents.append({
            "filename": filename,
            "data": extracted_data,
            "document_types": list(result.document_groups.keys())
        })
        
        # Move to next question
        state.awaiting_followup = False
        state.current_question_index += 1
        
        # Determine next message
        if state.current_question_index >= len(QUESTIONS):
            message = "Thank you for completing the onboarding process."
            done = True
        else:
            message = QUESTIONS[state.current_question_index]
            done = False
        
        sessions[session_id] = state
        
        return DocumentProcessResponse(
            success=True,
            filename=filename,
            extracted_data=extracted_data,
            document_types=list(result.document_groups.keys())
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

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