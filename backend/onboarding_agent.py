# backend/onboarding_agent.py
from typing import Dict, List, Optional, Any, Tuple
from models import OnboardingState, QuestionResponse, DocumentProcessResponse
from google import genai
import base64
import json
import logging

class GeminiOnboardingAgent:
    """
    Conversational Medical Onboarding Agent powered by Gemini
    that guides users through document scanning with natural language understanding.
    """
    
    # Core questions that must be asked during onboarding
    CORE_QUESTIONS = [
        "Do you take any medication?", 
        "Have you been to the hospital?", 
        "Do you have any chronic diseases?"
    ]
    
    # Document types to request for each question
    DOCUMENT_SUGGESTIONS = {
        "Do you take any medication?": ["medication box", "prescription", "medication list"],
        "Have you been to the hospital?": ["hospital letter", "doctor letter", "discharge summary"],
        "Do you have any chronic diseases?": ["doctor letter", "lab report", "diagnosis document"]
    }
    
    # Alternative follow-ups when user doesn't have documents
    ALTERNATIVE_FOLLOWUPS = {
        "Do you take any medication?": "Can you tell me which medications you're taking, including dosage if you know it?",
        "Have you been to the hospital?": "Could you share when you visited the hospital and what it was for?",
        "Do you have any chronic diseases?": "What chronic conditions have you been diagnosed with, and when were you diagnosed?"
    }
    
    def __init__(self, document_processor):
        """
        Initialize the agent with a document processor and Gemini client
        
        Args:
            document_processor: The document processor for handling uploaded documents
        """
        self.document_processor = document_processor
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini client
        try:
            self.client = genai.Client(
                vertexai=True,
                project="avi-cdtm-hack-team-9800",
                location="us-central1",
            )
            self.model = "gemini-2.0-flash-001"  # Using a powerful model for conversation
            self.logger.info("Gemini client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {e}")
            raise
            
        # Schema for analyzing user responses
        self.response_analysis_schema = {
            "type": "OBJECT",
            "properties": {
                "response_type": {
                    "type": "STRING",
                    "enum": ["positive", "negative", "unclear", "question"],
                    "description": "Classification of the user's response"
                },
                "confidence": {
                    "type": "NUMBER",
                    "description": "Confidence score for the classification (0-1)"
                },
                "reasoning": {
                    "type": "STRING",
                    "description": "Explanation for the classification"
                },
                "mentioned_entities": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Medical entities mentioned in the response (medications, conditions, etc.)"
                }
            },
            "required": ["response_type", "confidence"]
        }
    
    def get_next_question(self, state: OnboardingState) -> QuestionResponse:
        """
        Determine the next question or message to send to the user,
        maintaining conversational flow.
        """
        # Check if we've completed all core questions
        if state.current_question_index >= len(self.CORE_QUESTIONS) and not state.awaiting_followup:
            return QuestionResponse(
                message="Thank you for completing the onboarding process. I've recorded all your information.",
                awaiting_followup=False,
                done=True,
                current_question_index=state.current_question_index,
                extracted_data_preview=self._get_collected_data_summary(state)
            )
            
        # If we're awaiting a document upload
        if state.awaiting_followup and state.awaiting_document:
            current_q = self.CORE_QUESTIONS[state.current_question_index]
            doc_suggestions = self.DOCUMENT_SUGGESTIONS.get(current_q, ["relevant medical document"])
            
            return QuestionResponse(
                message=f"Please take a picture of your {' or '.join(doc_suggestions)}. This will help us better understand your medical situation.",
                awaiting_followup=True,
                done=False,
                current_question_index=state.current_question_index,
                extracted_data_preview=None,
                suggested_documents=doc_suggestions
            )
            
        # If we're awaiting a text followup (when user doesn't have documents)
        elif state.awaiting_followup and not state.awaiting_document:
            current_q = self.CORE_QUESTIONS[state.current_question_index]
            followup_q = self.ALTERNATIVE_FOLLOWUPS.get(current_q, f"Could you tell me more about your answer to '{current_q}'?")
            
            return QuestionResponse(
                message=followup_q,
                awaiting_followup=True,
                done=False,
                current_question_index=state.current_question_index,
                extracted_data_preview=None
            )
        
        # If we're waiting for clarification on an ambiguous answer
        elif hasattr(state, "awaiting_clarification") and state.awaiting_clarification:
            current_q = self.CORE_QUESTIONS[state.current_question_index]
            return QuestionResponse(
                message=f"I'm not sure I understood your answer. Could you please answer with 'yes' or 'no' to: {current_q}",
                awaiting_followup=False,
                done=False,
                current_question_index=state.current_question_index,
                extracted_data_preview=None
            )
        
        # Normal question flow
        elif state.current_question_index < len(self.CORE_QUESTIONS):
            # Check if we should use a conversational opener
            if state.current_question_index == 0:
                message = "To provide you with the best care, I need to ask a few health questions. " + self.CORE_QUESTIONS[0]
            else:
                # Make the conversation flow more naturally for follow-up questions
                message = self.CORE_QUESTIONS[state.current_question_index]
            
            return QuestionResponse(
                message=message,
                awaiting_followup=False,
                done=False,
                current_question_index=state.current_question_index,
                extracted_data_preview=None
            )
    
    def process_answer(self, state: OnboardingState, answer: str) -> QuestionResponse:
        """
        Process a user's answer using Gemini for natural language understanding
        and maintain conversational flow
        """
        # Ensure we have a current question
        if state.current_question_index >= len(self.CORE_QUESTIONS):
            return QuestionResponse(
                message="Thank you for completing the onboarding process.",
                awaiting_followup=False,
                done=True,
                current_question_index=state.current_question_index,
                extracted_data_preview=self._get_collected_data_summary(state)
            )
        
        # Make sure we initialize awaiting_document if not present
        if not hasattr(state, "awaiting_document"):
            state.awaiting_document = False
            
        # Make sure we initialize awaiting_clarification if not present
        if not hasattr(state, "awaiting_clarification"):
            state.awaiting_clarification = False
        
        current_q = self.CORE_QUESTIONS[state.current_question_index]
        
        # If we're awaiting clarification and get a response
        if state.awaiting_clarification:
            # Use Gemini to analyze the response
            analysis = self._analyze_response_with_gemini(answer, current_q)
            response_type = analysis.get("response_type", "unclear")
            
            if response_type == "unclear" or response_type == "question":
                # Still unclear, keep asking for clarification
                return QuestionResponse(
                    message=f"I still need a clear yes or no. Do you {current_q.lower()[3:]}",
                    awaiting_followup=False,
                    done=False,
                    current_question_index=state.current_question_index,
                    extracted_data_preview=None
                )
            
            # Clear the clarification flag since we got a clear answer
            state.awaiting_clarification = False
            
            # Process as a normal response now that it's clear
            if response_type == "positive":
                return self._handle_positive_response(state, answer, current_q)
            else:  # is_negative
                return self._handle_negative_response(state, answer, current_q)
        
        # If we're awaiting a text followup (alternative to document)
        elif state.awaiting_followup and not state.awaiting_document:
            # User has provided the requested text information
            # Save their detailed answer
            self._update_state(state, self.ALTERNATIVE_FOLLOWUPS.get(current_q, "Follow-up"), answer, None)
            
            # Now move to the next question
            state.awaiting_followup = False
            state.current_question_index += 1
            
            # Return the next question or completion
            return self.get_next_question(state)
            
        # Handle the no document followup flow
        elif state.awaiting_followup and state.awaiting_document:
            # Analyze if they're saying they don't have the document
            analysis = self._analyze_response_with_gemini(
                answer, 
                f"Do you have a {self.DOCUMENT_SUGGESTIONS.get(current_q, ['document'])[0]}?"
            )
            response_type = analysis.get("response_type", "unclear")
            
            if response_type == "negative" or "don't have" in answer.lower() or "do not have" in answer.lower():
                # They don't have the document, switch to text followup instead
                state.awaiting_document = False
                
                # Offer the alternative
                followup_q = self.ALTERNATIVE_FOLLOWUPS.get(current_q, f"Could you tell me more about your answer to '{current_q}'?")
                
                return QuestionResponse(
                    message=f"No problem. {followup_q}",
                    awaiting_followup=True,
                    done=False,
                    current_question_index=state.current_question_index,
                    extracted_data_preview=None
                )
            
            # If they said something else, assume they still want to upload
            return QuestionResponse(
                message="Please take a picture of your document when you're ready.",
                awaiting_followup=True,
                done=False,
                current_question_index=state.current_question_index,
                extracted_data_preview=None,
                suggested_documents=self.DOCUMENT_SUGGESTIONS.get(current_q, ["medical document"])
            )
            
        # Normal response to a question
        else:
            # Use Gemini to analyze the response
            analysis = self._analyze_response_with_gemini(answer, current_q)
            response_type = analysis.get("response_type", "unclear")
            
            if response_type == "unclear" or response_type == "question":
                # Handle unclear/ambiguous responses by asking for clarification
                state.awaiting_clarification = True
                return QuestionResponse(
                    message=f"I'm not sure I understood your answer. Could you please answer with 'yes' or 'no' to: {current_q}",
                    awaiting_followup=False,
                    done=False,
                    current_question_index=state.current_question_index,
                    extracted_data_preview=None
                )
            
            if response_type == "positive":
                return self._handle_positive_response(state, answer, current_q)
            else:  # is_negative
                return self._handle_negative_response(state, answer, current_q)
    
    def _handle_positive_response(self, state: OnboardingState, answer: str, current_q: str) -> QuestionResponse:
        """Handle a positive response to a question"""
        # Save the answer
        self._update_state(state, current_q, answer, None)
        
        # Ask if they have a document they can upload
        state.awaiting_followup = True
        state.awaiting_document = True
        state.last_question = current_q
        
        # Get document suggestions for this question
        doc_suggestions = self.DOCUMENT_SUGGESTIONS.get(current_q, ["relevant medical document"])
        doc_list = ', '.join(doc_suggestions[:-1]) + ' or ' + doc_suggestions[-1] if len(doc_suggestions) > 1 else doc_suggestions[0]
        
        return QuestionResponse(
            message=f"Do you have a {doc_list} that you can take a picture of?",
            awaiting_followup=True,
            done=False,
            current_question_index=state.current_question_index,
            extracted_data_preview=None,
            suggested_documents=doc_suggestions
        )
    
    def _handle_negative_response(self, state: OnboardingState, answer: str, current_q: str) -> QuestionResponse:
        """Handle a negative response to a question"""
        # Save the negative answer and move to next question
        self._update_state(state, current_q, answer, None)
        state.current_question_index += 1
        
        # Check if we've completed all questions
        if state.current_question_index >= len(self.CORE_QUESTIONS):
            return QuestionResponse(
                message="Thank you for completing the onboarding process. I've recorded all your information.",
                awaiting_followup=False,
                done=True,
                current_question_index=state.current_question_index,
                extracted_data_preview=self._get_collected_data_summary(state)
            )
        else:
            # Get the next question
            return self.get_next_question(state)
    
    def process_document(self, state: OnboardingState, image_bytes: bytes, filename: str) -> DocumentProcessResponse:
        """
        Process a document image and extract relevant information,
        then provide helpful feedback based on what was found.
        """
        # Process the document using the document processor
        try:
            result = self.document_processor.process_pages([image_bytes])
            
            # Extract relevant information
            extracted_data = self._extract_relevant_info(result)
            
            # Use Gemini to provide an intelligent response based on the extracted data
            response_message = self._generate_document_response(state, extracted_data, result.document_groups.keys())
            
            # Check if extracted data answers the current question
            current_q = self.CORE_QUESTIONS[state.current_question_index] if state.current_question_index < len(self.CORE_QUESTIONS) else state.last_question
            
            # Update state with the answer and document
            self._update_state(state, current_q, "Yes - document uploaded", filename)
            
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
            state.awaiting_document = False
            state.current_question_index += 1
            
            return DocumentProcessResponse(
                success=True,
                filename=filename,
                extracted_data=extracted_data,
                document_types=list(result.document_groups.keys()),
                message=response_message
            )
        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}")
            
            # Fallback to basic processing if Gemini enhancement fails
            try:
                result = self.document_processor.process_pages([image_bytes])
                extracted_data = self._extract_relevant_info(result)
                
                # Update state
                current_q = self.CORE_QUESTIONS[state.current_question_index] if state.current_question_index < len(self.CORE_QUESTIONS) else state.last_question
                self._update_state(state, current_q, "Yes - document uploaded", filename)
                
                if not hasattr(state, "extracted_documents"):
                    state.extracted_documents = []
                    
                state.extracted_documents.append({
                    "filename": filename,
                    "data": extracted_data,
                    "document_types": list(result.document_groups.keys())
                })
                
                # Move to next question
                state.awaiting_followup = False
                state.awaiting_document = False
                state.current_question_index += 1
                
                return DocumentProcessResponse(
                    success=True,
                    filename=filename,
                    extracted_data=extracted_data,
                    document_types=list(result.document_groups.keys()),
                    message="Thank you for uploading the document. I've extracted the relevant information."
                )
            except Exception as nested_error:
                self.logger.error(f"Fallback document processing failed: {str(nested_error)}")
                raise ValueError(f"Error processing document: {str(e)}. Fallback also failed: {str(nested_error)}")
    
    def _analyze_response_with_gemini(self, text: str, question: str) -> Dict[str, Any]:
        """
        Use Gemini to analyze the user's response to classify it as positive, negative, or unclear.
        """
        try:
            # Create the prompt for Gemini
            prompt = f"""
            You are an AI medical assistant analyzing a patient's response to a question.
            
            QUESTION: "{question}"
            PATIENT'S RESPONSE: "{text}"
            
            TASK:
            Analyze the response to determine whether it's:
            - "positive" (affirmative, yes, agreeing)
            - "negative" (denial, no, disagreeing)
            - "unclear" (ambiguous, can't tell if positive or negative)
            - "question" (the patient is asking a question instead of answering)
            
            For example:
            - "Yes" or "I do" or "correct" → positive
            - "No" or "I don't" or "never" → negative
            - "Maybe" or "hello?" or "what?" → unclear
            - "What medications are you referring to?" → question
            
            Also identify any medical entities mentioned (medications, conditions, etc.)
            """
            
            # Generate the response
            content_parts = [{"text": prompt}]
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=content_parts,
                config={
                    "temperature": 0.1,
                    "max_output_tokens": 4096,
                    "response_mime_type": "application/json",
                    "response_schema": self.response_analysis_schema
                }
            )
            
            try:
                # Parse the JSON response
                result = json.loads(response.text)
                return result
            except Exception as json_error:
                self.logger.error(f"Failed to parse Gemini response: {json_error}")
                # If response isn't proper JSON, try to extract the classification
                if "positive" in response.text.lower():
                    return {"response_type": "positive", "confidence": 0.7}
                elif "negative" in response.text.lower():
                    return {"response_type": "negative", "confidence": 0.7}
                elif "question" in response.text.lower():
                    return {"response_type": "question", "confidence": 0.7}
                else:
                    return {"response_type": "unclear", "confidence": 0.7}
                
        except Exception as e:
            self.logger.error(f"Failed to analyze response with Gemini: {e}")
            
            # Fallback to basic analysis
            text_lower = text.lower().strip()
            
            # Simple pattern matching as fallback
            positive_indicators = ["yes", "yeah", "yep", "sure", "ok", "okay", "correct", "right", "true", "i do", "i am", "i have"]
            negative_indicators = ["no", "nope", "nah", "not", "don't", "do not", "none", "never"]
            
            if any(indicator in text_lower for indicator in positive_indicators):
                return {"response_type": "positive", "confidence": 0.6}
            elif any(indicator in text_lower for indicator in negative_indicators):
                return {"response_type": "negative", "confidence": 0.6}
            elif "?" in text:
                return {"response_type": "question", "confidence": 0.6}
            else:
                return {"response_type": "unclear", "confidence": 0.6}
    
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
    
    def _get_collected_data_summary(self, state: OnboardingState) -> Dict[str, Any]:
        """Generate a summary of all collected data"""
        summary = {
            "medications": [],
            "diagnoses": [],
            "hospital_visits": [],
            "test_results": [],
            "patient": {}
        }
        
        # Merge data from all documents
        for doc in getattr(state, "extracted_documents", []):
            data = doc.get("data", {})
            
            # Merge medications
            if "medications" in data:
                for med in data["medications"]:
                    if med not in summary["medications"]:
                        summary["medications"].append(med)
                
            # Merge diagnoses
            if "diagnoses" in data:
                for diag in data["diagnoses"]:
                    if diag not in summary["diagnoses"]:
                        summary["diagnoses"].append(diag)
                
            # Merge hospital visits
            if "hospital_visits" in data:
                for visit in data["hospital_visits"]:
                    if visit not in summary["hospital_visits"]:
                        summary["hospital_visits"].append(visit)
                
            # Merge test results
            if "test_results" in data:
                for test in data["test_results"]:
                    if test not in summary["test_results"]:
                        summary["test_results"].append(test)
                
            # Update patient info
            if "patient" in data:
                summary["patient"].update(data["patient"])
        
        return summary
    
    def _generate_document_response(self, state: OnboardingState, extracted_data: Dict[str, Any], doc_types: List[str]) -> str:
        """Generate a helpful response based on the extracted document data"""
        try:
            # Format the extracted data for the prompt
            data_str = json.dumps(extracted_data, indent=2)
            doc_types_str = ", ".join(doc_types)
            
            # Create the prompt for Gemini
            prompt = f"""
            You are a friendly medical assistant helping with patient onboarding.
            
            The patient has just uploaded a document that was identified as: {doc_types_str}
            
            The following data was extracted from the document:
            {data_str}
            
            Generate a brief, friendly confirmation message that:
            1. Acknowledges what type of document was processed
            2. Mentions 1-3 key pieces of information that were successfully extracted (like medication names, diagnoses, etc.)
            3. Is concise (maximum 2 sentences)
            4. Has a warm, reassuring tone
            
            Do not mention any information that wasn't in the extracted data, and don't ask any questions.
            """
            
            # Generate the response
            content_parts = [{"text": prompt}]
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=content_parts,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 200,
                }
            )
            
            # Return the generated message, or a fallback if needed
            return response.text.strip() or "Thank you for uploading your document. I've successfully processed it."
            
        except Exception as e:
            self.logger.error(f"Failed to generate document response: {e}")
            
            # Create a basic response based on what was extracted
            message = "Thank you for uploading your document."
            
            # Add details about what was found
            if "medications" in extracted_data and extracted_data["medications"]:
                med_names = [m.get("name", "medication") for m in extracted_data["medications"][:2]]
                message += f" I found information about {' and '.join(med_names)}."
            elif "diagnoses" in extracted_data and extracted_data["diagnoses"]:
                diag_names = [d.get("condition", "condition") for d in extracted_data["diagnoses"][:2]]
                message += f" I found information about {' and '.join(diag_names)}."
            elif "hospital_visits" in extracted_data and extracted_data["hospital_visits"]:
                message += " I found information about your hospital visit."
            
            return message