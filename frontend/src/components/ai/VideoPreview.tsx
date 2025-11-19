import React, { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';

interface VideoPreviewProps {
  stream: MediaStream | null;
  className?: string;
}

export interface VideoPreviewHandle {
  getVideoElement: () => HTMLVideoElement | null;
}

export const VideoPreview = forwardRef<VideoPreviewHandle, VideoPreviewProps>(
  ({ stream, className = '' }, ref) => {
    const videoRef = useRef<HTMLVideoElement>(null);

    useImperativeHandle(ref, () => ({
      getVideoElement: () => videoRef.current,
    }));

    useEffect(() => {
      if (videoRef.current) {
        if (stream) {
          videoRef.current.srcObject = stream;
          // Ensure video starts playing
          videoRef.current.play().catch((err) => {
            console.warn('VideoPreview: Auto-play prevented:', err);
          });
        } else {
          videoRef.current.srcObject = null;
        }
      }
    }, [stream]);

    return (
      <div className={`relative bg-gray-900 rounded-lg overflow-hidden ${className}`}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />
        {!stream && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
            <p className="text-gray-400">No video stream</p>
          </div>
        )}
      </div>
    );
  }
);

VideoPreview.displayName = 'VideoPreview';

