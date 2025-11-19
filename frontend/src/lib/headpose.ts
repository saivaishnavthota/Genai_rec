/**
 * Head pose visualization and threshold constants
 */

export const HEAD_POSE_THRESHOLDS = {
  MODERATE_YAW: 35, // degrees
  MODERATE_DURATION: 2.0, // seconds
  HIGH_YAW: 45, // degrees
  HIGH_DURATION: 3.0, // seconds
  COMFORT_ZONE_YAW: 20, // degrees - green zone
} as const;

export interface HeadPose {
  yaw: number; // -180 to 180 degrees
  pitch: number; // -180 to 180 degrees
  roll: number; // -180 to 180 degrees
  confidence: number; // 0 to 1
}

/**
 * Map yaw/pitch to UI arc position
 */
export function mapPoseToArc(pose: HeadPose, arcRadius: number = 100): { x: number; y: number } {
  // Normalize yaw (-180 to 180) to (-1 to 1)
  const normalizedYaw = pose.yaw / 180;
  const normalizedPitch = pose.pitch / 180;
  
  // Map to arc coordinates (semi-circle)
  const angle = normalizedYaw * Math.PI;
  const distance = Math.abs(normalizedYaw) * arcRadius;
  
  const x = Math.sin(angle) * distance;
  const y = -normalizedPitch * arcRadius; // Negative because pitch up is visually up
  
  return { x, y };
}

/**
 * Check if head pose is within comfort zone
 */
export function isWithinComfortZone(pose: HeadPose): boolean {
  return Math.abs(pose.yaw) < HEAD_POSE_THRESHOLDS.COMFORT_ZONE_YAW;
}

/**
 * Get head pose severity level (UI indicator only)
 */
export function getPoseSeverity(pose: HeadPose): 'good' | 'warning' | 'critical' {
  const absYaw = Math.abs(pose.yaw);
  
  if (absYaw >= HEAD_POSE_THRESHOLDS.HIGH_YAW) {
    return 'critical';
  } else if (absYaw >= HEAD_POSE_THRESHOLDS.MODERATE_YAW) {
    return 'warning';
  }
  return 'good';
}

