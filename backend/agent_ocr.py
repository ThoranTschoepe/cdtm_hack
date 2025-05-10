from google import genai
from google.genai import types
import base64
from dataclasses import dataclass
from typing import Optional, List, Literal
import json

# Define document types at module level for use in both classes
DocumentType = Literal[
    "DoctorLetter", 
    "LabReport", 
    "MedicationBox", 
    "MedicationDescription", 
    "InsuranceCard", 
    "VaccinationPass",
    "MedicationPlan", 
    "Prescription",
    "unknown"  # Added for error cases
]

# List of valid document types (excluding "unknown")
DOCUMENT_TYPES = [
    "DoctorLetter", 
    "LabReport", 
    "MedicationBox", 
    "MedicationDescription", 
    "InsuranceCard", 
    "VaccinationPass",
    "MedicationPlan", 
    "Prescription"
]

@dataclass
class OCRResult:
    """Return type for AgentOCR processing results"""
    is_correct_type: bool                      # Whether the image matches the suspected type
    detected_type: DocumentType                # The actually detected document type
    suspected_type: DocumentType               # The type that was suspected
    is_processable: bool                       # Whether the image quality is sufficient for processing
    quality_issues: List[str]                  # List of detected quality issues
    confidence_score: float                    # Confidence score for the classification (0-1)
    error_message: Optional[str] = None        # Error message if processing failed

class AgentOCR:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project="avi-cdtm-hack-team-9800",
            location="us-central1",
        )
        # Use the module-level document types
        self.types = DOCUMENT_TYPES
        self.model = "gemini-2.0-flash-001"
        
    def generate_config(self, temperature: int, schema: Optional[str] = None) -> types.GenerateContentConfig:
        generate_content_config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=1,
            seed=0,
            max_output_tokens=8192,
            response_modalities=["TEXT"],
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="OFF"
                )
            ],
            response_mime_type="application/json",
            response_schema=schema,
        )
        
        return generate_content_config
        
    def categorize(self, image_bytes) -> DocumentType:
        """
        Categorize the image document into one of the predefined categories.
        
        Args:
            image_bytes (bytes): The image content as bytes
            
        Returns:
            DocumentType: The detected document type
        """
        # Convert image to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Prepare prompt for categorization
        prompt = f"""
        Analyze this medical document image and determine its type.
        Possible types are:
        {", ".join(f"- {t}" for t in self.types)}
        
        Return the document type and your confidence level in the classification.
        """
        
        # Define the response schema for categorization
        categorization_schema = {
            "type": "OBJECT",
            "properties": {
                "document_type": {
                    "type": "STRING",
                    "enum": self.types
                },
                "confidence": {
                    "type": "NUMBER",
                    "description": "Confidence score between 0 and 1"
                },
                "reasoning": {
                    "type": "STRING",
                    "description": "Brief explanation for the classification"
                }
            },
            "required": ["document_type", "confidence"]
        }
        
        # Create the content parts with the image and prompt
        content_parts = [
            {
                "text": prompt
            },
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64_image
                }
            }
        ]
        
        # Generate response using configuration with schema
        categorization_config = self.generate_config(temperature=0.2, schema=categorization_schema)
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=content_parts,
            config=categorization_config
        )
        
        # Parse JSON response
        try:
            result = json.loads(response.text)
            doc_type = result.get("document_type")
            confidence = result.get("confidence", 0.0)
            
            # Store confidence for later use in quality assessment
            self._last_classification_confidence = confidence
            
            # Validate the returned type
            if doc_type not in self.types:
                raise ValueError(f"Categorization returned unsupported type: {doc_type}")
                
            return doc_type
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse categorization response: {e}")
        
    def check_image_quality(self, image_bytes):
        """
        Check the quality of the image for potential issues
        
        Args:
            image_bytes (bytes): The image content as bytes
            
        Returns:
            tuple: (is_processable, list of quality issues, confidence score)
        """
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = """
        Analyze this medical document image and check for quality issues that might affect optical character recognition.
        Check for the following issues:
        1. Blurriness
        2. Poor lighting or low contrast
        3. Partial coverage (document cut off)
        4. Obstructions or shadows
        5. Skewed or rotated perspective
        6. Folded or crumpled document
        """
        
        # Define the response schema for quality check
        quality_schema = {
            "type": "OBJECT",
            "properties": {
                "is_processable": {
                    "type": "BOOLEAN",
                    "description": "Whether the image quality is sufficient for OCR"
                },
                "quality_issues": {
                    "type": "ARRAY",
                    "items": {
                        "type": "STRING"
                    },
                    "description": "List of detected quality issues"
                },
                "confidence_score": {
                    "type": "NUMBER",
                    "description": "Confidence score between 0 and 1 for successful OCR"
                }
            },
            "required": ["is_processable", "quality_issues", "confidence_score"]
        }
        
        content_parts = [
            {
                "text": prompt
            },
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64_image
                }
            }
        ]
        
        quality_config = self.generate_config(temperature=0.2, schema=quality_schema)
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=content_parts,
                config=quality_config
            )
            
            # Parse JSON response
            quality_result = json.loads(response.text)
            
            return (
                quality_result.get("is_processable", False),
                quality_result.get("quality_issues", []),
                quality_result.get("confidence_score", 0.0)
            )
        except Exception as e:
            return False, [f"Error checking image quality: {str(e)}"], 0.0
    
    def __call__(self, image_bytes, suspected_type: DocumentType) -> OCRResult:
        """
        Process an image, verify its type against the suspected type,
        and check for quality issues
        
        Args:
            image_bytes (bytes): The image content as bytes
            suspected_type (DocumentType): The type we suspect the document to be
            
        Returns:
            OCRResult: Result object containing classification and quality checks
        """
        # Initialize classification confidence for later use
        self._last_classification_confidence = 0.0
        
        if suspected_type not in self.types:
            return OCRResult(
                is_correct_type=False,
                detected_type="unknown",
                suspected_type=suspected_type,
                is_processable=False,
                quality_issues=["Invalid suspected type"],
                confidence_score=0.0,
                error_message=f"Suspected type '{suspected_type}' is not valid. Valid types: {', '.join(self.types)}"
            )
        
        try:
            # First, check image quality
            is_processable, quality_issues, quality_confidence = self.check_image_quality(image_bytes)
            
            # Then, categorize the image
            try:
                detected_type = self.categorize(image_bytes)
                is_correct_type = detected_type == suspected_type
                
                # Use the classification confidence captured during categorization
                classification_confidence = self._last_classification_confidence
            except Exception as e:
                # If categorization fails but image quality check passed
                return OCRResult(
                    is_correct_type=False,
                    detected_type="unknown",
                    suspected_type=suspected_type,
                    is_processable=is_processable,
                    quality_issues=quality_issues + ["Document type detection failed"],
                    confidence_score=0.0,
                    error_message=f"Error during document type detection: {str(e)}"
                )
            
            # Combine quality and classification confidence
            combined_confidence = (quality_confidence + classification_confidence) / 2
            
            # Adjust confidence score if wrong type detected
            if not is_correct_type:
                combined_confidence *= 0.5  # Reduce confidence if type mismatch
            
            return OCRResult(
                is_correct_type=is_correct_type,
                detected_type=detected_type,
                suspected_type=suspected_type,
                is_processable=is_processable,
                quality_issues=quality_issues,
                confidence_score=combined_confidence
            )
            
        except Exception as e:
            return OCRResult(
                is_correct_type=False,
                detected_type="unknown",
                suspected_type=suspected_type,
                is_processable=False,
                quality_issues=["Processing error"],
                confidence_score=0.0,
                error_message=f"Error processing image: {str(e)}"
            )
        

if __name__ == "__main__":
    # Example usage
    agent_ocr = AgentOCR()
    with open("data/IMG_2221.jpg", "rb") as image_file:
        image_bytes = image_file.read()
    
    result = agent_ocr(image_bytes, "LabReport")
    print(result)