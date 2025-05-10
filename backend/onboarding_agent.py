# backend/agent.py
from typing import Dict, List, Optional, Any
from models import OnboardingState, QuestionResponse, DocumentProcessResponse

class OnboardingAgent:
    """
    Medical Onboarding Agent that guides users through the onboarding process.
    This agent handles the conversation flow, processes user inputs, and manages
    document processing.
    """
    
    # Questions to ask during onboarding
    QUESTIONS = [
        "Do you take any medication?", 
        "Have you been to the hospital?", 
        "Do you have any chronic diseases"
    ]
    
    def __init__(self, document_processor):
        """Initialize the agent with a document processor"""
        self.document_processor = document_processor
    
    def get_next_question(self, state: OnboardingState) -> QuestionResponse:
        """Determine the next question or message to send to the user"""
        message = ""
        done = False
        
        if state.current_question_index >= len(self.QUESTIONS):
            message = "Thank you for completing the onboarding process."
            done = True
        elif not state.awaiting_followup:
            message = self.QUESTIONS[state.current_question_index]
        else:
            # Awaiting document upload
            current_q = self.QUESTIONS[state.current_question_index]
            message = f"Do you have a report for the question: {current_q}?"
        
        return QuestionResponse(
            message=message,
            awaiting_followup=state.awaiting_followup,
            done=done,
            current_question_index=state.current_question_index,
            extracted_data_preview=None
        )
    
    def process_answer(self, state: OnboardingState, answer: str) -> QuestionResponse:
        """Process a user's answer to the current question"""
        message = ""
        
        current_q = self.QUESTIONS[state.current_question_index]
        
        if self._is_positive(answer):
            message = f"Do you have a report for the question: {current_q}?"
            state.awaiting_followup = True
            state.last_question = current_q
        else:
            self._update_state(state, current_q, "no", None)
            state.current_question_index += 1
            
            if state.current_question_index >= len(self.QUESTIONS):
                message = "Thank you for completing the onboarding process."
                done = True
            else:
                message = self.QUESTIONS[state.current_question_index]
                done = False
        
        return QuestionResponse(
            message=message,
            awaiting_followup=state.awaiting_followup,
            done=state.current_question_index >= len(self.QUESTIONS),
            current_question_index=state.current_question_index,
            extracted_data_preview=None
        )
    
    def process_document(self, state: OnboardingState, image_bytes: bytes, filename: str) -> DocumentProcessResponse:
        """Process a document uploaded by the user"""
        # Process the document using the document processor
        result = self.document_processor.process_pages([image_bytes])
        
        # Extract relevant information
        extracted_data = self._extract_relevant_info(result)
        
        # Check if extracted data answers the current question
        current_q = self.QUESTIONS[state.current_question_index]
        auto_answer = self._check_extracted_data_for_answer(current_q, extracted_data)
        
        # Update state with the answer and document
        self._update_state(state, current_q, auto_answer or "yes", filename)
        
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
        
        return DocumentProcessResponse(
            success=True,
            filename=filename,
            extracted_data=extracted_data,
            document_types=list(result.document_groups.keys())
        )
    
    def _is_positive(self, text: str) -> bool:
        """Check if user response is positive"""
        return "yes" in text.lower()
    
    def _update_state(self, state: OnboardingState, question=None, answer=None, followup_file=None):
        """Update session state with new question/answer"""
        state.previous_questions.append({
            "question": question,
            "answer": answer,
            "followup": followup_file
        })
        return state
    
    def _extract_relevant_info(self, result) -> Dict[str, Any]:
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
    
    def _check_extracted_data_for_answer(self, question, extracted_data):
        """Check if the extracted data can answer the current question"""
        question_lower = question.lower()
        
        if "medication" in question_lower and extracted_data.get("medications"):
            return "yes - found in document: " + ", ".join(m.get("name", "") for m in extracted_data.get("medications", [])[:3])
            
        if "hospital" in question_lower and extracted_data.get("hospital_visits"):
            return "yes - found in document: " + extracted_data.get("hospital_visits", [{}])[0].get("name", "Hospital visit confirmed")
            
        if "chronic" in question_lower and "disease" in question_lower and extracted_data.get("diagnoses"):
            return "yes - found in document: " + ", ".join(d.get("condition", "") for d in extracted_data.get("diagnoses", [])[:3])
            
        return None