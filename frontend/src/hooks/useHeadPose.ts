import { useState, useEffect, useRef, useCallback } from 'react';
// Use face-api.js instead of MediaPipe (more reliable, no Docker issues)
import { detectFaces, calculateHeadPose, initializeFaceDetection } from '../lib/faceDetection';
import { HeadPose } from '../lib/headpose';
import { aiInterviewAPI, ClientEvent } from '../lib/api';

export interface UseHeadPoseReturn {
  headPose: HeadPose | null;
  facePresent: boolean;
  faceCount: number;
  confidence: number;
  error: string | null;
  startTracking: (video: HTMLVideoElement, sessionId: number, sessionStartTime: number) => void;
  stopTracking: () => void;
}

const TELEMETRY_RATE = 8; // Hz
const TELEMETRY_INTERVAL = 1000 / TELEMETRY_RATE;
const BATCH_SIZE = 10; // Send events in batches

export function useHeadPose(): UseHeadPoseReturn {
  const [headPose, setHeadPose] = useState<HeadPose | null>(null);
  const [facePresent, setFacePresent] = useState(false);
  const [faceCount, setFaceCount] = useState(0);
  const [confidence, setConfidence] = useState(0);
  const [error, setError] = useState<string | null>(null);
  
  const trackingRef = useRef<{
    video: HTMLVideoElement | null;
    sessionId: number | null;
    sessionStartTime: number;
    intervalId: number | null;
    eventBuffer: ClientEvent[];
    lastSendTime: number;
  }>({
    video: null,
    sessionId: null,
    sessionStartTime: 0,
    intervalId: null,
    eventBuffer: [],
    lastSendTime: 0,
  });

  const sendEventsBatch = useCallback(async () => {
    const { sessionId, eventBuffer } = trackingRef.current;
    
    if (eventBuffer.length === 0 || !sessionId) return;

    try {
      await aiInterviewAPI.postClientEvents(sessionId, [...eventBuffer]);
      trackingRef.current.eventBuffer = [];
      trackingRef.current.lastSendTime = Date.now();
    } catch (err: any) {
      console.error('Failed to send client events:', err);
    }
  }, []);

  const processFrame = useCallback(async () => {
    const { video, sessionId, sessionStartTime } = trackingRef.current;
    
    if (!video || !sessionId) {
      if (!video) console.warn('No video element for head pose tracking');
      if (!sessionId) console.warn('No session ID for head pose tracking');
      return;
    }

    // Check if video is ready
    if (video.readyState < 2) {
      console.warn('Video not ready, readyState:', video.readyState);
      return; // Video not ready yet
    }

    // Check video dimensions
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      console.warn('Video has no dimensions:', video.videoWidth, 'x', video.videoHeight);
      return;
    }

    try {
      // Use video's current time for MediaPipe (it uses milliseconds internally)
      const timestamp = video.currentTime;
      const detection = await detectFaces(video, timestamp);
      
      if (!detection) {
        // No detection result - might be face detection not initialized
        console.warn('detectFaces returned null');
        return;
      }

        if (detection) {
        // Log detection status
        if (detection.faceCount === 0) {
          // Log occasionally when no face detected
          if (Math.random() < 0.1) { // Log 10% of the time
            console.log('No face detected in frame');
          }
        }
        setFacePresent(detection.faceCount > 0);
        setFaceCount(detection.faceCount);
        setConfidence(detection.confidence);

        // Calculate elapsed time since session start
        const elapsed = (Date.now() - sessionStartTime) / 1000;

        if (detection.landmarks.length > 0) {
          const pose = calculateHeadPose(detection.landmarks);
          
          if (pose) {
            const headPoseData: HeadPose = {
              yaw: pose.yaw,
              pitch: pose.pitch,
              roll: pose.roll,
              confidence: detection.confidence,
            };
            setHeadPose(headPoseData);

            // Add to event buffer
            const event: ClientEvent = {
              event_type: 'head_pose',
              timestamp,
              confidence: detection.confidence,
              yaw: pose.yaw,
              pitch: pose.pitch,
              roll: pose.roll,
              metadata: { faceCount: detection.faceCount },
            };
            trackingRef.current.eventBuffer.push(event);

            // Add face_present event
            const faceEvent: ClientEvent = {
              event_type: 'face_present',
              timestamp,
              confidence: detection.confidence,
              face_count: detection.faceCount,
              metadata: { faceCount: detection.faceCount },
            };
            trackingRef.current.eventBuffer.push(faceEvent);

            // Add multi_face event (always send to track duration correctly)
            const multiFaceEvent: ClientEvent = {
              event_type: 'multi_face',
              timestamp,
              confidence: detection.faceCount > 1 ? detection.confidence : 0.0,
              face_count: detection.faceCount,
              metadata: {},
            };
            trackingRef.current.eventBuffer.push(multiFaceEvent);

            // Send batch if buffer is full or enough time has passed
            const now = Date.now();
            if (
              trackingRef.current.eventBuffer.length >= BATCH_SIZE ||
              (now - trackingRef.current.lastSendTime) > 1000 // Send at least once per second
            ) {
              await sendEventsBatch();
            }
          }
        } else {
          // No face detected
          setFacePresent(false);
          setFaceCount(0);
          setConfidence(0);
          setHeadPose(null);
          
          const event: ClientEvent = {
            event_type: 'face_present',
            timestamp,
            confidence: 0,
            face_count: 0,
            metadata: { faceCount: 0 },
          };
          trackingRef.current.eventBuffer.push(event);
        }
      } else {
        // detection is null - MediaPipe might not be initialized
        console.warn('Face detection returned null - MediaPipe might not be initialized');
      }
    } catch (err: any) {
      console.error('Head pose tracking error:', err);
      setError(`Head pose tracking error: ${err.message}`);
    }
  }, [sendEventsBatch]);

  const startTracking = useCallback((video: HTMLVideoElement, sessionId: number, sessionStartTime: number) => {
    console.log('Starting head pose tracking:', {
      hasVideo: !!video,
      sessionId,
      videoReadyState: video.readyState,
      videoDimensions: `${video.videoWidth}x${video.videoHeight}`,
      videoPaused: video.paused,
      videoSrcObject: !!video.srcObject
    });

    // Verify video is ready
    if (video.readyState < 2) {
      console.warn('Video not ready for tracking, readyState:', video.readyState);
      setError('Video not ready. Please wait for video to load.');
      return;
    }

    if (video.videoWidth === 0 || video.videoHeight === 0) {
      console.warn('Video has no dimensions');
      setError('Video has no dimensions. Please check your camera.');
      return;
    }

    trackingRef.current.video = video;
    trackingRef.current.sessionId = sessionId;
    trackingRef.current.sessionStartTime = sessionStartTime;
    trackingRef.current.lastSendTime = Date.now();

    // Initialize face detection (face-api.js)
    console.log('Initializing face detection...');
    initializeFaceDetection()
      .then((success) => {
        if (success) {
          console.log('Face detection initialized successfully, starting frame processing');
          // Start processing frames immediately
          processFrame(); // Process first frame
          // Then start interval
          const intervalId = window.setInterval(() => {
            processFrame();
          }, TELEMETRY_INTERVAL);
          trackingRef.current.intervalId = intervalId;
          console.log('Frame processing started at', TELEMETRY_INTERVAL, 'ms interval');
        } else {
          // Face detection failed but we can continue without it
          console.warn('Face detection not available, continuing without proctoring');
          setError('Face detection unavailable. Interview will continue without proctoring features.');
          // Set default values so UI doesn't break
          setFacePresent(false);
          setFaceCount(0);
          setConfidence(0);
        }
      })
      .catch((error) => {
        console.error('Failed to initialize face detection for tracking:', error);
        // Don't block the interview - just show warning
        setError('Face detection unavailable. Interview will continue without proctoring features.');
        setFacePresent(false);
        setFaceCount(0);
        setConfidence(0);
      });
  }, [processFrame]);

  const stopTracking = useCallback(() => {
    if (trackingRef.current.intervalId) {
      clearInterval(trackingRef.current.intervalId);
      trackingRef.current.intervalId = null;
    }

    // Send remaining events
    sendEventsBatch();

    trackingRef.current.video = null;
    trackingRef.current.sessionId = null;
  }, [sendEventsBatch]);

  useEffect(() => {
    return () => {
      stopTracking();
    };
  }, [stopTracking]);

  return {
    headPose,
    facePresent,
    faceCount,
    confidence,
    error,
    startTracking,
    stopTracking,
  };
}

