# backend/onboarding_agent.py
from typing import Dict, List, Optional, Any, Tuple
from models import OnboardingState, QuestionResponse, DocumentProcessResponse
from google import genai
from google.genai import types
import json

class OnboardingAgent:
    """
    Medical Onboarding Agent that guides users through the onboarding process.
    Uses an LLM to create a more natural conversation flow and ensure clear responses.
    """
    
    # Core questions for onboarding
    QUESTIONS = [
        "Do you take any medication?", 
        "Have you been to the hospital?", 
        "Do you have any chronic diseases?"
    ]
    
    # Explanations for questions that might be confusing
    EXPLANATIONS = {
        "Do you take any medication?": "This includes prescription medications, over-the-counter medicines, supplements, or vitamins that you take regularly.",
        "Have you been to the hospital?": "This includes any hospital stays, emergency room visits, or outpatient procedures in the past few years.",
        "Do you have any chronic diseases?": "Chronic diseases are long-term medical conditions like diabetes, high blood pressure, asthma, heart disease, or arthritis."
    }
    
    def __init__(self, document_processor):
        """Initialize the agent with a document processor and LLM client"""
        self.document_processor = document_processor
        self.genai_client = genai.Client(
            vertexai=True,
            project="avi-cdtm-hack-team-9800",
            location="us-central1",
        )
        self.model = "gemini-2.0-flash-001"
    
    def get_next_question(self, state: OnboardingState) -> QuestionResponse:
        """Generate a conversational prompt for the next question"""
        # Check if we've completed all questions
        if state.current_question_index >= len(self.QUESTIONS):
            summary = self._generate_summary(state)
            return QuestionResponse(
                message=summary,
                awaiting_followup=False,
                done=True,
                current_question_index=state.current_question_index,
                extracted_data_preview=self._get_data_preview(state)
            )
            
        # If we're awaiting a document upload
        if state.awaiting_followup:
            current_q = self.QUESTIONS[state.current_question_index]
            prompt = self._generate_upload_prompt(current_q, state)
            
            return QuestionResponse(
                message=prompt,
                awaiting_followup=True,
                done=False,
                current_question_index=state.current_question_index,
                extracted_data_preview=None
            )
        
        # If we need to clarify a previous ambiguous answer
        if state.needs_clarification:
            current_q = self.QUESTIONS[state.current_question_index]
            clarification_q = self._generate_clarification(current_q, state.last_answer, state)
            
            return QuestionResponse(
                message=clarification_q,
                awaiting_followup=False,
                done=False,
                current_question_index=state.current_question_index,
                extracted_data_preview=None
            )
        
        # Generate a conversational version of the current question
        current_q = self.QUESTIONS[state.current_question_index]
        conversational_q = self._generate_question(current_q, state)
        
        return QuestionResponse(
            message=conversational_q,
            awaiting_followup=False,
            done=False,
            current_question_index=state.current_question_index,
            extracted_data_preview=None
        )
    
    def process_answer(self, state: OnboardingState, answer: str) -> QuestionResponse:
        """Process a user's answer with LLM assistance"""
        current_q = self.QUESTIONS[state.current_question_index]
        
        # Store the last answer for potential clarification
        state.last_answer = answer
        
        # If this is a skip for document upload
        if state.awaiting_followup and answer.lower() == "skip":
            # Record that they skipped document upload
            self._update_state(state, current_q, "Yes - no document provided", None)
            # Move to next question
            state.awaiting_followup = False
            state.current_question_index += 1
            return self.get_next_question(state)
        
        # Evaluate if the answer is clear and what type of response it is
        is_clear, response_type = self._evaluate_answer(answer, current_q)
        
        # If the answer isn't clear and we're not already asking for clarification,
        # mark that we need clarification and ask again
        if not is_clear:
            state.needs_clarification = True
            return self.get_next_question(state)
        
        # We got a clear answer, so reset clarification flag if it was set
        state.needs_clarification = False
        
        # Clear answer - process based on the response type
        if response_type in ["strong_yes", "yes"]:
            # Update state and request document upload
            state.awaiting_followup = True
            state.last_question = current_q
            
            # Generate a prompt for document upload
            prompt = self._generate_upload_prompt(current_q, state)
            
            return QuestionResponse(
                message=prompt,
                awaiting_followup=True,
                done=False,
                current_question_index=state.current_question_index,
                extracted_data_preview=None
            )
        else:  # "no" or "strong_no"
            # Update state with the negative answer
            self._update_state(state, current_q, f"{response_type}: {answer}", None)
            state.current_question_index += 1
            
            # Check if we're done with all questions
            if state.current_question_index >= len(self.QUESTIONS):
                summary = self._generate_summary(state)
                return QuestionResponse(
                    message=summary,
                    awaiting_followup=False,
                    done=True,
                    current_question_index=state.current_question_index,
                    extracted_data_preview=self._get_data_preview(state)
                )
            else:
                # Get the next question
                return self.get_next_question(state)
    
    def process_document(self, state: OnboardingState, image_bytes: bytes, filename: str) -> DocumentProcessResponse:
        """Process a document uploaded by the user"""
        # Process the document using the document processor
        result = self.document_processor.process_pages([image_bytes])
        
        # Extract relevant information
        extracted_data = self._extract_relevant_info(result)
        
        # Check if extracted data answers the current question
        current_q = self.QUESTIONS[state.current_question_index]
        auto_answer = self._generate_answer_from_document(current_q, extracted_data)
        
        # Update state with the answer and document
        self._update_state(state, current_q, f"strong_yes: {auto_answer}", filename)
        
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

    def _evaluate_answer(self, answer: str, question: str) -> Tuple[bool, str]:
        """
        Evaluate if the answer is clear and determine the response type.
        Returns (is_clear, response_type)
        
        response_type can be: strong_yes, yes, no, strong_no, unsure
        """
        prompt = f"""
        Question: {question}
        Patient response: "{answer}"
        
        Evaluate this response for clarity and content.
        """
        
        # Define the JSON schema
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "is_clear": {
                    "type": "BOOLEAN",
                    "description": "Whether the response clearly indicates yes or no"
                },
                "response_type": {
                    "type": "STRING",
                    "enum": ["strong_yes", "yes", "no", "strong_no", "unsure"],
                    "description": "The type of response provided by the patient"
                }
            },
            "required": ["is_clear", "response_type"]
        }
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": 0.1,
                    "response_mime_type": "application/json",
                    "response_schema": response_schema
                }
            )
            
            # Parse the JSON response
            result = json.loads(response.text)
            is_clear = result.get("is_clear", False)
            response_type = result.get("response_type", "unsure")
            
            return is_clear, response_type
            
        except Exception as e:
            print(f"Error evaluating answer: {e}")
            
            # Fallback evaluation
            if "yes" in answer.lower():
                return True, "yes"
            elif "no" in answer.lower():
                return True, "no"
            else:
                return False, "unsure"    

    def _generate_question(self, question: str, state: OnboardingState) -> str:
        """Generate a conversational version of the question"""
        # Get the history of previous questions and answers
        history = ""
        for item in state.previous_questions:
            if item.get("question") and item.get("answer"):
                history += f"- Question: {item['question']}\n  Answer: {item['answer']}\n"
        
        prompt = f"""
        You are a friendly medical assistant helping a patient through an onboarding process.
        
        Previous conversation:
        {history}
        
        Next question to ask: {question}
        
        Generate a friendly, conversational way to ask this question.
        Keep it brief and simple.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.7}
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"Error generating question: {e}")
            return f"{question} Please answer yes or no."
    
    def _generate_clarification(self, question: str, last_answer: str, state: OnboardingState) -> str:
        """Generate a clarification request for an ambiguous answer"""
        explanation = self.EXPLANATIONS.get(question, "")
        
        prompt = f"""
        You are a friendly medical assistant helping a patient through an onboarding process.
        
        Question asked: {question}
        Patient's ambiguous response: "{last_answer}"
        Additional explanation available: {explanation}
        
        Generate a friendly message that:
        1. Acknowledges their response
        2. Explains what the question means (using the explanation provided)
        4. Emphasizes we need this information before we can proceed
        5. Keeps the tone patient and supportive
        
        Keep it conversational but direct.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.7}
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"Error generating clarification: {e}")
            return f"I understand that might not be clear. {explanation} We need a yes or no answer before we can continue. Could you please let me know: {question}"
    
    def _generate_upload_prompt(self, question: str, state: OnboardingState) -> str:
        """Generate a prompt asking the user to upload a relevant document"""
        document_type = ""
        examples = ""
        
        if "medication" in question.lower():
            document_type = "medication"
            examples = "prescription, medication box, medication plan"
        elif "hospital" in question.lower():
            document_type = "hospital visit"
            examples = "hospital letter, doctor's note, discharge summary"
        elif "disease" in question.lower() or "chronic" in question.lower():
            document_type = "medical condition"
            examples = "diagnosis letter, doctor's report, lab results"
        
        prompt = f"""
        The patient has indicated they have information about: {document_type}
        
        Generate a brief, friendly message asking them to upload a relevant document (such as {examples}).
        Explain this will help pre-fill their medical information accurately.
        Also mention they can type "skip" if they don't have documents to upload right now.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.7}
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"Error generating upload prompt: {e}")
            return f"Could you please upload a document related to your {document_type}? Examples include {examples}. This helps us pre-fill your medical information accurately. If you don't have documents to upload right now, just type 'skip'."
    
    def _generate_answer_from_document(self, question: str, extracted_data: Dict[str, Any]) -> str:
        """Generate an answer based on document content"""
        data_json = json.dumps(extracted_data, indent=2)
        
        prompt = f"""
        Question: {question}
        
        Extracted data from patient document:
        {data_json}
        
        Based on this document data, generate a concise answer to the question.
        Include 1-2 key details from the document to confirm the information source.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.3}
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"Error generating document-based answer: {e}")
            
            # Fallback answer
            if "medication" in question.lower() and extracted_data.get("medications"):
                return f"Yes - medication found in document: {', '.join(m.get('name', '') for m in extracted_data.get('medications', [])[:2])}"
            elif "hospital" in question.lower() and extracted_data.get("hospital_visits"):
                return f"Yes - hospital visit found in document: {extracted_data.get('hospital_visits', [{}])[0].get('name', 'Hospital visit confirmed')}"
            elif "disease" in question.lower() and extracted_data.get("diagnoses"):
                return f"Yes - condition found in document: {', '.join(d.get('condition', '') for d in extracted_data.get('diagnoses', [])[:2])}"
            else:
                return "Yes - details found in document"
    
    def _generate_summary(self, state: OnboardingState) -> str:
        """Generate a summary of the onboarding information"""
        # Collect all questions and answers
        qa_pairs = []
        for item in state.previous_questions:
            if item.get("question") and item.get("answer"):
                qa_pair = f"Question: {item['question']}\nAnswer: {item['answer']}"
                if item.get("followup"):
                    qa_pair += f"\nDocument: {item['followup']}"
                qa_pairs.append(qa_pair)
        
        qa_text = "\n\n".join(qa_pairs)
        
        # Collect extracted documents data
        documents_data = []
        for doc in getattr(state, "extracted_documents", []):
            doc_info = f"Document: {doc.get('filename')}\nTypes: {', '.join(doc.get('document_types', []))}"
            if doc.get('data'):
                doc_info += f"\nExtracted data: {json.dumps(doc.get('data'), indent=2)}"
            documents_data.append(doc_info)
        
        docs_text = "\n\n".join(documents_data)
        
        prompt = f"""
        You are a friendly medical assistant helping a patient through an onboarding process.
        
        Patient responses:
        {qa_text}
        
        Extracted document data:
        {docs_text}
        
        Generate a friendly, brief summary of the patient's onboarding information.
        For each medical question:
        1. Clearly state whether they answered yes or no
        2. Include any specific details they provided
        
        Highlight the key medical information collected, and thank them for completing the process.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.7}
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Thank you for completing your onboarding process. Your information has been recorded."
    
    def _extract_relevant_info(self, result) -> Dict[str, Any]:
        """Extract relevant information from OCR result based on document type"""
        extracted_info = {}
        
        for doc_type, group in result.document_groups.items():
            if not group.combined_data:
                continue
                
            data = group.combined_data
            
            # Process based on document type
            if doc_type == "MedicationBox" or doc_type == "Prescription" or doc_type == "MedicationPlan":
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
    
    def _update_state(self, state: OnboardingState, question=None, answer=None, followup_file=None):
        """Update session state with new question/answer"""
        state.previous_questions.append({
            "question": question,
            "answer": answer,
            "followup": followup_file
        })
        return state
    
    def _get_data_preview(self, state: OnboardingState) -> Dict[str, Any]:
        """Get a preview of extracted data for the UI"""
        preview = {}
        
        # Combine data from all documents
        for doc in getattr(state, "extracted_documents", []):
            data = doc.get("data", {})
            
            # Add medications
            if "medications" in data:
                if "medications" not in preview:
                    preview["medications"] = []
                preview["medications"].extend(data["medications"])
                
            # Add diagnoses
            if "diagnoses" in data:
                if "diagnoses" not in preview:
                    preview["diagnoses"] = []
                preview["diagnoses"].extend(data["diagnoses"])
                
            # Add hospital visits
            if "hospital_visits" in data:
                if "hospital_visits" not in preview:
                    preview["hospital_visits"] = []
                preview["hospital_visits"].extend(data["hospital_visits"])
                
            # Add patient info
            if "patient" in data and not preview.get("patient"):
                preview["patient"] = data["patient"]
        
        return preview