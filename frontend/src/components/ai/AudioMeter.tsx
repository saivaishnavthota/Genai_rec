import React, { useEffect, useRef, useState } from 'react';

interface AudioMeterProps {
  stream: MediaStream | null;
}

export const AudioMeter: React.FC<AudioMeterProps> = ({ stream }) => {
  const [audioLevel, setAudioLevel] = useState(0);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    if (!stream) {
      setAudioLevel(0);
      return;
    }

    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const microphone = audioContext.createMediaStreamSource(stream);
    
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.8;
    microphone.connect(analyser);
    
    analyserRef.current = analyser;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const updateLevel = () => {
      if (analyserRef.current) {
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        setAudioLevel(average / 255);
      }
      animationFrameRef.current = requestAnimationFrame(updateLevel);
    };

    updateLevel();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      audioContext.close();
    };
  }, [stream]);

  const levelPercentage = Math.min(audioLevel * 100, 100);
  const levelColor = levelPercentage > 80 ? 'bg-red-500' : levelPercentage > 50 ? 'bg-yellow-500' : 'bg-green-500';

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-600 w-12">Audio:</span>
      <div className="flex-1 h-4 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${levelColor} transition-all duration-100`}
          style={{ width: `${levelPercentage}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 w-8">{Math.round(levelPercentage)}%</span>
    </div>
  );
};

