import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { applicationService } from '../../services/applicationService';
import { interviewService } from '../../services/interviewService';
import { aiInterviewAPI } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import { 
  ArrowLeftIcon,
  UserIcon,
  EnvelopeIcon,
  BriefcaseIcon,
  CalendarDaysIcon,
  StarIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  EyeIcon,
  UserPlusIcon
} from '@heroicons/react/24/outline';
import Swal from 'sweetalert2';

const ApplicationDetails = () => {
  const { applicationId } = useParams();
  const id = applicationId; // For backward compatibility with existing code
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updating, setUpdating] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [interviewDetails, setInterviewDetails] = useState(null);
  const [reviewData, setReviewData] = useState(null);
  const [interviewReviews, setInterviewReviews] = useState([]);
  const [aiInterviewSessions, setAiInterviewSessions] = useState([]);
  const [loadingAISessions, setLoadingAISessions] = useState(false);
  const [interviewStarted, setInterviewStarted] = useState(false);
  const [interviewStartResult, setInterviewStartResult] = useState(null);

  const loadApplication = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await applicationService.getApplication(id);
      setApplication(data);
      // Reset interview start state when loading a new application
      setInterviewStarted(false);
      setInterviewStartResult(null);
    } catch (err) {
      setError('Failed to load application details');
      console.error('Error loading application:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadApplication();
  }, [loadApplication]);

  // Auto-refresh for applications with resume update requests 
  useEffect(() => { 
    if (!application) return; 
 
    // Check if this application has an active resume update request or was just selected after an update
    const shouldAutoRefresh = ['resume_update_requested', 'pending_llm_evaluation', 'selected'].includes(application.status); 
 
    if (shouldAutoRefresh) { 
      // Poll every 30 seconds to check for updates 
      const interval = setInterval(() => { 
        loadApplication(); 
      }, 30000); 
 
      return () => clearInterval(interval); 
    } 
  }, [application, loadApplication]);

  // Load AI interview sessions
  const loadAISessions = useCallback(async () => {
    if (!id) return;
    try {
      setLoadingAISessions(true);
      const data = await aiInterviewAPI.getApplicationAISessions(parseInt(id));
      setAiInterviewSessions(data.sessions || []);
    } catch (err) {
      console.error('Error loading AI interview sessions:', err);
      setAiInterviewSessions([]);
    } finally {
      setLoadingAISessions(false);
    }
  }, [id]);

  // Auto-refresh AI interview sessions if there are any live or finalizing sessions
  useEffect(() => {
    if (!id) return;
    
    // Check if there are any sessions that need status updates
    const hasActiveSessions = aiInterviewSessions.some(session => 
      session.status === 'live' || session.status === 'finalizing' || 
      (session.ended_at && session.status === 'live')
    );
    
    if (hasActiveSessions) {
      // Poll every 15 seconds to check for status updates
      const interval = setInterval(() => {
        loadAISessions();
      }, 15000);
      
      return () => clearInterval(interval);
    }
  }, [id, aiInterviewSessions, loadAISessions]);

  const handleStatusUpdate = async (newStatus) => {
    try {
      setUpdating(true);
      await applicationService.updateApplicationStatus(id, newStatus);
      await loadApplication(); // Reload data
    } catch (err) {
      setError('Failed to update application status');
      console.error('Error updating application:', err);
    } finally {
      setUpdating(false);
    }
  };

  const handleRescore = async () => {
    try {
      setUpdating(true);
      const result = await applicationService.rescoreApplication(id);
      Swal.fire({
        title: 'Application Rescored',
        text: result?.message ? `${result.message}${result?.score ? ` (Score: ${result.score})` : ''}` : `New AI score: ${result?.score ?? ''}`,
        icon: 'success',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
      await loadApplication();
      setError('');
    } catch (err) {
      setError('Failed to rescore application');
      console.error('Error rescoring application:', err);
      Swal.fire({
        title: 'Error',
        text: err.response?.data?.detail || 'Failed to rescore application',
        icon: 'error',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
    } finally {
      setUpdating(false);
    }
  };

  const handleStartAIInterview = async () => {
    if (!application || interviewStarted) return;
    
    try {
      setUpdating(true);
      setInterviewStartResult(null);
      
      // Start AI interview session
      const response = await aiInterviewAPI.startInterview({
        application_id: parseInt(id),
        job_id: application.job_id
      });
      
      // Mark as started and show success message
      setInterviewStarted(true);
      setInterviewStartResult({
        success: true,
        message: `Interview invitation email has been sent successfully to ${application.email}`,
        sessionId: response.session_id
      });
      
      // Reload application to get updated data
      await loadApplication();
      
    } catch (err) {
      setInterviewStartResult({
        success: false,
        message: err.response?.data?.detail || 'Failed to start AI interview session. Could not send invitation email.',
      });
      console.error('Error starting AI interview:', err);
    } finally {
      setUpdating(false);
    }
  };

  const handleFetchAvailability = async () => {
    // Confirm action before generating and sending availability
    const resultConfirm = await Swal.fire({
      title: 'Fetch Availability?',
      text: 'This will generate interview slots and email the candidate.',
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: 'Send Availability',
      cancelButtonText: 'Cancel',
      confirmButtonColor: '#AF69ED',
      cancelButtonColor: '#6b7280',
      heightAuto: false,
    });

    if (!resultConfirm.isConfirmed) return;

    try {
      setUpdating(true);
      const result = await interviewService.fetchAvailability(id);
      await loadApplication(); // Reload data
      setError('');

      const fromDate = result?.slots_from ? new Date(result.slots_from).toLocaleDateString() : null;
      const toDate = result?.slots_to ? new Date(result.slots_to).toLocaleDateString() : null;
      const slotsInfo = result?.slots_count ? ` (${result.slots_count} slots)` : '';
      const rangeInfo = fromDate && toDate ? `
Slots cover: ${fromDate} to ${toDate}.` : '';

      await Swal.fire({
        title: 'Availability Requested',
        text: `${result?.message ?? 'Availability slots generated and email sent.'}${slotsInfo}${rangeInfo ? `\n${rangeInfo}` : ''}`,
        icon: 'success',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
    } catch (err) {
      setError('Failed to fetch availability slots');
      console.error('Error fetching availability:', err);
      Swal.fire({
        title: 'Error',
        text: err.response?.data?.detail || 'Failed to fetch availability slots',
        icon: 'error',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
    } finally {
      setUpdating(false);
    }
  };

  const handleScheduleInterview = async (interviewerData) => {
    try {
      setUpdating(true);
      await interviewService.scheduleInterview(id, interviewerData);
      await loadApplication(); // Reload data
      setShowScheduleModal(false);
      setError('');
    } catch (err) {
      setError('Failed to schedule interview');
      console.error('Error scheduling interview:', err);
    } finally {
      setUpdating(false);
    }
  };

  const handleMarkInterviewCompleted = async () => {
    try {
      setUpdating(true);
      const result = await interviewService.markInterviewCompleted(id);
      
      // Show success message with review token info using SweetAlert2 centered modal
      const message = (result && result.message)
        ? result.message
        : 'Interview marked as completed and review tokens sent successfully!';

      Swal.fire({
        title: 'Success',
        text: message,
        icon: 'success',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
      
      await loadApplication(); // Reload data
      setError('');
    } catch (err) {
      setError('Failed to mark interview as completed and send review tokens');
      console.error('Error marking interview completed:', err);
      Swal.fire({
        title: 'Error',
        text: err.response?.data?.detail || 'Failed to mark interview as completed and send review tokens',
        icon: 'error',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
    } finally {
      setUpdating(false);
    }
  };


  const handleFinalDecision = async (decision) => {
    const isHire = decision === 'hired';
    const resultConfirm = await Swal.fire({
      title: isHire ? 'Hire Candidate?' : 'Reject Candidate?',
      text: isHire
        ? 'This will mark the candidate as hired and send an email notification.'
        : 'This will mark the candidate as rejected and send an email notification.',
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: isHire ? 'Confirm Hire' : 'Confirm Reject',
      cancelButtonText: 'Cancel',
      confirmButtonColor: isHire ? '#AF69ED' : '#dc2626',
      cancelButtonColor: '#6b7280',
      heightAuto: false,
    });

    if (!resultConfirm.isConfirmed) return;

    try {
      setUpdating(true);
      const result = await interviewService.makeFinalDecision(id, decision);
      await loadApplication(); // Reload data
      setError('');
      await Swal.fire({
        title: 'Success',
        text: result?.message || `Candidate ${isHire ? 'hired' : 'rejected'} successfully! Email notification sent.`,
        icon: 'success',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
    } catch (err) {
      setError('Failed to make final decision');
      console.error('Error making final decision:', err);
      Swal.fire({
        title: 'Error',
        text: err.response?.data?.detail || 'Failed to make final decision',
        icon: 'error',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
    } finally {
      setUpdating(false);
    }
  };

  // Load interview details and review data when application loads
  useEffect(() => {
    const loadInterviewData = async () => {
      if (application && ['slot_selected', 'interview_confirmed', 'interview_completed', 'review_received'].includes(application.status)) {
        try {
          const details = await interviewService.getInterviewDetails(id);
          setInterviewDetails(details);
        } catch (err) {
          console.error('Error loading interview details:', err);
        }
      }

      if (application && application.status === 'review_received') {
        try {
          // Load all interview reviews
          const reviewsData = await interviewService.getAllInterviewReviews(id);
          setInterviewReviews(reviewsData.reviews || []);
          
          // Keep the old single review for backward compatibility
          const review = await interviewService.getInterviewReview(id);
          setReviewData(review);
        } catch (err) {
          console.error('Error loading review data:', err);
        }
      }
    };

    if (application) {
      loadInterviewData();
    }
    
    // Load AI interview sessions
    if (id) {
      loadAISessions();
    }
  }, [application, id]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'under_review':
        return 'bg-orange-100 text-orange-800';
      case 'shortlisted':
        return 'bg-blue-100 text-blue-800';
      case 'selected':
        return 'bg-emerald-100 text-emerald-800';
      case 'availability_requested':
        return 'bg-sky-100 text-sky-800';
      case 'slot_selected':
        return 'bg-violet-100 text-violet-800';
      case 'interview_confirmed':
        return 'bg-indigo-100 text-indigo-800';
      case 'interview_completed':
        return 'bg-amber-100 text-amber-800';
      case 'review_received':
        return 'bg-orange-100 text-orange-800';
      case 'interview_scheduled':
        return 'bg-purple-100 text-purple-800';
      case 'hired':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'under_review':
        return 'Under Review';
      case 'selected':
        return 'Selected';
      case 'availability_requested':
        return 'Availability Requested';
      case 'slot_selected':
        return 'Slot Selected';
      case 'interview_confirmed':
        return 'Interview Confirmed';
      case 'interview_completed':
        return 'Interview Completed';
      case 'review_received':
        return 'Review Received';
      case 'interview_scheduled':
        return 'Interview Scheduled';
      default:
        return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const canUpdateStatus = user?.user_type === 'hr' || user?.user_type === 'admin';

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center">
          <button onClick={() => navigate(location.state?.fromDashboard === 'hr' ? '/hr-dashboard' : '/applications')} className="mr-4">
            <ArrowLeftIcon className="h-6 w-6 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Application Details</h1>
            <p className="text-gray-600">Loading application information...</p>
          </div>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (error || !application) {
    return (
      <div className="space-y-6">
        <div className="flex items-center">
          <button onClick={() => navigate(location.state?.fromDashboard === 'hr' ? '/hr-dashboard' : '/applications')} className="mr-4">
            <ArrowLeftIcon className="h-6 w-6 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Application Details</h1>
            <p className="text-gray-600">Error loading application</p>
          </div>
        </div>
        <div className="card bg-gradient-to-br from-teal-50 to-emerald-100">
          <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-md">
            {error || 'Application not found'}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex items-center">
          <button onClick={() => navigate(location.state?.fromDashboard === 'hr' ? '/hr-dashboard' : '/applications')} className="mr-4">
            <ArrowLeftIcon className="h-6 w-6 text-gray-600 hover:text-gray-800" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{application.candidate_name}</h1>
            <p className="text-gray-600">Application for {application.job_title}</p>
            <div className="flex items-center mt-2">
              <span className={`status-badge ${getStatusColor(application.status)}`}>
                {getStatusText(application.status)}
              </span>
            </div>
          </div>
        </div>

        {/* Status Update Actions */}
        {canUpdateStatus && (
          <div className="flex space-x-2">
            {(application.status === 'pending' || application.status === 'under_review') && (
              <>
                {/* Rescore button removed */}
                <button
                  onClick={() => handleStatusUpdate('shortlisted')}
                  disabled={updating}
                  className="btn-secondary flex items-center"
                >
                  <CheckCircleIcon className="h-4 w-4 mr-2" />
                  Shortlist
                </button>
                <button
                  onClick={() => handleStatusUpdate('rejected')}
                  disabled={updating}
                  className="btn-danger flex items-center"
                >
                  <XCircleIcon className="h-4 w-4 mr-2" />
                  Reject
                </button>
              </>
            )}
            
            {application.status === 'shortlisted' && (
              <>
                <button
                  onClick={() => handleStatusUpdate('interview_scheduled')}
                  disabled={updating}
                  className="btn-primary flex items-center"
                >
                  <ClockIcon className="h-4 w-4 mr-2" />
                  Schedule Interview
                </button>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={handleStartAIInterview}
                    disabled={updating || interviewStarted}
                    className="flex items-center bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-4 py-2 rounded-md transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                    title="Start AI-powered interview with automated proctoring"
                  >
                    <UserIcon className="h-4 w-4 mr-2" />
                    {interviewStarted ? 'Interview Invitation Sent' : 'Start AI Interview'}
                  </button>
                  
                  {/* Report/Status Message */}
                  {interviewStartResult && (
                    <div className={`p-3 rounded-md text-sm ${
                      interviewStartResult.success 
                        ? 'bg-green-50 border border-green-200 text-green-800' 
                        : 'bg-red-50 border border-red-200 text-red-800'
                    }`}>
                      <div className="flex items-start">
                        {interviewStartResult.success ? (
                          <CheckCircleIcon className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
                        ) : (
                          <XCircleIcon className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
                        )}
                        <div>
                          <p className="font-medium">
                            {interviewStartResult.success ? 'Success' : 'Error'}
                          </p>
                          <p className="mt-1">{interviewStartResult.message}</p>
                          {interviewStartResult.sessionId && (
                            <p className="mt-1 text-xs opacity-75">
                              Session ID: {interviewStartResult.sessionId}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <button
                  onClick={() => handleStatusUpdate('rejected')}
                  disabled={updating}
                  className="btn-danger flex items-center"
                >
                  <XCircleIcon className="h-4 w-4 mr-2" />
                  Reject
                </button>
              </>
            )}
            
            {/* SELECTED - HR needs to fetch availability */}
            {application.status === 'selected' && (
              <>
                <button
                  onClick={handleFetchAvailability}
                  disabled={updating}
                  className="flex items-center bg-purple-500 hover:bg-purple-600 text-white font-medium px-4 py-2 rounded-md transition-colors"
                >
                  <CalendarDaysIcon className="h-4 w-4 mr-2" />
                  Fetch Availability
                </button>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={handleStartAIInterview}
                    disabled={updating || interviewStarted}
                    className="flex items-center bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-4 py-2 rounded-md transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                    title="Start AI-powered interview with automated proctoring"
                  >
                    <UserIcon className="h-4 w-4 mr-2" />
                    {interviewStarted ? 'Interview Invitation Sent' : 'Start AI Interview'}
                  </button>
                  
                  {/* Report/Status Message */}
                  {interviewStartResult && (
                    <div className={`p-3 rounded-md text-sm ${
                      interviewStartResult.success 
                        ? 'bg-green-50 border border-green-200 text-green-800' 
                        : 'bg-red-50 border border-red-200 text-red-800'
                    }`}>
                      <div className="flex items-start">
                        {interviewStartResult.success ? (
                          <CheckCircleIcon className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
                        ) : (
                          <XCircleIcon className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
                        )}
                        <div>
                          <p className="font-medium">
                            {interviewStartResult.success ? 'Success' : 'Error'}
                          </p>
                          <p className="mt-1">{interviewStartResult.message}</p>
                          {interviewStartResult.sessionId && (
                            <p className="mt-1 text-xs opacity-75">
                              Session ID: {interviewStartResult.sessionId}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* SLOT_SELECTED - HR can schedule interview */}
            {/* Moved to Interview Details card header */}

            {/* INTERVIEW_CONFIRMED - HR can mark as completed (auto-sends review tokens) */}
            {application.status === 'interview_confirmed' && (
              <button
                onClick={handleMarkInterviewCompleted}
                disabled={updating}
                className="flex items-center bg-purple-500 hover:bg-purple-600 text-white font-medium px-4 py-2 rounded-md transition-colors"
              >
                <CheckCircleIcon className="h-4 w-4 mr-2" />
                Mark Interview Completed & Send Review Tokens
              </button>
            )}

            {/* REVIEW_RECEIVED - HR makes final decision */}
            {application.status === 'review_received' && (
              <>
                <button
                  onClick={() => handleFinalDecision('hired')}
                  disabled={updating}
                  className="inline-flex items-center px-4 py-2 rounded-md text-white bg-[#AF69ED] hover:bg-[#BF92E4] shadow-sm transition-colors"
                >
                  <CheckCircleIcon className="h-4 w-4 mr-2" />
                  Hire Candidate
                </button>
                <button
                  onClick={() => handleFinalDecision('rejected')}
                  disabled={updating}
                  className="btn-danger flex items-center"
                >
                  <XCircleIcon className="h-4 w-4 mr-2" />
                  Reject Candidate
                </button>
              </>
            )}

            {/* Legacy support for old interview_scheduled status */}
            {application.status === 'interview_scheduled' && (
              <>
                <button
                  onClick={() => handleStatusUpdate('hired')}
                  disabled={updating}
                  className="btn-success flex items-center"
                >
                  <CheckCircleIcon className="h-4 w-4 mr-2" />
                  Hire
                </button>
                <button
                  onClick={() => handleStatusUpdate('rejected')}
                  disabled={updating}
                  className="btn-danger flex items-center"
                >
                  <XCircleIcon className="h-4 w-4 mr-2" />
                  Reject
                </button>
              </>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 lg:grid-cols-3 gap-4">
        {/* Main Content */}
        <div className="xl:col-span-3 lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* AI Analysis */}
          <div className="card bg-gradient-to-br from-sky-50 to-indigo-100 md:col-span-2 h-[52vh] overflow-y-auto">
             <h2 className="text-lg font-semibold mb-3">AI Analysis</h2>
             <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
               <div className={`p-3 rounded-lg ${application.ai_score != null ? getScoreColor(application.ai_score) : 'bg-gray-100 text-gray-600'}`}>
                 <div className="flex items-center justify-between mb-1">
                   <span className="text-xs font-medium">Overall AI Score</span>
                   <StarIcon className="h-4 w-4" />
                 </div>
                 <div className="text-xl font-bold">
                   {application.ai_score != null ? `${application.ai_score}%` : 'N/A'}
                 </div>
               </div>
               <div className={`p-3 rounded-lg ${application.match_score != null ? getScoreColor(application.match_score) : 'bg-gray-100 text-gray-600'}`}>
                 <div className="flex items-center justify-between mb-1">
                   <span className="text-xs font-medium">Match Score</span>
                   <CheckCircleIcon className="h-4 w-4" />
                 </div>
                 <div className="text-xl font-bold">
                   {application.match_score != null ? `${application.match_score}%` : 'N/A'}
                 </div>
               </div>
               <div className={`p-3 rounded-lg ${application.ats_score != null ? getScoreColor(application.ats_score) : 'bg-gray-100 text-gray-600'}`}>
                 <div className="flex items-center justify-between mb-1">
                   <span className="text-xs font-medium">ATS Score</span>
                   <DocumentTextIcon className="h-4 w-4" />
                 </div>
                 <div className="text-xl font-bold">
                   {application.ats_score != null ? `${application.ats_score}%` : 'N/A'}
                 </div>
               </div>
             </div>
             
             {application.ai_summary && (
               <div className="mb-4">
                 <h3 className="font-medium mb-2">AI Summary</h3>
                 <p className="text-gray-700 leading-relaxed">{application.ai_summary}</p>
               </div>
             )}
             
             {application.score_explanation && (
               <div className="mt-4 pt-4 border-t border-gray-300">
                 <h3 className="font-medium mb-2 text-indigo-700">Detailed Score Explanation</h3>
                 <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{application.score_explanation}</p>
               </div>
             )}
             
             {!application.ai_score && !application.match_score && !application.ats_score && (
               <div className="text-center py-4 text-gray-500">
                 <p>No scores available yet. The application may still be processing.</p>
                 <button
                   onClick={handleRescore}
                   disabled={updating}
                   className="mt-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm font-medium disabled:opacity-50"
                 >
                   {updating ? 'Processing...' : 'Score Application'}
                 </button>
               </div>
             )}
           </div>

          {interviewDetails && (
            <div className="md:col-span-2">
              <InterviewDetailsCard 
                details={interviewDetails}
                application={application}
                updating={updating}
                onScheduleClick={() => setShowScheduleModal(true)}
              />
            </div>
          )}

          {/* Cover Letter */}
          {application.cover_letter && (
            <div className="card bg-gradient-to-br from-rose-50 to-pink-100">
               <h2 className="text-lg font-semibold mb-4">Cover Letter</h2>
               <div className="prose max-w-none">
                 <div className="whitespace-pre-wrap text-gray-700">
                   {application.cover_letter}
                 </div>
               </div>
             </div>
          )}

          {/* Resume Content */}
          {application.resume_text && (
            <div className="card bg-gradient-to-br from-gray-50 to-slate-100">
               <h2 className="text-lg font-semibold mb-4">Resume Content</h2>
               <div className="prose max-w-none">
                 <div className="whitespace-pre-wrap text-gray-700 text-sm">
                   {application.resume_text}
                 </div>
               </div>
             </div>
          )}

          {/* Skills Match */}
          {application.skills_match && application.skills_match.length > 0 && (
            <div className="card bg-gradient-to-br from-emerald-50 to-green-100">
               <h2 className="text-lg font-semibold mb-4">Skills Analysis</h2>
               <div className="space-y-2">
                 {application.skills_match.map((skill, index) => (
                   <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                     <span className="font-medium">{skill.skill}</span>
                     <span className={`text-sm ${skill.match ? 'text-green-600' : 'text-red-600'}`}>
                       {skill.match ? '✓ Match' : '✗ Missing'}
                     </span>
                   </div>
                 ))}
               </div>
             </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="grid grid-cols-1 gap-4">
          {/* Candidate Info */}
          <div className="card bg-gradient-to-br from-amber-50 to-orange-100">
             <h3 className="text-lg font-semibold mb-3">Candidate Information</h3>
             <div className="space-y-2.5">
               <div className="flex items-start">
                 <UserIcon className="h-4 w-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0" />
                 <div className="min-w-0 flex-1">
                   <div className="text-xs text-gray-500 uppercase tracking-wide">Name</div>
                   <div className="font-medium text-sm truncate">{application.candidate_name}</div>
                 </div>
               </div>

               <div className="flex items-start">
                 <EnvelopeIcon className="h-4 w-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0" />
                 <div className="min-w-0 flex-1">
                   <div className="text-xs text-gray-500 uppercase tracking-wide">Email</div>
                   <div className="font-medium text-sm truncate" title={application.candidate_email}>
                     {application.candidate_email}
                   </div>
                 </div>
               </div>

               {application.candidate_phone && (
                 <div className="flex items-start">
                   <UserIcon className="h-4 w-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0" />
                   <div className="min-w-0 flex-1">
                     <div className="text-xs text-gray-500 uppercase tracking-wide">Phone</div>
                     <div className="font-medium text-sm">{application.candidate_phone}</div>
                   </div>
                 </div>
               )}

               <div className="flex items-start">
                 <BriefcaseIcon className="h-4 w-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0" />
                 <div className="min-w-0 flex-1">
                   <div className="text-xs text-gray-500 uppercase tracking-wide">Position</div>
                   <div className="font-medium text-sm">{application.job_title}</div>
                 </div>
               </div>

               <div className="flex items-start">
                 <CalendarDaysIcon className="h-4 w-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0" />
                 <div className="min-w-0 flex-1">
                   <div className="text-xs text-gray-500 uppercase tracking-wide">Applied</div>
                   <div className="font-medium text-sm">
                     {new Date(application.created_at).toLocaleDateString()}
                   </div>
                 </div>
               </div>

               {application.ai_score != null && (
                 <div className="flex items-start">
                   <StarIcon className="h-4 w-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0" />
                   <div className="min-w-0 flex-1">
                     <div className="text-xs text-gray-500 uppercase tracking-wide">AI Score</div>
                     <div className={`font-medium text-sm ${getScoreColor(application.ai_score).split(' ')[0]}`}>
                       {application.ai_score}%
                     </div>
                   </div>
                 </div>
               )}

               {application.match_score != null && (
                 <div className="flex items-start">
                   <CheckCircleIcon className="h-4 w-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0" />
                   <div className="min-w-0 flex-1">
                     <div className="text-xs text-gray-500 uppercase tracking-wide">Match Score</div>
                     <div className={`font-medium text-sm ${getScoreColor(application.match_score).split(' ')[0]}`}>
                       {application.match_score}%
                     </div>
                   </div>
                 </div>
               )}

               {application.ats_score != null && (
                 <div className="flex items-start">
                   <DocumentTextIcon className="h-4 w-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0" />
                   <div className="min-w-0 flex-1">
                     <div className="text-xs text-gray-500 uppercase tracking-wide">ATS Score</div>
                     <div className={`font-medium text-sm ${getScoreColor(application.ats_score).split(' ')[0]}`}>
                       {application.ats_score}%
                     </div>
                   </div>
                 </div>
               )}
             </div>
           </div>

          {/* Resume Download */}
          {application.resume_filename && (
            <div className="card bg-gradient-to-br from-sky-50 to-cyan-100">
               <h3 className="text-lg font-semibold mb-2">Resume</h3>
               <div className="flex items-center justify-between p-2.5 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                 <div className="flex items-center min-w-0 flex-1">
                   <DocumentTextIcon className="h-5 w-5 text-blue-500 mr-2.5 flex-shrink-0" />
                   <div className="min-w-0">
                     <div className="font-medium text-sm truncate" title={application.resume_filename}>
                       {application.resume_filename.split('-').slice(-1)[0] || 'Resume File'}
                     </div>
                     <div className="text-xs text-gray-500">PDF Document</div>
                   </div>
                 </div>
                 <button
                   onClick={() => {
                     const baseApiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
                     const resumePath = application.resume_url || `/uploads/${application.resume_filename}`;
                     const absoluteUrl = resumePath.startsWith('http') ? resumePath : `${baseApiUrl}${resumePath}`;
                     window.open(absoluteUrl, '_blank');
                   }}
                   className="p-1.5 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors flex-shrink-0"
                   title="View Resume"
                 >
                   <EyeIcon className="h-4 w-4" />
                 </button>
               </div>
             </div>
          )}

          {/* Additional Info */}
          {application.additional_info && (
            <div className="card bg-gradient-to-br from-violet-50 to-purple-100">
               <h3 className="text-lg font-semibold mb-3">Additional Information</h3>
               <p className="text-gray-700 text-sm leading-relaxed">
                 {application.additional_info}
               </p>
             </div>
          )}

          {/* Application Timeline */}
          <div className="card bg-gradient-to-br from-slate-50 to-gray-100">
             <h3 className="text-lg font-semibold mb-2">Timeline</h3>
             <div className="space-y-2.5">
               <div className="flex items-start">
                 <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-2.5 mt-1.5 flex-shrink-0"></div>
                 <div className="min-w-0">
                   <div className="text-sm font-medium">Application Submitted</div>
                   <div className="text-xs text-gray-500">
                     {new Date(application.created_at).toLocaleDateString()} at {new Date(application.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                   </div>
                 </div>
               </div>
               
               {application.processed_at && (
                 <div className="flex items-start">
                   <div className="w-1.5 h-1.5 bg-yellow-500 rounded-full mr-2.5 mt-1.5 flex-shrink-0"></div>
                   <div className="min-w-0">
                     <div className="text-sm font-medium">AI Processing Complete</div>
                     <div className="text-xs text-gray-500">
                       {new Date(application.processed_at).toLocaleDateString()} at {new Date(application.processed_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                     </div>
                   </div>
                 </div>
               )}
               
               {application.updated_at !== application.created_at && (
                 <div className="flex items-start">
                   <div className="w-1.5 h-1.5 bg-green-500 rounded-full mr-2.5 mt-1.5 flex-shrink-0"></div>
                   <div className="min-w-0">
                     <div className="text-sm font-medium">Status Updated</div>
                     <div className="text-xs text-gray-500">
                       {new Date(application.updated_at).toLocaleDateString()} at {new Date(application.updated_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                     </div>
                   </div>
                 </div>
               )}
             </div>
           </div>
        </div>
      </div>

      {/* Schedule Interview Modal */}
      {showScheduleModal && (
        <ScheduleInterviewModal
          application={application}
          onClose={() => setShowScheduleModal(false)}
          onSchedule={handleScheduleInterview}
          updating={updating}
        />
      )}


      {/* AI Interview Sessions Section */}
      {aiInterviewSessions.length > 0 && (
        <div className="card bg-gradient-to-br from-purple-50 to-indigo-100 md:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">AI Interview Sessions</h2>
            <span className="text-sm text-gray-600">
              {aiInterviewSessions.length} session{aiInterviewSessions.length !== 1 ? 's' : ''}
            </span>
          </div>
          
          <div className="space-y-3">
            {aiInterviewSessions.map((session) => {
              // Determine effective status: if ended_at exists but status is still 'live', treat as finalizing
              const effectiveStatus = session.ended_at && session.status === 'live' 
                ? 'finalizing' 
                : session.status;
              
              // Show View Report button if completed, finalizing, or has ended_at (interview finished)
              const showViewReport = effectiveStatus === 'completed' || 
                                    effectiveStatus === 'finalizing' || 
                                    session.ended_at !== null;
              
              return (
              <div key={session.id} className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-sm font-medium text-gray-900">
                        Session #{session.id}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        effectiveStatus === 'completed' ? 'bg-green-100 text-green-800' :
                        effectiveStatus === 'finalizing' ? 'bg-yellow-100 text-yellow-800' :
                        effectiveStatus === 'live' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {effectiveStatus === 'completed' ? 'COMPLETED' :
                         effectiveStatus === 'finalizing' ? 'FINALIZING' :
                         effectiveStatus === 'live' ? 'LIVE' :
                         effectiveStatus?.toUpperCase() || 'CREATED'}
                    </span>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      {session.started_at && (
                        <span>
                          Started: {new Date(session.started_at).toLocaleString()}
                        </span>
                      )}
                      {session.ended_at && (
                        <span>
                          Ended: {new Date(session.ended_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                    
                    {session.total_score !== null && session.total_score !== undefined && (
                      <div className="mt-2">
                        <span className="text-sm font-medium text-gray-700">Score: </span>
                        <span className={`text-lg font-bold ${
                          Number(session.total_score) >= 8 ? 'text-green-600' :
                          Number(session.total_score) >= 6 ? 'text-yellow-600' :
                          'text-red-600'
                        }`}>
                          {Number(session.total_score).toFixed(1)}/10
                        </span>
                      </div>
                    )}
                    
                    {session.recommendation && (
                      <div className="mt-1">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          session.recommendation === 'pass' ? 'bg-green-100 text-green-800' :
                          session.recommendation === 'review' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {session.recommendation.toUpperCase()}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex gap-2 ml-4">
                    {showViewReport && (
                      <button
                        onClick={() => navigate(`/review/ai-interview/${session.id}`)}
                        className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm font-medium"
                      >
                        View Report
                      </button>
                    )}
                    {/* View Live button removed - only show View Report for completed/finalizing sessions */}
                  </div>
                </div>
              </div>
            )})}
          </div>
        </div>
      )}

      {/* Interview Reviews Section */}
      {interviewReviews.length > 0 && (
        <div className="mt-6">
          <div className="card bg-gradient-to-br from-violet-50 to-purple-100 backdrop-blur">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <EyeIcon className="h-5 w-5 text-purple-600" />
                <h3 className="text-lg font-semibold">Interview Reviews</h3>
              </div>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-white/70 text-purple-700">
                {interviewReviews.length} reviews
              </span>
            </div>
            <div className="space-y-6">
              {interviewReviews.map((review, index) => (
                <div key={review.id || index} className="rounded-lg p-4 bg-white/60 border border-white/70 shadow-sm hover:shadow-md transition">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-medium text-gray-900">
                      {review.interviewer_name || review.interviewer_email}
                      <span className="ml-2 text-sm text-gray-500">
                        ({review.interviewer_type === 'primary' ? 'Primary' : 'Backup'} Interviewer)
                      </span>
                    </h4>
                    <span className="text-xs text-gray-500">
                      {review.review_submitted_at ? new Date(review.review_submitted_at).toLocaleString() : 'N/A'}
                    </span>
                  </div>
                  <InterviewReviewCard 
                    review={review}
                    application={application}
                    hideHeader={true}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Fallback: Single Review Data Section (for backward compatibility) */}
      {reviewData && interviewReviews.length === 0 && (
        <div className="mt-6">
          <InterviewReviewCard 
            review={reviewData}
            application={application}
          />
        </div>
      )}
    </div>
  );
};

// Schedule Interview Modal Component
const ScheduleInterviewModal = ({ application, onClose, onSchedule, updating }) => {
  const [formData, setFormData] = useState({
    primary_interviewer_name: '',
    primary_interviewer_email: '',
    backup_interviewer_name: '',
    backup_interviewer_email: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const primaryEmail = (formData.primary_interviewer_email || '').trim().toLowerCase();
    const backupEmail = (formData.backup_interviewer_email || '').trim().toLowerCase();

    if (primaryEmail && backupEmail && primaryEmail === backupEmail) {
      Swal.fire({
        icon: 'error',
        title: 'Emails must differ',
        text: 'Primary and Secondary interviewer emails cannot be the same.',
        confirmButtonColor: '#AF69ED'
      });
      return;
    }

    onSchedule(formData);
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    // Style Schedule Interview Modal with lumen green theme and improved layout
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-gradient-to-br from-purple-50 to-purple-200 border border-purple-300 rounded-lg p-6 w-full max-w-lg shadow-xl">
        <h3 className="text-lg font-semibold mb-4 text-purple-800">Schedule Interview</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Primary Interviewer Name *</label>
              <input
                type="text"
                required
                value={formData.primary_interviewer_name}
                onChange={(e) => handleChange('primary_interviewer_name', e.target.value)}
                className="w-full border border-purple-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-50 bg-white/80"
                placeholder="John Smith"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Primary Interviewer Email *</label>
              <input
                type="email"
                required
                value={formData.primary_interviewer_email}
                onChange={(e) => handleChange('primary_interviewer_email', e.target.value)}
                className="w-full border border-purple-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-50 bg-white/80"
                placeholder="john.smith@company.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Secondary Interviewer Name *</label>
              <input
                type="text"
                required
                value={formData.backup_interviewer_name}
                onChange={(e) => handleChange('backup_interviewer_name', e.target.value)}
                className="w-full border border-purple-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-50 bg-white/80"
                placeholder="Jane Doe"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Secondary Interviewer Email *</label>
              <input
                type="email"
                required
                value={formData.backup_interviewer_email}
                onChange={(e) => handleChange('backup_interviewer_email', e.target.value)}
                className="w-full border border-purple-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-50 bg-white/80"
                placeholder="jane.doe@company.com"
              />
            </div>
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={updating}
              className="flex-1 btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updating}
              className="flex-1 inline-flex justify-center items-center px-4 py-2 rounded-md text-white bg-[#AF69ED] hover:bg-[BF92E4] transition-colors shadow-sm"
            >
              {updating ? 'Scheduling...' : 'Schedule Interview'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Interview Details Card Component
const InterviewDetailsCard = ({ details, application, updating, onScheduleClick }) => {
  return (
    <div className="card bg-gradient-to-br from-teal-50 to-emerald-100">
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-semibold">Interview Details</h3>
        {application.status === 'slot_selected' && (
          <button
            onClick={onScheduleClick}
            disabled={updating}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-[#AF69ED] hover:bg-[#BF92E4] transition-colors shadow-sm"
          >
            <UserPlusIcon className="h-4 w-4 mr-2" />
            Schedule Interview
          </button>
        )}
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div className="space-y-2">
          <div>
            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">Date & Time</label>
            <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-2">
              <p className="text-sm font-medium text-gray-900">
                {details.selected_slot_date ? new Date(details.selected_slot_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }) : 'Not selected'}
              </p>
              <span className="hidden sm:inline text-gray-400">•</span>
              <p className="text-sm text-gray-700">
                {details.selected_slot_time ? new Date(`2000-01-01T${details.selected_slot_time}`).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }) : 'Not selected'}
              </p>
            </div>
          </div>
          
          <div>
            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">Duration</label>
            <p className="text-sm text-gray-900">{details.interview_duration || 60} minutes</p>
          </div>
        </div>
        
        <div className="space-y-2">
          <div>
            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">Primary Interviewer</label>
            <p className="text-sm font-medium text-gray-900 truncate" title={details.primary_interviewer_name}>
              {details.primary_interviewer_name || 'Not assigned'}
            </p>
            <p className="text-xs text-gray-600 truncate" title={details.primary_interviewer_email}>
              {details.primary_interviewer_email}
            </p>
          </div>
          
          <div>
            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">Backup Interviewer</label>
            <p className="text-sm font-medium text-gray-900 truncate" title={details.backup_interviewer_name}>
              {details.backup_interviewer_name || 'Not assigned'}
            </p>
            <p className="text-xs text-gray-600 truncate" title={details.backup_interviewer_email}>
              {details.backup_interviewer_email}
            </p>
          </div>
        </div>
      </div>
      
      {details.google_meet_link && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="ml-2">
                  <p className="text-sm font-medium text-green-800">Video Call Ready</p>
                </div>
              </div>
              <a 
                href={details.google_meet_link} 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700 transition-colors"
              >
                Join Meeting
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Interview Review Card Component
const InterviewReviewCard = ({ review, application, hideHeader = false }) => {
  const getScoreColor = (score) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    if (score >= 4) return 'text-orange-600';
    return 'text-red-600';
  };

  const getRecommendationColor = (recommendation) => {
    switch (recommendation) {
      case 'hire': return 'bg-green-100 text-green-800';
      case 'maybe': return 'bg-yellow-100 text-yellow-800';
      case 'reject': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className={hideHeader ? "" : "card bg-gradient-to-br from-violet-50 to-purple-100 backdrop-blur"}>
      {!hideHeader && (
        <div className="flex items-center space-x-2 mb-4">
          <EyeIcon className="h-5 w-5 text-purple-600" />
          <h3 className="text-lg font-semibold">Interview Review</h3>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 className="font-medium mb-3">Scores (1-10 scale)</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Technical Skills:</span>
              <span className={`font-medium ${getScoreColor(review.technical_score)}`}>
                {review.technical_score}/10
              </span>
            </div>
            <div className="flex justify-between">
              <span>Communication:</span>
              <span className={`font-medium ${getScoreColor(review.communication_score)}`}>
                {review.communication_score}/10
              </span>
            </div>
            <div className="flex justify-between">
              <span>Problem Solving:</span>
              <span className={`font-medium ${getScoreColor(review.problem_solving_score)}`}>
                {review.problem_solving_score}/10
              </span>
            </div>
            <div className="flex justify-between">
              <span>Cultural Fit:</span>
              <span className={`font-medium ${getScoreColor(review.cultural_fit_score)}`}>
                {review.cultural_fit_score}/10
              </span>
            </div>
            {review.leadership_potential && (
              <div className="flex justify-between">
                <span>Leadership Potential:</span>
                <span className={`font-medium ${getScoreColor(review.leadership_potential)}`}>
                  {review.leadership_potential}/10
                </span>
              </div>
            )}
          </div>
        </div>
        
        <div>
          <h4 className="font-medium mb-3">Overall Assessment</h4>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700">Recommendation</label>
              <span className={`inline-block px-2 py-1 rounded-full text-sm font-medium ${getRecommendationColor(review.overall_recommendation)}`}>
                {review.overall_recommendation?.toUpperCase()}
              </span>
            </div>
            
            {review.overall_rating && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Overall Rating</label>
                <p className={`text-lg font-semibold ${getScoreColor(review.overall_rating)}`}>
                  {review.overall_rating}/10
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {review.strengths && (
        <div className="mt-6">
          <h4 className="font-medium mb-2">Strengths</h4>
          <p className="text-gray-700 whitespace-pre-line">{review.strengths}</p>
        </div>
      )}
      
      {review.areas_for_improvement && (
        <div className="mt-4">
          <h4 className="font-medium mb-2">Areas for Improvement</h4>
          <p className="text-gray-700 whitespace-pre-line">{review.areas_for_improvement}</p>
        </div>
      )}
      
      {review.additional_comments && (
        <div className="mt-4">
          <h4 className="font-medium mb-2">Additional Comments</h4>
          <p className="text-gray-700 whitespace-pre-line">{review.additional_comments}</p>
        </div>
      )}
      
      {!hideHeader && (
        <div className="mt-4 pt-4 border-t text-sm text-gray-500">
          <p>Review submitted: {review.review_submitted_at ? new Date(review.review_submitted_at).toLocaleString() : 'N/A'}</p>
          <p>Interviewer: {review.interviewer_name || review.interviewer_email}</p>
          {review.interviewer_type && <p>Role: {review.interviewer_type === 'primary' ? 'Primary' : 'Backup'} Interviewer</p>}
        </div>
      )}
    </div>
  );
};

export default ApplicationDetails;