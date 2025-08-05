# main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List, Dict, Any, Optional
import os
import shutil
import re
from pathlib import Path
from docx import Document
import PyPDF2
from PIL import Image
import pytesseract
import spacy
import uuid
import json

# --- 1. Project Setup ---
# Load spaCy model for NLP tasks
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# --- 2. FastAPI Application ---
app = FastAPI()

# Global variable to store the output schema template.
# This maps the desired output keys to the keys of the extracted data.
output_schema_template: Dict[str, str] = {
    "Skill_Set": "skills",
    "Experience_Summary": "experience",
    "Anonymized_Resume_Text": "anonymized_resume_text",
    "Certifications_List": "certifications",
    "Education_Records": "education"
}

@app.get("/")
async def read_root():
    """
    Root endpoint that provides a simple welcome message.
    """
    return {"message": "Welcome to the Simplified Resume Parser API! Visit /docs to see the single upload endpoint."}

@app.post("/upload-and-parse/")
async def upload_and_parse(
    file: UploadFile = File(..., description="Resume file to upload (PDF, DOCX, or Image)")
):
    """
    This is a single, unprotected endpoint that handles resume file uploads
    and returns a structured JSON response.
    """
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF, DOCX, and JPG/PNG are supported."
        )

    temp_file_path = Path(f"temp_{uuid.uuid4()}_{file.filename}")
    file_size_read = 0
    max_file_size_bytes = 5 * 1024 * 1024 # 5 MB
    
    try:
        with temp_file_path.open("wb") as buffer:
            while True:
                chunk = await file.read(1024)
                if not chunk:
                    break
                file_size_read += len(chunk)
                if file_size_read > max_file_size_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail="File size exceeds the 5 MB limit."
                    )
                buffer.write(chunk)
        
        # Process the resume and get the structured data
        structured_data = process_resume(temp_file_path, file.content_type)
        
        return structured_data

    finally:
        if temp_file_path.exists():
            os.remove(temp_file_path)

# --- 3. Resume Parsing & Information Extraction ---
def process_resume(file_path: Path, content_type: str) -> dict:
    """
    Extracts text, anonymizes PII, and extracts key information from a resume file.
    """
    text = ""
    if content_type == "application/pdf":
        text = extract_text_from_pdf(file_path)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = extract_text_from_docx(file_path)
    elif content_type in ["image/jpeg", "image/png"]:
        text = extract_text_from_image(file_path)
    
    anonymized_text, anonymized_info = anonymize_data(text)
    extracted_info = extract_info(anonymized_text)
    
    # Combine all extracted information into a single dictionary
    combined_data = {
        "anonymized_resume_text": anonymized_text,
        **extracted_info,
        **anonymized_info
    }
    
    # Map the combined data to the desired output schema
    final_output = {}
    for key, value_key in output_schema_template.items():
        # Check if the value_key is a list of sub-keys (for nested structures)
        if isinstance(value_key, list):
            final_output[key] = {sub_key: combined_data.get(sub_key, None) for sub_key in value_key}
        else:
            final_output[key] = combined_data.get(value_key, None)
    
    return final_output

def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extracts text from a PDF file using PyPDF2.
    """
    text = ""
    try:
        with file_path.open("rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""
    return text

def extract_text_from_docx(file_path: Path) -> str:
    """
    Extracts text from a DOCX file using python-docx.
    """
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""
    return text

def extract_text_from_image(file_path: Path) -> str:
    """
    Extracts text from an image file using Tesseract OCR.
    """
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return ""
    return text

def extract_info(text: str) -> dict:
    """
    Extracts key sections like skills, experience, and certifications
    using regular expressions and simple pattern matching.
    """
    extracted_data = {
        "skills": [],
        "education": [],
        "experience": [],
        "certifications": []
    }
    
    # Define patterns to look for sections
    skills_match = re.search(r"Skills?[:\s]*(.*?)(\n|$)", text, re.IGNORECASE | re.DOTALL)
    if skills_match and skills_match.group(1):
        skills_raw = skills_match.group(1).strip()
        extracted_data["skills"] = [skill.strip() for skill in skills_raw.split(',') if skill.strip()]

    education_match = re.search(r"Education[:\s]*(.*?)(\n\n|$)", text, re.IGNORECASE | re.DOTALL)
    if education_match and education_match.group(1):
        education_raw = education_match.group(1).strip()
        extracted_data["education"] = [edu.strip() for edu in education_raw.split('\n') if edu.strip()]

    experience_match = re.search(r"Experience|Work History[:\s]*(.*?)(\n\n|$)", text, re.IGNORECASE | re.DOTALL)
    if experience_match and experience_match.group(1):
        experience_raw = experience_match.group(1).strip()
        extracted_data["experience"] = [exp.strip() for exp in experience_raw.split('\n') if exp.strip()]

    certifications_match = re.search(r"Certifications[:\s]*(.*?)(\n\n|$)", text, re.IGNORECASE | re.DOTALL)
    if certifications_match and certifications_match.group(1):
        certifications_raw = certifications_match.group(1).strip()
        extracted_data["certifications"] = [cert.strip() for cert in certifications_raw.split('\n') if cert.strip()]
        
    return extracted_data

def anonymize_data(text: str) -> (str, dict):
    """
    Anonymizes PII like names, emails, phone numbers, and addresses.
    Returns the anonymized text and a dictionary of masked info.
    """
    anonymized_info = {
        "masked_emails": [],
        "masked_phones": [],
        "masked_addresses": []
    }
    
    # Anonymize emails
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    emails = re.findall(email_pattern, text)
    anonymized_info["masked_emails"] = emails
    anonymized_text = re.sub(email_pattern, "***@***.com", text)
    
    # Anonymize phone numbers
    phone_pattern = r"\b(\+?\d{1,3}[-.\s]??)?(\(?\d{3}\)?[-.\s]??\d{3}[-.\s]??\d{4}|\d{10})\b"
    phones = re.findall(phone_pattern, anonymized_text)
    phones_flat = [p[1] for p in phones if p[1]]
    anonymized_info["masked_phones"] = phones_flat
    anonymized_text = re.sub(phone_pattern, "XXX-XXX-XXXX", anonymized_text)

    # Anonymize names using spaCy NER
    doc = nlp(anonymized_text)
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    if names:
        candidate_name = names[0]
        anonymized_text = anonymized_text.replace(candidate_name, "[CANDIDATE NAME]")
        anonymized_info["masked_name"] = candidate_name
        
    # Anonymize addresses using spaCy NER
    addresses = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]]
    if addresses:
        for address in addresses:
            anonymized_text = anonymized_text.replace(address, "[ADDRESS]")
    anonymized_info["masked_addresses"] = addresses
    
    return anonymized_text, anonymized_info
