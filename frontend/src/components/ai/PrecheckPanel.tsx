import React from 'react';
import { useMediaDevices } from '../../hooks/useMediaDevices';

interface PrecheckPanelProps {
  onReady: () => void;
  stream?: MediaStream | null;
  mediaDevices?: ReturnType<typeof useMediaDevices>;
}

export const PrecheckPanel: React.FC<PrecheckPanelProps> = ({ 
  onReady, 
  stream: externalStream,
  mediaDevices: externalMediaDevices 
}) => {
  const internalMediaDevices = useMediaDevices();
  
  // Use external media devices if provided, otherwise use internal
  const mediaDevices = externalMediaDevices || internalMediaDevices;
  const {
    videoDevices,
    audioDevices,
    selectedVideoDeviceId,
    selectedAudioDeviceId,
    stream: internalStream,
    error,
    isLoading,
    setSelectedVideoDevice,
    setSelectedAudioDevice,
    startStream,
    stopStream,
    refreshDevices,
  } = mediaDevices;

  // Use external stream if provided, otherwise use internal stream
  const stream = externalStream !== undefined ? externalStream : internalStream;
  const isReady = stream !== null && error === null;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Device Pre-Check</h2>
      
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      <div className="space-y-4">
        {/* Video Device Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Camera
          </label>
          <select
            value={selectedVideoDeviceId || ''}
            onChange={(e) => setSelectedVideoDevice(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            disabled={isLoading}
          >
            {videoDevices.map((device) => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.label}
              </option>
            ))}
          </select>
        </div>

        {/* Audio Device Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Microphone
          </label>
          <select
            value={selectedAudioDeviceId || ''}
            onChange={(e) => setSelectedAudioDevice(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            disabled={isLoading}
          >
            {audioDevices.map((device) => (
              <option key={device.deviceId} value={device.deviceId}>
                {device.label}
              </option>
            ))}
          </select>
        </div>

        {/* Video Preview */}
        {stream && (
          <div className="relative">
            <video
              ref={(video) => {
                if (video && stream) {
                  video.srcObject = stream;
                }
              }}
              autoPlay
              playsInline
              muted
              className="w-full rounded-lg border border-gray-300"
            />
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={startStream}
            disabled={isLoading || stream !== null}
            className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Testing...' : stream ? 'Stream Active' : 'Test Camera & Mic'}
          </button>
          
          {stream && (
            <button
              onClick={stopStream}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
            >
              Stop Test
            </button>
          )}
          
          <button
            onClick={refreshDevices}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
          >
            Refresh Devices
          </button>
        </div>

        {/* Status */}
        {isReady && (
          <div className="space-y-3">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800 font-medium">✓ Devices ready</p>
            </div>
            <button
              onClick={() => {
                console.log('Continue button clicked, calling onReady');
                onReady();
              }}
              className="w-full px-6 py-3 bg-primary-600 text-white font-medium rounded-md hover:bg-primary-700 transition-colors shadow-sm"
            >
              Continue to Interview
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

