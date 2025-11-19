/**
 * Cloud-based Face Detection using AWS Rekognition or Azure Face API
 * More reliable and production-ready than client-side libraries
 * 
 * This requires backend API endpoints to handle the cloud API calls
 */

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
 * Detect faces using cloud API (backend proxy)
 * Sends video frame to backend which calls AWS/Azure API
 */
export async function detectFacesCloud(
  video: HTMLVideoElement,
  sessionId: number,
  apiUrl: string = '/api/ai-interview/face-detection'
): Promise<FaceDetectionResult | null> {
  if (!video || video.readyState < 2) {
    return null;
  }

  try {
    // Capture frame from video
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0);
    
    // Convert to blob
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) resolve(blob);
        else reject(new Error('Failed to create blob'));
      }, 'image/jpeg', 0.8);
    });

    // Send to backend for cloud API processing
    const formData = new FormData();
    formData.append('image', blob, 'frame.jpg');
    formData.append('session_id', sessionId.toString());

    const response = await fetch(apiUrl, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Cloud face detection failed: ${response.statusText}`);
    }

    const result = await response.json();
    
    return {
      landmarks: result.landmarks || [],
      faceCount: result.face_count || 0,
      confidence: result.confidence || 0,
    };
  } catch (error) {
    console.error('Cloud face detection error:', error);
    return null;
  }
}

/**
 * Calculate head pose from cloud API response
 */
export function calculateHeadPoseCloud(apiResponse: any): HeadPose | null {
  if (!apiResponse || !apiResponse.pose) {
    return null;
  }

  return {
    yaw: apiResponse.pose.yaw || 0,
    pitch: apiResponse.pose.pitch || 0,
    roll: apiResponse.pose.roll || 0,
  };
}

/**
 * Initialize cloud face detection (no-op, just check API availability)
 */
export async function initializeCloudFaceDetection(): Promise<void> {
  // Check if backend API is available
  try {
    const response = await fetch('/api/ai-interview/face-detection/health', {
      method: 'GET',
    });
    if (!response.ok) {
      throw new Error('Cloud face detection API not available');
    }
    console.log('Cloud face detection API available');
  } catch (error) {
    console.warn('Cloud face detection API not available, will use fallback:', error);
    throw error;
  }
}

