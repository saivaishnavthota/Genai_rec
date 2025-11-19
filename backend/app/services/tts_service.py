"""Text-to-Speech service for converting interview questions to audio"""
import logging
from typing import Optional
import tempfile
import os
from gtts import gTTS
import io

logger = logging.getLogger(__name__)


class TTSService:
    """Service for converting text to speech"""

    def __init__(self):
        """Initialize TTS service"""
        self.language = 'en'
        self.tld = 'com'  # Top-level domain for accent (com = US, co.uk = UK, etc.)
        self.slow = False

    def text_to_speech(self, text: str, language: str = 'en', slow: bool = False) -> bytes:
        """
        Convert text to speech and return audio bytes

        Args:
            text: Text to convert to speech
            language: Language code (default: 'en')
            slow: Whether to speak slowly (default: False)

        Returns:
            Audio bytes in MP3 format
        """
        try:
            # Create gTTS object
            tts = gTTS(text=text, lang=language, slow=slow, tld=self.tld)

            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            return audio_buffer.read()

        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            raise

    def text_to_speech_file(self, text: str, output_path: str, language: str = 'en', slow: bool = False) -> str:
        """
        Convert text to speech and save to file

        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            language: Language code (default: 'en')
            slow: Whether to speak slowly (default: False)

        Returns:
            Path to saved audio file
        """
        try:
            # Create gTTS object
            tts = gTTS(text=text, lang=language, slow=slow, tld=self.tld)

            # Save to file
            tts.save(output_path)

            logger.info(f"Saved TTS audio to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error saving speech to file: {e}")
            raise

    def batch_text_to_speech(self, texts: list[str], language: str = 'en') -> list[bytes]:
        """
        Convert multiple texts to speech

        Args:
            texts: List of texts to convert
            language: Language code (default: 'en')

        Returns:
            List of audio bytes
        """
        audio_list = []

        for i, text in enumerate(texts):
            try:
                audio_bytes = self.text_to_speech(text, language=language)
                audio_list.append(audio_bytes)
                logger.info(f"Generated audio {i+1}/{len(texts)}")
            except Exception as e:
                logger.error(f"Error generating audio for text {i+1}: {e}")
                audio_list.append(b'')  # Empty bytes on error

        return audio_list
