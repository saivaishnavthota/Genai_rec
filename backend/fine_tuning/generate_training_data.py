"""
Generate training data for fine-tuning the LLM for resume screening and ATS scoring

This script generates synthetic training examples that can be used to fine-tune
the Ollama model for better resume evaluation.
"""

import json
import random
from typing import List, Dict, Any
from pathlib import Path


# Sample job roles with requirements
JOB_TEMPLATES = [
    {
        "title": "Senior Software Engineer",
        "skills": ["Python", "Django", "PostgreSQL", "Docker", "AWS", "REST API", "Git"],
        "experience": "5+ years",
        "education": "Bachelor's in Computer Science or related field"
    },
    {
        "title": "Full Stack Developer",
        "skills": ["React", "Node.js", "MongoDB", "JavaScript", "TypeScript", "HTML", "CSS"],
        "experience": "3-5 years",
        "education": "Bachelor's degree in relevant field"
    },
    {
        "title": "Data Scientist",
        "skills": ["Python", "Machine Learning", "TensorFlow", "Pandas", "SQL", "Statistics", "Data Visualization"],
        "experience": "3+ years",
        "education": "Master's in Data Science, Statistics, or related field"
    },
    {
        "title": "DevOps Engineer",
        "skills": ["Kubernetes", "Docker", "Jenkins", "AWS", "Terraform", "Linux", "CI/CD"],
        "experience": "4+ years",
        "education": "Bachelor's in Computer Science or equivalent"
    },
    {
        "title": "Frontend Developer",
        "skills": ["React", "Vue.js", "JavaScript", "TypeScript", "HTML5", "CSS3", "Webpack"],
        "experience": "2-4 years",
        "education": "Bachelor's degree or equivalent experience"
    },
]


# Candidate profile templates
CANDIDATE_PROFILES = {
    "excellent": {
        "skill_match": 0.9,
        "experience_years": 6,
        "education_level": "Master's",
        "ats_quality": "excellent",
        "expected_score": 85,
        "recommendation": "hire"
    },
    "good": {
        "skill_match": 0.75,
        "experience_years": 4,
        "education_level": "Bachelor's",
        "ats_quality": "good",
        "expected_score": 72,
        "recommendation": "interview"
    },
    "average": {
        "skill_match": 0.6,
        "experience_years": 2,
        "education_level": "Bachelor's",
        "ats_quality": "average",
        "expected_score": 58,
        "recommendation": "interview"
    },
    "below_average": {
        "skill_match": 0.4,
        "experience_years": 1,
        "education_level": "Associate",
        "ats_quality": "poor",
        "expected_score": 42,
        "recommendation": "reject"
    },
    "poor": {
        "skill_match": 0.2,
        "experience_years": 0,
        "education_level": "High School",
        "ats_quality": "poor",
        "expected_score": 25,
        "recommendation": "reject"
    }
}


def generate_candidate_skills(job_skills: List[str], match_ratio: float) -> List[str]:
    """Generate candidate skills based on job requirements and match ratio"""
    num_matching = int(len(job_skills) * match_ratio)
    matching_skills = random.sample(job_skills, min(num_matching, len(job_skills)))
    
    # Add some extra skills
    extra_skills = ["Agile", "Scrum", "Problem Solving", "Team Collaboration", "Communication"]
    num_extra = random.randint(2, 4)
    extra = random.sample(extra_skills, num_extra)
    
    return matching_skills + extra


def generate_training_example(
    job: Dict[str, Any],
    profile_type: str,
    profile: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate a single training example"""
    
    # Generate candidate skills
    candidate_skills = generate_candidate_skills(job["skills"], profile["skill_match"])
    
    # Calculate matched and missing skills
    matched_skills = [s for s in candidate_skills if s in job["skills"]]
    missing_skills = [s for s in job["skills"] if s not in candidate_skills]
    
    # Generate strengths and gaps based on profile
    if profile_type == "excellent":
        strengths = [
            "Strong technical skill set matching all key requirements",
            "Extensive relevant experience",
            "Advanced degree in relevant field",
            "Well-formatted, ATS-optimized resume"
        ]
        gaps = ["Minor: Could benefit from additional certifications"]
    elif profile_type == "good":
        strengths = [
            "Solid technical foundation with most required skills",
            "Relevant work experience",
            "Good educational background"
        ]
        gaps = [
            f"Missing some key skills: {', '.join(missing_skills[:2])}",
            "Could use more years of experience"
        ]
    elif profile_type == "average":
        strengths = [
            "Has foundational skills",
            "Some relevant experience",
            "Meets basic educational requirements"
        ]
        gaps = [
            f"Missing several key skills: {', '.join(missing_skills[:3])}",
            "Limited experience in the field",
            "Resume could be better optimized"
        ]
    elif profile_type == "below_average":
        strengths = [
            "Shows interest in the field",
            "Has some transferable skills"
        ]
        gaps = [
            f"Significant skill gaps: {', '.join(missing_skills[:4])}",
            "Insufficient relevant experience",
            "Education level below requirements",
            "Poor resume formatting"
        ]
    else:  # poor
        strengths = ["Willing to learn"]
        gaps = [
            "Does not meet minimum skill requirements",
            "No relevant experience",
            "Education level significantly below requirements",
            "Resume needs major improvements"
        ]
    
    # Create the prompt
    prompt = f"""Evaluate this candidate for the {job['title']} position.

JOB REQUIREMENTS:
- Title: {job['title']}
- Required Skills: {', '.join(job['skills'])}
- Experience: {job['experience']}
- Education: {job['education']}

CANDIDATE PROFILE:
- Skills: {', '.join(candidate_skills)}
- Matched Skills: {', '.join(matched_skills)}
- Missing Skills: {', '.join(missing_skills)}
- Experience: {profile['experience_years']} years
- Education: {profile['education_level']}

PRELIMINARY SCORES:
- Skills Match: {profile['skill_match'] * 100:.1f}%
- Experience Match: {min(profile['experience_years'] * 15, 90):.1f}%
- Education Match: {70 if 'Bachelor' in profile['education_level'] else 50}%
- ATS Score: {85 if profile['ats_quality'] == 'excellent' else 70 if profile['ats_quality'] == 'good' else 55 if profile['ats_quality'] == 'average' else 35}%

Provide a JSON response with:
{{
  "overall_score": <0-100>,
  "confidence": <"high"|"medium"|"low">,
  "key_strengths": ["strength1", "strength2", "strength3"],
  "key_gaps": ["gap1", "gap2", "gap3"],
  "recommendation": "<hire|interview|reject>",
  "brief_summary": "<2-3 sentences>"
}}"""

    # Create the expected response
    response = {
        "overall_score": profile["expected_score"],
        "confidence": "high" if profile_type in ["excellent", "poor"] else "medium",
        "key_strengths": strengths[:3],
        "key_gaps": gaps[:3],
        "recommendation": profile["recommendation"],
        "brief_summary": f"Candidate demonstrates {profile_type} fit for the {job['title']} role with {profile['skill_match']*100:.0f}% skill match and {profile['experience_years']} years of experience. {strengths[0]}. Recommendation: {profile['recommendation'].upper()}."
    }
    
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are an expert technical recruiter. Evaluate candidates objectively based on job requirements. Respond with valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            },
            {
                "role": "assistant",
                "content": json.dumps(response, indent=2)
            }
        ]
    }


def generate_training_dataset(num_examples_per_profile: int = 20) -> List[Dict[str, Any]]:
    """Generate a complete training dataset"""
    dataset = []
    
    for job in JOB_TEMPLATES:
        for profile_type, profile in CANDIDATE_PROFILES.items():
            for _ in range(num_examples_per_profile):
                example = generate_training_example(job, profile_type, profile)
                dataset.append(example)
    
    return dataset


def save_training_data(dataset: List[Dict[str, Any]], output_path: str):
    """Save training data in JSONL format (one JSON object per line)"""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        for example in dataset:
            f.write(json.dumps(example) + '\n')
    
    print(f"✅ Generated {len(dataset)} training examples")
    print(f"📁 Saved to: {output_file}")


def generate_validation_dataset(num_examples: int = 50) -> List[Dict[str, Any]]:
    """Generate a smaller validation dataset"""
    dataset = []
    
    for _ in range(num_examples):
        job = random.choice(JOB_TEMPLATES)
        profile_type = random.choice(list(CANDIDATE_PROFILES.keys()))
        profile = CANDIDATE_PROFILES[profile_type]
        
        example = generate_training_example(job, profile_type, profile)
        dataset.append(example)
    
    return dataset


if __name__ == "__main__":
    print("🚀 Generating training data for resume screening LLM...")
    
    # Generate training dataset
    print("\n📊 Generating training dataset...")
    training_data = generate_training_dataset(num_examples_per_profile=20)
    save_training_data(training_data, "backend/fine_tuning/data/training_data.jsonl")
    
    # Generate validation dataset
    print("\n📊 Generating validation dataset...")
    validation_data = generate_validation_dataset(num_examples=50)
    save_training_data(validation_data, "backend/fine_tuning/data/validation_data.jsonl")
    
    print("\n✅ Training data generation complete!")
    print("\n📝 Next steps:")
    print("1. Review the generated data in backend/fine_tuning/data/")
    print("2. Use the data to fine-tune your Ollama model")
    print("3. Run: python backend/fine_tuning/fine_tune_model.py")
