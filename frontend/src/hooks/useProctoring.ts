import { useState, useEffect, useCallback, useRef } from 'react';
import { aiInterviewAPI, ClientEvent } from '../lib/api';

const TELEMETRY_RATE = 2; // Hz for tab/phone detection (less frequent than head pose)
const TELEMETRY_INTERVAL = 1000 / TELEMETRY_RATE;
const BATCH_SIZE = 10;

export interface UseProctoringReturn {
  isTracking: boolean;
  startTracking: (sessionId: number, sessionStartTime: number) => void;
  stopTracking: () => void;
}

export function useProctoring(): UseProctoringReturn {
  const [isTracking, setIsTracking] = useState(false);
  
  const trackingRef = useRef<{
    sessionId: number | null;
    sessionStartTime: number;
    intervalId: number | null;
    eventBuffer: ClientEvent[];
    lastSendTime: number;
    tabVisible: boolean;
    lastTabVisibilityChange: number;
    visibilityHandler: (() => void) | null;
  }>({
    sessionId: null,
    sessionStartTime: 0,
    intervalId: null,
    eventBuffer: [],
    lastSendTime: 0,
    tabVisible: true,
    lastTabVisibilityChange: 0,
    visibilityHandler: null,
  });

  const sendEventsBatch = useCallback(async () => {
    const { sessionId, eventBuffer } = trackingRef.current;
    
    if (eventBuffer.length === 0 || !sessionId) return;

    try {
      await aiInterviewAPI.postClientEvents(sessionId, [...eventBuffer]);
      trackingRef.current.eventBuffer = [];
      trackingRef.current.lastSendTime = Date.now();
    } catch (err: any) {
      console.error('Failed to send proctoring events:', err);
    }
  }, []);

  const detectPhone = useCallback(async (): Promise<boolean> => {
    // Basic phone detection using device orientation and motion sensors
    // This is a simplified approach - in production, you'd use computer vision
    try {
      // Check if device orientation API is available
      if (window.DeviceOrientationEvent) {
        // Device orientation can indicate phone usage
        // This is a heuristic - not perfect but better than nothing
        return false; // Placeholder - would need more sophisticated detection
      }
    } catch (err) {
      console.warn('Phone detection not available:', err);
    }
    return false;
  }, []);

  const checkTabVisibility = useCallback(() => {
    const isVisible = !document.hidden;
    const now = Date.now();
    
    if (isVisible !== trackingRef.current.tabVisible) {
      trackingRef.current.tabVisible = isVisible;
      trackingRef.current.lastTabVisibilityChange = now;
    }
    
    return isVisible;
  }, []);

  const processProctoringCheck = useCallback(async () => {
    const { sessionId, sessionStartTime } = trackingRef.current;
    
    if (!sessionId || !isTracking) return;

    try {
      const timestamp = (Date.now() - sessionStartTime) / 1000;
      
      // Check tab visibility (send continuously to track duration)
      const tabVisible = checkTabVisibility();
      
      // Always send tab_switch event to track duration correctly
      const tabEvent: ClientEvent = {
        event_type: 'tab_switch',
        timestamp,
        confidence: tabVisible ? 0.0 : 0.9, // High confidence when tab is hidden
        tab_visible: tabVisible,
        metadata: {
          tab_visible: tabVisible,
          visibility_change_time: trackingRef.current.lastTabVisibilityChange,
        },
      };
      trackingRef.current.eventBuffer.push(tabEvent);

      // Phone detection (simplified)
      // TODO: Implement proper phone detection using computer vision (YOLO or similar)
      // For now, this is a placeholder that always returns false
      // In production, you would analyze video frames to detect phones
      const phoneDetected = await detectPhone();
      
      // Always send phone event to track duration correctly
      // When phone is detected, send high confidence; otherwise send 0
      const phoneEvent: ClientEvent = {
        event_type: 'phone',
        timestamp,
        confidence: phoneDetected ? 0.7 : 0.0, // Medium confidence when phone detected
        phone_detected: phoneDetected,
        metadata: {
          phone_detected: phoneDetected,
        },
      };
      trackingRef.current.eventBuffer.push(phoneEvent);

      // Send events in batches
      if (trackingRef.current.eventBuffer.length >= BATCH_SIZE) {
        await sendEventsBatch();
      }
    } catch (err: any) {
      console.error('Proctoring check error:', err);
    }
  }, [isTracking, checkTabVisibility, detectPhone, sendEventsBatch]);

  const startTracking = useCallback((sessionId: number, sessionStartTime: number) => {
    trackingRef.current.sessionId = sessionId;
    trackingRef.current.sessionStartTime = sessionStartTime;
    trackingRef.current.tabVisible = !document.hidden;
    trackingRef.current.lastTabVisibilityChange = Date.now();
    
    // Set up visibility change listener
    const handleVisibilityChange = () => {
      checkTabVisibility();
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    trackingRef.current.visibilityHandler = handleVisibilityChange;
    
    // Start interval for proctoring checks
    const intervalId = window.setInterval(() => {
      processProctoringCheck();
    }, TELEMETRY_INTERVAL);
    
    trackingRef.current.intervalId = intervalId;
    setIsTracking(true);
  }, [processProctoringCheck, checkTabVisibility]);

  const stopTracking = useCallback(() => {
    if (trackingRef.current.intervalId !== null) {
      clearInterval(trackingRef.current.intervalId);
      trackingRef.current.intervalId = null;
    }
    
    // Remove visibility change listener
    if (trackingRef.current.visibilityHandler) {
      document.removeEventListener('visibilitychange', trackingRef.current.visibilityHandler);
      trackingRef.current.visibilityHandler = null;
    }
    
    // Send any remaining events
    sendEventsBatch();
    
    setIsTracking(false);
    trackingRef.current.sessionId = null;
    trackingRef.current.eventBuffer = [];
  }, [sendEventsBatch]);

  useEffect(() => {
    return () => {
      stopTracking();
    };
  }, [stopTracking]);

  return {
    isTracking,
    startTracking,
    stopTracking,
  };
}

