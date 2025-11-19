import logging
import json
import os
from typing import List, Dict, Any, Optional
from ..config import settings
import httpx

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        """
        Initialize to use Ollama if enabled; otherwise keep fallback.
        No local GGUF loading needed when use_ollama=True.
        """
        self.fallback_mode = not bool(getattr(settings, "use_ollama", True))
        self.ollama_base = settings.ollama_base_url
        self.ollama_model = settings.ollama_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout_seconds

        if self.fallback_mode:
            print("⚠️ Ollama disabled; running in FALLBACK mode.")
        else:
            print(f"🤖 Using Ollama model: {self.ollama_model} @ {self.ollama_base}")

    async def _chat_ollama(self, messages: list, temperature: Optional[float] = None, max_tokens: Optional[int] = None, timeout: Optional[int] = None) -> str:
        """
        Call Ollama /api/chat and return assistant content as string.
        """
        if self.fallback_mode:
            raise RuntimeError("Ollama not enabled")

        # Use custom timeout if provided, otherwise use default
        request_timeout = timeout if timeout is not None else self.timeout
        # Convert to httpx.Timeout if it's an integer
        if isinstance(request_timeout, int):
            timeout_obj = httpx.Timeout(request_timeout, connect=10.0)
        else:
            timeout_obj = request_timeout

        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "options": {
                "temperature": temperature if temperature is not None else self.temperature,
                "num_predict": max_tokens if max_tokens is not None else self.max_tokens,
            },
            # We want a single final message string (non-stream)
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=timeout_obj) as client:
            try:
                # Try /api/chat endpoint first
                r = await client.post(f"{self.ollama_base}/api/chat", json=payload)
                r.raise_for_status()
                data = r.json()
                
                # Ollama returns {"message": {"role": "assistant", "content": "..."}}
                if "message" in data and "content" in data["message"]:
                    return data["message"]["content"]
                else:
                    raise ValueError(f"Unexpected response format: {data}")
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # If /api/chat doesn't exist, try /api/generate as fallback
                    logger.warning(f"/api/chat endpoint not found, trying /api/generate with model {self.ollama_model}")
                    
                    # Convert messages to a prompt for /api/generate
                    prompt_parts = []
                    for msg in messages:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        if role == "system":
                            prompt_parts.append(f"System: {content}\n\n")
                        elif role == "user":
                            prompt_parts.append(f"User: {content}\n\n")
                        elif role == "assistant":
                            prompt_parts.append(f"Assistant: {content}\n\n")
                    
                    prompt = "".join(prompt_parts).strip()
                    
                    generate_payload = {
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "options": {
                            "temperature": temperature if temperature is not None else self.temperature,
                            "num_predict": max_tokens if max_tokens is not None else self.max_tokens,
                        },
                        "stream": False,
                    }
                    
                    r = await client.post(f"{self.ollama_base}/api/generate", json=generate_payload)
                    r.raise_for_status()
                    data = r.json()
                    
                    if "response" in data:
                        return data["response"]
                    else:
                        raise ValueError(f"Unexpected response format from /api/generate: {data}")
                else:
                    raise

    async def generate_job_fields(self, project_name: str, role_title: str, role_description: str) -> Dict[str, Any]:
        """Generate additional job fields using the configured LLM (Ollama)."""
        try:
            logger.info(f"🤖 Generating job fields for role: {role_title}")

            if self.fallback_mode:
                print("⚠️ Using fallback mode - LLM not available")
                return self._smart_fallback_job_fields(role_title, role_description)

            prompt = f"""Generate job requirements for: {role_title}
Description: {role_description}
Project: {project_name}

Return JSON only:
{{
  "key_skills": ["list 4-5 specific technical skills for this role"],
  "required_experience": "years and type of experience needed",
  "certifications": ["relevant certifications or empty array"],
  "additional_requirements": ["3-4 other important requirements"]
}}"""

            messages = [{"role": "user", "content": prompt}]

            print(f"\n🤖 === OLLAMA JOB FIELDS REQUEST ===")
            print(f"📝 Role: {role_title}")
            print(f"🏢 Project: {project_name}")
            print(f"📋 Description: {role_description}")
            print(f"📤 Generating with Ollama...")

            # No custom stop tokens; we'll parse JSON safely
            content = await self._chat_ollama(messages, temperature=0.3, max_tokens=220)

            print(f"\n📥 === OLLAMA RAW RESPONSE ===")
            print(f"📏 Response Length: {len(content)} characters")
            print(f"📄 Full Response:")
            print("=" * 80)
            print(content)
            print("=" * 80)

            # JSON extraction
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            print(f"\n🔍 === JSON PARSING ATTEMPT ===")
            print(f"JSON Start Position: {json_start}")
            print(f"JSON End Position: {json_end}")
            
            if json_start != -1 and json_end > json_start:
                json_text = content[json_start:json_end]
                print(f"📋 Extracted JSON Text:")
                print("-" * 40)
                print(json_text)
                print("-" * 40)
                
                result = json.loads(json_text)
                print(f"✅ JSON PARSING SUCCESS!")
                print(f"📊 Parsed Result: {result}")
                
                # Validate and normalize the result to match schema
                normalized_result = self._normalize_job_fields_response(result)
                print(f"🔧 Normalized Result: {normalized_result}")
                return normalized_result
            else:
                print("❌ No valid JSON found, using fallback")
                return self._fallback_job_fields(role_title)

        except Exception as e:
            logger.error(f"❌ Error generating job fields: {e}")
            print(f"❌ OLLAMA API ERROR: {e}")
            print(f"🔄 Falling back to predefined job fields")
            return self._smart_fallback_job_fields(role_title, role_description)

    async def generate_job_description(
        self,
        project_name: str,
        role_title: str,
        role_description: str,
        key_skills: List[str],
        required_experience: str,
        certifications: List[str],
        additional_requirements: List[str]
    ) -> Dict[str, str]:
        """Generate complete job description using the configured LLM (Ollama)."""
        try:
            logger.info(f"🤖 Generating job description for role: {role_title}")

            if self.fallback_mode:
                print("⚠️ Using fallback mode - LLM not available")
                return self._smart_fallback_job_description(
                    role_title, role_description, key_skills, required_experience, certifications, additional_requirements
                )

            skills_str = ", ".join(key_skills)
            certs_str = ", ".join(certifications) if certifications else "None specified"
            reqs_str = ", ".join(additional_requirements)

            prompt = f"""Create a professional, comprehensive job description based on the following information:

Project Name: {project_name}
Role Title: {role_title}
Basic Description: {role_description}
Key Skills: {skills_str}
Required Experience: {required_experience}
Certifications: {certs_str}
Additional Requirements: {reqs_str}

Create a well-structured job description with clear sections. Return ONLY a JSON object with these exact keys:

{{
  "description": "A comprehensive job description with sections for responsibilities, requirements, and benefits (300-400 words)",
  "short_description": "A brief 2-3 sentence summary of the role and key requirements"
}}

Make the description professional, engaging, and well-structured with proper sections:
- Role Summary
- Key Responsibilities (bulleted)
- Required Qualifications
- Preferred Qualifications
- Benefits & Culture

Respond with ONLY valid JSON, no other text.
"""

            messages = [
                {"role": "system", "content": "You are an expert HR professional creating compelling job descriptions. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ]

            print(f"\n🤖 === OLLAMA JOB DESCRIPTION REQUEST ===")
            print(f"📝 Role: {role_title}")
            print(f"🏢 Project: {project_name}")
            print(f"📤 Generating comprehensive job description...")

            content = await self._chat_ollama(messages, temperature=0.4, max_tokens=2000)

            print(f"\n📥 === OLLAMA JOB DESCRIPTION RAW RESPONSE ===")
            print(f"📏 Response Length: {len(content)} characters")
            print(f"📄 Full Response:")
            print("=" * 80)
            print(content)
            print("=" * 80)

            # Try to extract JSON with improved logic
            json_start = content.find('{')
            
            print(f"\n🔍 === JSON PARSING ATTEMPT (JOB DESCRIPTION) ===")
            print(f"JSON Start Position: {json_start}")
            
            if json_start == -1:
                print("❌ No opening brace found, using fallback")
                return self._fallback_job_description(role_title, role_description)
            
            # Find the matching closing brace by counting braces
            brace_count = 0
            json_end = -1
            for i in range(json_start, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            print(f"JSON End Position: {json_end}")
            
            if json_end > json_start:
                json_text = content[json_start:json_end]
                print(f"📋 Extracted JSON Text:")
                print("-" * 40)
                print(json_text)
                print("-" * 40)
                
                try:
                    result = json.loads(json_text)
                    print(f"✅ JSON PARSING SUCCESS!")
                    print(f"📊 Parsed Result Keys: {list(result.keys())}")
                    
                    # Validate and normalize the result to match schema
                    normalized_result = self._normalize_job_description_response(result)
                    print(f"🔧 Normalized Result Keys: {list(normalized_result.keys())}")
                    return normalized_result
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    print("🔄 Attempting to fix JSON...")
                    # Try to fix common JSON issues
                    json_text_fixed = self._fix_json_string(json_text)
                    try:
                        result = json.loads(json_text_fixed)
                        print(f"✅ JSON PARSING SUCCESS after fix!")
                        normalized_result = self._normalize_job_description_response(result)
                        return normalized_result
                    except:
                        print("❌ Could not fix JSON, using fallback")
                        return self._fallback_job_description(role_title, role_description)
            else:
                # If no closing brace found, try to extract what we have and add closing brace
                print("⚠️ No closing brace found, attempting to fix...")
                json_text = content[json_start:].strip()
                # Remove any trailing non-JSON text
                last_brace = json_text.rfind('}')
                if last_brace != -1:
                    json_text = json_text[:last_brace + 1]
                else:
                    # Try to add closing brace if JSON seems complete
                    if json_text.count('{') > json_text.count('}'):
                        json_text += '}'
                
                try:
                    result = json.loads(json_text)
                    print(f"✅ JSON PARSING SUCCESS after fix!")
                    normalized_result = self._normalize_job_description_response(result)
                    return normalized_result
                except:
                    print("❌ No valid JSON found, using fallback")
                    return self._fallback_job_description(role_title, role_description)

        except Exception as e:
            logger.error(f"❌ Error generating job description: {e}")
            print(f"❌ OLLAMA API ERROR: {e}")
            print(f"🔄 Falling back to predefined job description")
            return self._fallback_job_description(role_title, role_description)

    def _normalize_job_fields_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize LLM response to match expected schema"""
        normalized = {}
        
        # Ensure key_skills is a list of strings
        key_skills = result.get('key_skills', [])
        if isinstance(key_skills, str):
            normalized['key_skills'] = [key_skills]
        elif isinstance(key_skills, list):
            normalized['key_skills'] = [str(skill) for skill in key_skills]
        else:
            normalized['key_skills'] = []
        
        # Ensure required_experience is a string
        required_exp = result.get('required_experience', '')
        if isinstance(required_exp, list):
            # If it's a list, join the items or take the first one
            normalized['required_experience'] = ', '.join(str(item) for item in required_exp) if required_exp else ''
        else:
            normalized['required_experience'] = str(required_exp)
        
        # Ensure certifications is a list of strings
        certifications = result.get('certifications', [])
        if isinstance(certifications, str):
            normalized['certifications'] = [certifications] if certifications else []
        elif isinstance(certifications, list):
            normalized['certifications'] = [str(cert) for cert in certifications]
        else:
            normalized['certifications'] = []
        
        # Ensure additional_requirements is a list of strings
        additional_reqs = result.get('additional_requirements', [])
        if isinstance(additional_reqs, str):
            normalized['additional_requirements'] = [additional_reqs]
        elif isinstance(additional_reqs, list):
            normalized['additional_requirements'] = [str(req) for req in additional_reqs]
        else:
            normalized['additional_requirements'] = []
        
        return normalized

    def _fix_json_string(self, json_text: str) -> str:
        """Attempt to fix common JSON issues in LLM responses"""
        # Remove any trailing text after the last }
        last_brace = json_text.rfind('}')
        if last_brace != -1:
            json_text = json_text[:last_brace + 1]
        
        # Fix unescaped newlines in strings
        import re
        # This is a simple fix - in production you might want more sophisticated handling
        # For now, we'll just ensure the JSON structure is valid
        
        # Try to balance braces if needed
        open_count = json_text.count('{')
        close_count = json_text.count('}')
        if open_count > close_count:
            json_text += '}' * (open_count - close_count)
        elif close_count > open_count:
            # Remove extra closing braces from the end
            json_text = json_text.rstrip('}')
            while json_text.count('{') < json_text.count('}'):
                json_text = json_text.rstrip('}')
        
        return json_text.strip()

    def _normalize_job_description_response(self, result: Dict[str, Any]) -> Dict[str, str]:
        """Normalize LLM job description response to match expected schema"""
        normalized = {}
        
        # Ensure description is a string
        description = result.get('description', '')
        normalized['description'] = str(description)
        
        # Ensure short_description is a string
        short_description = result.get('short_description', '')
        normalized['short_description'] = str(short_description)
        
        return normalized

    def _smart_fallback_job_fields(self, role_title: str, role_description: str) -> Dict[str, Any]:
        """Smart fallback that analyzes job title and description"""
        role_lower = role_title.lower()
        desc_lower = role_description.lower()
        
        # Analyze keywords in both title and description
        tech_keywords = ["python", "javascript", "java", "react", "node", "api", "backend", "frontend", "full stack", "software", "web", "mobile", "app"]
        data_keywords = ["data", "analyst", "sql", "analytics", "science", "machine learning", "ai", "statistics"]
        management_keywords = ["manager", "lead", "director", "senior", "head", "supervisor", "team lead"]
        hr_keywords = ["hr", "human resources", "recruiter", "talent", "people", "recruitment"]
        
        # Smart detection based on content
        is_tech = any(keyword in role_lower or keyword in desc_lower for keyword in tech_keywords)
        is_data = any(keyword in role_lower or keyword in desc_lower for keyword in data_keywords)
        is_management = any(keyword in role_lower or keyword in desc_lower for keyword in management_keywords)
        is_hr = any(keyword in role_lower or keyword in desc_lower for keyword in hr_keywords)
        
        print(f"🧠 Smart analysis: Tech={is_tech}, Data={is_data}, Mgmt={is_management}, HR={is_hr}")
        
        if is_tech:
            return {
                "key_skills": ["Programming", "Problem Solving", "System Design", "Code Review", "API Development"],
                "required_experience": "3-5 years of software development experience",
                "certifications": ["AWS Certified Developer", "Relevant technical certifications"],
                "additional_requirements": ["Strong communication skills", "Agile methodology", "Version control (Git)", "Team collaboration"]
            }
        elif is_data:
            return {
                "key_skills": ["Data Analysis", "SQL", "Python/R", "Statistical Analysis", "Data Visualization"],
                "required_experience": "2-4 years in data analysis or related field",
                "certifications": ["Data analysis certifications", "Cloud platform certifications"],
                "additional_requirements": ["Attention to detail", "Business acumen", "Excel proficiency", "Reporting skills"]
            }
        elif is_hr:
            return {
                "key_skills": ["Recruitment", "Employee Relations", "HR Policies", "Talent Management", "Interviewing"],
                "required_experience": "3-5 years in HR or talent acquisition",
                "certifications": ["SHRM-CP", "PHR", "Relevant HR certifications"],
                "additional_requirements": ["Excellent communication", "Confidentiality", "Stakeholder management", "HRIS systems"]
            }
        else:
            return {
                "key_skills": ["Communication", "Leadership", "Problem Solving", "Project Management", "Strategic Planning"],
                "required_experience": "3-5 years of relevant experience",
                "certifications": ["Industry relevant certifications"],
                "additional_requirements": ["Team management skills", "Strategic thinking", "Cross-functional collaboration", "Results-oriented"]
            }

    def _smart_fallback_job_description(
        self, 
        role_title: str, 
        role_description: str,
        key_skills: List[str],
        required_experience: str,
        certifications: List[str],
        additional_requirements: List[str]
    ) -> Dict[str, str]:
        """Smart job description generation using provided fields"""
        skills_text = ", ".join(key_skills) if key_skills else "relevant technical skills"
        certs_text = ", ".join(certifications) if certifications else "industry-relevant certifications"
        reqs_text = ", ".join(additional_requirements) if additional_requirements else "strong communication and teamwork skills"
        
        description = f"""**Position:** {role_title}

**Role Summary:**
We are seeking a qualified {role_title} to join our dynamic team. {role_description} The ideal candidate will bring {required_experience} and contribute to our continued success.

**Key Responsibilities:**
• Execute core responsibilities related to {role_description.lower()}
• Collaborate effectively with cross-functional teams
• Contribute to project success and organizational goals
• Maintain high standards of work quality and professionalism
• Participate in continuous improvement initiatives

**Required Qualifications:**
• {required_experience}
• Proficiency in: {skills_text}
• {reqs_text}
• Strong problem-solving and analytical abilities

**Preferred Qualifications:**
• {certs_text}
• Advanced experience with industry-specific tools and technologies
• Proven track record of successful project delivery
• Leadership experience (for senior roles)

**What We Offer:**
• Competitive salary and benefits package
• Professional development opportunities
• Collaborative and innovative work environment
• Health and wellness benefits
• Flexible work arrangements
• Career growth opportunities"""

        short_description = f"We are seeking a qualified {role_title} with {required_experience}. Key skills include {skills_text[:100]}{'...' if len(skills_text) > 100 else ''}. Join our team to contribute to exciting projects and grow your career."

        return {
            "description": description,
            "short_description": short_description
        }

    def _fallback_job_fields(self, role_title: str) -> Dict[str, Any]:
        """Fallback job fields if LLM fails"""
        # Simple keyword-based suggestions
        tech_roles = ["developer", "engineer", "programmer", "architect", "software"]
        data_roles = ["data", "analyst", "scientist", "analytics"]
        management_roles = ["manager", "lead", "director", "head"]
        
        role_lower = role_title.lower()
        
        if any(tech in role_lower for tech in tech_roles):
            return {
                "key_skills": ["Programming", "Problem Solving", "System Design", "Code Review"],
                "required_experience": "3-5 years of software development experience",
                "certifications": ["AWS Certified Developer", "Relevant technical certifications"],
                "additional_requirements": ["Strong communication skills", "Agile methodology experience", "Team collaboration"]
            }
        elif any(data in role_lower for data in data_roles):
            return {
                "key_skills": ["Data Analysis", "SQL", "Statistical Analysis", "Machine Learning"],
                "required_experience": "2-4 years in data analysis or science",
                "certifications": ["Data Science Certification", "Cloud Data Certifications"],
                "additional_requirements": ["Attention to detail", "Business acumen", "Data visualization skills"]
            }
        else:
            return {
                "key_skills": ["Communication", "Leadership", "Problem Solving", "Strategic Planning"],
                "required_experience": "3-5 years of relevant experience in a leadership role",
                "certifications": ["Project Management Professional (PMP)", "Leadership Certifications"],
                "additional_requirements": ["Team management skills", "Strategic thinking", "Stakeholder management"]
            }
    
    def _fallback_job_description(self, role_title: str, role_description: str) -> Dict[str, str]:
        """Fallback job description if LLM fails"""
        return {
            "description": f"""
            **Position:** {role_title}

            **Role Summary:**
            We are seeking a qualified {role_title} to join our team. This role involves {role_description.lower()}. The ideal candidate will bring relevant experience and contribute to our team's success.

            **Key Responsibilities:**
            • Execute primary job functions as outlined
            • Collaborate with team members effectively
            • Contribute to project success and company goals
            • Maintain high standards of work quality
            • Participate in continuous improvement initiatives

            **Required Qualifications:**
            • Relevant experience in the field
            • Strong communication and teamwork skills
            • Ability to work independently and manage priorities
            • Commitment to continuous learning and improvement
            • Bachelor's degree in a related field (or equivalent experience)

            **Preferred Qualifications:**
            • Master's degree or advanced certifications
            • Experience with industry-specific tools and technologies
            • Proven track record of successful project delivery

            **Benefits & Culture:**
            • Competitive salary package
            • Professional development opportunities
            • Collaborative work environment
            • Health and wellness benefits
            • Flexible work arrangements
            """,
            "short_description": f"We are seeking a qualified {role_title} to join our team. This role involves {role_description.lower()[:100]}... The ideal candidate will bring relevant experience and contribute to our team's success."
        }
    
    async def generate_interview_questions(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        key_skills: List[str],
        experience_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate interview questions from resume and job details using LLM
        
        Args:
            resume_text: Full text extracted from candidate's resume
            job_title: Job title
            job_description: Job description
            key_skills: List of key skills required for the job
            experience_level: Experience level (e.g., "entry", "mid", "senior")
            
        Returns:
            List of question dictionaries with id, text, type, and time_limit
        """
        try:
            logger.info(f"🤖 Generating interview questions for role: {job_title}")

            if self.fallback_mode:
                logger.warning("⚠️ Using fallback mode - LLM not available")
                return self._fallback_questions(job_title, key_skills, experience_level)

            # Build resume summary from parsed data if available
            skills_text = ", ".join(key_skills) if key_skills else "relevant technical skills"
            
            # Truncate resume text to avoid token limits (keep first 2000 chars)
            resume_summary = resume_text[:2000] if len(resume_text) > 2000 else resume_text
            
            prompt = f"""Generate 5 personalized interview questions for a candidate based on their resume and the job requirements.

Job Title: {job_title}
Job Description: {job_description[:500]}
Required Skills: {skills_text}
Experience Level: {experience_level or "Not specified"}

Candidate Resume Summary:
{resume_summary}

Generate 5 interview questions that:
1. Are personalized based on the candidate's resume content
2. Test relevant skills and experience mentioned in their resume
3. Are appropriate for the job role and experience level
4. MUST include 2-3 behavioral questions about past experiences, problem-solving, and teamwork
5. Include 1-2 technical questions based on their resume and required skills
6. Are clear, concise, and interview-appropriate

Return ONLY a JSON array with this exact format:
[
  {{
    "id": 1,
    "text": "Question text here",
    "type": "behavioral|technical|experience|closing",
    "time_limit": 120
  }},
  ...
]

Question types (ensure variety):
- "behavioral": Questions about past experiences, problem-solving, teamwork, challenges faced (MUST HAVE 2-3 OF THESE)
- "technical": Questions about specific skills, technologies, or technical knowledge from their resume
- "experience": Questions about work history and relevant experience mentioned in resume
- "closing": Final question asking if candidate has questions

Time limits should be in seconds (typically 120-180 seconds per question).

Respond with ONLY the JSON array, no other text."""

            messages = [
                {"role": "system", "content": "You are an expert HR interviewer. Generate personalized interview questions based on candidate resumes. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ]

            logger.info(f"📤 Generating questions with Ollama...")
            content = await self._chat_ollama(messages, temperature=0.5, max_tokens=1500)

            logger.info(f"📥 Received response from LLM (length: {len(content)} chars)")

            # Extract JSON array
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = content[json_start:json_end]
                try:
                    questions = json.loads(json_text)
                    # Validate questions structure
                    if isinstance(questions, list) and len(questions) > 0:
                        # Ensure all questions have required fields
                        validated_questions = []
                        for i, q in enumerate(questions):
                            if isinstance(q, dict) and "text" in q:
                                validated_questions.append({
                                    "id": q.get("id", i + 1),
                                    "text": str(q.get("text", "")),
                                    "type": q.get("type", "behavioral"),
                                    "time_limit": int(q.get("time_limit", 120))
                                })
                        
                        if len(validated_questions) >= 3:  # At least 3 questions
                            logger.info(f"✅ Generated {len(validated_questions)} questions successfully")
                            return validated_questions
                        else:
                            logger.warning(f"⚠️ Only {len(validated_questions)} valid questions, using fallback")
                            return self._fallback_questions(job_title, key_skills, experience_level)
                    else:
                        logger.warning("⚠️ Invalid questions format, using fallback")
                        return self._fallback_questions(job_title, key_skills, experience_level)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error: {e}")
                    logger.debug(f"Failed JSON text: {json_text[:500]}")
                    return self._fallback_questions(job_title, key_skills, experience_level)
            else:
                logger.warning("⚠️ No JSON array found in response, using fallback")
                return self._fallback_questions(job_title, key_skills, experience_level)

        except Exception as e:
            logger.error(f"❌ Error generating interview questions: {e}", exc_info=True)
            return self._fallback_questions(job_title, key_skills, experience_level)
    
    def _fallback_questions(
        self,
        job_title: str,
        key_skills: List[str],
        experience_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fallback questions if LLM generation fails"""
        questions = []
        
        # Question 1: Introduction
        questions.append({
            "id": 1,
            "text": "Tell us about yourself and why you're interested in this position.",
            "type": "behavioral",
            "time_limit": 120
        })
        
        # Question 2: Role-specific
        if key_skills:
            skills_text = ", ".join(key_skills[:3])
            questions.append({
                "id": 2,
                "text": f"This role requires skills in {skills_text}. Can you share your experience with these technologies?",
                "type": "technical",
                "time_limit": 180
            })
        
        # Question 3: Experience
        if experience_level:
            questions.append({
                "id": 3,
                "text": f"With this being a {experience_level} level position, what relevant experience do you bring to this role?",
                "type": "experience",
                "time_limit": 150
            })
        else:
            questions.append({
                "id": 3,
                "text": "What relevant experience do you bring to this role?",
                "type": "experience",
                "time_limit": 150
            })
        
        # Question 4: Problem-solving
        questions.append({
            "id": 4,
            "text": "Describe a challenging project or problem you've worked on. How did you approach it and what was the outcome?",
            "type": "behavioral",
            "time_limit": 180
        })
        
        # Question 5: Closing
        questions.append({
            "id": 5,
            "text": "Do you have any questions about the role or the company?",
            "type": "closing",
            "time_limit": 120
        })
        
        return questions