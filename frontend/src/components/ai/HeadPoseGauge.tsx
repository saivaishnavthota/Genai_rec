import React from 'react';
import { HeadPose } from '../../lib/headpose';
import { mapPoseToArc, isWithinComfortZone, getPoseSeverity, HEAD_POSE_THRESHOLDS } from '../../lib/headpose';

interface HeadPoseGaugeProps {
  headPose: HeadPose | null;
  baseline?: HeadPose | null;
}

export const HeadPoseGauge: React.FC<HeadPoseGaugeProps> = ({ headPose, baseline }) => {
  if (!headPose) {
    return (
      <div className="w-64 h-64 mx-auto flex items-center justify-center bg-gray-100 rounded-full">
        <p className="text-gray-500">Waiting for face detection...</p>
      </div>
    );
  }

  const severity = getPoseSeverity(headPose);
  const inComfortZone = isWithinComfortZone(headPose);
  const { x, y } = mapPoseToArc(headPose, 100);

  const severityColors = {
    good: 'bg-green-500',
    warning: 'bg-yellow-500',
    critical: 'bg-red-500',
  };

  return (
    <div className="w-64 h-64 mx-auto relative">
      {/* Outer arc visualization */}
      <svg className="w-full h-full" viewBox="0 0 200 200">
        {/* Arc background */}
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="4"
        />
        
        {/* Comfort zone indicator */}
        <path
          d={`M ${100 - 80 * Math.sin((HEAD_POSE_THRESHOLDS.COMFORT_ZONE_YAW * Math.PI) / 180)} ${
            100 - 80 * Math.cos((HEAD_POSE_THRESHOLDS.COMFORT_ZONE_YAW * Math.PI) / 180)
          } A 80 80 0 0 1 ${
            100 + 80 * Math.sin((HEAD_POSE_THRESHOLDS.COMFORT_ZONE_YAW * Math.PI) / 180)
          } ${100 - 80 * Math.cos((HEAD_POSE_THRESHOLDS.COMFORT_ZONE_YAW * Math.PI) / 180)}`}
          fill="none"
          stroke="#10b981"
          strokeWidth="6"
          opacity="0.3"
        />
        
        {/* Current position indicator */}
        <circle
          cx={100 + x}
          cy={100 + y}
          r="8"
          fill={severityColors[severity]}
          className="transition-all duration-200"
        />
        
        {/* Center point */}
        <circle cx="100" cy="100" r="4" fill="#6b7280" />
      </svg>

      {/* Status text */}
      <div className="absolute bottom-0 left-0 right-0 text-center">
        <div className={`inline-block px-4 py-2 rounded-full ${
          inComfortZone ? 'bg-green-100 text-green-800' : severityColors[severity] + ' text-white'
        }`}>
          <span className="font-medium">
            {inComfortZone ? '✓ Aligned' : severity === 'warning' ? '⚠ Look forward' : '⚠ Look straight ahead'}
          </span>
        </div>
        <div className="mt-2 text-sm text-gray-600">
          Yaw: {headPose.yaw.toFixed(1)}° | Pitch: {headPose.pitch.toFixed(1)}°
        </div>
      </div>
    </div>
  );
};

