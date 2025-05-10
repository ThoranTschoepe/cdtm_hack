from google import genai
from google.genai import types
import base64
from dataclasses import dataclass
from typing import Optional, List, Literal, Dict, Any, Union
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
    extracted_data: Optional[Dict[str, Any]] = None  # Extracted structured data if available

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
        
        # Initialize schema dictionary for different document types
        self._init_schemas()
        
    def _init_schemas(self):
        """Initialize schema definitions for different document types"""
        # Lab Report Schema
        self.lab_report_schema = {
            "type": "OBJECT",
            "properties": {
                "report_metadata": {
                    "type": "OBJECT",
                    "properties": {
                        "lab_name": {"type": "STRING"},
                        "report_date": {"type": "STRING"},
                        "report_id": {"type": "STRING"}
                    }
                },
                "patient_information": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "id": {"type": "STRING"},
                        "date_of_birth": {"type": "STRING"},
                        "gender": {"type": "STRING"}
                    },
                    "required": ["name", "id"]
                },
                "test_results": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "test_name": {"type": "STRING"},
                            "test_category": {"type": "STRING"},
                            "test_code": {"type": "STRING", "nullable": True},
                            "value": {"type": "STRING"},
                            "unit": {"type": "STRING"},
                            "reference_range": {
                                "type": "OBJECT",
                                "properties": {
                                    "lower_limit": {"type": "STRING", "nullable": True},
                                    "upper_limit": {"type": "STRING", "nullable": True},
                                    "text_range": {"type": "STRING", "nullable": True}
                                }
                            },
                            "flag": {
                                "type": "STRING",
                                "enum": ["normal", "low", "high", "critical_low", "critical_high", "abnormal", "not_applicable"],
                                "nullable": True
                            },
                            "comments": {"type": "STRING", "nullable": True}
                        },
                        "required": ["test_name", "value"]
                    }
                },
                "interpretation": {"type": "STRING", "nullable": True}
            },
            "required": ["patient_information", "test_results"]
        }
        
        # Doctor Letter Schema (simplified example)
        self.doctor_letter_schema = {
            "type": "OBJECT",
            "properties": {
                "letter_metadata": {
                    "type": "OBJECT",
                    "properties": {
                        "doctor_name": {"type": "STRING"},
                        "doctor_specialization": {"type": "STRING"},
                        "clinic_name": {"type": "STRING"},
                        "letter_date": {"type": "STRING"}
                    },
                    "required": ["doctor_name"]
                },
                "patient_information": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "id": {"type": "STRING", "nullable": True},
                        "date_of_birth": {"type": "STRING", "nullable": True},
                        "gender": {"type": "STRING", "nullable": True}
                    },
                    "required": ["name"]
                },
                "clinical_details": {
                    "type": "OBJECT",
                    "properties": {
                        "diagnosis": {"type": "STRING"},
                        "symptoms": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "treatment_plan": {"type": "STRING"},
                        "medications": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "name": {"type": "STRING"},
                                    "dosage": {"type": "STRING"},
                                    "frequency": {"type": "STRING"},
                                    "duration": {"type": "STRING", "nullable": True}
                                },
                                "required": ["name"]
                            }
                        },
                        "follow_up": {"type": "STRING", "nullable": True}
                    }
                },
                "recommendations": {"type": "STRING", "nullable": True}
            },
            "required": ["letter_metadata", "patient_information", "clinical_details"]
        }
        
        # Map document types to their schemas
        self.schema_map = {
            "LabReport": self.lab_report_schema,
            "DoctorLetter": self.doctor_letter_schema,
            # Add other document type schemas as needed
        }
        
    def generate_config(self, temperature: float, schema: Optional[dict] = None) -> types.GenerateContentConfig:
        """
        Generate configuration for the content generation API
        
        Args:
            temperature (float): Temperature for generation (0.0-1.0)
            schema (Optional[dict]): Response schema definition
            
        Returns:
            GenerateContentConfig: Configuration object for API call
        """
        generate_content_config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.95,
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
            
    def extract_data(self, image_bytes: bytes, doc_type: DocumentType) -> Dict[str, Any]:
        """
        Extract structured data from an image based on document type
        
        Args:
            image_bytes (bytes): The image content as bytes
            doc_type (DocumentType): The type of document to extract data from
            
        Returns:
            Dict[str, Any]: Extracted data in structured format
        """
        # Get schema for document type
        schema = self.schema_map.get(doc_type)
        if not schema:
            raise ValueError(f"No extraction schema defined for document type: {doc_type}")
        
        # Convert image to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Create prompt based on document type
        prompt = f"Extract all data from this {doc_type} image according to the provided schema."
        
        # Create content for the API call
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
        
        # Generate configuration with the schema
        extraction_config = self.generate_config(temperature=0.7, schema=schema)
        
        try:
            # Call the API
            response = self.client.models.generate_content(
                model=self.model,
                contents=content_parts,
                config=extraction_config
            )
            
            # Parse JSON response
            extracted_data = json.loads(response.text)
            return extracted_data
            
        except Exception as e:
            raise ValueError(f"Error extracting data from {doc_type}: {str(e)}")
    
    def __call__(self, image_bytes, suspected_type: DocumentType) -> OCRResult:
        """
        Process an image, verify its type against the suspected type,
        check for quality issues, and extract data if possible
        
        Args:
            image_bytes (bytes): The image content as bytes
            suspected_type (DocumentType): The type we suspect the document to be
            
        Returns:
            OCRResult: Result object containing classification, quality checks, and extracted data
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
            
            # If document is processable and type is detected correctly, extract data
            extracted_data = None
            if is_processable and is_correct_type:
                try:
                    # Use the detected type for extraction, not the suspected type
                    extracted_data = self.extract_data(image_bytes, detected_type)
                except Exception as e:
                    # Continue even if data extraction fails
                    quality_issues.append("Data extraction failed")
                    
            return OCRResult(
                is_correct_type=is_correct_type,
                detected_type=detected_type,
                suspected_type=suspected_type,
                is_processable=is_processable,
                quality_issues=quality_issues,
                confidence_score=combined_confidence,
                extracted_data=extracted_data
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
    
    # Option 1: Process with classification and quality check, plus extraction
    result = agent_ocr(image_bytes, "LabReport")
    print(f"Document type: {result.detected_type}")
    print(f"Is correct type: {result.is_correct_type}")
    print(f"Is processable: {result.is_processable}")
    print(f"Quality issues: {result.quality_issues}")
    print(f"Confidence score: {result.confidence_score}")
    if result.extracted_data:
        print("Extracted data:")
        print(json.dumps(result.extracted_data, indent=2))