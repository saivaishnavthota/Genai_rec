/**
 * MediaPipe Face Landmarker wrapper
 * Uses dynamic imports to avoid webpack module resolution cache issues
 */

// Type definitions
type FaceLandmarkerType = any;
type FilesetResolverType = any;

let faceLandmarker: FaceLandmarkerType | null = null;
let isInitialized = false;
let initializationPromise: Promise<FaceLandmarkerType> | null = null;
let mediapipeModule: { FaceLandmarker: FaceLandmarkerType; FilesetResolver: FilesetResolverType } | null = null;

export interface FaceLandmark {
  x: number;
  y: number;
  z: number;
}

export interface FaceDetectionResult {
  landmarks: FaceLandmark[];
  faceCount: number;
  confidence: number;
}

/**
 * Dynamically load MediaPipe module to avoid webpack cache issues
 */
async function loadMediaPipeModule(): Promise<{ FaceLandmarker: FaceLandmarkerType; FilesetResolver: FilesetResolverType }> {
  if (mediapipeModule) {
    return mediapipeModule;
  }

  try {
    console.log('Loading MediaPipe module dynamically...');
    // Use dynamic import to avoid webpack static analysis issues
    // @ts-ignore - Dynamic import bypasses TypeScript module resolution at compile time
    const module = await import('@mediapipe/tasks-vision');
    mediapipeModule = module;
    console.log('MediaPipe module loaded successfully');
    return module;
  } catch (error) {
    console.error('Failed to load MediaPipe module:', error);
    // Retry once after a short delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    try {
      console.log('Retrying MediaPipe module load...');
      // @ts-ignore - Dynamic import bypasses TypeScript module resolution at compile time
      const module = await import('@mediapipe/tasks-vision');
      mediapipeModule = module;
      console.log('MediaPipe module loaded on retry');
      return module;
    } catch (retryError) {
      console.error('Failed to load MediaPipe module after retry:', retryError);
      throw new Error(`Failed to load MediaPipe module: ${retryError instanceof Error ? retryError.message : String(retryError)}`);
    }
  }
}

/**
 * Initialize MediaPipe Face Landmarker
 */
export async function initializeMediaPipe(): Promise<FaceLandmarkerType> {
  if (isInitialized && faceLandmarker) {
    console.log('MediaPipe already initialized, reusing');
    return faceLandmarker;
  }

  // If initialization is in progress, wait for it
  if (initializationPromise) {
    console.log('MediaPipe initialization already in progress, waiting...');
    return initializationPromise;
  }

  initializationPromise = (async () => {
    try {
      // Load the module dynamically first
      const { FaceLandmarker, FilesetResolver } = await loadMediaPipeModule();
      
      console.log('Initializing MediaPipe FilesetResolver...');
      const vision = await FilesetResolver.forVisionTasks(
        'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm'
      );
      console.log('FilesetResolver loaded');

      console.log('Loading FaceLandmarker model...');
      faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
          delegate: 'GPU', // Fallback to CPU if GPU not available
        },
        outputFaceBlendshapes: false,
        runningMode: 'VIDEO',
        numFaces: 2, // Detect up to 2 faces
        minFaceDetectionConfidence: 0.5,
        minFacePresenceConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });

      isInitialized = true;
      initializationPromise = null;
      console.log('MediaPipe FaceLandmarker initialized successfully');
      return faceLandmarker!;
    } catch (error) {
      console.error('Failed to initialize MediaPipe:', error);
      isInitialized = false;
      faceLandmarker = null;
      initializationPromise = null;
      mediapipeModule = null; // Reset module cache on error
      throw error;
    }
  })();

  return initializationPromise;
}

/**
 * Detect faces in video frame
 */
export async function detectFaces(
  video: HTMLVideoElement,
  timestamp: number
): Promise<FaceDetectionResult | null> {
  // Check if video is ready
  if (!video) {
    console.warn('Video element is null');
    return null;
  }

  // Video readyState: 0=HAVE_NOTHING, 1=HAVE_METADATA, 2=HAVE_CURRENT_DATA, 3=HAVE_FUTURE_DATA, 4=HAVE_ENOUGH_DATA
  // We need at least HAVE_CURRENT_DATA (2) for detection
  if (video.readyState < 2) {
    console.warn('Video not ready for face detection, readyState:', video.readyState);
    return null;
  }

  // Check video dimensions
  if (video.videoWidth === 0 || video.videoHeight === 0) {
    console.warn('Video has no dimensions:', video.videoWidth, 'x', video.videoHeight);
    return null;
  }

  if (!faceLandmarker) {
    try {
      console.log('Initializing MediaPipe...');
      await initializeMediaPipe();
      console.log('MediaPipe initialized successfully');
    } catch (error) {
      console.error('Failed to initialize MediaPipe:', error);
      return null;
    }
  }

  if (!faceLandmarker) {
    console.error('FaceLandmarker is null after initialization');
    return null;
  }

  try {
    // MediaPipe VIDEO mode expects timestamp in milliseconds relative to video start
    // Use video's currentTime converted to milliseconds
    const videoTimestamp = Math.floor(video.currentTime * 1000);
    
    // Log first few frames for debugging
    const shouldLog = videoTimestamp < 2000 || Math.floor(videoTimestamp / 1000) % 5 === 0;
    
    if (shouldLog) {
      console.log('Detecting faces - video timestamp:', videoTimestamp, 'ms, dimensions:', video.videoWidth, 'x', video.videoHeight, 'paused:', video.paused);
    }
    
    const results = faceLandmarker.detectForVideo(video, videoTimestamp);
    
    // Always log results to see what's happening
    const hasFaces = results.faceLandmarks && results.faceLandmarks.length > 0;
    
    if (shouldLog || hasFaces) {
      console.log('MediaPipe detection results:', {
        faceCount: results.faceLandmarks?.length || 0,
        hasLandmarks: hasFaces,
        timestamp: videoTimestamp
      });
    }
    
    if (results.faceLandmarks && results.faceLandmarks.length > 0) {
      const faceCount = results.faceLandmarks.length;
      const primaryFace = results.faceLandmarks[0];
      
      // MediaPipe provides 468 landmarks for full face
      // Calculate confidence based on landmark count and quality
      let confidence = 0.7;
      if (primaryFace.length >= 468) {
        confidence = 0.95;
      } else if (primaryFace.length >= 200) {
        confidence = 0.85;
      } else if (primaryFace.length >= 100) {
        confidence = 0.75;
      }
      
      // Always log when face is detected (important event)
      console.log('✓ Face detected:', {
        faceCount,
        landmarkCount: primaryFace.length,
        confidence: (confidence * 100).toFixed(0) + '%'
      });
      
      return {
        landmarks: primaryFace.map((lm) => ({ x: lm.x, y: lm.y, z: lm.z })),
        faceCount,
        confidence,
      };
    }
    
    // Don't log every frame when no face detected (too verbose)
    // Only log occasionally
    if (Math.random() < 0.05) { // Log 5% of frames
      console.log('No faces detected in frame');
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
export function calculateHeadPose(landmarks: FaceLandmark[]): {
  yaw: number;
  pitch: number;
  roll: number;
} | null {
  if (landmarks.length < 10) {
    return null;
  }

  // Use key facial landmarks for pose estimation
  // Simplified calculation - in production, use more sophisticated methods
  const noseTip = landmarks[4] || landmarks[0];
  const leftEye = landmarks[33] || landmarks[0];
  const rightEye = landmarks[263] || landmarks[0];
  const chin = landmarks[18] || landmarks[0];

  if (!noseTip || !leftEye || !rightEye || !chin) {
    return null;
  }

  // Calculate yaw (left-right rotation)
  const eyeCenterX = (leftEye.x + rightEye.x) / 2;
  const yaw = (noseTip.x - eyeCenterX) * 180;

  // Calculate pitch (up-down rotation)
  const eyeCenterY = (leftEye.y + rightEye.y) / 2;
  const pitch = (noseTip.y - eyeCenterY) * 180;

  // Calculate roll (tilt)
  const eyeDeltaY = rightEye.y - leftEye.y;
  const eyeDeltaX = rightEye.x - leftEye.x;
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

/**
 * Reset MediaPipe module cache (useful for debugging or after errors)
 */
export function resetMediaPipeCache(): void {
  console.log('Resetting MediaPipe cache...');
  faceLandmarker = null;
  isInitialized = false;
  initializationPromise = null;
  mediapipeModule = null;
  console.log('MediaPipe cache reset complete');
}

