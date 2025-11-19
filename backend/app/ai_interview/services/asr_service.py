"""ASR service using faster-whisper"""
import logging
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from faster_whisper import WhisperModel
from ...config import settings

logger = logging.getLogger(__name__)


class ASRService:
    """Automatic Speech Recognition service using Whisper"""
    
    def __init__(self):
        """Initialize Whisper model"""
        import os
        self.model_size = settings.whisper_model_size
        self.device = settings.whisper_device
        self.compute_type = settings.whisper_compute_type
        self.enable_diarization = settings.enable_diarization
        
        # Set cache directory to a writable location (Docker-friendly)
        cache_dir = os.getenv('HF_HOME', '/tmp/hf_cache')
        os.makedirs(cache_dir, exist_ok=True)
        os.environ['HF_HOME'] = cache_dir
        os.environ['TRANSFORMERS_CACHE'] = cache_dir
        os.environ['HF_HUB_CACHE'] = cache_dir
        
        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=cache_dir  # Use writable cache directory
            )
            logger.info(f"Initialized Whisper model: {self.model_size} on {self.device} (cache: {cache_dir})")
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {e}", exc_info=True)
            self.model = None
    
    async def transcribe_streaming(
        self,
        audio_chunk: bytes,
        sample_rate: int = 16000
    ) -> Optional[str]:
        """
        Transcribe a single audio chunk (interim results)
        
        Args:
            audio_chunk: Audio bytes (16kHz PCM)
            sample_rate: Sample rate (default 16kHz)
            
        Returns:
            Interim transcript text or None
        """
        if not self.model:
            return None
        
        try:
            # Convert bytes to numpy array (simplified - actual implementation needs proper conversion)
            # For now, return None for streaming (would need proper buffering)
            return None
        except Exception as e:
            logger.error(f"Streaming transcription error: {e}")
            return None
    
    async def transcribe_file(
        self,
        audio_path: str,
        language: Optional[str] = None,
        with_timestamps: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe audio file (final transcription)
        
        Args:
            audio_path: Path to audio file
            language: Optional language code (e.g., 'en')
            with_timestamps: Include word-level timestamps
            
        Returns:
            Transcript dictionary with words and timestamps
        """
        if not self.model:
            raise RuntimeError("Whisper model not initialized")
        
        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                word_timestamps=with_timestamps,
                vad_filter=True,  # Voice Activity Detection
                beam_size=5
            )
            
            # Collect segments
            transcript_segments = []
            words = []
            
            for segment in segments:
                segment_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                }
                transcript_segments.append(segment_data)
                
                # Collect word-level timestamps if available
                if hasattr(segment, 'words') and segment.words:
                    for word in segment.words:
                        words.append({
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability
                        })
            
            return {
                "language": info.language,
                "language_probability": info.language_probability,
                "segments": transcript_segments,
                "words": words if with_timestamps else [],
                "text": " ".join([s["text"] for s in transcript_segments])
            }
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise RuntimeError(f"Failed to transcribe audio: {e}")
    
    async def transcribe_with_diarization(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transcribe with speaker diarization (optional)
        
        Args:
            audio_path: Path to audio file
            num_speakers: Optional number of speakers
            
        Returns:
            Transcript with speaker labels
        """
        if not self.enable_diarization:
            # Fallback to regular transcription
            return await self.transcribe_file(audio_path)
        
        # Diarization would require pyannote.audio or similar
        # For now, return regular transcription
        logger.warning("Diarization requested but not fully implemented")
        return await self.transcribe_file(audio_path)

