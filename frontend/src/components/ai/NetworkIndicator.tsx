import React from 'react';
import { WebRTCStats } from '../../lib/webrtc';

interface NetworkIndicatorProps {
  connectionState: string;
  stats: WebRTCStats | null;
}

export const NetworkIndicator: React.FC<NetworkIndicatorProps> = ({
  connectionState,
  stats,
}) => {
  const getConnectionColor = () => {
    switch (connectionState) {
      case 'connected':
        return 'text-green-600';
      case 'connecting':
        return 'text-yellow-600';
      case 'disconnected':
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getConnectionIcon = () => {
    switch (connectionState) {
      case 'connected':
        return '🟢';
      case 'connecting':
        return '🟡';
      case 'disconnected':
      case 'failed':
        return '🔴';
      default:
        return '⚪';
    }
  };

  return (
    <div className="flex items-center gap-4 text-sm">
      <div className="flex items-center gap-2">
        <span>{getConnectionIcon()}</span>
        <span className={getConnectionColor()}>
          {connectionState.charAt(0).toUpperCase() + connectionState.slice(1)}
        </span>
      </div>

      {stats && connectionState === 'connected' && (
        <>
          <div className="text-gray-600">
            Bitrate: {(stats.bitrate / 1000).toFixed(0)} kbps
          </div>
          {stats.packetLoss > 0 && (
            <div className="text-yellow-600">
              Loss: {stats.packetLoss.toFixed(1)}%
            </div>
          )}
          {stats.rtt > 0 && (
            <div className="text-gray-600">
              RTT: {stats.rtt.toFixed(0)}ms
            </div>
          )}
        </>
      )}
    </div>
  );
};

