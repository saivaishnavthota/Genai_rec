/**
 * Timecode utilities for video/audio processing
 */

export function formatTimecode(seconds: number | string): string {
  // Ensure we have a number
  const numSeconds = typeof seconds === 'string' ? Number(seconds) : seconds;
  if (isNaN(numSeconds) || !isFinite(numSeconds)) {
    return '0:00.000';
  }
  
  const hours = Math.floor(numSeconds / 3600);
  const minutes = Math.floor((numSeconds % 3600) / 60);
  const secs = Math.floor(numSeconds % 60);
  const millis = Math.floor((numSeconds % 1) * 1000);
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${millis.toString().padStart(3, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}.${millis.toString().padStart(3, '0')}`;
}

export function parseTimecode(timecode: string): number {
  const parts = timecode.split(':');
  if (parts.length === 3) {
    const hours = parseInt(parts[0], 10);
    const minutes = parseInt(parts[1], 10);
    const secParts = parts[2].split('.');
    const seconds = parseInt(secParts[0], 10);
    const millis = parseInt(secParts[1] || '0', 10);
    return hours * 3600 + minutes * 60 + seconds + millis / 1000;
  } else if (parts.length === 2) {
    const minutes = parseInt(parts[0], 10);
    const secParts = parts[1].split('.');
    const seconds = parseInt(secParts[0], 10);
    const millis = parseInt(secParts[1] || '0', 10);
    return minutes * 60 + seconds + millis / 1000;
  }
  return 0;
}

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

