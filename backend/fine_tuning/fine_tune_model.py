"""
Fine-tune Ollama model for resume screening and ATS scoring

This script provides instructions and utilities for fine-tuning your Ollama model
using the generated training data.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any


def load_training_data(file_path: str) -> List[Dict[str, Any]]:
    """Load training data from JSONL file"""
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data


def create_modelfile(base_model: str, training_data_path: str, output_path: str):
    """
    Create a Modelfile for Ollama fine-tuning
    
    Note: Ollama doesn't support traditional fine-tuning yet, but you can:
    1. Create a custom model with system prompts and examples
    2. Use the model with few-shot learning
    3. Wait for Ollama to support fine-tuning (coming soon)
    """
    
    # Load a few examples for few-shot learning
    training_data = load_training_data(training_data_path)
    few_shot_examples = training_data[:5]  # Use first 5 examples
    
    # Create system prompt with examples
    system_prompt = """You are an expert technical recruiter specializing in resume evaluation and ATS scoring.

Your task is to evaluate candidates objectively based on:
1. Skill match with job requirements
2. Relevant work experience
3. Educational background
4. Resume quality and ATS compatibility

Always respond with valid JSON in this exact format:
{
  "overall_score": <0-100>,
  "confidence": <"high"|"medium"|"low">,
  "key_strengths": ["strength1", "strength2", "strength3"],
  "key_gaps": ["gap1", "gap2", "gap3"],
  "recommendation": "<hire|interview|reject>",
  "brief_summary": "<2-3 sentences>"
}

Scoring guidelines:
- 80-100: Excellent match, strong hire recommendation
- 70-79: Good match, recommend interview
- 60-69: Average match, consider for interview
- 40-59: Below average, likely reject
- 0-39: Poor match, reject

Here are some examples of proper evaluations:
"""
    
    # Add few-shot examples to system prompt
    for i, example in enumerate(few_shot_examples[:3], 1):
        user_msg = next(m['content'] for m in example['messages'] if m['role'] == 'user')
        assistant_msg = next(m['content'] for m in example['messages'] if m['role'] == 'assistant')
        
        system_prompt += f"\n\nExample {i}:\nUser: {user_msg[:200]}...\nAssistant: {assistant_msg[:200]}..."
    
    # Create Modelfile
    modelfile_content = f"""FROM {base_model}

# Set the system prompt with examples
SYSTEM \"\"\"
{system_prompt}
\"\"\"

# Set parameters for better JSON generation
PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_predict 500

# Set stop tokens
PARAMETER stop "<|im_end|>"
PARAMETER stop "</s>"
"""
    
    # Save Modelfile
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(modelfile_content)
    
    print(f"✅ Created Modelfile at: {output_file}")
    return output_file


def create_custom_model(modelfile_path: str, model_name: str):
    """Create a custom Ollama model from Modelfile"""
    try:
        print(f"\n🚀 Creating custom Ollama model: {model_name}")
        print(f"📁 Using Modelfile: {modelfile_path}")
        
        # Run ollama create command
        result = subprocess.run(
            ["ollama", "create", model_name, "-f", modelfile_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully created model: {model_name}")
            print(f"\n📝 To use this model, update your .env file:")
            print(f"   OLLAMA_MODEL={model_name}")
            return True
        else:
            print(f"❌ Error creating model:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ Ollama CLI not found. Please install Ollama first:")
        print("   https://ollama.ai/download")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_custom_model(model_name: str):
    """Test the custom model with a sample evaluation"""
    test_prompt = """Evaluate this candidate for the Senior Software Engineer position.

JOB REQUIREMENTS:
- Title: Senior Software Engineer
- Required Skills: Python, Django, PostgreSQL, Docker, AWS, REST API, Git
- Experience: 5+ years
- Education: Bachelor's in Computer Science or related field

CANDIDATE PROFILE:
- Skills: Python, Django, Flask, PostgreSQL, Docker, Git, Agile
- Matched Skills: Python, Django, PostgreSQL, Docker, Git
- Missing Skills: AWS, REST API
- Experience: 6 years
- Education: Bachelor's in Computer Science

PRELIMINARY SCORES:
- Skills Match: 71.4%
- Experience Match: 90.0%
- Education Match: 70%
- ATS Score: 85%

Provide a JSON response with your evaluation."""

    try:
        print(f"\n🧪 Testing model: {model_name}")
        print("📤 Sending test prompt...")
        
        # Create a temporary file with the prompt
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_prompt)
            prompt_file = f.name
        
        # Run ollama run command
        result = subprocess.run(
            ["ollama", "run", model_name],
            input=test_prompt,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("\n📥 Model response:")
            print("=" * 80)
            print(result.stdout)
            print("=" * 80)
            
            # Try to parse as JSON
            try:
                response_text = result.stdout.strip()
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    parsed = json.loads(json_text)
                    print("\n✅ Valid JSON response!")
                    print(f"   Overall Score: {parsed.get('overall_score')}")
                    print(f"   Recommendation: {parsed.get('recommendation')}")
                else:
                    print("\n⚠️  Response is not valid JSON")
            except json.JSONDecodeError:
                print("\n⚠️  Could not parse response as JSON")
        else:
            print(f"❌ Error testing model:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏱️  Test timed out after 60 seconds")
    except Exception as e:
        print(f"❌ Error testing model: {e}")


def main():
    print("🎯 Ollama Model Fine-Tuning for Resume Screening")
    print("=" * 80)
    
    # Configuration
    base_model = "qwen2.5:3b-instruct"  # Your current model
    custom_model_name = "resume-screener:latest"
    training_data_path = "backend/fine_tuning/data/training_data.jsonl"
    modelfile_path = "backend/fine_tuning/Modelfile"
    
    # Check if training data exists
    if not Path(training_data_path).exists():
        print(f"❌ Training data not found at: {training_data_path}")
        print("   Please run: python backend/fine_tuning/generate_training_data.py")
        return
    
    print(f"\n📊 Configuration:")
    print(f"   Base Model: {base_model}")
    print(f"   Custom Model: {custom_model_name}")
    print(f"   Training Data: {training_data_path}")
    
    # Step 1: Create Modelfile
    print(f"\n📝 Step 1: Creating Modelfile...")
    modelfile = create_modelfile(base_model, training_data_path, modelfile_path)
    
    # Step 2: Create custom model
    print(f"\n🔨 Step 2: Creating custom Ollama model...")
    success = create_custom_model(str(modelfile), custom_model_name)
    
    if success:
        # Step 3: Test the model
        print(f"\n🧪 Step 3: Testing custom model...")
        test_custom_model(custom_model_name)
        
        print(f"\n✅ Fine-tuning complete!")
        print(f"\n📝 Next steps:")
        print(f"1. Update your .env file:")
        print(f"   OLLAMA_MODEL={custom_model_name}")
        print(f"2. Restart your backend service")
        print(f"3. Test the enhanced scoring with real resumes")
    else:
        print(f"\n❌ Fine-tuning failed. Please check the errors above.")
        print(f"\n💡 Alternative approach:")
        print(f"   Since Ollama doesn't support full fine-tuning yet, you can:")
        print(f"   1. Use the enhanced scoring service with better prompts")
        print(f"   2. Use few-shot learning with examples in prompts")
        print(f"   3. Wait for Ollama to add fine-tuning support")


if __name__ == "__main__":
    main()
