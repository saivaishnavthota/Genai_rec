# Resume Screening & ATS Scoring LLM Fine-Tuning

This directory contains tools and scripts for fine-tuning the LLM used in resume screening and ATS scoring.

## 🎯 Overview

The enhanced system provides:

1. **Improved Resume Parser** - Better extraction of skills, experience, and education
2. **Semantic Skill Matching** - Understands similar technologies (e.g., React = ReactJS)
3. **Enhanced Scoring Prompts** - More accurate LLM-based evaluation
4. **Training Data Generation** - Synthetic data for model fine-tuning
5. **Custom Model Creation** - Optimized Ollama model for resume screening

## 📁 Directory Structure

```
backend/fine_tuning/
├── README.md                      # This file
├── generate_training_data.py      # Generate synthetic training data
├── fine_tune_model.py             # Create custom Ollama model
├── data/                          # Generated training data
│   ├── training_data.jsonl        # Training examples
│   └── validation_data.jsonl      # Validation examples
└── Modelfile                      # Ollama model configuration
```

## 🚀 Quick Start

### Step 1: Generate Training Data

```bash
cd backend
python fine_tuning/generate_training_data.py
```

This generates:
- 500 training examples (20 per profile type × 5 job roles × 5 profile types)
- 50 validation examples
- Data saved in JSONL format

### Step 2: Create Custom Model

```bash
python fine_tuning/fine_tune_model.py
```

This will:
1. Create a Modelfile with optimized prompts and examples
2. Build a custom Ollama model: `resume-screener:latest`
3. Test the model with a sample evaluation

### Step 3: Update Configuration

Update your `.env` file:

```env
OLLAMA_MODEL=resume-screener:latest
```

### Step 4: Use Enhanced Scoring

Update your application code to use the enhanced scoring service:

```python
from app.services.enhanced_scoring_service import EnhancedScoringService

# In your application processing
scoring_service = EnhancedScoringService()
score = await scoring_service.score_application_enhanced(
    db=db,
    application=application,
    use_llm_evaluation=True
)
```

## 📊 Training Data Format

Each training example follows this structure:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an expert technical recruiter..."
    },
    {
      "role": "user",
      "content": "Evaluate this candidate for the Senior Software Engineer position..."
    },
    {
      "role": "assistant",
      "content": "{\"overall_score\": 85, \"confidence\": \"high\", ...}"
    }
  ]
}
```

## 🎓 Profile Types

The training data includes 5 candidate profile types:

1. **Excellent** (85+ score)
   - 90% skill match
   - 6+ years experience
   - Master's degree
   - Excellent ATS quality

2. **Good** (72+ score)
   - 75% skill match
   - 4+ years experience
   - Bachelor's degree
   - Good ATS quality

3. **Average** (58+ score)
   - 60% skill match
   - 2+ years experience
   - Bachelor's degree
   - Average ATS quality

4. **Below Average** (42+ score)
   - 40% skill match
   - 1 year experience
   - Associate degree
   - Poor ATS quality

5. **Poor** (25+ score)
   - 20% skill match
   - No experience
   - High school
   - Poor ATS quality

## 🔧 Enhanced Features

### 1. Enhanced Resume Parser

Located in: `backend/app/utils/enhanced_resume_parser.py`

Features:
- Expanded skill patterns (10+ categories)
- Better job title extraction with seniority levels
- Improved education parsing with GPA extraction
- Enhanced certification detection
- Detailed ATS scoring breakdown

### 2. Enhanced Scoring Service

Located in: `backend/app/services/enhanced_scoring_service.py`

Features:
- Semantic skill matching (understands similar technologies)
- Context-aware experience evaluation
- Education level assessment
- LLM-based holistic evaluation
- Detailed feedback generation

### 3. Semantic Skill Matching

The system understands technology equivalents:

```python
{
    'react': ['reactjs', 'react.js', 'react native'],
    'node': ['nodejs', 'node.js'],
    'python': ['python3', 'python2'],
    'kubernetes': ['k8s', 'container orchestration'],
    # ... and more
}
```

## 📈 Scoring Breakdown

### Match Score (50% weight)
- **Skills Match** (50%): Semantic + keyword matching
- **Experience Match** (30%): Years + relevance
- **Education Match** (20%): Degree level + field relevance

### ATS Score (50% weight)
- **Format Score** (25%): File type compatibility
- **Structure Score** (25%): Standard sections present
- **Keyword Score** (25%): Skill density
- **Readability Score** (25%): Formatting quality

### Final Score
```
Final Score = (Match Score × 0.5) + (ATS Score × 0.5)
```

With LLM evaluation enabled, the LLM can adjust the final score based on holistic assessment.

## 🧪 Testing

### Test Enhanced Parser

```python
from app.utils.enhanced_resume_parser import parse_resume_enhanced

result = parse_resume_enhanced(
    file_path="path/to/resume.pdf",
    filename="resume.pdf"
)

print(f"Skills: {result['parsed_skills']}")
print(f"ATS Score: {result['ats_score']}")
print(f"Breakdown: {result['ats_score_breakdown']}")
```

### Test Enhanced Scoring

```python
from app.services.enhanced_scoring_service import EnhancedScoringService

service = EnhancedScoringService()
score = await service.score_application_enhanced(
    db=db,
    application=application,
    use_llm_evaluation=True
)

print(f"Final Score: {score.final_score}")
print(f"Feedback: {score.ai_feedback}")
```

## 🔄 Integration Steps

### Option 1: Replace Existing Service

1. Backup current scoring service:
```bash
cp backend/app/services/scoring_service.py backend/app/services/scoring_service.py.backup
```

2. Update imports in your application:
```python
# Old
from app.services.scoring_service import ScoringService

# New
from app.services.enhanced_scoring_service import EnhancedScoringService as ScoringService
```

### Option 2: Gradual Migration

1. Use enhanced parser with existing scoring:
```python
from app.utils.enhanced_resume_parser import parse_resume_enhanced

# In your application processing
parsed_data = parse_resume_enhanced(file_path, filename)
application.parsed_skills = parsed_data['parsed_skills']
application.ats_score_breakdown = parsed_data['ats_score_breakdown']
```

2. Enable LLM evaluation selectively:
```python
# Use enhanced scoring for high-priority jobs
if job.priority == "high":
    score = await enhanced_service.score_application_enhanced(db, application)
else:
    score = await standard_service.score_application(db, application)
```

## 📝 Configuration Options

### Scoring Weights

Update in `backend/app/config.py`:

```python
# Scoring Configuration
match_score_weight: float = 0.5  # Weight for match score
ats_score_weight: float = 0.5    # Weight for ATS score
shortlist_threshold: int = 70    # Auto-select threshold
requalify_threshold: int = 60    # Review threshold
```

### LLM Parameters

Update in `backend/app/config.py`:

```python
# LLM Configuration
ollama_model: str = "resume-screener:latest"
llm_temperature: float = 0.2     # Lower = more consistent
llm_max_tokens: int = 500        # Response length
llm_timeout_seconds: int = 60    # Request timeout
```

## 🐛 Troubleshooting

### Issue: Model not found

```bash
# List available models
ollama list

# Pull base model if needed
ollama pull qwen2.5:3b-instruct

# Recreate custom model
python fine_tuning/fine_tune_model.py
```

### Issue: Poor JSON parsing

The custom model is optimized for JSON output. If you still have issues:

1. Check temperature (should be ≤ 0.3)
2. Verify stop tokens in Modelfile
3. Test with base model to compare

### Issue: Slow scoring

1. Reduce `llm_max_tokens` in config
2. Disable LLM evaluation for bulk processing:
```python
score = await service.score_application_enhanced(
    db=db,
    application=application,
    use_llm_evaluation=False  # Faster, rule-based only
)
```

## 📚 Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Ollama Modelfile Reference](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)
- [Resume Parsing Best Practices](https:/