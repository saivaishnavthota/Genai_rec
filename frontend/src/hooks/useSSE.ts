import { useState, useEffect, useRef, useCallback } from 'react';
import { Flag } from '../lib/api';
import config from '../utils/config';

const API_BASE_URL = config.apiUrl || 'http://localhost:8000';

export interface UseSSEReturn {
  flags: Flag[];
  isConnected: boolean;
  error: string | null;
  connect: (sessionId: number) => void;
  disconnect: () => void;
}

export function useSSE(): UseSSEReturn {
  const [flags, setFlags] = useState<Flag[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);

  const connect = useCallback((sessionId: number) => {
    try {
      setError(null);
      
      // Use polling for flags (SSE/WebSocket can be added later)
      const token = localStorage.getItem('token');
      
      const pollFlags = async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/api/ai-interview/${sessionId}/flags`, {
            headers: token ? {
              'Authorization': `Bearer ${token}`,
            } : {},
          });
          if (response.ok) {
            const fetchedFlags = await response.json();
            setFlags(fetchedFlags);
            setIsConnected(true);
          }
        } catch (err) {
          console.error('Failed to fetch flags:', err);
          setError('Failed to fetch flags');
          setIsConnected(false);
        }
      };
      
      // Initial fetch
      pollFlags();
      
      // Poll every 2 seconds
      const pollInterval = window.setInterval(pollFlags, 2000);
      intervalRef.current = pollInterval;
      
      setIsConnected(true);
    } catch (err: any) {
      setError(`Failed to connect: ${err.message}`);
      setIsConnected(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsConnected(false);
    setFlags([]);
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    flags,
    isConnected,
    error,
    connect,
    disconnect,
  };
}
