import React, { useEffect, useState } from 'react';
import { Flag } from '../../lib/api';

interface ProctorFlagToastProps {
  flag: Flag;
  onDismiss: () => void;
}

const FLAG_TYPE_LABELS: Record<string, string> = {
  head_turn: 'Head Turn Detected',
  face_absent: 'Face Not Visible',
  multi_face: 'Multiple Faces',
  phone: 'Phone Detected',
  audio_multi_speaker: 'Multiple Speakers',
  screen_policy: 'Screen Policy Violation',
};

const SEVERITY_COLORS = {
  low: 'bg-blue-100 border-blue-300 text-blue-800',
  moderate: 'bg-yellow-100 border-yellow-300 text-yellow-800',
  high: 'bg-red-100 border-red-300 text-red-800',
};

export const ProctorFlagToast: React.FC<ProctorFlagToastProps> = ({ flag, onDismiss }) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // Auto-dismiss after 5 seconds
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onDismiss, 300); // Wait for fade-out
    }, 5000);

    return () => clearTimeout(timer);
  }, [onDismiss]);

  if (!isVisible) return null;

  return (
    <div
      className={`fixed bottom-4 right-4 p-4 rounded-lg shadow-lg border-2 max-w-sm z-50 transition-opacity duration-300 ${
        SEVERITY_COLORS[flag.severity]
      }`}
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-semibold mb-1">
            {FLAG_TYPE_LABELS[flag.flag_type] || flag.flag_type}
          </h4>
          <p className="text-sm opacity-90">
            {flag.severity === 'high' && '⚠ High severity violation detected'}
            {flag.severity === 'moderate' && '⚠ Moderate violation detected'}
            {flag.severity === 'low' && 'ℹ Minor issue detected'}
          </p>
          <p className="text-xs mt-1 opacity-75">
            Time: {typeof flag.t_start === 'number' ? flag.t_start.toFixed(1) : Number(flag.t_start || 0).toFixed(1)}s
          </p>
        </div>
        <button
          onClick={() => {
            setIsVisible(false);
            setTimeout(onDismiss, 300);
          }}
          className="ml-4 text-current opacity-70 hover:opacity-100"
          aria-label="Dismiss"
        >
          ×
        </button>
      </div>
    </div>
  );
};

