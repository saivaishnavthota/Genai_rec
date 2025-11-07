"""Timecode utilities for video/audio processing"""
from typing import Union


class Timecode:
    """Timecode utilities for converting between formats"""
    
    @staticmethod
    def seconds_to_hms(seconds: float) -> str:
        """Convert seconds to HH:MM:SS.mmm format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    @staticmethod
    def hms_to_seconds(hms: str) -> float:
        """Convert HH:MM:SS.mmm format to seconds"""
        parts = hms.split(":")
        if len(parts) != 3:
            raise ValueError("Invalid timecode format")
        
        hours = int(parts[0])
        minutes = int(parts[1])
        sec_parts = parts[2].split(".")
        seconds = int(sec_parts[0])
        millis = int(sec_parts[1]) if len(sec_parts) > 1 else 0
        
        return hours * 3600 + minutes * 60 + seconds + millis / 1000.0
    
    @staticmethod
    def format_for_ffmpeg(seconds: float) -> str:
        """Format seconds for ffmpeg duration/seek parameters"""
        return Timecode.seconds_to_hms(seconds)
    
    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max"""
        return max(min_val, min(max_val, value))

