# Resume-Parsing-and-Management-Platform

### Objective
#### This project is a high-performance web application built with FastAPI that automatically extracts, anonymizes, and structures key information from resumes. Its primary purpose is to streamline recruitment workflows by providing a clean, structured JSON output that protects candidate privacy by masking Personally Identifiable Information (PII) like names, emails, and phone numbers.

### Technology Stack
#### Backend Framework: FastAPI

#### Resume Parsing:

#### PyPDF2 for PDF files

#### python-docx for DOCX files

#### Pillow and pytesseract for OCR on image files (JPG/PNG)

#### Natural Language Processing (NLP):

#### spaCy for Named Entity Recognition (NER) to detect and anonymize names and addresses.

#### Project Management: uvicorn and pip

### Key Features
#### Single, Unprotected Endpoint: A simple POST endpoint to upload resumes and receive a JSON response.

#### Multi-Format Support: Handles resumes in PDF, DOCX, JPG, and PNG formats.

#### Intelligent PII Anonymization:

#### Identifies and masks phone numbers and emails using regular expressions.

#### Detects and replaces names and addresses with placeholders using spaCy's NER capabilities.

#### Structured Data Extraction: Automatically extracts sections like skills, experience, and certifications.

#### Configurable JSON Output: The output is a structured JSON file with configurable field names for easy integration into other systems.

### How It Works (Steps)
#### File Upload: A user uploads a resume file to the /upload-and-parse/ endpoint.

#### File Validation: The API validates the file type and size to ensure it meets the requirements.

#### Text Extraction: The appropriate library is used to extract the raw text from the file (e.g., PyPDF2 for PDFs).

#### Data Anonymization: The raw text is passed through an anonymization process where regex patterns and spaCy's NER are used to replace PII with standard placeholders.

#### Information Extraction: The cleaned text is then scanned using regex to pull out key sections like skills, experience, and certifications.

#### JSON Output: The extracted and anonymized data is compiled into a single, structured JSON object and returned as the API's response.

### Setup and Installation
#### Prerequisites
#### Python 3.7+

#### pip

### Steps
#### go to command prompt 
#### mkdir my_project
#### cd my_project 

### Create a virtual environment and activate it:

#### python -m venv venv
#### source venv/bin/activate  # On Windows: venv\Scripts\activate

### Install dependencies:

#### pip install "fastapi[all]" python-docx PyPDF2 Pillow pytesseract spacy
#### python -m spacy download en_core_web_sm

### Run the application:

#### uvicorn main:app --reload

#### The application will now be running on http://127.0.0.1:8000.

### Usage
#### Once the server is running, you can access the interactive API documentation at:
#### http://127.0.0.1:8000/docs

#### From there, you can use the Swagger UI to test the /upload-and-parse/ endpoint by uploading a resume file.
