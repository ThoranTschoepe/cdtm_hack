from google import genai
from google.genai import types
import base64
from dataclasses import dataclass
from typing import Optional, List, Literal, Dict, Any, Union
import json
from collections import defaultdict

# Original document types remain the same
DocumentType = Literal[
    "DoctorLetter", 
    "LabReport", 
    "MedicationBox", 
    "MedicationDescription", 
    "InsuranceCard", 
    "VaccinationPass",
    "MedicationPlan", 
    "Prescription",
    "unknown"
]

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
class PageResult:
    """Result for a single page"""
    page_number: int
    detected_type: DocumentType
    confidence_score: float
    is_processable: bool
    quality_issues: List[str]
    extracted_data: Optional[Dict[str, Any]] = None

@dataclass
class DocumentGroup:
    """Group of pages of the same document type"""
    document_type: DocumentType
    page_results: List[PageResult]
    combined_data: Optional[Dict[str, Any]] = None
    
@dataclass
class MultiDocumentResult:
    """Result containing multiple document groups from a set of pages"""
    document_groups: Dict[DocumentType, DocumentGroup]
    total_pages: int
    processable_pages: int

class AgentOCR:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project="avi-cdtm-hack-team-9800",
            location="us-central1",
        )
        self.types = DOCUMENT_TYPES
        self.model = "gemini-2.0-flash-001"
        self.check_quality = False
        
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

        # Doctor Letter Schema
        self.doctor_letter_schema = {
            "type": "OBJECT",
            "properties": {
                "letter_metadata": {
                    "type": "OBJECT",
                    "properties": {
                        "date": {"type": "STRING"},
                        "doctor_name": {"type": "STRING"},
                        "doctor_credentials": {"type": "STRING", "nullable": True},
                        "clinic_name": {"type": "STRING", "nullable": True},
                        "clinic_address": {"type": "STRING", "nullable": True}
                    }
                },
                "patient_information": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "id": {"type": "STRING", "nullable": True},
                        "date_of_birth": {"type": "STRING", "nullable": True},
                        "address": {"type": "STRING", "nullable": True}
                    },
                    "required": ["name"]
                },
                "content": {"type": "STRING"},
                "diagnosis": {"type": "STRING", "nullable": True},
                "recommendations": {"type": "STRING", "nullable": True},
                "signature": {"type": "STRING", "nullable": True}
            },
            "required": ["patient_information", "content"]
        }

        # Medication Box Schema
        self.medication_box_schema = {
            "type": "OBJECT",
            "properties": {
                "medication_details": {
                    "type": "OBJECT",
                    "properties": {
                        "brand_name": {"type": "STRING"},
                        "generic_name": {"type": "STRING", "nullable": True},
                        "manufacturer": {"type": "STRING", "nullable": True},
                        "strength": {"type": "STRING"},
                        "dosage_form": {"type": "STRING"},
                        "package_size": {"type": "STRING", "nullable": True},
                        "batch_number": {"type": "STRING", "nullable": True},
                        "expiration_date": {"type": "STRING", "nullable": True}
                    },
                    "required": ["brand_name", "strength", "dosage_form"]
                },
                "administration": {
                    "type": "OBJECT",
                    "properties": {
                        "route": {"type": "STRING", "nullable": True},
                        "standard_dosage": {"type": "STRING", "nullable": True},
                        "frequency": {"type": "STRING", "nullable": True}
                    }
                },
                "active_ingredients": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "amount": {"type": "STRING"},
                            "unit": {"type": "STRING", "nullable": True}
                        },
                        "required": ["name"]
                    }
                },
                "warnings": {"type": "STRING", "nullable": True},
                "storage_instructions": {"type": "STRING", "nullable": True},
                "additional_info": {"type": "STRING", "nullable": True}
            },
            "required": ["medication_details"]
        }

        # Medication Description Schema
        self.medication_description_schema = {
            "type": "OBJECT",
            "properties": {
                "medication_name": {"type": "STRING"},
                "therapeutic_class": {"type": "STRING", "nullable": True},
                "description": {"type": "STRING"},
                "indications": {"type": "STRING"},
                "contraindications": {"type": "STRING", "nullable": True},
                "dosage_and_administration": {"type": "STRING"},
                "side_effects": {"type": "STRING", "nullable": True},
                "drug_interactions": {"type": "STRING", "nullable": True},
                "precautions": {"type": "STRING", "nullable": True},
                "storage_conditions": {"type": "STRING", "nullable": True},
                "pharmacology": {"type": "STRING", "nullable": True},
                "pregnancy_category": {"type": "STRING", "nullable": True}
            },
            "required": ["medication_name", "description", "indications", "dosage_and_administration"]
        }

        # Medication Plan Schema
        self.medication_plan_schema = {
            "type": "OBJECT",
            "properties": {
                "patient_information": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "id": {"type": "STRING", "nullable": True},
                        "date_of_birth": {"type": "STRING", "nullable": True}
                    },
                    "required": ["name"]
                },
                "plan_details": {
                    "type": "OBJECT",
                    "properties": {
                        "date_created": {"type": "STRING", "nullable": True},
                        "created_by": {"type": "STRING", "nullable": True},
                        "valid_until": {"type": "STRING", "nullable": True}
                    }
                },
                "medications": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "dosage": {"type": "STRING"},
                            "form": {"type": "STRING"},
                            "frequency": {"type": "STRING"},
                            "timing": {"type": "STRING", "nullable": True},
                            "instructions": {"type": "STRING", "nullable": True},
                            "reason": {"type": "STRING", "nullable": True},
                            "duration": {"type": "STRING", "nullable": True}
                        },
                        "required": ["name", "dosage", "frequency"]
                    }
                },
                "special_instructions": {"type": "STRING", "nullable": True}
            },
            "required": ["patient_information", "medications"]
        }

        # Prescription Schema
        self.prescription_schema = {
            "type": "OBJECT",
            "properties": {
                "prescription_header": {
                    "type": "OBJECT",
                    "properties": {
                        "prescriber_name": {"type": "STRING"},
                        "prescriber_credentials": {"type": "STRING", "nullable": True},
                        "prescriber_address": {"type": "STRING", "nullable": True},
                        "prescriber_phone": {"type": "STRING", "nullable": True},
                        "prescriber_license": {"type": "STRING", "nullable": True},
                        "date": {"type": "STRING"}
                    },
                    "required": ["prescriber_name", "date"]
                },
                "patient_information": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "date_of_birth": {"type": "STRING", "nullable": True},
                        "address": {"type": "STRING", "nullable": True},
                        "insurance_info": {"type": "STRING", "nullable": True}
                    },
                    "required": ["name"]
                },
                "prescribed_medications": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "strength": {"type": "STRING"},
                            "form": {"type": "STRING"},
                            "quantity": {"type": "STRING"},
                            "directions": {"type": "STRING"},
                            "refills": {"type": "STRING", "nullable": True},
                            "substitution_allowed": {"type": "BOOLEAN", "nullable": True},
                            "daw": {"type": "BOOLEAN", "nullable": True}
                        },
                        "required": ["name", "directions"]
                    }
                },
                "signature": {"type": "STRING", "nullable": True},
                "notes": {"type": "STRING", "nullable": True}
            },
            "required": ["prescription_header", "patient_information", "prescribed_medications"]
        }

        self.vaccination_pass_schema = {
            "type": "OBJECT",
            "properties": {
                "document_info": {
                    "type": "OBJECT",
                    "properties": {
                        "document_type": {"type": "STRING", "enum": ["International Certificate of Vaccination"]},
                        "issuing_authority": {"type": "STRING", "nullable": True},
                        "document_number": {"type": "STRING", "nullable": True}
                    }
                },
                "personal_information": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "date_of_birth": {"type": "STRING"},
                        "sex": {"type": "STRING", "nullable": True},
                        "nationality": {"type": "STRING", "nullable": True},
                        "passport_number": {"type": "STRING", "nullable": True},
                        "address": {"type": "STRING", "nullable": True}
                    },
                    "required": ["name"]
                },
                "vaccinations": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "category": {
                                "type": "STRING", 
                                "description": "Category of vaccination (e.g. standard, influenza, COVID-19, etc.)"
                            },
                            "disease": {"type": "STRING", "nullable": True},
                            "vaccine_name": {"type": "STRING"},
                            "vaccine_type": {"type": "STRING", "nullable": True},
                            "manufacturer": {"type": "STRING", "nullable": True},
                            "batch_number": {"type": "STRING", "nullable": True},
                            "date_administered": {"type": "STRING"},
                            "administering_center": {"type": "STRING", "nullable": True},
                            "healthcare_professional": {"type": "STRING", "nullable": True},
                            "next_dose_due": {"type": "STRING", "nullable": True},
                            "certificate_valid_from": {"type": "STRING", "nullable": True},
                            "certificate_valid_until": {"type": "STRING", "nullable": True}
                        },
                        "required": ["vaccine_name", "date_administered"]
                    }
                },
                "verification": {
                    "type": "OBJECT",
                    "properties": {
                        "official_stamps": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "remarks": {"type": "STRING", "nullable": True}
                    }
                }
            },
            "required": ["personal_information", "vaccinations"]
        }

        # Map document types to their schemas
        self.schema_map = {
            "LabReport": self.lab_report_schema,
            "DoctorLetter": self.doctor_letter_schema,
            "MedicationBox": self.medication_box_schema,
            "MedicationDescription": self.medication_description_schema,
            "MedicationPlan": self.medication_plan_schema,
            "Prescription": self.prescription_schema,
            "VaccinationPass": self.vaccination_pass_schema,
            # Add other document type schemas as needed
        }
    
    def generate_config(self, temperature: float, schema: Optional[dict] = None) -> types.GenerateContentConfig:
        """Generate configuration for the content generation API"""
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
        
    def categorize(self, image_bytes):
        """Categorize the document image"""
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = f"""
        Analyze this medical document image and determine its type.
        Possible types are:
        {", ".join(f"- {t}" for t in self.types)}
        
        Return the document type and your confidence level in the classification.
        """
        
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
        
        content_parts = [
            {"text": prompt},
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64_image
                }
            }
        ]
        
        categorization_config = self.generate_config(temperature=0.2, schema=categorization_schema)
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=content_parts,
                config=categorization_config
            )
            
            result = json.loads(response.text)
            doc_type = result.get("document_type")
            confidence = result.get("confidence", 0.0)
            
            if doc_type not in self.types:
                raise ValueError(f"Categorization returned unsupported type: {doc_type}")
                
            return doc_type, confidence
        except Exception as e:
            raise ValueError(f"Failed to parse categorization response: {e}")
        
    def check_image_quality(self, image_bytes):
        """Check the quality of the image for OCR"""
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
            {"text": prompt},
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
            
            quality_result = json.loads(response.text)
            
            return (
                quality_result.get("is_processable", False),
                quality_result.get("quality_issues", []),
                quality_result.get("confidence_score", 0.0)
            )
        except Exception as e:
            return False, [f"Error checking image quality: {str(e)}"], 0.0
            
    def extract_data(self, image_bytes: bytes, doc_type: DocumentType) -> Dict[str, Any]:
        """Extract structured data from an image based on document type"""
        schema = self.schema_map.get(doc_type)
        if not schema:
            raise ValueError(f"No extraction schema defined for document type: {doc_type}")
        
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = f"Extract all data from this {doc_type} image according to the provided schema."
        
        content_parts = [
            {"text": prompt},
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64_image
                }
            }
        ]
        
        extraction_config = self.generate_config(temperature=0.2, schema=schema)
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=content_parts,
                config=extraction_config
            )
            
            extracted_data = json.loads(response.text)
            return extracted_data
            
        except Exception as e:
            raise ValueError(f"Error extracting data from {doc_type}: {str(e)}")
    
    def process_page(self, image_bytes: bytes, page_number: int) -> PageResult:
        """Process a single page: categorize, check quality, and extract data"""
        try:
            # First check image quality
            is_processable = True
            quality_issues = []
            quality_confidence = 1.0
            if self.check_quality:
                is_processable, quality_issues, quality_confidence = self.check_image_quality(image_bytes)
            
            # Then categorize the image
            doc_type, classification_confidence = self.categorize(image_bytes)
            
            # Combine quality and classification confidence
            combined_confidence = (quality_confidence + classification_confidence) / 2
            
            # Extract data if the image is processable
            extracted_data = None
            if is_processable:
                try:
                    extracted_data = self.extract_data(image_bytes, doc_type)
                except Exception as e:
                    quality_issues.append(f"Data extraction failed: {str(e)}")
            
            return PageResult(
                page_number=page_number,
                detected_type=doc_type,
                confidence_score=combined_confidence,
                is_processable=is_processable,
                quality_issues=quality_issues,
                extracted_data=extracted_data
            )
            
        except Exception as e:
            return PageResult(
                page_number=page_number,
                detected_type="unknown",
                confidence_score=0.0,
                is_processable=False,
                quality_issues=[f"Processing error: {str(e)}"],
                extracted_data=None
            )


class MultiDocumentProcessor:
    """Processes multiple pages, classifies them, and groups them by document type"""
    
    def __init__(self):
        self.ocr_agent = AgentOCR()
        

    def process_document_batch(self, doc_type: DocumentType, image_bytes_list: List[bytes], page_numbers: List[int]) -> Dict[str, Any]:
        """Process all pages of the same document type together"""
        schema = self.ocr_agent.schema_map.get(doc_type)
        if not schema:
            raise ValueError(f"No extraction schema defined for document type: {doc_type}")
        
        # Convert all images to base64
        base64_images = [base64.b64encode(img).decode("utf-8") for img in image_bytes_list]
        
        # Build multi-page prompt
        prompt = f"""
        Extract data from these {len(image_bytes_list)} pages of a {doc_type} document.
        These pages belong to the same document. Please create a single coherent structured extraction.
        If pages contain conflicting information, use the clearest or most complete information.
        For patient information like name, use the most consistently appearing version across pages.
        """
        
        # Create content parts with all images
        content_parts = [{"text": prompt}]
        for i, b64_img in enumerate(base64_images):
            content_parts.append({
                "text": f"\nPage {page_numbers[i]}:"
            })
            content_parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": b64_img
                }
            })
        
        extraction_config = self.ocr_agent.generate_config(temperature=0.2, schema=schema)
        
        try:
            response = self.ocr_agent.client.models.generate_content(
                model=self.ocr_agent.model,
                contents=content_parts,
                config=extraction_config
            )
            
            extracted_data = json.loads(response.text)
            return extracted_data
            
        except Exception as e:
            raise ValueError(f"Error batch processing {doc_type} pages: {str(e)}")

    def process_pages(self, image_bytes_list: List[bytes]) -> MultiDocumentResult:
        """Process a list of page images with batch processing for each document type"""
        if not image_bytes_list:
            return MultiDocumentResult(
                document_groups={},
                total_pages=0,
                processable_pages=0
            )
        
        # First, categorize each page individually
        page_categories = []
        for page_num, image_bytes in enumerate(image_bytes_list, start=1):
            try:
                doc_type, confidence = self.ocr_agent.categorize(image_bytes)
                
                # Check if the image is processable
                is_processable = True
                quality_issues = []
                if self.ocr_agent.check_quality:
                    is_processable, quality_issues, _ = self.ocr_agent.check_image_quality(image_bytes)
                
                page_categories.append({
                    'page_number': page_num,
                    'doc_type': doc_type,
                    'confidence': confidence,
                    'is_processable': is_processable,
                    'quality_issues': quality_issues
                })
            except Exception as e:
                page_categories.append({
                    'page_number': page_num,
                    'doc_type': "unknown",
                    'confidence': 0.0,
                    'is_processable': False,
                    'quality_issues': [f"Categorization error: {str(e)}"]
                })
        
        # Group pages by document type
        doc_type_groups = defaultdict(list)
        for page_info in page_categories:
            if page_info['is_processable'] and page_info['doc_type'] != "unknown":
                doc_type_groups[page_info['doc_type']].append(page_info['page_number'] - 1)  # Convert to 0-indexed
        
        # Process each document type as a batch
        document_groups = {}
        processable_pages = sum(1 for page in page_categories if page['is_processable'])
        
        for doc_type, page_indices in doc_type_groups.items():
            # Get the corresponding images
            doc_images = [image_bytes_list[idx] for idx in page_indices]
            page_numbers = [idx + 1 for idx in page_indices]  # Convert back to 1-indexed
            
            # Process all pages of this document type together
            try:
                combined_data = self.process_document_batch(doc_type, doc_images, page_numbers)
                
                # Create individual page results
                page_results = []
                for i, page_idx in enumerate(page_indices):
                    page_info = next(p for p in page_categories if p['page_number'] == page_idx + 1)
                    
                    # Create a single-page result but with the combined data
                    page_result = PageResult(
                        page_number=page_idx + 1,
                        detected_type=doc_type,
                        confidence_score=page_info['confidence'],
                        is_processable=page_info['is_processable'],
                        quality_issues=page_info['quality_issues'],
                        extracted_data=combined_data if i == 0 else None  # Only include data for first page to avoid duplication
                    )
                    page_results.append(page_result)
                
                document_groups[doc_type] = DocumentGroup(
                    document_type=doc_type,
                    page_results=page_results,
                    combined_data=combined_data
                )
                
            except Exception as e:
                print(f"Error processing {doc_type} batch: {e}")
                # Create empty group with error
                document_groups[doc_type] = DocumentGroup(
                    document_type=doc_type,
                    page_results=[],
                    combined_data=None
                )
        
        return MultiDocumentResult(
            document_groups=document_groups,
            total_pages=len(image_bytes_list),
            processable_pages=processable_pages
        )    

    def _group_pages_by_type(self, page_results: List[PageResult], image_bytes_list: List[bytes]) -> MultiDocumentResult:
        """Group pages by document type and combine data for each group"""
        # Count processable pages
        processable_pages = sum(1 for result in page_results if result.is_processable)
        
        # Group by document type
        groups = defaultdict(list)
        for result in page_results:
            groups[result.detected_type].append(result)
            
        # Create document groups with combined data
        document_groups = {}
        for doc_type, results in groups.items():
            # Sort by page number
            results.sort(key=lambda r: r.page_number)
            
            # Combine data for pages of this document type
            combined_data = self._combine_data(results)
            
            document_groups[doc_type] = DocumentGroup(
                document_type=doc_type,
                page_results=results,
                combined_data=combined_data
            )
            
        return MultiDocumentResult(
            document_groups=document_groups,
            total_pages=len(page_results),
            processable_pages=processable_pages
        )
    
    def _combine_data(self, page_results: List[PageResult]) -> Dict[str, Any]:
        """
        General-purpose method to combine data from multiple pages
        This method intelligently handles different field types
        without needing document type-specific logic
        """
        # Filter pages with extracted data
        pages_with_data = [p for p in page_results if p.extracted_data is not None]
        
        if not pages_with_data:
            return None
            
        # Start with data from first page
        combined = pages_with_data[0].extracted_data.copy()
        
        # Process each subsequent page
        for page in pages_with_data[1:]:
            page_data = page.extracted_data
            if not page_data:
                continue
                
            # Recursively merge data from this page
            self._merge_dict(combined, page_data, page.page_number)
            
        return combined
    
    def _merge_dict(self, target: Dict[str, Any], source: Dict[str, Any], page_num: int) -> None:
        """
        Recursively merge source dictionary into target dictionary
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
            page_num: Page number for reference
        """
        for key, value in source.items():
            # If key not in target, just add it
            if key not in target:
                target[key] = value
                continue
                
            target_value = target[key]
            
            # Handle different value types
            if isinstance(value, dict) and isinstance(target_value, dict):
                # Recursively merge dictionaries
                self._merge_dict(target_value, value, page_num)
                
            elif isinstance(value, list) and isinstance(target_value, list):
                # Merge lists based on content type
                if value and isinstance(value[0], dict) and "name" in value[0]:
                    # List of named objects (like medications, test results, ingredients)
                    self._merge_named_object_lists(target_value, value, page_num)
                else:
                    # For other lists, just extend
                    target_value.extend(value)
                    
            elif isinstance(value, str) and isinstance(target_value, str):
                # Concatenate string values if they're different
                if value not in target_value:
                    target[key] = f"{target_value}\n\n[Page {page_num}]\n{value}"
            
            # For other types, keep the target value (first page's value)
    
    def _merge_named_object_lists(self, target_list: List[Dict], source_list: List[Dict], page_num: int) -> None:
        """
        Merge lists of objects with 'name' field, avoiding duplicates
        
        Args:
            target_list: Target list to merge into
            source_list: Source list to merge from
            page_num: Page number for reference
        """
        # Create a set of existing names for fast lookup
        existing_names = {item.get("name").lower() for item in target_list 
                         if isinstance(item, dict) and "name" in item}
        
        # Add items that don't exist in the target list
        for item in source_list:
            if not isinstance(item, dict) or "name" not in item:
                target_list.append(item)
                continue
                
            name = item.get("name").lower()
            if name not in existing_names:
                # Add page number reference
                item["page"] = page_num
                target_list.append(item)
                existing_names.add(name)
            else:
                # If item exists, update any missing fields
                existing_item = next(i for i in target_list if i.get("name").lower() == name)
                for k, v in item.items():
                    if k not in existing_item or not existing_item[k]:
                        existing_item[k] = v


# Example usage
if __name__ == "__main__":
    processor = MultiDocumentProcessor()
    
    image_bytes_list = []

    # Load all 5 images
    for i in range(1, 4):
        try:
            with open(f"data/doctor_letter/1/{i}.jpg", "rb") as f:
                image_bytes = f.read()
                image_bytes_list.append(image_bytes)
        except Exception as e:
            print(f"Error loading image {i}: {str(e)}")
    
    # Process single page medication
    result = processor.process_pages(image_bytes_list)
    
    # Print results
    print(f"Processed {result.total_pages} pages")
    
    # Check for medication documents
    for doc_type, group in result.document_groups.items():
        print(f"\nDetected document type: {doc_type}")
        
        if group.combined_data:
            print(f"Extracted data available for {doc_type}")
            print(json.dumps(group.combined_data, indent=2))