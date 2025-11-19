import { useState, useEffect, useRef, useCallback } from 'react';
import { WebRTCManager, WebRTCStats } from '../lib/webrtc';
import config from '../utils/config';

const API_BASE_URL = config.apiUrl || 'http://localhost:8000';

export interface UseWebRTCReturn {
  connectionState: string;
  stats: WebRTCStats | null;
  error: string | null;
  connect: (stream: MediaStream, sessionId: number, webrtcToken?: string) => Promise<void>;
  disconnect: () => void;
  sendAudioChunk: (chunk: Float32Array | Int16Array) => void;
}

export function useWebRTC(): UseWebRTCReturn {
  const [connectionState, setConnectionState] = useState<string>('disconnected');
  const [stats, setStats] = useState<WebRTCStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const managerRef = useRef<WebRTCManager | null>(null);

  const connect = useCallback(async (stream: MediaStream, sessionId: number, webrtcToken?: string) => {
    try {
      setError(null);
      setConnectionState('connecting');

      const wsUrl = webrtcToken
        ? `${API_BASE_URL.replace('http', 'ws')}/api/ai-interview/${sessionId}/stream?token=${webrtcToken}`
        : `${API_BASE_URL.replace('http', 'ws')}/api/ai-interview/${sessionId}/stream`;

      const manager = new WebRTCManager(wsUrl, (state) => {
        setConnectionState(state);
      });

      manager.onStatsUpdate = (newStats) => {
        setStats(newStats);
      };

      await manager.initialize(stream);
      managerRef.current = manager;
    } catch (err: any) {
      setError(`WebRTC connection failed: ${err.message}`);
      setConnectionState('failed');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (managerRef.current) {
      managerRef.current.disconnect();
      managerRef.current = null;
    }
    setConnectionState('disconnected');
    setStats(null);
  }, []);

  const sendAudioChunk = useCallback((chunk: Float32Array | Int16Array) => {
    if (managerRef.current) {
      managerRef.current.sendAudioChunk(chunk);
    }
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connectionState,
    stats,
    error,
    connect,
    disconnect,
    sendAudioChunk,
  };
}

