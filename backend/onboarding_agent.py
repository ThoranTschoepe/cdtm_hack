# backend/onboarding_agent.py
from typing import Dict, List, Optional, Any, Tuple
from models import OnboardingState, QuestionResponse, DocumentProcessResponse, ExtractedDocument
from google import genai
from google.genai import types
import json

class OnboardingAgent:
    """
    Medical Onboarding Agent that guides users through the onboarding process.
    Uses an LLM to create a more natural conversation flow and ensure clear responses.
    """
    
    # Core categories for onboarding
    CATEGORIES = [
        "current_symptoms",
        "insurance",
        "medication",
        "health_record",
        "review_data"
    ]
    
    # Questions for each category
    QUESTIONS = {
        "current_symptoms": "Hi, I am Shelly. How can I help you?",
        "insurance": "Do you have health insurance?",
        "medication": "Do you take any medication?",
        "health_record": "Do you have any health records or medical history?",
        "review_data": "Let me review the information you've provided to see if anything is missing. Do you want to proceed?"
    }
    
    # Explanations for questions that might be confusing
    EXPLANATIONS = {
        "current_symptoms": "Please describe any symptoms or health concerns you're currently experiencing that led you to seek medical care.",
        "insurance": "This information helps us process your medical claims and determine coverage for treatments.",
        "medication": "This includes prescription medications, over-the-counter medicines, supplements, or vitamins that you take regularly.",
        "health_record": "Health records include hospital visits, doctor's notes, lab results, or any medical history documentation.",
        "review_data": "I'll check for any important health information that might be missing, such as medication details, vaccination status, or allergies."
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
        """Generate a conversational prompt for the next question or document request"""
        current_category = state.current_category
        
        # Ensure all categories are initialized in category_states
        for category in self.CATEGORIES:
            if category not in state.category_states:
                state.category_states[category] = "not_started"
                
        # Also ensure document_count is initialized for all categories
        for category in self.CATEGORIES:
            if category not in state.document_count:
                state.document_count[category] = 0
        
        # Check if we've completed all categories
        if all(state.category_states.get(cat) in ["enough_data", "not_enough_data"] for cat in self.CATEGORIES):
            summary = self._generate_summary(state)
            return QuestionResponse(
                message=summary,
                awaiting_followup=False,
                done=True,
                current_question_index=len(self.CATEGORIES),  # All complete
                extracted_data=self._get_data_preview(state)
            )
        
        # Special handling for review_data category
        if current_category == "review_data" and state.category_states[current_category] == "not_started":
            # First time entering the review data category
            question = self.QUESTIONS[current_category]
            conversational_q = self._generate_question(question, state)
            
            # Update state
            state.category_states[current_category] = "asked"
            
            return QuestionResponse(
                message=conversational_q,
                awaiting_followup=False,
                done=False,
                current_question_index=self.CATEGORIES.index(current_category),
                extracted_data=None
            )
        elif current_category == "review_data" and state.category_states[current_category] == "asked":
            # After user has agreed to review, analyze for missing data
            # Analyze for missing information
            missing_data = self._analyze_for_missing_data(state)
            
            if missing_data and len(missing_data) > 0:
                # Store the missing data items in the state
                state.missing_data_items = missing_data
                
                # Get the first item and ask about it
                first_item = missing_data.pop(0)
                state.current_missing_data_item = first_item
                
                # Mark category as in progress
                state.category_states[current_category] = "in_progress"
                
                prompt = self._generate_missing_data_question(first_item, state)
                return QuestionResponse(
                    message=prompt,
                    awaiting_followup=False,
                    done=False,
                    current_question_index=self.CATEGORIES.index(current_category),
                    extracted_data=self._get_data_preview(state)
                )
            else:
                # No missing data items, mark as complete
                state.category_states[current_category] = "enough_data"
                
                # Return the final summary
                summary = self._generate_summary(state)
                return QuestionResponse(
                    message=summary,
                    awaiting_followup=False,
                    done=True,
                    current_question_index=len(self.CATEGORIES),
                    extracted_data=self._get_data_preview(state)
                )
        
        # Get current category state
        category_state = state.category_states[current_category]
        
        # Handle different states for the current category
        if category_state == "not_started":
            # Ask initial question for this category
            question = self.QUESTIONS[current_category]
            conversational_q = self._generate_question(question, state)
            
            # Update state
            state.category_states[current_category] = "asked"
            
            return QuestionResponse(
                message=conversational_q,
                awaiting_followup=False,
                done=False,
                current_question_index=self.CATEGORIES.index(current_category),
                extracted_data=None
            )
            
        elif category_state == "asked":
            # We're waiting for an answer to the initial question
            # This state is handled in process_answer, so this shouldn't happen
            # But include it for completeness
            question = self.QUESTIONS[current_category]
            
            return QuestionResponse(
                message=f"{question}",
                awaiting_followup=False,
                done=False,
                current_question_index=self.CATEGORIES.index(current_category),
                extracted_data=None
            )
            
        elif category_state == "needs_clarification":
            # We need to clarify the previous answer
            question = self.QUESTIONS[current_category]
            clarification_q = self._generate_clarification(question, state.last_answer, state)
            
            return QuestionResponse(
                message=clarification_q,
                awaiting_followup=False,
                done=False,
                current_question_index=self.CATEGORIES.index(current_category),
                extracted_data=None
            )
            
        elif category_state == "awaiting_document":
            # We're waiting for document upload
            prompt = self._generate_upload_prompt(current_category, state)
            
            return QuestionResponse(
                message=prompt,
                awaiting_followup=True,
                done=False,
                current_question_index=self.CATEGORIES.index(current_category),
                extracted_data=self._get_data_preview(state)
            )
            
        elif category_state == "processed":
            # We've processed a document, ask if they have more
            prompt = self._generate_more_documents_prompt(current_category, state)
            
            return QuestionResponse(
                message=prompt,
                awaiting_followup=True,
                done=False,
                current_question_index=self.CATEGORIES.index(current_category),
                extracted_data=self._get_data_preview(state)
            )
            
        else:  # "enough_data" or "not_enough_data" - move to next category
            # Find the next category that hasn't been completed
            next_category = None
            for cat in self.CATEGORIES:
                if state.category_states[cat] == "not_started":
                    next_category = cat
                    break
                    
            if next_category:
                state.current_category = next_category
                return self.get_next_question(state)
            else:
                # All categories are done
                summary = self._generate_summary(state)
                return QuestionResponse(
                    message=summary,
                    awaiting_followup=False,
                    done=True,
                    current_question_index=len(self.CATEGORIES),
                    extracted_data=self._get_data_preview(state)
                )
    
    def process_answer(self, state: OnboardingState, answer: str) -> QuestionResponse:
        """Process a user's answer with LLM assistance"""
        current_category = state.current_category
        category_state = state.category_states[current_category]
        
        # Store the last answer for potential clarification
        state.last_answer = answer
        
        # Special handling for the review_data category
        if current_category == "review_data":
            if category_state == "asked":
                # User responding to the initial question about reviewing data
                is_clear, response_type = self._evaluate_answer(answer, self.QUESTIONS[current_category])
                
                if response_type in ["strong_yes", "yes"]:
                    # User wants to proceed with review
                    # Analyze for missing information
                    missing_data = self._analyze_for_missing_data(state)
                    
                    if missing_data and len(missing_data) > 0:
                        # Store the missing data items in the state
                        state.missing_data_items = missing_data
                        
                        # Get the first item and ask about it
                        first_item = missing_data.pop(0)
                        state.current_missing_data_item = first_item
                        
                        # Mark category as in progress
                        state.category_states[current_category] = "in_progress"
                        
                        prompt = self._generate_missing_data_question(first_item, state)
                        return QuestionResponse(
                            message=prompt,
                            awaiting_followup=False,
                            done=False,
                            current_question_index=self.CATEGORIES.index(current_category),
                            extracted_data=self._get_data_preview(state)
                        )
                    else:
                        # No missing data items, mark as complete
                        state.category_states[current_category] = "enough_data"
                        
                        # Return the final summary
                        summary = self._generate_summary(state)
                        return QuestionResponse(
                            message=summary,
                            awaiting_followup=False,
                            done=True,
                            current_question_index=len(self.CATEGORIES),
                            extracted_data=self._get_data_preview(state)
                        )
                else:
                    # User doesn't want to proceed with review, mark as enough_data and finish
                    state.category_states[current_category] = "enough_data"
                    
                    # Return the final summary
                    summary = self._generate_summary(state)
                    return QuestionResponse(
                        message=summary,
                        awaiting_followup=False,
                        done=True,
                        current_question_index=len(self.CATEGORIES),
                        extracted_data=self._get_data_preview(state)
                    )
            elif category_state == "in_progress":
                # User responding to a question about specific missing data
                # Store the answer to the specific missing data question
                if hasattr(state, 'current_missing_data_item') and state.current_missing_data_item:
                    item = state.current_missing_data_item
                    if not hasattr(state, 'missing_data_responses'):
                        state.missing_data_responses = {}
                    state.missing_data_responses[item] = answer
                
                # Check if we have more missing data items to ask about
                if hasattr(state, 'missing_data_items') and state.missing_data_items:
                    if len(state.missing_data_items) > 0:
                        # Get the next item and ask about it
                        next_item = state.missing_data_items.pop(0)
                        state.current_missing_data_item = next_item
                        
                        prompt = self._generate_missing_data_question(next_item, state)
                        return QuestionResponse(
                            message=prompt,
                            awaiting_followup=False,
                            done=False,
                            current_question_index=self.CATEGORIES.index(current_category),
                            extracted_data=self._get_data_preview(state)
                        )
                    else:
                        # No more items, mark this category as done
                        state.category_states[current_category] = "enough_data"
                        
                        # Generate a summary of the missing data responses
                        if hasattr(state, 'missing_data_responses') and state.missing_data_responses:
                            state.missing_data_recommendations = self._generate_missing_data_summary(state.missing_data_responses)
                        
                        # Return the final summary
                        summary = self._generate_summary(state)
                        return QuestionResponse(
                            message=summary,
                            awaiting_followup=False,
                            done=True,
                            current_question_index=len(self.CATEGORIES),
                            extracted_data=self._get_data_preview(state)
                        )
        
        # Special handling for current_symptoms category (first question)
        if current_category == "current_symptoms" and category_state == "asked":
            # Extract symptoms from answer
            symptoms = self._extract_symptoms(answer)
            
            # Generate a more clinical description
            clinical_summary = self._generate_clinical_summary(answer)
            
            # Update state with the symptoms info
            question = self.QUESTIONS[current_category]
            self._update_state(state, question, f"Presenting Concern: {clinical_summary}", None)
            
            # Store the symptoms info
            state.symptoms_info["description"] = clinical_summary
            if symptoms:
                state.symptoms_info["extracted_symptoms"] = symptoms
            
            # For current_symptoms, we don't ask for documents - move to next category
            state.category_states[current_category] = "enough_data" 
            self._move_to_next_category(state)
            return self.get_next_question(state)
        
        # Check for skip response at any stage
        if answer.lower() == "skip":
            # Special handling for review_data category when skipping
            if current_category == "review_data":
                if category_state == "in_progress":
                    # Skip the current item and move to the next one
                    if hasattr(state, 'missing_data_items') and state.missing_data_items:
                        if len(state.missing_data_items) > 0:
                            # Get the next item and ask about it
                            next_item = state.missing_data_items.pop(0)
                            state.current_missing_data_item = next_item
                            
                            prompt = self._generate_missing_data_question(next_item, state)
                            return QuestionResponse(
                                message=prompt,
                                awaiting_followup=False,
                                done=False,
                                current_question_index=self.CATEGORIES.index(current_category),
                                extracted_data=self._get_data_preview(state)
                            )
                        else:
                            # No more items, mark as done
                            state.category_states[current_category] = "enough_data"
                            
                            # Generate a summary of the missing data responses
                            if hasattr(state, 'missing_data_responses') and state.missing_data_responses:
                                state.missing_data_recommendations = self._generate_missing_data_summary(state.missing_data_responses)
                            
                            # Return the final summary
                            summary = self._generate_summary(state)
                            return QuestionResponse(
                                message=summary,
                                awaiting_followup=False,
                                done=True,
                                current_question_index=len(self.CATEGORIES),
                                extracted_data=self._get_data_preview(state)
                            )
                elif category_state == "asked":
                    # User is skipping the entire review process
                    state.category_states[current_category] = "enough_data"
                    
                    # Return the final summary
                    summary = self._generate_summary(state)
                    return QuestionResponse(
                        message=summary,
                        awaiting_followup=False,
                        done=True,
                        current_question_index=len(self.CATEGORIES),
                        extracted_data=self._get_data_preview(state)
                    )
            
            # Handle skip based on current state
            if category_state == "asked":
                # When skipping the initial category question, treat as "no"
                question = self.QUESTIONS[current_category]
                self._update_state(state, question, "No - skipped by user", None)
                
                # Mark category as not enough data and move to next category
                state.category_states[current_category] = "not_enough_data"
                self._move_to_next_category(state)
                return self.get_next_question(state)
                
            elif category_state == "awaiting_document":
                # When skipping document upload
                if state.document_count[current_category] > 0:
                    # Already has some documents, mark as enough
                    state.category_states[current_category] = "enough_data"
                else:
                    # No documents uploaded, mark as not enough
                    state.category_states[current_category] = "not_enough_data"
                
                # Move to next category
                self._move_to_next_category(state)
                return self.get_next_question(state)
                
            elif category_state == "processed":
                # When skipping additional document uploads, treat as "done"
                has_enough_data = state.document_count[current_category] > 0
                state.category_states[current_category] = "enough_data" if has_enough_data else "not_enough_data"
                
                # Move to next category
                self._move_to_next_category(state)
                return self.get_next_question(state)
        
        # Handle answer based on current category state
        if category_state == "asked":
            # User is answering the initial category question
            question = self.QUESTIONS[current_category]
            
            # Evaluate if the answer is clear and what type of response it is
            is_clear, response_type = self._evaluate_answer(answer, question)
            
            # If the answer isn't clear, ask for clarification
            if not is_clear:
                state.category_states[current_category] = "needs_clarification"
                return self.get_next_question(state)
            
            # Clear answer - process based on the response type
            if response_type in ["strong_yes", "yes"]:
                # Update state to await document upload
                state.category_states[current_category] = "awaiting_document"
                
                # Store the answer
                self._update_state(state, question, f"{response_type}: {answer}", None)
                
                # Get the document upload prompt
                return self.get_next_question(state)
            else:  # "no" or "strong_no"
                # No documents for this category, mark as not enough data
                state.category_states[current_category] = "not_enough_data"
                
                # Store the answer
                self._update_state(state, question, f"{response_type}: {answer}", None)
                
                # Move to next category
                self._move_to_next_category(state)
                return self.get_next_question(state)
                
        elif category_state == "needs_clarification":
            # User is clarifying their previous answer
            question = self.QUESTIONS[current_category]
            
            # Evaluate the clarified answer
            is_clear, response_type = self._evaluate_answer(answer, question)
            
            # If still not clear, keep asking (but limit to one retry)
            if not is_clear:
                # Just accept it and move on to avoid frustration
                response_type = "no" if "no" in answer.lower() else "yes"
            
            # Process the clarified answer
            if response_type in ["strong_yes", "yes"]:
                # Update state to await document upload
                state.category_states[current_category] = "awaiting_document"
                
                # Store the answer
                self._update_state(state, question, f"{response_type}: {answer}", None)
                
                # Get the document upload prompt
                return self.get_next_question(state)
            else:  # "no" or "strong_no"
                # No documents for this category, mark as not enough data
                state.category_states[current_category] = "not_enough_data"
                
                # Store the answer
                self._update_state(state, question, f"{response_type}: {answer}", None)
                
                # Move to next category
                self._move_to_next_category(state)
                return self.get_next_question(state)
        
        elif category_state == "processed":
            # User is answering if they have more documents
            # Check if they want to upload more or move on
            has_more = self._check_has_more_documents(answer)
            
            if has_more:
                # User wants to upload more documents
                state.category_states[current_category] = "awaiting_document"
                return self.get_next_question(state)
            else:
                # User is done with this category
                # Check if we have enough documents
                has_enough_data = state.document_count[current_category] > 0
                state.category_states[current_category] = "enough_data" if has_enough_data else "not_enough_data"
                
                # Move to next category
                self._move_to_next_category(state)
                return self.get_next_question(state)
        
        # Default response if none of the conditions are met
        return self.get_next_question(state)

    def _move_to_next_category(self, state):
        """Find and move to the next unprocessed category"""
        current_index = self.CATEGORIES.index(state.current_category)
        
        # Try categories after the current one
        for i in range(current_index + 1, len(self.CATEGORIES)):
            cat = self.CATEGORIES[i]
            if state.category_states[cat] == "not_started":
                state.current_category = cat
                # Set to "asked" state to ensure we get a question, not a document prompt
                state.category_states[cat] = "asked"
                return
                
        # If we get here, we've gone through all categories
        # Leave the current category as is, the get_next_question will handle completion
    
    def process_documents(self, state: OnboardingState, image_bytes_list: List[bytes], filenames: List[str]) -> DocumentProcessResponse:
        """Process multiple documents uploaded by the user"""
        current_category = state.current_category
        
        # If no files were uploaded or empty list, treat as a skip
        if not image_bytes_list or len(image_bytes_list) == 0:
            # Handle skipping based on the current category
            if state.document_count[current_category] > 0:
                # Already has some documents, mark as enough
                state.category_states[current_category] = "enough_data"
            else:
                # No documents uploaded, mark as not enough
                state.category_states[current_category] = "not_enough_data"
            
            # Move to next category
            self._move_to_next_category(state)
            
            # Return a response indicating skip was successful
            return DocumentProcessResponse(
                success=True,
                filename="skipped",
                extracted_data={"status": "skipped"},
                document_types=[]
            )
        
        # Special handling for medication category - ensure we always provide medication data
        is_medication = current_category == "medication"
        
        # Process all documents together using the document processor
        try:
            result = self.document_processor.process_pages(image_bytes_list)
            
            # Extract relevant information
            extracted_data = self._extract_relevant_info(result)
            
            # For medication category, ensure we have medication data
            if is_medication and "medications" not in extracted_data:
                extracted_data["medications"] = [
                    {
                        "name": "Medication from uploaded document",
                        "dosage": "See document for details",
                        "document_type": "Uploaded Document"
                    }
                ]
            
            # Check if we found medications but we're not in the medication category
            # or if we found medication document types
            medication_doc_types = ["MedicationBox", "Prescription", "MedicationPlan"]
            doc_types = list(result.document_groups.keys())
            
            is_medication_doc = any(doc_type in medication_doc_types for doc_type in doc_types)
            has_medications = "medications" in extracted_data and extracted_data["medications"]
            
            if (has_medications or is_medication_doc) and current_category != "medication":
                # Update current category for this document
                current_category = "medication"
                
                # Update state's current category if medications are found
                state.current_category = "medication"
                state.category_states["medication"] = "processed"  # Mark as processed
            
            # Add extracted data to state
            files_str = ", ".join(filenames)
            
            # If we have no document types but we're in medication category, create a medication type
            if not doc_types and is_medication:
                doc_types = ["MedicationDocument"]
            
            # Create an ExtractedDocument instance
            doc = ExtractedDocument(
                filename=files_str,
                data=extracted_data,
                document_types=doc_types,
                category=current_category
            )
            
            # Add to state's extracted documents
            state.extracted_documents.append(doc)
            
            # Increment document count for this category
            state.document_count[current_category] += 1
            
            # Update state to processed
            state.category_states[current_category] = "processed"
            
            # Create response with extracted data
            response = DocumentProcessResponse(
                success=True,
                filename=files_str,
                extracted_data=extracted_data,
                document_types=doc_types
            )
            
            return response
        except Exception as e:
            # Log the error but continue
            print(f"Error processing documents: {e}")
            
            # Still mark this category as processed even if document processing failed
            # This ensures the conversation flow continues
            files_str = ", ".join(filenames)
            
            # Create some basic data for the category
            if current_category == "insurance":
                empty_data = {"insurance": {"provider": "Unknown", "policy_number": "Processing Failed"}}
            elif current_category == "medication":
                empty_data = {"medications": [{"name": "Document Processing Failed", "dosage": "N/A"}]}
            elif current_category == "health_record":
                empty_data = {"health_records": {"diagnoses": [{"condition": "Document Processing Failed"}]}}
            else:
                empty_data = {}
            
            # Create a minimal document instance
            doc = ExtractedDocument(
                filename=files_str,
                data=empty_data,
                document_types=["ProcessingFailed"],
                category=current_category
            )
            
            # Add to state's extracted documents
            state.extracted_documents.append(doc)
            
            # Increment document count for this category
            state.document_count[current_category] += 1
            
            # Update state to processed
            state.category_states[current_category] = "processed"
            
            # Create response with minimal data
            response = DocumentProcessResponse(
                success=True,
                filename=files_str,
                extracted_data=empty_data,
                document_types=["ProcessingFailed"]
            )
            
            return response
            
    def _generate_more_documents_prompt(self, category: str, state: OnboardingState) -> str:
        """Generate a prompt asking if user has more documents for the current category"""
        # Use a direct, focused message
        return f"Do you have additional {category.replace('_', ' ')} documents to include? Type or click 'skip' if complete."

    def _check_has_more_documents(self, answer: str) -> bool:
        """Check if user indicated they have more documents to upload"""
        prompt = f"""
        Patient response: "{answer}"
        
        Does this response indicate they have more documents to upload? 
        Respond YES if they want to upload more documents.
        Respond NO if they are done, have no more documents, or want to move on.
        
        IMPORTANT: Do not include any quotation marks in your response.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.1}
            )
            
            # Remove any quotation marks from the response
            cleaned_response = response.text.strip().replace('"', '').replace("'", "").upper()
            return "YES" in cleaned_response
        except Exception as e:
            print(f"Error checking for more documents: {e}")
            
            # Fallback check
            answer_lower = answer.lower()
            positive_indicators = ["yes", "more", "another", "upload", "have"]
            negative_indicators = ["no", "done", "finished", "complete", "that's all", "that's it"]
            
            # Check for negative indicators first (they take priority)
            for word in negative_indicators:
                if word in answer_lower:
                    return False
                    
            # Then check for positive indicators
            for word in positive_indicators:
                if word in answer_lower:
                    return True
                    
            # Default to no more documents if unclear
            return False

    def _generate_upload_prompt(self, category: str, state: OnboardingState) -> str:
        """Generate a prompt asking the user to upload a relevant document"""
        # For current_symptoms, we don't expect documents
        if category == "current_symptoms":
            # Move to next category immediately
            state.category_states[category] = "enough_data"
            self._move_to_next_category(state)
            return self.get_next_question(state).message
            
        examples = ""
        
        if category == "insurance":
            examples = "insurance card, insurance policy documents, coverage statements"
        elif category == "medication":
            examples = "prescription, medication box, medication plan"
        elif category == "health_record":
            examples = "hospital letter, doctor's note, discharge summary, lab results, immunization records"
        
        # Use a direct message that clearly indicates both upload and skip options
        return f"Please upload your {category.replace('_', ' ')} documents (e.g., {examples}) for your general practice appointment. Click 'Skip' to continue without uploading."
    
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
        # Special handling for the first question (Shelly's greeting)
        if question == self.QUESTIONS["current_symptoms"]:
            return "I'm Shelly, your medical assistant. I'll help you prepare the necessary documents for your general practice appointment. To get started, please tell me what brings you in today."
            
        # Get the history of previous questions and answers
        history = ""
        for item in state.previous_questions:
            if item.get("question") and item.get("answer"):
                history += f"- Question: {item['question']}\n  Answer: {item['answer']}\n"
        
        prompt = f"""
        You are Shelly, a medical assistant helping a patient prepare documents for their general practice appointment.
        
        Previous conversation:
        {history}
        
        Next question to ask: {question}
        
        Generate a direct, professional way to ask this question.
        Focus on gathering the information needed to prepare for their appointment.
        Make it clear you're helping them get their documents ready for the general practice.
        
        IMPORTANT:
        - DO NOT start with greetings like "Hi", "Hello", or "Good day"
        - Make the question direct and concise (1-3 sentences maximum)
        - No small talk or unnecessary preamble
        - Mention that they can type "skip" if they prefer not to answer
        - Focus solely on gathering the specific information needed
        
        IMPORTANT: Do not include any quotation marks in your response.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.7}
            )
            
            # Remove any quotation marks from the response
            cleaned_response = response.text.strip().replace('"', '').replace("'", "")
            return cleaned_response
        except Exception as e:
            print(f"Error generating question: {e}")
            return f"For your general practice appointment: {question} You can type 'skip' to move to the next question."
    
    def _generate_clarification(self, question: str, last_answer: str, state: OnboardingState) -> str:
        """Generate a clarification request for an ambiguous answer"""
        explanation = self.EXPLANATIONS.get(question, "")
        
        prompt = f"""
        You are Shelly, a medical assistant helping a patient prepare documents for their general practice appointment.
        
        Question asked: {question}
        Patient's ambiguous response: "{last_answer}"
        Additional explanation available: {explanation}
        
        Generate a direct, professional clarification request that:
        1. Briefly acknowledges their response
        2. Clearly states what information is needed
        3. Explains why this is important for their appointment documents
        4. Asks for a more specific response
        
        IMPORTANT:
        - DO NOT start with greetings like "Hi", "Hello", or "Good day"
        - Make the question direct and concise (1-3 sentences maximum)
        - No small talk or unnecessary preamble
        - Focus solely on getting the specific medical information needed
        
        IMPORTANT: Do not include any quotation marks in your response.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.7}
            )
            
            # Remove any quotation marks from the response
            cleaned_response = response.text.strip().replace('"', '').replace("'", "")
            return cleaned_response
        except Exception as e:
            print(f"Error generating clarification: {e}")
            return f"I need a clearer answer about: {question} {explanation} Please provide this information for your medical records."
    
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
            elif "doctor" in question.lower() and "health_records" in extracted_data:
                health_records = extracted_data.get("health_records", {})
                
                if "hospital_visits" in health_records and health_records["hospital_visits"]:
                    return f"Yes - health record found in document: {health_records.get('hospital_visits', [{}])[0].get('name', 'Hospital visit')}"
                elif "diagnoses" in health_records and health_records["diagnoses"]:
                    return f"Yes - health record found in document with diagnoses: {', '.join(d.get('condition', '') for d in health_records.get('diagnoses', [])[:2])}"
                elif "test_results" in health_records and health_records["test_results"]:
                    return f"Yes - health record found in document with test results: {', '.join(t.get('name', '') for t in health_records.get('test_results', [])[:2])}"
                else:
                    return "Yes - health records found in document"
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
        
        # Get symptoms info directly from the state
        symptoms_description = state.symptoms_info.get("description", "No symptoms described")
        symptoms_list = state.symptoms_info.get("extracted_symptoms", [])
        symptoms_text = ", ".join(symptoms_list) if symptoms_list else "None extracted"
        
        # Create a summary of document counts by category
        doc_counts = state.document_count
        doc_count_summary = "\n".join([
            f"- {category.replace('_', ' ').title()}: {count} document(s)" 
            for category, count in doc_counts.items()
        ])
        
        # Collect extracted documents data by category
        documents_by_category = {}
        for doc in state.extracted_documents:
            category = doc.category if isinstance(doc, ExtractedDocument) else doc.get("category", "unknown")
            if category not in documents_by_category:
                documents_by_category[category] = []
            
            doc_info = f"Document: {doc.filename if isinstance(doc, ExtractedDocument) else doc.get('filename')}\nTypes: {', '.join(doc.document_types if isinstance(doc, ExtractedDocument) else doc.get('document_types', []))}"
            if hasattr(doc, 'data') and doc.data:
                doc_info += f"\nExtracted data: {json.dumps(doc.data, indent=2)}"
            elif isinstance(doc, dict) and doc.get('data'):
                doc_info += f"\nExtracted data: {json.dumps(doc.get('data'), indent=2)}"
            
            documents_by_category[category].append(doc_info)
        
        # Format the documents by category
        docs_text = ""
        for category, docs in documents_by_category.items():
            docs_text += f"\n\n{category.replace('_', ' ').title()} Documents:\n"
            docs_text += "\n\n".join(docs)
        
        # Include missing data recommendations if available
        missing_data_recommendations = ""
        if hasattr(state, 'missing_data_recommendations') and state.missing_data_recommendations:
            missing_data_recommendations = f"\n\nRecommendations for missing information:\n{state.missing_data_recommendations}"
        
        prompt = f"""
        You are Shelly, a medical assistant helping patients prepare documents for their general practice appointment.
        
        Patient's main concerns/symptoms:
        Description: {symptoms_description}
        Extracted symptoms: {symptoms_text}
        
        Patient responses:
        {qa_text}
        
        Document summary:
        {doc_count_summary}
        
        Extracted document data:{docs_text}
        {missing_data_recommendations}
        
        Generate a concise, professional summary of the documents prepared for the general practice appointment.
        
        Your summary should:
        1. Thank the patient for providing their information and documents
        2. Clearly state what documents have been prepared for the appointment
        3. Mention the patient's main concerns that will be addressed
        4. Provide a brief overview of what to expect at the appointment
        5. Let them know if any additional documents might be helpful to bring
        6. Keep the tone professional and focused on the upcoming appointment
        
        IMPORTANT: Do not include any quotation marks in your response.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.7}
            )
            
            # Remove any quotation marks from the response
            cleaned_response = response.text.strip().replace('"', '').replace("'", "")
            return cleaned_response
        except Exception as e:
            print(f"Error generating summary: {e}")
            
            # Fallback summary 
            summary = f"Thank you for completing your general practice pre-appointment preparation. "
            
            if symptoms_description and symptoms_description != "No symptoms described":
                summary += f"I've noted your main concern regarding: {symptoms_description}. "
                
            summary += "We've prepared the following documents for your appointment: "
            
            for category, count in doc_counts.items():
                if count > 0:
                    category_name = category.replace('_', ' ').title()
                    summary += f"{count} {category_name} document(s), "
                    
            summary += "Please bring these documents to your appointment. Your doctor will review this information to provide you with the best care possible."
            return summary
    
    def _extract_relevant_info(self, result) -> Dict[str, Any]:
        """Extract relevant information from OCR result based on document type"""
        extracted_info = {}
        
        # If no document groups or empty result, create basic medication structure
        if not result or not result.document_groups or len(result.document_groups) == 0:
            # Add default medication data if we're in the medication category
            return {
                "status": "No data extracted from document",
                "medications": [
                    {
                        "name": "Medication from uploaded document",
                        "dosage": "See document for details",
                        "document_type": "Uploaded Document"
                    }
                ]
            }
        
        for doc_type, group in result.document_groups.items():
            if not group.combined_data:
                continue
                
            data = group.combined_data
            
            # Process based on document type
            if doc_type == "InsuranceCard":
                # Extract insurance information
                if "insurance" not in extracted_info:
                    extracted_info["insurance"] = {}
                
                # Add document type for reference
                extracted_info["insurance"]["document_type"] = "Insurance Card"
                
                # Extract common insurance card fields
                insurance_fields = ["provider", "policy_number", "group_number", "member_id", "coverage_type"]
                for field in insurance_fields:
                    if field in data:
                        extracted_info["insurance"][field] = data[field]
                
                # Extract from policyholder if present
                if "policyholder" in data and isinstance(data["policyholder"], dict):
                    for field, value in data["policyholder"].items():
                        if field not in extracted_info["insurance"]:
                            extracted_info["insurance"][field] = value
                
                # Extract from card_details if present
                if "card_details" in data and isinstance(data["card_details"], dict):
                    for field, value in data["card_details"].items():
                        if field not in extracted_info["insurance"]:
                            extracted_info["insurance"][field] = value
                            
            elif doc_type == "MedicationBox" or doc_type == "Prescription" or doc_type == "MedicationPlan":
                if "medications" not in extracted_info:
                    extracted_info["medications"] = []
                
                # For MedicationBox, extract from active_ingredients or medication_details
                if doc_type == "MedicationBox":
                    if "active_ingredients" in data and isinstance(data["active_ingredients"], list):
                        for ingredient in data["active_ingredients"]:
                            med = {
                                "name": ingredient.get("name", "Unknown"),
                                "amount": ingredient.get("amount", ""),
                                "document_type": "Medication Box"
                            }
                            extracted_info["medications"].append(med)
                    elif "medication_details" in data and isinstance(data["medication_details"], dict):
                        med_details = data["medication_details"]
                        med = {
                            "name": med_details.get("brand_name", "Unknown"),
                            "generic_name": med_details.get("generic_name", ""),
                            "strength": med_details.get("strength", ""),
                            "document_type": "Medication Box"
                        }
                        extracted_info["medications"].append(med)
                
                # For Prescription, extract from prescribed_medications
                elif doc_type == "Prescription":
                    for med in data["prescribed_medications"]:
                        medication = {
                            "name": med.get("name", "Unknown"),
                            "dosage": med.get("strength", ""),
                            "instructions": med.get("directions", ""),
                            "document_type": "Prescription"
                        }
                        extracted_info["medications"].append(medication)
                
                # For MedicationPlan, extract from medications
                elif doc_type == "MedicationPlan":
                    for med in data["medications"]:
                        medication = {
                            "name": med.get("name", "Unknown"),
                            "dosage": med.get("dosage", ""),
                            "frequency": med.get("frequency", ""),
                            "timing": med.get("timing", ""),
                            "document_type": "Medication Plan"
                        }
                        extracted_info["medications"].append(medication)
            
            elif doc_type == "HospitalLetter" or doc_type == "DoctorLetter":
                # Create health_records if not present
                if "health_records" not in extracted_info:
                    extracted_info["health_records"] = {}
                
                # Extract diagnoses if present
                if "diagnoses" in data and isinstance(data["diagnoses"], list):
                    if "diagnoses" not in extracted_info["health_records"]:
                        extracted_info["health_records"]["diagnoses"] = []
                    
                    for diagnosis in data["diagnoses"]:
                        diag = {
                            "condition": diagnosis.get("diagnosis") or diagnosis.get("condition", "Unknown"),
                            "document_type": doc_type
                        }
                        if "details" in diagnosis:
                            diag["details"] = diagnosis["details"]
                        if "code" in diagnosis:
                            diag["code"] = diagnosis["code"]
                        
                        extracted_info["health_records"]["diagnoses"].append(diag)
                
                # Extract hospital/doctor information
                if "letter_metadata" in data and isinstance(data["letter_metadata"], dict):
                    if "hospital_visits" not in extracted_info["health_records"]:
                        extracted_info["health_records"]["hospital_visits"] = []
                    
                    visit = {
                        "document_type": doc_type
                    }
                    
                    if doc_type == "HospitalLetter":
                        visit["name"] = data["letter_metadata"].get("hospital_name", "Unknown Hospital")
                        visit["department"] = data["letter_metadata"].get("hospital_department", "")
                    else:  # DoctorLetter
                        visit["name"] = data["letter_metadata"].get("clinic_name", "Unknown Clinic")
                        visit["doctor"] = data["letter_metadata"].get("doctor_name", "")
                    
                    visit["date"] = data["letter_metadata"].get("date", "")
                    
                    extracted_info["health_records"]["hospital_visits"].append(visit)
                    
            elif doc_type == "LabReport":
                # Create health_records if not present
                if "health_records" not in extracted_info:
                    extracted_info["health_records"] = {}
                
                # Extract test results
                if "test_results" in data and isinstance(data["test_results"], list):
                    if "test_results" not in extracted_info["health_records"]:
                        extracted_info["health_records"]["test_results"] = []
                    
                    for test in data["test_results"]:
                        result = {
                            "name": test.get("test_name", "Unknown Test"),
                            "document_type": "Lab Report"
                        }
                        
                        if "value" in test:
                            result["value"] = test["value"]
                        
                        if "reference_range" in test and isinstance(test["reference_range"], dict):
                            range_text = []
                            if "lower_limit" in test["reference_range"] and "upper_limit" in test["reference_range"]:
                                range_text.append(f"{test['reference_range']['lower_limit']} - {test['reference_range']['upper_limit']}")
                            elif "text_range" in test["reference_range"]:
                                range_text.append(test["reference_range"]["text_range"])
                            
                            if range_text:
                                result["reference_range"] = ", ".join(range_text)
                        
                        if "flag" in test:
                            result["status"] = test["flag"]
                        
                        extracted_info["health_records"]["test_results"].append(result)
            
            # Add patient info from any document type
            if "patient_information" in data and isinstance(data["patient_information"], dict):
                if "patient" not in extracted_info:
                    extracted_info["patient"] = {}
                
                # Copy patient information fields
                for field, value in data["patient_information"].items():
                    if field not in extracted_info["patient"] or not extracted_info["patient"][field]:
                        extracted_info["patient"][field] = value
            
            # Also check for policyholder info which might contain patient details
            elif "policyholder" in data and isinstance(data["policyholder"], dict):
                if "patient" not in extracted_info:
                    extracted_info["patient"] = {}
                
                # Copy policyholder information as patient info
                for field, value in data["policyholder"].items():
                    if field not in extracted_info["patient"] or not extracted_info["patient"][field]:
                        extracted_info["patient"][field] = value
        
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
        preview = {
            "current_symptoms": {},
            "insurance": {
                "_note": "No insurance documents uploaded yet. Upload insurance cards or documents to see information here."
            },
            "medications": [],
            "health_records": {
                "diagnoses": [],
                "hospital_visits": [],
                "test_results": [],
                "_note": "No health record documents processed yet. Upload medical records to see information here."
            }
        }
        
        # Add symptoms info if available
        if state.symptoms_info:
            preview["current_symptoms"] = state.symptoms_info
        else:
            preview["current_symptoms"]["_note"] = "No symptoms information provided yet."
        
        # Add patient info if available (store it in insurance since we removed personal_info)
        if state.patient_info and len(state.patient_info) > 0:
            preview["insurance"].update(state.patient_info)
            # Remove note if we have data
            if "_note" in preview["insurance"]:
                del preview["insurance"]["_note"]
        
        # First pass: check all documents for medications specifically
        has_medications = False
        for i, doc in enumerate(state.extracted_documents):
            data = doc.data if isinstance(doc, ExtractedDocument) else doc.get("data", {})
            if "medications" in data and data["medications"]:
                has_medications = True
                # Important: Always clear the placeholder first if we find real medications
                if preview["medications"] and any("_note" in med for med in preview["medications"]):
                    preview["medications"] = []
                # Add the medications to the preview
                preview["medications"].extend(data["medications"])
        
        # Combine data from all documents
        for i, doc in enumerate(state.extracted_documents):
            data = doc.data if isinstance(doc, ExtractedDocument) else doc.get("data", {})
            category = doc.category if isinstance(doc, ExtractedDocument) else doc.get("category", "unknown")
            
            # Add insurance data
            if "insurance" in data:
                preview["insurance"].update(data["insurance"])
                # Remove note if we have data
                if "_note" in preview["insurance"]:
                    del preview["insurance"]["_note"]
            
            # Skip medications here since we already processed them above
            
            # Add health records data
            if "health_records" in data:
                health_records = data["health_records"]
                
                # Add diagnoses
                if "diagnoses" in health_records and health_records["diagnoses"]:
                    preview["health_records"]["diagnoses"].extend(health_records["diagnoses"])
                    # Remove note if we have real data
                    if "_note" in preview["health_records"]:
                        del preview["health_records"]["_note"]
                
                # Add hospital visits
                if "hospital_visits" in health_records and health_records["hospital_visits"]:
                    preview["health_records"]["hospital_visits"].extend(health_records["hospital_visits"])
                    # Remove note if we have real data
                    if "_note" in preview["health_records"]:
                        del preview["health_records"]["_note"]
                
                # Add test results
                if "test_results" in health_records and health_records["test_results"]:
                    preview["health_records"]["test_results"].extend(health_records["test_results"])
                    # Remove note if we have real data
                    if "_note" in preview["health_records"]:
                        del preview["health_records"]["_note"]
            
            # Handle older format data (for backward compatibility)
            # Add diagnoses directly in data
            if "diagnoses" in data and data["diagnoses"]:
                preview["health_records"]["diagnoses"].extend(data["diagnoses"])
                # Remove note if we have real data
                if "_note" in preview["health_records"]:
                    del preview["health_records"]["_note"]
            
            # Add hospital visits directly in data
            if "hospital_visits" in data and data["hospital_visits"]:
                preview["health_records"]["hospital_visits"].extend(data["hospital_visits"])
                # Remove note if we have real data
                if "_note" in preview["health_records"]:
                    del preview["health_records"]["_note"]
            
            # Add test results directly in data
            if "test_results" in data and data["test_results"]:
                preview["health_records"]["test_results"].extend(data["test_results"])
                # Remove note if we have real data
                if "_note" in preview["health_records"]:
                    del preview["health_records"]["_note"]
            
            # Handle current symptoms from documents
            if category == "current_symptoms" and "symptoms" in data:
                if "extracted_symptoms" not in preview["current_symptoms"]:
                    preview["current_symptoms"]["extracted_symptoms"] = []
                preview["current_symptoms"]["extracted_symptoms"].extend(data["symptoms"])
            
            # Add patient info from documents
            if "patient" in data:
                # Add patient info to insurance data
                patient_data = data["patient"]
                for key, value in patient_data.items():
                    if key not in preview["insurance"] or preview["insurance"][key] == "unknown":
                        preview["insurance"][key] = value
                # Remove note if we have real data
                if "_note" in preview["insurance"]:
                    del preview["insurance"]["_note"]
        
        # If medications is empty and we haven't found any, add a placeholder message
        if not preview["medications"] and not has_medications:
            preview["medications"] = [{"_note": "No medication documents uploaded yet. Upload prescriptions or medication documents to see information here."}]
        
        return preview

    def _extract_symptoms(self, answer: str) -> List[str]:
        """Extract symptoms from patient's description using medical terminology"""
        prompt = f"""
        Extract the patient's symptoms and health concerns from their response, using proper medical terminology:
        "{answer}"
        
        Return a JSON with the following structure:
        {{
            "symptoms": ["medical term for symptom1", "medical term for symptom2", ...]
        }}
        
        For example:
        - If the patient says "My head hurts", use "Cephalgia" or "Headache"
        - If they mention "I feel dizzy", use "Vertigo" or "Dizziness"
        - For "I can't sleep", use "Insomnia"
        - For "I feel tired all the time", use "Fatigue" or "Lethargy"
        
        Use the most appropriate clinical terminology while keeping it understandable.
        Only include clear symptoms or health concerns, not general statements.
        If no clear symptoms are mentioned, return an empty list.
        
        IMPORTANT: Return ONLY the JSON object, with no markdown formatting, code blocks, or other text.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.1}
            )
            
            # Clean the response text
            clean_response = response.text.strip()
            
            # Handle markdown code blocks
            if "```" in clean_response:
                # Extract between code blocks
                start_idx = clean_response.find("```") + 3
                # Find the actual JSON start after the language identifier
                json_start = clean_response.find("{", start_idx)
                
                # Find the end of the code block
                end_idx = clean_response.rfind("```")
                
                if json_start > 0 and end_idx > json_start:
                    clean_response = clean_response[json_start:end_idx].strip()
            
            try:
                # Try to parse directly
                extracted_info = json.loads(clean_response)
            except json.JSONDecodeError:
                # If that fails, try to extract just the JSON part
                json_start = clean_response.find("{")
                json_end = clean_response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_text = clean_response[json_start:json_end]
                    extracted_info = json.loads(json_text)
                else:
                    # If we can't find valid JSON, create a minimal structure
                    return []
            
            # Remove any quotation marks from each symptom
            clean_symptoms = []
            for symptom in extracted_info.get("symptoms", []):
                clean_symptom = symptom.replace('"', '').replace("'", "")
                if clean_symptom:
                    clean_symptoms.append(clean_symptom)
            
            return clean_symptoms
            
        except Exception as e:
            print(f"Error extracting symptoms: {str(e)}")
            return []

    def _generate_clinical_summary(self, patient_description: str) -> str:
        """Generate a clinical summary of patient's symptoms"""
        prompt = f"""
        Rewrite this patient description in more clinical medical terminology:
        "{patient_description}"
        
        Your response should:
        1. Be concise (1-2 sentences)
        2. Use appropriate medical terms
        3. Maintain all the key symptoms and concerns
        4. Be written in third-person clinical style
        
        For example:
        Patient: "My stomach hurts and I feel nauseous after eating. This has been happening for a week."
        Clinical: "Patient presents with epigastric pain and post-prandial nausea persisting for 7 days."
        
        IMPORTANT: Return ONLY the clinical description with no additional text or formatting.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.3}
            )
            
            # Clean the response text
            clinical_summary = response.text.strip()
            
            # Remove any markdown artifacts
            if "```" in clinical_summary:
                # Just extract the clean text
                lines = clinical_summary.splitlines()
                clean_lines = []
                in_code_block = False
                
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if not in_code_block and not line.strip().startswith("`"):
                        clean_lines.append(line)
                
                clinical_summary = " ".join(clean_lines).strip()
            
            # Remove any quotation marks
            clinical_summary = clinical_summary.replace('"', '').replace("'", "")
            
            return clinical_summary
        except Exception as e:
            print(f"Error generating clinical summary: {str(e)}")
            return patient_description  # Return original if processing fails

    def _analyze_for_missing_data(self, state: OnboardingState) -> List[str]:
        """
        Analyze the collected data to identify missing information that would be 
        important for a general practitioner.
        
        Returns a list of missing data items to query the patient about.
        """
        # Get the data preview to analyze
        data_preview = self._get_data_preview(state)
        
        # Convert to JSON for the prompt
        data_json = json.dumps(data_preview, indent=2)
        
        # Get symptoms info
        symptoms_description = state.symptoms_info.get("description", "No symptoms described")
        symptoms_list = state.symptoms_info.get("extracted_symptoms", [])
        
        prompt = f"""
        You are a medical assistant reviewing a patient's information before their general practice appointment.
        Your task is to identify important missing medical information that would be helpful for the doctor.
        
        Patient's main concern: {symptoms_description}
        Extracted symptoms: {', '.join(symptoms_list) if symptoms_list else 'None extracted'}
        
        Patient's current data:
        {data_json}
        
        Based on the information provided, identify what CRITICAL medical information is missing that would be important for the general practitioner. Focus on:

        1. Missing medication details:
           - Missing doses for any mentioned medications
           - Missing frequency/timing of medication intake
           - Duration of current medication usage
        
        2. Vaccination status:
           - Missing information about relevant vaccinations based on symptoms or age
           - Missing information about recent vaccinations
        
        3. Allergies:
           - Any missing information about medication allergies
           - Any missing information about food allergies that could be relevant
           - Any missing information about environmental allergies
        
        4. Medical history:
           - Missing information about chronic conditions
           - Missing information about previous surgeries or hospitalizations
           - Family history of relevant conditions
        
        5. Current symptoms details:
           - Duration of symptoms
           - Severity of symptoms
           - Factors that worsen or improve symptoms
        
        Return ONLY a JSON array of specific missing information items to ask the patient about.
        Format:
        {{
          "missing_data": [
            "specific item 1",
            "specific item 2",
            ...
          ]
        }}
        
        Be specific with each item (e.g., "Dosage for medication X" rather than just "medication details").
        Limit to 3-5 most important items based on medical priority.
        If no crucial information is missing, return an empty array.
        
        IMPORTANT: Return ONLY the JSON object, with no additional text.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.1}
            )
            
            # Clean the response text
            clean_response = response.text.strip()
            
            # Handle markdown code blocks
            if "```" in clean_response:
                # Extract between code blocks
                start_idx = clean_response.find("```") + 3
                # Skip any language identifier like "json"
                if clean_response[start_idx:start_idx+4].strip().lower() == "json":
                    start_idx = clean_response.find("\n", start_idx) + 1
                else:
                    # Find the actual JSON start
                    json_start = clean_response.find("{", start_idx)
                    if json_start > 0:
                        start_idx = json_start
                
                # Find the end of the code block
                end_idx = clean_response.rfind("```")
                
                if start_idx > 0 and end_idx > start_idx:
                    clean_response = clean_response[start_idx:end_idx].strip()
            
            try:
                # Try to parse directly
                extracted_info = json.loads(clean_response)
                missing_data = extracted_info.get("missing_data", [])
            except json.JSONDecodeError:
                # If that fails, try to extract just the JSON part
                json_start = clean_response.find("{")
                json_end = clean_response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_text = clean_response[json_start:json_end]
                    extracted_info = json.loads(json_text)
                    missing_data = extracted_info.get("missing_data", [])
                else:
                    # If we can't find valid JSON, return empty list
                    return []
            
            return missing_data
            
        except Exception as e:
            print(f"Error analyzing for missing data: {str(e)}")
            return []
    
    def _generate_missing_data_question(self, item: str, state: OnboardingState) -> str:
        """
        Generate a question to ask the patient about a specific missing data item.
        """
        # Get symptoms info for context
        symptoms_description = state.symptoms_info.get("description", "No symptoms described")
        symptoms_list = state.symptoms_info.get("extracted_symptoms", [])
        symptoms_context = f"Based on your symptoms ({', '.join(symptoms_list) if symptoms_list else symptoms_description})"
        
        prompt = f"""
        You are Shelly, a medical assistant helping a patient prepare for their general practice appointment.
        
        Patient's main concern: {symptoms_description}
        
        The patient needs to provide information about: "{item}"
        
        Generate a direct, professional question without any greetings like "hi" or "hello" that:
        1. Gets straight to the point about the specific missing information
        2. Explains briefly why this information is important for their doctor appointment
        3. Provides any helpful medical context if relevant
        4. Keeps the tone professional but warm
        
        Examples of good questions:
        - For medication dosage: "What is the dosage amount for your [medication]? This helps your doctor understand your current treatment."
        - For vaccination: "Have you received any [specific] vaccines in the past year? This information completes your preventive care record."
        - For allergies: "Do you have any known allergies to medications, foods, or environmental factors? This ensures your safety during treatment."
        
        IMPORTANT:
        - DO NOT start with greetings like "Hi", "Hello", or "Good day"
        - Make the question direct and concise (1-3 sentences maximum)
        - No small talk or unnecessary preamble
        - Focus solely on gathering the specific medical information
        
        IMPORTANT: Do not include any quotation marks in your response.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.7}
            )
            
            # Remove any quotation marks from the response
            cleaned_response = response.text.strip().replace('"', '').replace("'", "")
            
            # Ensure it ends with a clear request to continue or skip
            if "skip" not in cleaned_response.lower():
                cleaned_response += " You can type 'skip' if you don't have this information right now."
            
            return cleaned_response
        except Exception as e:
            print(f"Error generating missing data question: {str(e)}")
            return f"What information can you provide about {item}? This will help your doctor provide better care. You can type 'skip' if you don't have this information."
    
    def _generate_missing_data_summary(self, responses: Dict[str, str]) -> str:
        """
        Generate a summary of the missing data responses to include in the final report.
        """
        # Convert responses to JSON-friendly format
        responses_text = "\n".join([f"- {item}: {response}" for item, response in responses.items()])
        
        prompt = f"""
        You are a medical assistant summarizing patient information for a general practitioner.
        
        The patient has provided the following responses to questions about missing information:
        
        {responses_text}
        
        Create a concise, structured clinical summary of this information in a way that would be helpful for a doctor reviewing the patient's file.
        
        Your summary should:
        1. Organize the information by category (medications, allergies, vaccinations, medical history, etc.)
        2. Highlight the most medically significant information first
        3. Note any items where the patient could not provide information
        4. Include any follow-up recommendations where appropriate
        
        For example:
        
        MEDICATION DETAILS:
        - Patient takes Lisinopril 10mg once daily for hypertension
        - Unable to provide dosage for Metformin; patient advised to bring medication to appointment
        
        ALLERGIES:
        - Reports penicillin allergy with skin rash reaction
        - No known food allergies
        
        FOLLOW-UP NEEDED:
        - Patient needs vaccination records from previous provider
        
        Keep the summary professional, medically relevant, and formatted for quick review by a busy clinician.
        Exclude any information that doesn't add clinical value.
        
        IMPORTANT: Do not include any quotation marks in your response.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.5}
            )
            
            # Remove any quotation marks from the response
            cleaned_response = response.text.strip().replace('"', '').replace("'", "")
            return cleaned_response
        except Exception as e:
            print(f"Error generating missing data summary: {str(e)}")
            
            # Fallback summary - more structured than before
            summary = "ADDITIONAL PATIENT INFORMATION:\n"
            categories = {
                "medication": [],
                "allergy": [],
                "vaccination": [],
                "medical history": [],
                "symptoms": [],
                "other": []
            }
            
            # Sort responses into categories
            for item, response in responses.items():
                item_lower = item.lower()
                if any(med_term in item_lower for med_term in ["medication", "dose", "drug", "prescription"]):
                    categories["medication"].append(f"- {item}: {response}")
                elif any(allergy_term in item_lower for allergy_term in ["allergy", "allergic", "reaction"]):
                    categories["allergy"].append(f"- {item}: {response}")
                elif any(vax_term in item_lower for vax_term in ["vaccine", "vaccination", "immunization"]):
                    categories["vaccination"].append(f"- {item}: {response}")
                elif any(history_term in item_lower for history_term in ["history", "condition", "surgery", "chronic"]):
                    categories["medical history"].append(f"- {item}: {response}")
                elif any(symptom_term in item_lower for symptom_term in ["symptom", "pain", "duration", "severity"]):
                    categories["symptoms"].append(f"- {item}: {response}")
                else:
                    categories["other"].append(f"- {item}: {response}")
            
            # Build the summary
            for category, items in categories.items():
                if items:
                    summary += f"\n{category.upper()}:\n"
                    summary += "\n".join(items) + "\n"
            
            return summary