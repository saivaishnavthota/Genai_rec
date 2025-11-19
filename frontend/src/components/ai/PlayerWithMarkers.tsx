import React, { useRef, useEffect, useState } from 'react';
import { Flag } from '../../lib/api';
import { formatTimecode } from '../../lib/timecode';
import config from '../../utils/config';

interface PlayerWithMarkersProps {
  videoUrl: string;
  flags: Flag[];
  currentTime?: number;
  onTimeUpdate?: (time: number) => void;
  onSeek?: (time: number) => void;
}

const SEVERITY_COLORS = {
  low: '#3b82f6', // blue
  moderate: '#eab308', // yellow
  high: '#ef4444', // red
};

export const PlayerWithMarkers: React.FC<PlayerWithMarkersProps> = ({
  videoUrl,
  flags,
  currentTime: externalCurrentTime,
  onTimeUpdate,
  onSeek,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [internalCurrentTime, setInternalCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const currentTime = externalCurrentTime ?? internalCurrentTime;

  // Fetch video with authentication and create blob URL
  useEffect(() => {
    if (!videoUrl) {
      setLoading(false);
      return;
    }

    // If it's already a blob URL or data URL, use it directly
    if (videoUrl.startsWith('blob:') || videoUrl.startsWith('data:')) {
      setBlobUrl(videoUrl);
      setLoading(false);
      return;
    }

    // If it's a presigned URL (starts with http and contains query params), use it directly
    if (videoUrl.startsWith('http') && (videoUrl.includes('?') || videoUrl.includes('X-Amz'))) {
      setBlobUrl(videoUrl);
      setLoading(false);
      return;
    }

    // Otherwise, fetch with authentication
    const fetchVideo = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const token = localStorage.getItem('token');
        const headers: HeadersInit = {
          'Accept': 'video/mp4, video/*, */*',
        };
        
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        // Add token to URL as query param as fallback
        const urlWithToken = videoUrl.includes('?') 
          ? `${videoUrl}&token=${encodeURIComponent(token || '')}`
          : `${videoUrl}?token=${encodeURIComponent(token || '')}`;

        const response = await fetch(urlWithToken, { headers });
        
        if (!response.ok) {
          throw new Error(`Failed to load video: ${response.status} ${response.statusText}`);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setBlobUrl(url);
      } catch (err: any) {
        console.error('Failed to load video:', err);
        setError(err.message || 'Failed to load video');
      } finally {
        setLoading(false);
      }
    };

    fetchVideo();
  }, [videoUrl]);

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (blobUrl && blobUrl.startsWith('blob:')) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [blobUrl]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      const time = video.currentTime;
      setInternalCurrentTime(time);
      onTimeUpdate?.(time);
    };

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
    };
  }, [onTimeUpdate]);

  // Sync external currentTime
  useEffect(() => {
    if (externalCurrentTime !== undefined && videoRef.current) {
      const video = videoRef.current;
      if (Math.abs(video.currentTime - externalCurrentTime) > 0.5) {
        video.currentTime = externalCurrentTime;
      }
    }
  }, [externalCurrentTime]);

  const handleSeek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      onSeek?.(time);
    }
  };

  const getMarkerPosition = (flag: Flag): number => {
    const tStart = Number(flag.t_start || 0);
    return (tStart / Math.max(duration, 1)) * 100;
  };

  return (
    <div className="relative bg-black rounded-lg overflow-hidden">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black text-white">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
            <p>Loading video...</p>
          </div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black text-white">
          <div className="text-center">
            <p className="text-red-400">{error}</p>
            <p className="text-sm text-gray-400 mt-2">Video not available</p>
          </div>
        </div>
      )}
      {!loading && !error && blobUrl && (
        <video
          ref={videoRef}
          src={blobUrl}
          controls
          className="w-full h-full"
          onSeeked={(e) => {
            const time = (e.target as HTMLVideoElement).currentTime;
            setInternalCurrentTime(time);
            onSeek?.(time);
          }}
        />
      )}
      {!loading && !error && !blobUrl && (
        <div className="absolute inset-0 flex items-center justify-center bg-black text-white">
          <div className="text-center">
            <p className="text-gray-400">No video available</p>
          </div>
        </div>
      )}

      {/* Timeline with markers overlay */}
      {duration > 0 && (
        <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 p-2">
          <div className="relative h-2 bg-gray-600 rounded-full">
            {/* Progress indicator */}
            <div
              className="absolute top-0 left-0 h-full bg-primary-500 rounded-full"
              style={{ width: `${(currentTime / duration) * 100}%` }}
            />

            {/* Flag markers */}
            {flags.map((flag) => {
              const position = getMarkerPosition(flag);
              return (
                <button
                  key={flag.id}
                  onClick={() => handleSeek(Number(flag.t_start || 0))}
                  className="absolute top-0 h-full w-1 hover:w-2 transition-all"
                  style={{
                    left: `${position}%`,
                    backgroundColor: SEVERITY_COLORS[flag.severity],
                  }}
                  title={`${flag.flag_type} (${flag.severity}) at ${formatTimecode(flag.t_start)}`}
                  aria-label={`Flag at ${formatTimecode(flag.t_start)}`}
                />
              );
            })}
          </div>

          <div className="flex items-center justify-between mt-1 text-xs text-white">
            <span>{formatTimecode(currentTime)}</span>
            <span>{formatTimecode(duration)}</span>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-black bg-opacity-70 rounded-lg p-2 text-white text-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded" />
            <span>Low</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-500 rounded" />
            <span>Moderate</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded" />
            <span>High</span>
          </div>
        </div>
      </div>
    </div>
  );
};

