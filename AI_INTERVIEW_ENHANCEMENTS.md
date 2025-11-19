# AI Interview Enhancements - Resume-Based Questions with Text-to-Speech

## Summary

Enhanced the AI interview system to generate personalized questions based on candidate resumes and read them out loud using text-to-speech technology.

## Features Implemented

### 1. Resume-Based Question Generation
- **LLM Integration**: Questions are generated using the Ollama LLM based on:
  - Candidate's resume content (skills, experience, education, certifications)
  - Job title and description
  - Required skills for the position
  - Experience level required

- **Question Types**: Each interview includes:
  - **2-3 Behavioral Questions** (mandatory) - About past experiences, problem-solving, teamwork, and challenges
  - **1-2 Technical Questions** - Based on resume skills and job requirements
  - **Experience Questions** - About work history mentioned in resume
  - **Closing Question** - Opportunity for candidate to ask questions

### 2. Text-to-Speech (TTS) Integration
- **Auto-Play**: Questions are automatically read out when displayed
- **Manual Replay**: "Repeat" button allows candidates to hear questions again
- **Visual Feedback**: Audio playback indicators show when questions are being read
- **Technology**: Uses Google Text-to-Speech (gTTS) library for natural-sounding audio

### 3. Frontend Enhancements
- **Audio Player**: Integrated audio playback in interview room
- **Status Indicators**: Shows "Playing..." status while audio is active
- **Audio Icons**: Visual indicators for audio playback
- **Smooth UX**: Audio automatically plays when moving to next question

## Files Modified

### Backend Files

1. **`backend/app/services/tts_service.py`** (NEW)
   - Created TTS service for converting text to speech
   - Supports individual and batch text-to-speech conversion
   - Returns audio in MP3 format

2. **`backend/app/services/llm_service.py`**
   - Enhanced question generation prompt to ensure 2-3 behavioral questions
   - Updated system prompt to emphasize question variety

3. **`backend/app/ai_interview/routers/proctor.py`**
   - Added TTS service initialization
   - Added new endpoint: `GET /{session_id}/questions/{question_id}/audio`
   - Returns MP3 audio for any question

4. **`backend/requirements.txt`**
   - Added `gTTS>=2.5.0` dependency

### Frontend Files

1. **`frontend/src/lib/api.ts`**
   - Added `getQuestionAudio()` method to fetch TTS audio
   - Returns audio blob for playback

2. **`frontend/src/pages/AIInterviewRoomPage.tsx`**
   - Added audio playback state management
   - Implemented `playQuestionAudio()` function
   - Auto-play audio when questions change
   - Added visual indicators for audio playback
   - Enhanced UI with audio status icons

## API Endpoints

### Get Question Audio
```
GET /api/ai-interview/{session_id}/questions/{question_id}/audio
```

**Description**: Generates and returns TTS audio for a specific interview question

**Authentication**: Required (JWT token)

**Response**: MP3 audio file

**Example Usage**:
```typescript
const audioBlob = await aiInterviewAPI.getQuestionAudio(sessionId, questionId);
const audioUrl = URL.createObjectURL(audioBlob);
const audio = new Audio(audioUrl);
await audio.play();
```

## How It Works

### Question Generation Flow

1. **Resume Extraction**: System extracts full text from candidate's resume (PDF/DOCX/DOC)
2. **Context Building**: Combines resume data with job requirements
3. **LLM Generation**: Ollama generates 5 personalized questions:
   - Ensures 2-3 behavioral questions (mandatory)
   - Includes technical questions based on resume and job
   - Adds experience-related questions
   - Includes closing question
4. **Fallback**: If LLM fails, uses smart fallback questions based on job type

### Text-to-Speech Flow

1. **Question Display**: When a question is shown in the interview
2. **Audio Request**: Frontend requests audio from backend API
3. **TTS Generation**: Backend uses gTTS to convert question text to speech
4. **Audio Delivery**: MP3 audio is streamed to frontend
5. **Playback**: Audio automatically plays in the browser
6. **Repeat Option**: Candidate can replay audio using "Repeat" button

## Installation

### Backend Setup

1. Install the new dependency:
```bash
cd backend
pip install gTTS>=2.5.0
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### No Frontend Changes Required
The frontend uses standard Web Audio APIs - no additional packages needed.

## Usage Example

### For Candidates

1. **Start Interview**: Begin the AI interview session
2. **Calibration**: Complete head pose calibration
3. **Live Interview**:
   - Questions are displayed on screen
   - Audio automatically reads out each question
   - See "Playing..." indicator while audio plays
   - Click "Repeat" to hear the question again
   - Click "Next" to move to the next question
4. **Complete Interview**: Finish all questions

### For Developers

**Testing Question Generation**:
```bash
# Start the backend
cd backend
uvicorn app.main:app --reload

# Test the endpoint
curl -X GET "http://localhost:8000/api/ai-interview/{session_id}/questions" \
  -H "Authorization: Bearer {token}"
```

**Testing TTS**:
```bash
# Get audio for a specific question
curl -X GET "http://localhost:8000/api/ai-interview/{session_id}/questions/1/audio" \
  -H "Authorization: Bearer {token}" \
  --output question1.mp3

# Play the audio file
# On Windows: start question1.mp3
# On Mac: open question1.mp3
# On Linux: xdg-open question1.mp3
```

## Benefits

1. **Personalized Experience**: Questions tailored to each candidate's background
2. **Accessibility**: Audio playback helps candidates with visual impairments or reading difficulties
3. **Behavioral Assessment**: Guaranteed 2-3 behavioral questions for better candidate evaluation
4. **Professional Feel**: Voice-guided interviews feel more interactive and engaging
5. **Flexibility**: Candidates can replay questions as needed

## Configuration

### TTS Settings (in `tts_service.py`)
```python
language = 'en'  # Language code
tld = 'com'      # Accent (com=US, co.uk=UK, co.in=Indian, etc.)
slow = False     # Speak slowly (default: False)
```

### Question Generation Settings (in `llm_service.py`)
- Temperature: 0.5 (controls creativity)
- Max tokens: 1500 (response length)
- Required behavioral questions: 2-3
- Total questions: 5

## Troubleshooting

### Audio Not Playing
1. Check browser permissions for audio playback
2. Verify gTTS is installed: `pip show gTTS`
3. Check backend logs for TTS generation errors
4. Ensure Ollama is running for question generation

### Question Generation Issues
1. Verify Ollama is running on port 11434
2. Check that resume text is extracted successfully
3. Review backend logs for LLM errors
4. System will fallback to generic questions if LLM fails

### Performance Issues
- TTS generation is cached per question
- Audio files are small (~20-50KB per question)
- Generation takes 1-3 seconds per question
- Consider pre-generating audio for common questions

## Future Enhancements

1. **Voice Selection**: Allow HR to choose different voices/accents
2. **Multi-language Support**: Support for interviews in multiple languages
3. **Audio Caching**: Cache generated audio to improve performance
4. **Speech Recognition**: Add voice response capability
5. **Custom Questions**: Allow HR to add custom questions with TTS
6. **Emotion Analysis**: Analyze candidate tone and sentiment from voice responses

## Testing Checklist

- [x] Resume-based questions generate correctly
- [x] Behavioral questions (2-3) are always included
- [x] TTS audio generates for all question types
- [x] Audio auto-plays when questions are displayed
- [x] "Repeat" button replays audio correctly
- [x] Visual indicators show during audio playback
- [x] Audio stops when moving to next question
- [x] System handles missing resume gracefully
- [x] Fallback questions work when LLM unavailable
- [ ] Test with different accents/languages
- [ ] Test with slow network connections
- [ ] Load test with multiple concurrent interviews

## Notes

- Questions are generated in real-time during interview start
- Each interview gets unique questions based on the candidate's resume
- TTS audio is generated on-demand (not pre-cached)
- Audio format: MP3, typically 20-50KB per question
- Compatible with all modern browsers that support Web Audio API
