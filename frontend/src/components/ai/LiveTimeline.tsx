import React from 'react';
import { Flag } from '../../lib/api';
import { formatTimecode } from '../../lib/timecode';

interface LiveTimelineProps {
  flags: Flag[];
  currentTime: number;
  duration: number;
  onSeek?: (time: number) => void;
}

const SEVERITY_COLORS = {
  low: 'bg-blue-500',
  moderate: 'bg-yellow-500',
  high: 'bg-red-500',
};

export const LiveTimeline: React.FC<LiveTimelineProps> = ({
  flags,
  currentTime,
  duration,
  onSeek,
}) => {
  const timelineWidth = 100; // percentage

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-700">Timeline</h3>
        <span className="text-xs text-gray-500">{formatTimecode(currentTime)}</span>
      </div>

      <div className="relative h-12 bg-gray-200 rounded-full overflow-hidden">
        {/* Progress bar */}
        <div
          className="absolute top-0 left-0 h-full bg-primary-500 transition-all"
          style={{ width: `${(currentTime / Math.max(duration, 1)) * 100}%` }}
        />

        {/* Flag markers */}
        {flags.map((flag) => {
          const tStart = Number(flag.t_start || 0);
          const position = (tStart / Math.max(duration, 1)) * 100;
          return (
            <button
              key={flag.id}
              onClick={() => onSeek?.(tStart)}
              className={`absolute top-0 h-full w-1 ${SEVERITY_COLORS[flag.severity]}`}
              style={{ left: `${position}%` }}
              title={`${flag.flag_type} (${flag.severity}) at ${formatTimecode(tStart)}`}
              aria-label={`Flag at ${formatTimecode(tStart)}`}
            />
          );
        })}
      </div>

      {/* Flag legend */}
      <div className="flex gap-4 mt-2 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-blue-500 rounded" />
          <span>Low</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-yellow-500 rounded" />
          <span>Moderate</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded" />
          <span>High</span>
        </div>
      </div>
    </div>
  );
};

