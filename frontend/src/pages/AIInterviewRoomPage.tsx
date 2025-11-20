import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { aiInterviewAPI, StartInterviewResponse, Question } from '../lib/api';
import { useMediaDevices } from '../hooks/useMediaDevices';
import { useWebRTC } from '../hooks/useWebRTC';
import { useHeadPose } from '../hooks/useHeadPose';
import { useSSE } from '../hooks/useSSE';
import { useProctoring } from '../hooks/useProctoring';
import { PrecheckPanel } from '../components/ai/PrecheckPanel';
import { ConsentBanner } from '../components/ai/ConsentBanner';
import { HeadPoseGauge } from '../components/ai/HeadPoseGauge';
import { VideoPreview, VideoPreviewHandle } from '../components/ai/VideoPreview';
import { LiveTimeline } from '../components/ai/LiveTimeline';
import { ProctorFlagToast } from '../components/ai/ProctorFlagToast';
import { AudioMeter } from '../components/ai/AudioMeter';
import { NetworkIndicator } from '../components/ai/NetworkIndicator';
import { formatTimecode } from '../lib/timecode';

type InterviewStage = 'precheck' | 'consent' | 'calibration' | 'live' | 'completing' | 'completed';

const AIInterviewRoomPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  const videoPreviewRef = useRef<VideoPreviewHandle>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const recordingMimeTypeRef = useRef<string>('video/webm');

  const [stage, setStage] = useState<InterviewStage>('precheck');
  const [sessionData, setSessionData] = useState<StartInterviewResponse | null>(null);
  const [sessionStartTime, setSessionStartTime] = useState<number>(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [interviewDuration, setInterviewDuration] = useState(0);
  const [questionNumber, setQuestionNumber] = useState(1);
  const [questions, setQuestions] = useState<Array<{ id: number; text: string; type: string; time_limit: number }>>([]);
  const [totalQuestions, setTotalQuestions] = useState(2);
  const [questionStartTime, setQuestionStartTime] = useState<number>(0);
  const [questionTimeRemaining, setQuestionTimeRemaining] = useState<number>(60);
  const [dismissedFlags, setDismissedFlags] = useState<Set<number>>(new Set());
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const mediaDevices = useMediaDevices();
  const webrtc = useWebRTC();
  const headPose = useHeadPose();
  const sse = useSSE();
  const proctoring = useProctoring();

  // Initialize session
  useEffect(() => {
    if (!sessionId) {
      // If no sessionId, we'd need to start a new session
      // For now, redirect to error
      navigate('/');
      return;
    }

    // Don't connect to flags stream yet - wait until interview is live
  }, [sessionId, navigate]);

  // Set video srcObject for MediaPipe processing
  useEffect(() => {
    if (videoRef.current && mediaDevices.stream) {
      videoRef.current.srcObject = mediaDevices.stream;
      videoRef.current.muted = true;
      videoRef.current.playsInline = true;
      videoRef.current.autoplay = true;
      
      // Ensure video starts playing
      videoRef.current.play().catch((err) => {
        console.warn('Auto-play prevented, user interaction required:', err);
      });
    }
  }, [mediaDevices.stream]);

  // Start video recording when interview goes live
  useEffect(() => {
    if (stage === 'live' && mediaDevices.stream && !mediaRecorderRef.current) {
      try {
        // Check if MediaRecorder is supported
        if (!window.MediaRecorder) {
          console.warn('MediaRecorder not supported in this browser');
          return;
        }

        // Find supported MIME type
        const options: MediaRecorderOptions = {};
        const mimeTypes = [
          'video/webm;codecs=vp9,opus',
          'video/webm;codecs=vp8,opus',
          'video/webm',
          'video/mp4'
        ];

        for (const mimeType of mimeTypes) {
          if (MediaRecorder.isTypeSupported(mimeType)) {
            options.mimeType = mimeType;
            break;
          }
        }

        const recorder = new MediaRecorder(mediaDevices.stream, options);
        
        recorder.ondataavailable = (event) => {
          if (event.data && event.data.size > 0) {
            recordedChunksRef.current.push(event.data);
            console.log(`Recorded chunk: ${event.data.size} bytes`);
          }
        };

        recorder.onerror = (event) => {
          console.error('MediaRecorder error:', event);
        };

        recorder.onstop = () => {
          console.log('Recording stopped. Total chunks:', recordedChunksRef.current.length);
        };

        // Start recording, collecting data every 500ms for faster chunking and upload
        // This helps with faster video processing and storage
        recorder.start(500);
        mediaRecorderRef.current = recorder;
        recordingMimeTypeRef.current = options.mimeType || 'video/webm';
        recordedChunksRef.current = []; // Reset chunks
        console.log('Video recording started with MIME type:', recordingMimeTypeRef.current);
      } catch (error) {
        console.error('Failed to start video recording:', error);
      }
    }

    // Stop recording when interview is not live
    if (stage !== 'live' && mediaRecorderRef.current) {
      if (mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
        console.log('Video recording stopped');
      }
      mediaRecorderRef.current = null;
    }
  }, [stage, mediaDevices.stream]);

  // Handle precheck complete
  const handlePrecheckReady = () => {
    console.log('Precheck ready clicked, stream:', mediaDevices.stream);
    if (mediaDevices.stream) {
      console.log('Moving to consent stage');
      setStage('consent');
    } else {
      console.warn('Cannot proceed: stream not available');
    }
  };

  // Handle consent
  const handleConsent = async () => {
    if (!mediaDevices.stream) {
      console.error('No media stream available');
      return;
    }

    try {
      // Start interview session via API if not already started
      let currentSessionData = sessionData;
      
      if (!currentSessionData && sessionId) {
        // Session already exists (from URL), just use it
        currentSessionData = {
          session_id: parseInt(sessionId),
          policy_version: '1.0',
          rubric_version: '1.0',
        };
        setSessionData(currentSessionData);
      } else if (!currentSessionData) {
        // Need to create new session - would need application_id and job_id
        console.error('No session ID and no session data available');
        alert('Session not found. Please start interview from application page.');
        return;
      }

      setStage('calibration');
      const startTime = Date.now();
      setSessionStartTime(startTime);

      // Connect WebRTC
      if (currentSessionData.webrtc_token) {
        await webrtc.connect(mediaDevices.stream, currentSessionData.session_id, currentSessionData.webrtc_token);
      } else {
        await webrtc.connect(mediaDevices.stream, currentSessionData.session_id);
      }

      // Load questions for the interview
      try {
        const questionsData = await aiInterviewAPI.getQuestions(currentSessionData.session_id);
        setQuestions(questionsData.questions);
        setTotalQuestions(questionsData.total);
        console.log('Loaded questions:', questionsData);
      } catch (error) {
        console.error('Failed to load questions:', error);
        // Use default questions if API fails (2 questions with 60-second timers)
        setQuestions([
          { id: 1, text: "Tell us about yourself and why you're interested in this position.", type: "behavioral", time_limit: 60 },
          { id: 2, text: "Can you share your experience with the required technologies?", type: "technical", time_limit: 60 }
        ]);
        setTotalQuestions(2);
      }

      // Start head pose tracking - use the visible VideoPreview element instead of hidden one
      // MediaPipe works better with visible video elements
      setTimeout(() => {
        // Try to get the video element from VideoPreview first (visible element)
        let videoElement: HTMLVideoElement | null = null;
        
        if (videoPreviewRef.current) {
          videoElement = videoPreviewRef.current.getVideoElement();
          console.log('Using VideoPreview video element for MediaPipe');
        }
        
        // Fallback to hidden video element if VideoPreview not available
        if (!videoElement && videoRef.current) {
          videoElement = videoRef.current;
          console.log('Using hidden video element for MediaPipe');
        }
        
        if (!videoElement || !mediaDevices.stream) {
          console.error('No video element or stream available for head pose tracking', {
            hasVideoPreview: !!videoPreviewRef.current,
            hasVideoRef: !!videoRef.current,
            hasStream: !!mediaDevices.stream
          });
          return;
        }
        
        // Ensure video element has stream and is playing
        if (!videoElement.srcObject) {
          videoElement.srcObject = mediaDevices.stream;
        }
        
        // Set video properties for MediaPipe
        videoElement.muted = true;
        videoElement.playsInline = true;
        videoElement.autoplay = true;
        
        // Wait for video to be ready
        const checkVideoReady = () => {
          if (videoElement && videoElement.readyState >= 2 && 
              videoElement.videoWidth > 0 && videoElement.videoHeight > 0) {
            console.log('Video is ready for MediaPipe:', {
              readyState: videoElement.readyState,
              dimensions: `${videoElement.videoWidth}x${videoElement.videoHeight}`,
              playing: !videoElement.paused,
              isVisible: videoElement.offsetWidth > 0 && videoElement.offsetHeight > 0
            });
            
            if (currentSessionData) {
              console.log('Starting head pose tracking with session:', currentSessionData.session_id);
              headPose.startTracking(videoElement, currentSessionData.session_id, startTime);
            }
          } else {
            console.log('Video not ready yet, waiting...', {
              readyState: videoElement?.readyState,
              dimensions: videoElement ? `${videoElement.videoWidth}x${videoElement.videoHeight}` : 'no video'
            });
            setTimeout(checkVideoReady, 200);
          }
        };
        
        videoElement.play().then(() => {
          console.log('Video play() resolved, checking if ready...');
          setTimeout(checkVideoReady, 300);
        }).catch((err) => {
          console.error('Failed to play video:', err);
        });
        
        // Also check on loadedmetadata event
        videoElement.addEventListener('loadedmetadata', () => {
          console.log('Video loadedmetadata event fired');
          setTimeout(checkVideoReady, 100);
        }, { once: true });
      }, 500);
      
      // Note: Don't connect to flags stream yet - wait until 'live' stage
      // This prevents unnecessary polling before interview actually starts
    } catch (error) {
      console.error('Failed to start interview:', error);
    }
  };

  // Handle calibration complete
  const handleCalibrationComplete = () => {
    setStage('live');
    // Start polling for flags only when interview goes live
    if (sessionId) {
      sse.connect(parseInt(sessionId));
      // Start proctoring (tab switch and phone detection)
      proctoring.startTracking(parseInt(sessionId), sessionStartTime);
    }
  };

  // Handle interview end
  const handleEndInterview = async () => {
    if (!sessionId) return;

    setStage('completing');
    
    try {
      // Stop tracking and disconnect
      headPose.stopTracking();
      proctoring.stopTracking();
      webrtc.disconnect();
      sse.disconnect(); // Stop polling for flags

      // Stop video recording and upload
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        console.log('Stopping video recording...');
        
        // Wait for recording to stop and collect final data
        await new Promise<void>((resolve) => {
          if (!mediaRecorderRef.current) {
            resolve();
            return;
          }

          const onStop = () => {
            console.log('Recording stopped, preparing upload...');
            mediaRecorderRef.current?.removeEventListener('stop', onStop);
            resolve();
          };

          mediaRecorderRef.current.addEventListener('stop', onStop);
          mediaRecorderRef.current.stop();
        });

        // Create blob from recorded chunks
        if (recordedChunksRef.current.length > 0) {
          const blob = new Blob(recordedChunksRef.current, { 
            type: recordingMimeTypeRef.current
          });
          console.log(`Video blob created: ${blob.size} bytes (${(blob.size / 1024 / 1024).toFixed(2)} MB)`);

          // Upload video
          try {
            await aiInterviewAPI.uploadVideo(parseInt(sessionId), blob);
            console.log('Video uploaded successfully');
          } catch (uploadError) {
            console.error('Failed to upload video:', uploadError);
            // Continue even if upload fails
          }
          
          // Clear chunks
          recordedChunksRef.current = [];
        } else {
          console.warn('No video chunks recorded');
        }
      }

      // Stop media stream after recording is done
      mediaDevices.stopStream();

      // End session
      await aiInterviewAPI.endInterview(parseInt(sessionId));

      // Wait a bit for backend processing
      setTimeout(() => {
        setStage('completed');
      }, 3000);
    } catch (error) {
      console.error('Failed to end interview:', error);
      setStage('completed'); // Still mark as completed even on error
    }
  };

  // Update current time
  useEffect(() => {
    if (stage === 'live' && sessionStartTime > 0) {
      const interval = setInterval(() => {
        const elapsed = (Date.now() - sessionStartTime) / 1000;
        setCurrentTime(elapsed);
        setInterviewDuration(elapsed);
      }, 100);

      return () => clearInterval(interval);
    }
  }, [stage, sessionStartTime]);

  // Handle flag dismissal
  const handleDismissFlag = (flagId: number) => {
    setDismissedFlags((prev) => new Set(prev).add(flagId));
  };

  // Play audio for a question
  const playQuestionAudio = async (questionId: number) => {
    if (!sessionId) return;

    try {
      setIsPlayingAudio(true);

      // Fetch audio blob
      const audioBlob = await aiInterviewAPI.getQuestionAudio(parseInt(sessionId), questionId);

      // Create audio URL
      const audioUrl = URL.createObjectURL(audioBlob);

      // Create or update audio element
      if (!audioRef.current) {
        audioRef.current = new Audio();
      }

      audioRef.current.src = audioUrl;
      audioRef.current.onended = () => {
        setIsPlayingAudio(false);
        URL.revokeObjectURL(audioUrl);
      };

      audioRef.current.onerror = () => {
        console.error('Audio playback error');
        setIsPlayingAudio(false);
        URL.revokeObjectURL(audioUrl);
      };

      await audioRef.current.play();
      console.log(`Playing audio for question ${questionId}`);
    } catch (error) {
      console.error('Failed to play question audio:', error);
      setIsPlayingAudio(false);
    }
  };

  // Auto-play question audio when question changes and reset timer
  useEffect(() => {
    if (stage === 'live' && questions.length > 0 && questions[questionNumber - 1]) {
      const currentQuestion = questions[questionNumber - 1];
      playQuestionAudio(currentQuestion.id);
      // Reset question timer
      setQuestionStartTime(Date.now());
      setQuestionTimeRemaining(currentQuestion.time_limit);
    }
  }, [questionNumber, stage, questions]);

  // Update question timer countdown
  useEffect(() => {
    if (stage === 'live' && questionStartTime > 0 && questions.length > 0 && questions[questionNumber - 1]) {
      const currentQuestion = questions[questionNumber - 1];
      const timeLimit = currentQuestion.time_limit;
      
      const interval = setInterval(() => {
        const elapsed = (Date.now() - questionStartTime) / 1000;
        const remaining = Math.max(0, timeLimit - elapsed);
        setQuestionTimeRemaining(remaining);
        
        // Auto-advance to next question when time runs out
        if (remaining <= 0 && questionNumber < totalQuestions) {
          handleNextQuestion();
        } else if (remaining <= 0 && questionNumber >= totalQuestions) {
          // All questions completed
          handleEndInterview();
        }
      }, 100);

      return () => clearInterval(interval);
    }
  }, [stage, questionStartTime, questionNumber, questions, totalQuestions]);

  // Handle question navigation
  const handleNextQuestion = () => {
    if (questionNumber < totalQuestions) {
      setQuestionNumber((prev) => prev + 1);
      console.log(`Moving to question ${questionNumber + 1}`);
    } else {
      // Last question completed - auto-end interview after a short delay
      console.log('All questions completed');
      setTimeout(() => {
        handleEndInterview();
      }, 2000);
    }
  };

  const handleRepeatQuestion = () => {
    if (questions.length > 0 && questions[questionNumber - 1]) {
      const currentQuestion = questions[questionNumber - 1];
      playQuestionAudio(currentQuestion.id);
      console.log(`Repeating question ${questionNumber}`);
    }
  };

  // Get active flags (not dismissed)
  const activeFlags = sse.flags.filter((flag) => !dismissedFlags.has(flag.id));
  const latestFlag = activeFlags[activeFlags.length - 1];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold text-gray-900">AI Interview</h1>
          <NetworkIndicator connectionState={webrtc.connectionState} stats={webrtc.stats} />
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Pre-check Stage */}
        {stage === 'precheck' && (
          <div>
            <PrecheckPanel 
              onReady={handlePrecheckReady}
              stream={mediaDevices.stream}
              mediaDevices={mediaDevices}
            />
          </div>
        )}

        {/* Consent Stage */}
        {stage === 'consent' && (
          <div>
            <ConsentBanner onConsent={handleConsent} />
          </div>
        )}

        {/* Calibration Stage */}
        {stage === 'calibration' && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Position Calibration</h2>
              <p className="text-gray-600 mb-6">
                Please position yourself in the center of the frame and look straight ahead.
                We'll calibrate your head position in the next 20-40 seconds.
              </p>
              
              {/* Video Preview for Calibration */}
              {mediaDevices.stream && (
                <div className="mb-6">
                  <VideoPreview 
                    ref={videoPreviewRef}
                    stream={mediaDevices.stream} 
                    className="w-full max-w-md mx-auto rounded-lg" 
                  />
                </div>
              )}
              
              <HeadPoseGauge headPose={headPose.headPose} />
              
              {headPose.error && (
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-yellow-800 text-sm">{headPose.error}</p>
                </div>
              )}
              
              {headPose.headPose && headPose.headPose.confidence > 0.7 && (
                <div className="mt-6 text-center">
                  <button
                    onClick={handleCalibrationComplete}
                    className="px-6 py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700 font-medium"
                  >
                    Calibration Complete
                  </button>
                </div>
              )}
              
              {!headPose.headPose && (
                <div className="mt-4 text-center text-gray-500 text-sm space-y-2">
                  <p>Make sure your face is visible and well-lit</p>
                  {headPose.error && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-red-800 text-xs">{headPose.error}</p>
                    </div>
                  )}
                  {headPose.confidence > 0 && (
                    <p className="mt-2">Detection confidence: {(headPose.confidence * 100).toFixed(0)}%</p>
                  )}
                  {headPose.faceCount > 0 && (
                    <p className="text-xs">Faces detected: {headPose.faceCount}</p>
                  )}
                  <details className="mt-2 text-xs">
                    <summary className="cursor-pointer text-blue-600">Debug Info</summary>
                    <div className="mt-2 text-left bg-gray-50 p-2 rounded text-xs">
                      <p>Face Present: {headPose.facePresent ? 'Yes' : 'No'}</p>
                      <p>Face Count: {headPose.faceCount}</p>
                      <p>Confidence: {(headPose.confidence * 100).toFixed(0)}%</p>
                      {headPose.error && <p className="text-red-600">Error: {headPose.error}</p>}
                    </div>
                  </details>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Live Interview Stage */}
        {stage === 'live' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Video Preview */}
            <div className="lg:col-span-2">
              <VideoPreview 
                ref={videoPreviewRef}
                stream={mediaDevices.stream} 
                className="aspect-video" 
              />
              {/* Hidden video element as fallback for MediaPipe */}
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="hidden"
                style={{ 
                  width: '640px', 
                  height: '480px',
                  position: 'absolute',
                  top: '-9999px',
                  left: '-9999px'
                }}
              />
            </div>

            {/* Right: Live Timeline & Controls */}
            <div className="space-y-4">
              <LiveTimeline
                flags={sse.flags}
                currentTime={currentTime}
                duration={interviewDuration}
              />

              <div className="bg-white rounded-lg shadow p-4 space-y-3">
                <AudioMeter stream={mediaDevices.stream} />

                <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                  <span>Question {questionNumber} of {totalQuestions}</span>
                  {isPlayingAudio && (
                    <div className="flex items-center gap-2 text-blue-600">
                      <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span className="text-xs">Playing...</span>
                    </div>
                  )}
                </div>

                {/* Question Display */}
                <div className="bg-gray-50 rounded-lg p-4 min-h-[120px] border border-gray-200">
                  {questions.length > 0 && questions[questionNumber - 1] ? (
                    <div>
                      <div className="mb-2 flex items-center justify-between">
                        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                          {questions[questionNumber - 1].type}
                        </span>
                        {isPlayingAudio && (
                          <span className="text-xs text-blue-600 flex items-center gap-1">
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
                            </svg>
                            Audio
                          </span>
                        )}
                      </div>
                      <p className="text-gray-800 text-base leading-relaxed">
                        {questions[questionNumber - 1].text}
                      </p>
                      <div className="mt-3 flex items-center justify-between">
                        <span className="text-xs text-gray-500">
                          Time limit: {Math.floor(questions[questionNumber - 1].time_limit / 60)}:{(questions[questionNumber - 1].time_limit % 60).toString().padStart(2, '0')}
                        </span>
                        <span className={`text-sm font-mono font-semibold ${
                          questionTimeRemaining <= 10 ? 'text-red-600' : 
                          questionTimeRemaining <= 30 ? 'text-orange-600' : 
                          'text-gray-700'
                        }`}>
                          {Math.floor(questionTimeRemaining / 60)}:{(Math.floor(questionTimeRemaining % 60)).toString().padStart(2, '0')}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-400">
                      <p>Loading question...</p>
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <button 
                    onClick={handleRepeatQuestion}
                    className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors"
                  >
                    Repeat
                  </button>
                  <button 
                    onClick={handleNextQuestion}
                    disabled={questionNumber >= totalQuestions}
                    className={`flex-1 px-4 py-2 rounded-md transition-colors ${
                      questionNumber >= totalQuestions
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-primary-600 text-white hover:bg-primary-700'
                    }`}
                  >
                    {questionNumber >= totalQuestions ? 'Complete' : 'Next'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer Controls (Live Stage) */}
        {stage === 'live' && (
          <div className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg">
            <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
              <div className="text-lg font-mono text-gray-700">
                {formatTimecode(currentTime)}
              </div>
              <button
                onClick={handleEndInterview}
                className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 font-medium"
              >
                End Interview
              </button>
            </div>
          </div>
        )}

        {/* Completing Stage */}
        {stage === 'completing' && (
          <div className="max-w-md mx-auto mt-20">
            <div className="bg-white rounded-lg shadow-lg p-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Finalizing Interview</h2>
              <p className="text-gray-600">
                Uploading recording and analyzing results...
              </p>
            </div>
          </div>
        )}

        {/* Completed Stage */}
        {stage === 'completed' && (
          <div className="max-w-md mx-auto mt-20">
            <div className="bg-white rounded-lg shadow-lg p-8 text-center">
              <div className="text-6xl mb-4">✓</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Interview Submitted</h2>
              <p className="text-gray-600 mb-6">
                Thank you for completing the interview. We'll review your responses and get back to you soon.
              </p>
              <button
                onClick={() => navigate('/application-status')}
                className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 font-medium"
              >
                View Application Status
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Flag Toasts */}
      {latestFlag && !dismissedFlags.has(latestFlag.id) && (
        <ProctorFlagToast
          flag={latestFlag}
          onDismiss={() => handleDismissFlag(latestFlag.id)}
        />
      )}
    </div>
  );
};

export default AIInterviewRoomPage;
