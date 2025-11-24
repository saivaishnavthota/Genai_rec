import { useState, useEffect, useCallback } from 'react';

export interface MediaDevice {
  deviceId: string;
  label: string;
  kind: MediaDeviceKind;
}

export interface UseMediaDevicesReturn {
  videoDevices: MediaDevice[];
  audioDevices: MediaDevice[];
  selectedVideoDeviceId: string | null;
  selectedAudioDeviceId: string | null;
  stream: MediaStream | null;
  error: string | null;
  isLoading: boolean;
  setSelectedVideoDevice: (deviceId: string) => void;
  setSelectedAudioDevice: (deviceId: string) => void;
  startStream: () => Promise<void>;
  stopStream: () => void;
  refreshDevices: () => Promise<void>;
}

export function useMediaDevices(): UseMediaDevicesReturn {
  const [videoDevices, setVideoDevices] = useState<MediaDevice[]>([]);
  const [audioDevices, setAudioDevices] = useState<MediaDevice[]>([]);
  const [selectedVideoDeviceId, setSelectedVideoDeviceId] = useState<string | null>(null);
  const [selectedAudioDeviceId, setSelectedAudioDeviceId] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const refreshDevices = useCallback(async () => {
    try {
      // Check if mediaDevices API is available (requires HTTPS or localhost)
      if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
        const isSecureContext = window.isSecureContext || window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        if (!isSecureContext) {
          setError('Camera and microphone access requires HTTPS. Please access this page via HTTPS (https://) instead of HTTP.');
          return;
        }
        setError('MediaDevices API is not available in this browser. Please use a modern browser that supports camera/microphone access.');
        return;
      }

      // Request permission first to get device labels (labels are empty until permission is granted)
      try {
        await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      } catch (permErr: any) {
        // Permission denied is okay, we just need permission for labels
        if (permErr.name !== 'NotAllowedError' && permErr.name !== 'PermissionDeniedError') {
          throw permErr;
        }
      }

      const devices = await navigator.mediaDevices.enumerateDevices();
      const videos = devices
        .filter((d) => d.kind === 'videoinput')
        .map((d) => ({ deviceId: d.deviceId, label: d.label || `Camera ${d.deviceId.slice(0, 8)}`, kind: d.kind as MediaDeviceKind }));
      const audios = devices
        .filter((d) => d.kind === 'audioinput')
        .map((d) => ({ deviceId: d.deviceId, label: d.label || `Microphone ${d.deviceId.slice(0, 8)}`, kind: d.kind as MediaDeviceKind }));

      setVideoDevices(videos);
      setAudioDevices(audios);

      // Auto-select first device if none selected
      if (!selectedVideoDeviceId && videos.length > 0) {
        setSelectedVideoDeviceId(videos[0].deviceId);
      }
      if (!selectedAudioDeviceId && audios.length > 0) {
        setSelectedAudioDeviceId(audios[0].deviceId);
      }
      
      // Clear error if devices were found
      if (videos.length > 0 || audios.length > 0) {
        setError(null);
      }
    } catch (err: any) {
      const errorMessage = err?.message || String(err);
      setError(`Failed to enumerate devices: ${errorMessage}`);
    }
  }, [selectedVideoDeviceId, selectedAudioDeviceId]);

  useEffect(() => {
    refreshDevices();
  }, [refreshDevices]);

  const startStream = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Check if mediaDevices API is available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        const isSecureContext = window.isSecureContext || window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        if (!isSecureContext) {
          setError('Camera and microphone access requires HTTPS. Please access this page via HTTPS (https://) instead of HTTP.');
          return;
        }
        setError('MediaDevices API is not available in this browser. Please use a modern browser that supports camera/microphone access.');
        return;
      }

      const constraints: MediaStreamConstraints = {
        video: selectedVideoDeviceId
          ? { deviceId: { exact: selectedVideoDeviceId } }
          : true,
        audio: selectedAudioDeviceId
          ? { deviceId: { exact: selectedAudioDeviceId } }
          : true,
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(mediaStream);
      setError(null); // Clear any previous errors
    } catch (err: any) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Camera/microphone permission denied. Please allow access and try again.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setError('No camera or microphone found. Please connect a device and try again.');
      } else {
        setError(`Failed to access media devices: ${err.message || err}`);
      }
    } finally {
      setIsLoading(false);
    }
  }, [selectedVideoDeviceId, selectedAudioDeviceId]);

  const stopStream = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  }, [stream]);

  return {
    videoDevices,
    audioDevices,
    selectedVideoDeviceId,
    selectedAudioDeviceId,
    stream,
    error,
    isLoading,
    setSelectedVideoDevice: setSelectedVideoDeviceId,
    setSelectedAudioDevice: setSelectedAudioDeviceId,
    startStream,
    stopStream,
    refreshDevices,
  };
}

