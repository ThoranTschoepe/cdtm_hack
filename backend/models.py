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
    category: Optional[str] = None

class OnboardingState(BaseModel):
    id: str
    current_question_index: int = 0
    awaiting_followup: bool = False
    last_question: Optional[str] = None
    previous_questions: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_documents: List[ExtractedDocument] = Field(default_factory=list)
    
    # New fields for enhanced agent functionality
    needs_clarification: bool = False
    last_answer: Optional[str] = None
    
    # User info fields
    patient_info: Dict[str, Any] = Field(default_factory=dict)
    symptoms_info: Dict[str, Any] = Field(default_factory=dict)
    
    # Category-based approach fields
    category_states: Dict[str, str] = Field(default_factory=lambda: {
        "current_symptoms": "not_started",
        "insurance": "not_started",
        "medication": "not_started", 
        "health_record": "not_started",
        "review_data": "not_started"
    })
    current_category: str = "current_symptoms"
    document_count: Dict[str, int] = Field(default_factory=lambda: {
        "current_symptoms": 0,
        "insurance": 0,
        "medication": 0, 
        "health_record": 0,
        "review_data": 0
    })
    
    # Fields for review data feature
    missing_data_items: List[str] = Field(default_factory=list)
    current_missing_data_item: Optional[str] = None
    missing_data_responses: Dict[str, str] = Field(default_factory=dict)
    missing_data_recommendations: Optional[str] = None

class QuestionResponse(BaseModel):
    message: str
    awaiting_followup: bool
    done: bool
    current_question_index: int
    extracted_data: Optional[Dict[str, Any]] = None

class DocumentProcessResponse(BaseModel):
    success: bool
    filename: str
    extracted_data: Dict[str, Any]
    document_types: List[str]