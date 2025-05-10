lab_report_schema = {
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

hospital_letter_schema = {
    "type": "OBJECT",
    "properties": {
        "letter_metadata": {
            "type": "OBJECT",
            "properties": {
                "hospital_name": {"type": "STRING"},
                "hospital_department": {"type": "STRING", "nullable": True},
                "hospital_address": {"type": "STRING", "nullable": True},
                "document_type": {"type": "STRING", "nullable": True},
                "date": {"type": "STRING"},
                "case_number": {"type": "STRING", "nullable": True},
            },
            "required": ["date"]
        },
        "patient_information": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING"},
                "id": {"type": "STRING", "nullable": True},
                "date_of_birth": {"type": "STRING", "nullable": True},
                "gender": {"type": "STRING", "nullable": True},
                "address": {"type": "STRING", "nullable": True},
                "insurance_info": {"type": "STRING", "nullable": True},
                "anthropometrics": {
                    "type": "OBJECT",
                    "properties": {
                        "height": {"type": "STRING", "nullable": True},
                        "weight": {"type": "STRING", "nullable": True},
                        "bmi": {"type": "STRING", "nullable": True}
                    }
                }
            },
            "required": ["name"]
        },
        "referring_physician": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING", "nullable": True},
                "practice_name": {"type": "STRING", "nullable": True},
                "address": {"type": "STRING", "nullable": True},
                "contact_info": {"type": "STRING", "nullable": True}
            }
        },
        "admission_details": {
            "type": "OBJECT",
            "properties": {
                "admission_date": {"type": "STRING", "nullable": True},
                "discharge_date": {"type": "STRING", "nullable": True},
                "reason_for_admission": {"type": "STRING", "nullable": True},
                "department": {"type": "STRING", "nullable": True}
            }
        },
        "anamnesis": {
            "type": "OBJECT",
            "properties": {
                "chief_complaint": {"type": "STRING", "nullable": True},
                "present_illness": {"type": "STRING", "nullable": True},
                "past_medical_history": {"type": "STRING", "nullable": True},
                "family_history": {"type": "STRING", "nullable": True},
                "social_history": {"type": "STRING", "nullable": True},
                "allergies": {"type": "STRING", "nullable": True},
                "medications": {"type": "STRING", "nullable": True},
                "risk_factors": {"type": "STRING", "nullable": True}
            }
        },
        "physical_examination": {
            "type": "OBJECT",
            "properties": {
                "general_appearance": {"type": "STRING", "nullable": True},
                "vital_signs": {"type": "STRING", "nullable": True},
                "systems_review": {"type": "STRING", "nullable": True}
            }
        },
        "diagnostic_findings": {
            "type": "OBJECT",
            "properties": {
                "laboratory_results": {"type": "STRING", "nullable": True},
                "imaging_results": {"type": "STRING", "nullable": True},
                "ecg_findings": {"type": "STRING", "nullable": True},
                "other_tests": {"type": "STRING", "nullable": True}
            }
        },
        "procedures": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "procedure_name": {"type": "STRING"},
                    "procedure_date": {"type": "STRING", "nullable": True},
                    "findings": {"type": "STRING", "nullable": True},
                    "complications": {"type": "STRING", "nullable": True}
                },
                "required": ["procedure_name"]
            }
        },
        "diagnoses": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "diagnosis": {"type": "STRING"},
                    "code": {"type": "STRING", "nullable": True},
                    "details": {"type": "STRING", "nullable": True}
                },
                "required": ["diagnosis"]
            }
        },
        "treatment": {
            "type": "OBJECT",
            "properties": {
                "medications_prescribed": {"type": "STRING", "nullable": True},
                "procedures_performed": {"type": "STRING", "nullable": True},
                "other_treatments": {"type": "STRING", "nullable": True}
            }
        },
        "discharge_plan": {
            "type": "OBJECT",
            "properties": {
                "follow_up_instructions": {"type": "STRING", "nullable": True},
                "activity_restrictions": {"type": "STRING", "nullable": True},
                "diet_recommendations": {"type": "STRING", "nullable": True},
                "medication_instructions": {"type": "STRING", "nullable": True},
                "follow_up_appointments": {"type": "STRING", "nullable": True}
            }
        },
        "recommendations": {"type": "STRING", "nullable": True},
        "summary": {"type": "STRING", "nullable": True},
        "signature": {
            "type": "OBJECT",
            "properties": {
                "physician_name": {"type": "STRING", "nullable": True},
                "credentials": {"type": "STRING", "nullable": True},
                "date": {"type": "STRING", "nullable": True}
            }
        },
        "contact_information": {"type": "STRING", "nullable": True}
    },
    "required": ["patient_information"]
}

insurance_card_schema = {
    "type": "OBJECT",
    "properties": {
        "card_details": {
            "type": "OBJECT",
            "properties": {
                "insurance_provider": {"type": "STRING"},
                "card_number": {"type": "STRING", "nullable": True}
            },
            "required": ["insurance_provider"]
        },
        "policyholder": {
            "type": "OBJECT",
            "properties": {
                "name": {"type": "STRING"},
                "date_of_birth": {"type": "STRING", "nullable": True},
                "insurance_number": {"type": "STRING", "nullable": True},
                "company_number": {"type": "STRING", "nullable": True},
                "person_number": {"type": "STRING", "nullable": True}
            },
            "required": ["name"]
        },
        "coverage": {
            "type": "OBJECT",
            "properties": {
                "plan_type": {"type": "STRING", "nullable": True},
                "hospital_services": {"type": "STRING", "nullable": True},
                "room_type": {"type": "STRING", "nullable": True},
                "coverage_percentages": {
                    "type": "OBJECT",
                    "properties": {
                        "general_hospital_services": {"type": "STRING", "nullable": True},
                        "double_room_supplement": {"type": "STRING", "nullable": True},
                        "single_room_supplement": {"type": "STRING", "nullable": True},
                        "additional_supplements": {"type": "STRING", "nullable": True}
                    }
                }
            }
        },
        "contact_information": {
            "type": "OBJECT",
            "properties": {
                "address": {"type": "STRING", "nullable": True},
                "phone": {"type": "STRING", "nullable": True},
                "email": {"type": "STRING", "nullable": True},
                "website": {"type": "STRING", "nullable": True},
                "emergency_contact": {"type": "STRING", "nullable": True}
            }
        },
    },
    "required": ["card_details", "policyholder"]
}

# Doctor Letter Schema
doctor_letter_schema = {
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
medication_box_schema = {
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
medication_description_schema = {
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
medication_plan_schema = {
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
prescription_schema = {
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

vaccination_pass_schema = {
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
schema_map = {
    "DoctorLetter": doctor_letter_schema,
    "HospitalLetter": hospital_letter_schema,
    "LabReport": lab_report_schema,
    "MedicationBox": medication_box_schema,
    "InsuranceCard": insurance_card_schema,
    "MedicationDescription": medication_description_schema,
    "VaccinationPass": vaccination_pass_schema,
    "MedicationPlan": medication_plan_schema,
    "Prescription": prescription_schema,
    # Add other document type schemas as needed
}