import React, { useRef, useEffect } from 'react';
import { formatTimecode } from '../../lib/timecode';

interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
  speaker?: string;
}

interface TranscriptViewerProps {
  transcript: TranscriptSegment[];
  currentTime?: number;
  onSeek?: (time: number) => void;
}

export const TranscriptViewer: React.FC<TranscriptViewerProps> = ({
  transcript,
  currentTime = 0,
  onSeek,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeSegmentRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to active segment
  useEffect(() => {
    if (activeSegmentRef.current && containerRef.current) {
      const container = containerRef.current;
      const active = activeSegmentRef.current;
      const containerRect = container.getBoundingClientRect();
      const activeRect = active.getBoundingClientRect();

      if (
        activeRect.top < containerRect.top ||
        activeRect.bottom > containerRect.bottom
      ) {
        active.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [currentTime]);

  return (
    <div
      ref={containerRef}
      className="h-full overflow-y-auto bg-white border border-gray-200 rounded-lg"
    >
      <div className="p-4 space-y-2">
        {transcript.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No transcript available</p>
        ) : (
          transcript.map((segment, index) => {
            const isActive = currentTime >= segment.start && currentTime < segment.end;
            
            return (
              <div
                key={index}
                ref={isActive ? activeSegmentRef : null}
                className={`p-3 rounded-lg cursor-pointer transition-colors ${
                  isActive
                    ? 'bg-primary-50 border-2 border-primary-500'
                    : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                }`}
                onClick={() => onSeek?.(segment.start)}
              >
                <div className="flex items-start justify-between mb-1">
                  <span className="text-xs text-gray-500 font-mono">
                    {formatTimecode(segment.start)}
                  </span>
                  {segment.speaker && (
                    <span className="text-xs text-gray-600 bg-gray-200 px-2 py-0.5 rounded">
                      {segment.speaker}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-900">{segment.text}</p>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

