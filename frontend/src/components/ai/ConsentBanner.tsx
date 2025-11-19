import React, { useState } from 'react';

interface ConsentBannerProps {
  onConsent: () => void;
}

export const ConsentBanner: React.FC<ConsentBannerProps> = ({ onConsent }) => {
  const [consented, setConsented] = useState(false);
  const [readPrivacy, setReadPrivacy] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Interview Consent</h2>
      
      <div className="space-y-4 mb-6">
        <div className="prose max-w-none">
          <h3 className="text-lg font-semibold mb-2">Monitoring & Recording</h3>
          <p className="text-gray-700 mb-4">
            This interview will be monitored and recorded for proctoring purposes. The following will be tracked:
          </p>
          <ul className="list-disc list-inside space-y-2 text-gray-700 mb-4">
            <li>Video feed (camera) for face detection and head pose analysis</li>
            <li>Audio feed (microphone) for transcription and multi-speaker detection</li>
            <li>Screen activity (if applicable) for policy compliance</li>
          </ul>

          <h3 className="text-lg font-semibold mb-2">Data Retention</h3>
          <p className="text-gray-700 mb-4">
            Your interview recording and data will be retained for evaluation purposes and may be reviewed by HR and hiring managers.
          </p>

          <h3 className="text-lg font-semibold mb-2">Proctoring Flags</h3>
          <p className="text-gray-700 mb-4">
            The system may flag certain behaviors (e.g., looking away from screen, multiple faces detected) for review. These flags are part of the standard interview process.
          </p>
        </div>

        <div className="flex items-start space-x-3">
          <input
            type="checkbox"
            id="privacy-read"
            checked={readPrivacy}
            onChange={(e) => setReadPrivacy(e.target.checked)}
            className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
          />
          <label htmlFor="privacy-read" className="text-sm text-gray-700">
            I have read and understood the monitoring and retention policy
          </label>
        </div>

        <div className="flex items-start space-x-3">
          <input
            type="checkbox"
            id="consent"
            checked={consented}
            onChange={(e) => setConsented(e.target.checked)}
            disabled={!readPrivacy}
            className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded disabled:opacity-50"
          />
          <label htmlFor="consent" className="text-sm text-gray-700">
            I consent to being monitored and recorded during this interview
          </label>
        </div>
      </div>

      <button
        onClick={onConsent}
        disabled={!consented || !readPrivacy}
        className="w-full px-6 py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
      >
        Start Interview
      </button>
    </div>
  );
};

