import re
import PyPDF2
from docx import Document
from typing import Dict, List, Any
import logging
try:
    import olefile
    import struct
    OLEFILE_AVAILABLE = True
except ImportError:
    OLEFILE_AVAILABLE = False

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text_from_doc(file_path: str) -> str:
    """Extract text from DOC file (legacy Word format)"""
    try:
        # For .doc files, we'll use a simple approach
        # In production, you might want to use python-docx2txt or antiword
        
        if OLEFILE_AVAILABLE:
            # Try to extract basic text using olefile
            # This is a simplified approach and may not work for all .doc files
            with open(file_path, 'rb') as f:
                content = f.read()
                # Simple text extraction - look for readable text
                text = ""
                for i in range(len(content) - 1):
                    if 32 <= content[i] <= 126:  # Printable ASCII
                        text += chr(content[i])
                    elif content[i] in [10, 13]:  # Line breaks
                        text += "\n"
                
                # Clean up the text
                lines = text.split('\n')
                clean_lines = []
                for line in lines:
                    line = line.strip()
                    if len(line) > 2 and any(c.isalpha() for c in line):
                        clean_lines.append(line)
                
                return '\n'.join(clean_lines)
        else:
            # Fallback: try to read as text (may not work well)
            logger.warning("olefile not available, using basic text extraction for .doc file")
            with open(file_path, 'rb') as f:
                content = f.read()
                # Try to decode as latin-1 and extract meaningful text
                try:
                    text = content.decode('latin-1', errors='ignore')
                    # Filter out non-printable characters
                    clean_text = ''.join(c if c.isprintable() else ' ' for c in text)
                    return clean_text
                except Exception:
                    return ""
                    
    except Exception as e:
        logger.error(f"Error extracting text from DOC: {e}")
        return ""

def extract_skills(text: str) -> List[str]:
    """Extract skills from resume text"""
    # Common technical skills
    skills_patterns = [
        r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin)\b',
        r'\b(?:React|Angular|Vue|Node\.js|Express|Django|Flask|Spring|Laravel)\b',
        r'\b(?:MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch|Cassandra)\b',
        r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|GitHub)\b',
        r'\b(?:HTML|CSS|Bootstrap|Tailwind|Sass|Less)\b',
        r'\b(?:Machine Learning|AI|Data Science|Analytics|Statistics)\b',
        r'\b(?:Linux|Unix|Windows|MacOS)\b',
        r'\b(?:API|REST|GraphQL|Microservices|DevOps|Agile|Scrum)\b'
    ]
    
    skills = []
    for pattern in skills_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        skills.extend(matches)
    
    return list(set(skills))

def extract_experience(text: str) -> List[Dict[str, Any]]:
    """Extract work experience from resume text"""
    experience = []
    
    # Look for common job title patterns
    job_patterns = [
        r'(?:Software Engineer|Developer|Programmer|Architect|Manager|Lead|Senior|Junior|Intern)',
        r'(?:Data Scientist|Analyst|Researcher|Consultant|Specialist)',
        r'(?:Designer|Product Manager|Project Manager|Team Lead)'
    ]
    
    # Look for date patterns (years)
    date_pattern = r'\b(?:20\d{2}|19\d{2})\b'
    dates = re.findall(date_pattern, text)
    
    # Simple experience extraction (can be enhanced with NLP)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        for pattern in job_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Try to extract company and duration
                experience_entry = {
                    'title': line.strip(),
                    'company': '',
                    'duration': '',
                    'description': ''
                }
                
                # Look for company in next few lines
                for j in range(i+1, min(i+3, len(lines))):
                    if lines[j].strip() and not re.search(date_pattern, lines[j]):
                        experience_entry['company'] = lines[j].strip()
                        break
                
                experience.append(experience_entry)
                break
    
    return experience

def extract_education(text: str) -> List[Dict[str, Any]]:
    """Extract education information from resume text"""
    education = []
    
    # Common degree patterns
    degree_patterns = [
        r'\b(?:Bachelor|Master|PhD|Doctorate|B\.S\.|M\.S\.|B\.A\.|M\.A\.|B\.Tech|M\.Tech)\b',
        r'\b(?:Computer Science|Engineering|Mathematics|Business|MBA)\b'
    ]
    
    lines = text.split('\n')
    for line in lines:
        for pattern in degree_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                education.append({
                    'degree': line.strip(),
                    'institution': '',
                    'year': ''
                })
                break
    
    return education

def extract_certifications(text: str) -> List[str]:
    """Extract certifications from resume text"""
    cert_patterns = [
        r'\b(?:AWS Certified|Azure Certified|Google Cloud Certified)\b',
        r'\b(?:PMP|Scrum Master|Product Owner)\b',
        r'\b(?:CISSP|CompTIA|Cisco|Microsoft Certified)\b'
    ]
    
    certifications = []
    for pattern in cert_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        certifications.extend(matches)
    
    return list(set(certifications))

def calculate_ats_score(text: str, filename: str) -> float:
    """Calculate ATS compatibility score"""
    score = 0.0
    
    # File format score (PDF and DOCX are good for ATS)
    if filename.lower().endswith(('.pdf', '.docx')):
        score += 30
    
    # Check for common sections
    sections = ['experience', 'education', 'skills', 'summary', 'objective']
    for section in sections:
        if re.search(section, text, re.IGNORECASE):
            score += 10
    
    # Check for proper formatting indicators
    if re.search(r'\b\d{4}\b', text):  # Years
        score += 10
    
    if re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', text):  # Email
        score += 5
    
    if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text):  # Phone
        score += 5
    
    return min(score, 100.0)

def parse_resume(file_path: str, filename: str) -> Dict[str, Any]:
    """Parse resume and extract relevant information"""
    try:
        # Extract text based on file type
        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif filename.lower().endswith('.docx'):
            text = extract_text_from_docx(file_path)
        elif filename.lower().endswith('.doc'):
            text = extract_text_from_doc(file_path)
        else:
            return {
                'parsed_skills': [],
                'parsed_experience': [],
                'parsed_education': [],
                'parsed_certifications': [],
                'ats_score': 0.0,
                'raw_text': ''
            }
        
        # Extract information
        skills = extract_skills(text)
        experience = extract_experience(text)
        education = extract_education(text)
        certifications = extract_certifications(text)
        ats_score = calculate_ats_score(text, filename)
        
        return {
            'parsed_skills': skills,
            'parsed_experience': experience,
            'parsed_education': education,
            'parsed_certifications': certifications,
            'ats_score': ats_score,
            'raw_text': text[:1000]  # First 1000 chars for reference
        }
        
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        return {
            'parsed_skills': [],
            'parsed_experience': [],
            'parsed_education': [],
            'parsed_certifications': [],
            'ats_score': 0.0,
            'raw_text': ''
        }
