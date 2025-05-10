# backend/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal

class PatientInfo(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    id: Optional[str] = None

class Medication(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    prescriber: Optional[str] = None

class Diagnosis(BaseModel):
    condition: str
    date: Optional[str] = None
    doctor: Optional[str] = None

class HospitalVisit(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    reason: Optional[str] = None

class TestResult(BaseModel):
    name: str
    value: Optional[str] = None
    reference_range: Optional[str] = None
    date: Optional[str] = None

class ExtractedDocument(BaseModel):
    filename: str
    document_types: List[str]
    data: Dict[str, Any]

class OnboardingState(BaseModel):
    id: str
    current_question_index: int = 0
    awaiting_followup: bool = False
    awaiting_document: bool = False  # Flag to indicate if we're waiting for document upload
    awaiting_clarification: bool = False  # Flag to indicate if we need clarification on a response
    last_question: Optional[str] = None
    previous_questions: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_documents: List[ExtractedDocument] = Field(default_factory=list)
    # You can keep these if you had them in your previous implementation
    conversation_context: Optional[str] = None
    patient_profile: Optional[Dict[str, Any]] = Field(default_factory=dict)

class QuestionResponse(BaseModel):
    message: str
    awaiting_followup: bool
    done: bool
    current_question_index: int
    extracted_data_preview: Optional[Dict[str, Any]] = None
    # New fields for enhanced responses
    suggested_documents: Optional[List[str]] = None
    detected_entities: Optional[Dict[str, List[str]]] = None

class DocumentProcessResponse(BaseModel):
    success: bool
    filename: str
    extracted_data: Dict[str, Any]
    document_types: List[str]
    # New field for enhanced feedback after document processing
    message: str = "Thank you for uploading your document."