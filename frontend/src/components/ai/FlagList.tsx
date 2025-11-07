import React from 'react';
import { Flag } from '../../lib/api';
import { formatTimecode } from '../../lib/timecode';

interface FlagListProps {
  flags: Flag[];
  onJumpToTime?: (time: number) => void;
}

const FLAG_TYPE_LABELS: Record<string, string> = {
  head_turn: 'Head Turn',
  face_absent: 'Face Absent',
  multi_face: 'Multiple Faces',
  phone: 'Phone Detected',
  audio_multi_speaker: 'Multiple Speakers',
  screen_policy: 'Screen Policy',
  tab_switch: 'Tab Switched',
};

const SEVERITY_BADGES = {
  low: 'bg-blue-100 text-blue-800 border-blue-300',
  moderate: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  high: 'bg-red-100 text-red-800 border-red-300',
};

export const FlagList: React.FC<FlagListProps> = ({ flags, onJumpToTime }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Severity
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Confidence
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Duration
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {flags.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No flags detected
                </td>
              </tr>
            ) : (
              flags.map((flag) => (
                <tr key={flag.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900">
                    {formatTimecode(flag.t_start)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    {FLAG_TYPE_LABELS[flag.flag_type] || flag.flag_type}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded border ${SEVERITY_BADGES[flag.severity]}`}
                    >
                      {flag.severity.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                    {(flag.confidence * 100).toFixed(1)}%
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                    {(Number(flag.t_end || 0) - Number(flag.t_start || 0)).toFixed(1)}s
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">
                    {onJumpToTime && (
                      <button
                        onClick={() => onJumpToTime(Number(flag.t_start || 0))}
                        className="text-primary-600 hover:text-primary-800 font-medium"
                      >
                        Jump to
                      </button>
                    )}
                    {flag.clip_url && (
                      <a
                        href={flag.clip_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-3 text-primary-600 hover:text-primary-800 font-medium"
                      >
                        View clip
                      </a>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

