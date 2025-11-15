/**
 * Face Detection using face-api.js (alternative to MediaPipe)
 * Much simpler setup, no Docker issues, works reliably
 * 
 * This replaces MediaPipe with face-api.js which:
 * - Works better in Docker/containerized environments
 * - Can load from CDN (no npm install needed!)
 * - Loads models from CDN (no local files needed)
 * - Provides similar face detection and landmark capabilities
 * 
 * FALLBACK: If face-api.js fails, the system will gracefully degrade
 * and continue without face detection (interview can still proceed)
 */

// Dynamic import to avoid issues if package not installed yet
let faceapi: any = null;

let modelsLoaded = false;
let loadingPromise: Promise<void> | null = null;

export interface FaceDetectionResult {
  landmarks: Array<{ x: number; y: number; z: number }>;
  faceCount: number;
  confidence: number;
}

export interface HeadPose {
  yaw: number;
  pitch: number;
  roll: number;
}

/**
 * Load face-api.js module dynamically
 * Tries multiple methods: npm package, CDN, or window global
 */
async function loadFaceApiModule(): Promise<any> {
  if (faceapi) {
    return faceapi;
  }

  // Strategy 1: Check if already loaded on window (from CDN or previous load)
  if (typeof window !== 'undefined' && (window as any).faceapi) {
    faceapi = (window as any).faceapi;
    console.log('Using face-api.js from window global');
    return faceapi;
  }

  // Strategy 2: Load from CDN (no npm install needed!)
  try {
    // Load face-api.js from CDN
    if (typeof window !== 'undefined' && !(window as any).faceapi) {
      await loadScript('https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.7/dist/face-api.min.js');
    }
    
    if (typeof window !== 'undefined' && (window as any).faceapi) {
      faceapi = (window as any).faceapi;
      console.log('Loaded face-api.js from CDN');
      return faceapi;
    }
  } catch (cdnError) {
    console.warn('CDN load failed, trying window global...', cdnError);
  }

  // All strategies failed
  throw new Error(
    'Failed to load face-api.js from CDN. ' +
    'Please check your internet connection. The interview will continue without face detection.'
  );
}

/**
 * Helper to load script from URL
 */
function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof document === 'undefined') {
      reject(new Error('Document not available'));
      return;
    }

    // Check if script already loaded
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
    document.head.appendChild(script);
  });
}

/**
 * Load face-api.js models
 */
async function loadModels(): Promise<void> {
  if (modelsLoaded) {
    return;
  }

  if (loadingPromise) {
    return loadingPromise;
  }

  loadingPromise = (async () => {
    try {
      console.log('Loading face-api.js models...');
      
      // Load the module first
      const faceApi = await loadFaceApiModule();
      
      // Load models from CDN (no npm package needed!)
      const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/';
      
      // Check if nets are available (different versions have different APIs)
      if (faceApi.nets) {
        await Promise.all([
          faceApi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
          faceApi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
          faceApi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
        ]);
      } else if (faceApi.loadTinyFaceDetectorModel && faceApi.loadFaceLandmarkModel) {
        // Alternative API structure
        await Promise.all([
          faceApi.loadTinyFaceDetectorModel(MODEL_URL),
          faceApi.loadFaceLandmarkModel(MODEL_URL),
          faceApi.loadFaceRecognitionModel(MODEL_URL),
        ]);
      } else {
        throw new Error('face-api.js loaded but API structure not recognized');
      }

      modelsLoaded = true;
      loadingPromise = null;
      console.log('face-api.js models loaded successfully');
    } catch (error) {
      console.error('Failed to load face-api.js models:', error);
      loadingPromise = null;
      throw error;
    }
  })();

  return loadingPromise;
}

/**
 * Initialize face detection (loads models)
 * Returns true if successful, false if failed (graceful degradation)
 */
export async function initializeFaceDetection(): Promise<boolean> {
  try {
    await loadModels();
    return true;
  } catch (error) {
    console.error('Failed to initialize face detection:', error);
    console.warn('Face detection will be disabled. Interview can still proceed without proctoring.');
    // Don't throw - allow graceful degradation
    return false;
  }
}

/**
 * Detect faces in video frame
 * Returns null if face detection is not available (graceful degradation)
 */
export async function detectFaces(
  video: HTMLVideoElement,
  timestamp?: number
): Promise<FaceDetectionResult | null> {
  if (!video) {
    console.warn('Video element is null');
    return null;
  }

  // Check video is ready
  if (video.readyState < 2) {
    console.warn('Video not ready for face detection, readyState:', video.readyState);
    return null;
  }

  if (video.videoWidth === 0 || video.videoHeight === 0) {
    console.warn('Video has no dimensions:', video.videoWidth, 'x', video.videoHeight);
    return null;
  }

  // Ensure models are loaded
  if (!modelsLoaded) {
    try {
      await loadModels();
    } catch (error) {
      console.error('Failed to load models:', error);
      // Return null instead of throwing - allows graceful degradation
      return null;
    }
  }

  // If models still not loaded after attempt, return null
  if (!modelsLoaded) {
    return null;
  }

  try {
    // Ensure module is loaded
    const faceApi = await loadFaceApiModule();
    
    // Detect faces with landmarks - handle different API structures
    let detections;
    if (faceApi.detectAllFaces) {
      // Standard API
      detections = await faceApi
        .detectAllFaces(video, new faceApi.TinyFaceDetectorOptions())
        .withFaceLandmarks();
    } else if (faceApi.detectSingleFace) {
      // Alternative API - try single face detection
      const detection = await faceApi.detectSingleFace(video, new faceApi.TinyFaceDetectorOptions())
        .withFaceLandmarks();
      detections = detection ? [detection] : [];
    } else {
      throw new Error('face-api.js API not recognized');
    }

    if (detections && detections.length > 0) {
      const faceCount = detections.length;
      const primaryFace = detections[0];
      
      // Convert landmarks to our format - handle different API structures
      let landmarks: Array<{ x: number; y: number; z: number }> = [];
      let confidence = 0.8;
      
      if (primaryFace.landmarks && primaryFace.landmarks.positions) {
        landmarks = primaryFace.landmarks.positions.map((point: any) => ({
          x: point.x / video.videoWidth, // Normalize to 0-1
          y: point.y / video.videoHeight,
          z: 0, // face-api doesn't provide z, but we can estimate
        }));
      } else if (primaryFace.landmarks && Array.isArray(primaryFace.landmarks)) {
        landmarks = primaryFace.landmarks.map((point: any) => ({
          x: (point.x || point._x || 0) / video.videoWidth,
          y: (point.y || point._y || 0) / video.videoHeight,
          z: 0,
        }));
      }

      // Calculate confidence from detection score
      if (primaryFace.detection && primaryFace.detection.score) {
        confidence = primaryFace.detection.score;
      } else if (primaryFace.score) {
        confidence = primaryFace.score;
      } else if (primaryFace.confidence) {
        confidence = primaryFace.confidence;
      }

      return {
        landmarks,
        faceCount,
        confidence,
      };
    }

    return {
      landmarks: [],
      faceCount: 0,
      confidence: 0,
    };
  } catch (error) {
    console.error('Face detection error:', error);
    return null;
  }
}

/**
 * Calculate head pose from facial landmarks
 */
export function calculateHeadPose(landmarks: Array<{ x: number; y: number; z: number }>): HeadPose | null {
  if (landmarks.length < 10) {
    return null;
  }

  // face-api.js provides 68 landmarks
  // Key points: nose (30), left eye (36-41), right eye (42-47), chin (8)
  const noseIndex = 30;
  const leftEyeStart = 36;
  const rightEyeStart = 42;
  const chinIndex = 8;

  if (landmarks.length < 48) {
    return null;
  }

  const nose = landmarks[noseIndex] || landmarks[0];
  const leftEyeCenter = {
    x: (landmarks[leftEyeStart].x + landmarks[leftEyeStart + 3].x) / 2,
    y: (landmarks[leftEyeStart + 1].y + landmarks[leftEyeStart + 4].y) / 2,
  };
  const rightEyeCenter = {
    x: (landmarks[rightEyeStart].x + landmarks[rightEyeStart + 3].x) / 2,
    y: (landmarks[rightEyeStart + 1].y + landmarks[rightEyeStart + 4].y) / 2,
  };
  const chin = landmarks[chinIndex] || landmarks[0];

  if (!nose || !chin) {
    return null;
  }

  // Calculate yaw (left-right rotation)
  const eyeCenterX = (leftEyeCenter.x + rightEyeCenter.x) / 2;
  const yaw = (nose.x - eyeCenterX) * 180;

  // Calculate pitch (up-down rotation)
  const eyeCenterY = (leftEyeCenter.y + rightEyeCenter.y) / 2;
  const pitch = (nose.y - eyeCenterY) * 180;

  // Calculate roll (tilt)
  const eyeDeltaY = rightEyeCenter.y - leftEyeCenter.y;
  const eyeDeltaX = rightEyeCenter.x - leftEyeCenter.x;
  const roll = Math.atan2(eyeDeltaY, eyeDeltaX) * (180 / Math.PI);

  return {
    yaw: clamp(yaw, -180, 180),
    pitch: clamp(pitch, -180, 180),
    roll: clamp(roll, -180, 180),
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

