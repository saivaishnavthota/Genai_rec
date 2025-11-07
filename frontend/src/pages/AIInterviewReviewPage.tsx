import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { aiInterviewAPI, SessionReport } from '../lib/api';
import { PlayerWithMarkers } from '../components/ai/PlayerWithMarkers';
import { Scorecard } from '../components/ai/Scorecard';
import { TranscriptViewer } from '../components/ai/TranscriptViewer';
import { FlagList } from '../components/ai/FlagList';

type Tab = 'scorecard' | 'transcript' | 'flags';

const AIInterviewReviewPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [report, setReport] = useState<SessionReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('scorecard');
  const [currentTime, setCurrentTime] = useState(0);
  const [decision, setDecision] = useState<'PASS' | 'REVIEW' | 'FAIL' | null>(null);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [scoring, setScoring] = useState(false);

  useEffect(() => {
    if (!sessionId) {
      navigate('/hr-dashboard');
      return;
    }

    loadReport();
  }, [sessionId, navigate]);

  const loadReport = async () => {
    try {
      setLoading(true);
      const data = await aiInterviewAPI.getReport(parseInt(sessionId!));
      setReport(data);
      setDecision(data.session.recommendation?.toUpperCase() as 'PASS' | 'REVIEW' | 'FAIL' || null);
    } catch (err: any) {
      setError(err.message || 'Failed to load interview report');
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerScoring = async () => {
    if (!sessionId) return;
    
    try {
      setScoring(true);
      await aiInterviewAPI.triggerScoring(parseInt(sessionId));
      // Reload report to show new scores
      await loadReport();
      alert('Scoring completed successfully!');
    } catch (err: any) {
      alert(`Failed to trigger scoring: ${err.message}`);
    } finally {
      setScoring(false);
    }
  };

  const handleSubmitDecision = async () => {
    if (!sessionId || !decision) return;

    try {
      setSubmitting(true);
      await aiInterviewAPI.postReviewDecision(parseInt(sessionId), {
        status: decision,
        notes: notes || undefined,
      });
      
      // Reload report
      await loadReport();
      
      // Show success message
      alert('Decision submitted successfully!');
    } catch (err: any) {
      alert(`Failed to submit decision: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSeek = (time: number) => {
    setCurrentTime(time);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading interview report...</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Report not found'}</p>
          <button
            onClick={() => navigate('/hr-dashboard')}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const videoUrl = report.session.video_url || '';
  // Extract transcript segments - handle both array and object formats
  let transcript: any[] = [];
  if (report.transcript) {
    if (Array.isArray(report.transcript)) {
      transcript = report.transcript;
    } else if (report.transcript.segments && Array.isArray(report.transcript.segments)) {
      transcript = report.transcript.segments;
    } else if (typeof report.transcript === 'object') {
      // Try to find segments in nested structure
      transcript = [];
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI Interview Review</h1>
              <p className="text-sm text-gray-600 mt-1">
                Session #{report.session.id} | Status: {report.session.status}
                {report.session.total_score !== null && (
                  <span className="ml-2">
                    | Score: <span className="font-semibold">{report.session.total_score.toFixed(1)}/10</span>
                  </span>
                )}
              </p>
            </div>
            <div className="flex gap-2">
              {(!report.scores || report.scores.final_score === null) && (
                <button
                  onClick={handleTriggerScoring}
                  disabled={scoring}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {scoring ? 'Scoring...' : 'Trigger Scoring'}
                </button>
              )}
              <button
                onClick={() => navigate('/hr-dashboard')}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Video Player */}
          <div className="lg:col-span-2">
            <PlayerWithMarkers
              videoUrl={videoUrl}
              flags={report.flags}
              currentTime={currentTime}
              onTimeUpdate={setCurrentTime}
              onSeek={handleSeek}
            />
          </div>

          {/* Right: Tabs */}
          <div className="space-y-4">
            {/* Tab Navigation */}
            <div className="bg-white rounded-lg shadow border-b">
              <div className="flex">
                <button
                  onClick={() => setActiveTab('scorecard')}
                  className={`flex-1 px-4 py-3 text-sm font-medium ${
                    activeTab === 'scorecard'
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Scorecard
                </button>
                <button
                  onClick={() => setActiveTab('transcript')}
                  className={`flex-1 px-4 py-3 text-sm font-medium ${
                    activeTab === 'transcript'
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Transcript
                </button>
                <button
                  onClick={() => setActiveTab('flags')}
                  className={`flex-1 px-4 py-3 text-sm font-medium ${
                    activeTab === 'flags'
                      ? 'text-primary-600 border-b-2 border-primary-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Flags ({report.flags.length})
                </button>
              </div>
            </div>

            {/* Tab Content */}
            <div className="bg-white rounded-lg shadow p-4" style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {activeTab === 'scorecard' && report.scores && (
                <Scorecard
                  finalScore={report.scores.final_score}
                  criteria={report.scores.criteria}
                  summary={report.scores.summary}
                  improvementTip={report.scores.improvement_tip}
                  citations={report.scores.citations}
                />
              )}

              {activeTab === 'transcript' && (
                <TranscriptViewer
                  transcript={transcript}
                  currentTime={currentTime}
                  onSeek={handleSeek}
                />
              )}

              {activeTab === 'flags' && (
                <FlagList flags={report.flags} onJumpToTime={handleSeek} />
              )}
            </div>
          </div>
        </div>

        {/* Decision Footer */}
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Review Decision</h3>
          
          <div className="space-y-4">
            <div className="flex gap-4">
              <button
                onClick={() => setDecision('PASS')}
                className={`flex-1 px-4 py-3 rounded-md font-medium ${
                  decision === 'PASS'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                ✓ PASS
              </button>
              <button
                onClick={() => setDecision('REVIEW')}
                className={`flex-1 px-4 py-3 rounded-md font-medium ${
                  decision === 'REVIEW'
                    ? 'bg-yellow-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                ⚠ REVIEW
              </button>
              <button
                onClick={() => setDecision('FAIL')}
                className={`flex-1 px-4 py-3 rounded-md font-medium ${
                  decision === 'FAIL'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                ✗ FAIL
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes (optional)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                placeholder="Add any additional notes about this interview..."
              />
            </div>

            <button
              onClick={handleSubmitDecision}
              disabled={!decision || submitting}
              className="w-full px-6 py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
            >
              {submitting ? 'Submitting...' : 'Submit Decision'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIInterviewReviewPage;
