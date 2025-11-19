import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  DocumentArrowUpIcon, 
  DocumentTextIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon, 
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';
import api from '../services/api';

const ResumeUpdate = () => {
  const { referenceNumber } = useParams();
  const navigate = useNavigate();
  
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [guidelines, setGuidelines] = useState(null);
  const [error, setError] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/resume-update/status/${referenceNumber}`);
      setStatus(response.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching status:', error);
      setError(error.response?.data?.detail || 'Failed to load application status');
    } finally {
      setLoading(false);
    }
  }, [referenceNumber]);

  const fetchGuidelines = async () => {
    try {
      const response = await api.get('/api/resume-update/guidelines');
      setGuidelines(response.data);
    } catch (error) {
      console.error('Error fetching guidelines:', error);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchGuidelines();
  }, [fetchStatus]);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (!allowedTypes.includes(file.type)) {
        setError('Please select a PDF, DOC, or DOCX file');
        return;
      }
      
      // Validate file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }
      
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    try {
      setUploading(true);
      setUploadResult(null);
      
      const formData = new FormData();
      formData.append('resume', selectedFile);
      
      const response = await api.post(
        `/api/resume-update/upload/${referenceNumber}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      
      setUploadResult(response.data);
      setSelectedFile(null);
      
      // Refresh status after successful upload
      await fetchStatus();
      
    } catch (error) {
      console.error('Error uploading file:', error);
      setError(error.response?.data?.detail || 'Failed to upload resume');
    } finally {
      setUploading(false);
    }
  };

  const getStatusIcon = (statusType) => {
    switch (statusType) {
      case 'completed_success':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" />;
      case 'completed_failure':
        return <XCircleIcon className="w-6 h-6 text-red-500" />;
      case 'llm_rejected':
        return <XCircleIcon className="w-6 h-6 text-red-500" />;
      case 'email_sent':
      case 'llm_approved':
        return <ClockIcon className="w-6 h-6 text-blue-500" />;
      default:
        return <ExclamationTriangleIcon className="w-6 h-6 text-yellow-500" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading application status...</p>
        </div>
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-full max-w-md bg-white rounded-lg shadow-md p-6">
          <div className="text-center">
            <XCircleIcon className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Application Not Found</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <button 
              onClick={() => navigate('/')} 
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Go to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Resume Update Portal</h1>
          <p className="mt-2 text-gray-600">Improve your application with an updated resume</p>
        </div>

        {/* Application Status */}
        {status && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              {getStatusIcon(status.update_request?.status)}
              <h2 className="text-xl font-semibold">Application Status</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-sm text-gray-600">Reference Number</p>
                <p className="font-semibold">{status.application?.reference_number}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Candidate Name</p>
                <p className="font-semibold">{status.application?.candidate_name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Position</p>
                <p className="font-semibold">{status.application?.job_title}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Current Score</p>
                <p className="font-semibold">
                  {status.application?.current_score?.toFixed(1)}/100
                  <span className="text-sm text-gray-500 ml-2">
                    (Target: {status.application?.threshold_needed})
                  </span>
                </p>
              </div>
            </div>

            {/* Progress Bar */}
            {status.application && (
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Progress to Target</span>
                  <span>{((status.application.current_score / status.application.threshold_needed) * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${Math.min((status.application.current_score / status.application.threshold_needed) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Status Message */}
            <div className="p-4 rounded-lg border border-blue-200 bg-blue-50">
              <p className="text-blue-800">{status.message}</p>
            </div>

            {/* Attempts Tracking */}
            {status.update_request && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-semibold mb-2">Update Attempts</h4>
                <div className="flex items-center gap-4 text-sm">
                  <span>Used: {status.update_request.attempts_used}/{status.update_request.max_attempts}</span>
                  <span>Remaining: {status.update_request.attempts_remaining}</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Upload Section */}
        {status?.eligible_for_update && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <DocumentArrowUpIcon className="w-5 h-5" />
              <h2 className="text-xl font-semibold">Upload Updated Resume</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select your updated resume
                </label>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileSelect}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  disabled={uploading}
                />
                <p className="mt-1 text-xs text-gray-500">
                  Accepted formats: PDF, DOC, DOCX (Max size: 10MB)
                </p>
              </div>

              {selectedFile && (
                <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
                  <DocumentTextIcon className="w-4 h-4 text-blue-600" />
                  <span className="text-sm text-blue-800">{selectedFile.name}</span>
                  <span className="text-xs text-blue-600">
                    ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                  </span>
                </div>
              )}

              <button 
                onClick={handleUpload} 
                disabled={!selectedFile || uploading}
                className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {uploading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Processing Resume...
                  </>
                ) : (
                  <>
                    <DocumentArrowUpIcon className="w-4 h-4 mr-2" />
                    Upload and Process Resume
                  </>
                )}
              </button>

              {error && (
                <div className="p-4 rounded-lg border border-red-200 bg-red-50">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="w-4 h-4 text-red-600 mr-2" />
                    <p className="text-red-800">{error}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Upload Result */}
        {uploadResult && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              {uploadResult.threshold_achieved ? (
                <CheckCircleIcon className="w-5 h-5 text-green-500" />
              ) : (
                <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />
              )}
              <h2 className="text-xl font-semibold">Resume Processing Result</h2>
            </div>
            
            <div className="space-y-4">
              <div className={`p-4 rounded-lg border ${
                uploadResult.threshold_achieved ? 'border-green-200 bg-green-50' : 
                uploadResult.final_rejection ? 'border-red-200 bg-red-50' : 'border-yellow-200 bg-yellow-50'
              }`}>
                <p className={
                  uploadResult.threshold_achieved ? 'text-green-800' : 
                  uploadResult.final_rejection ? 'text-red-800' : 'text-yellow-800'
                }>
                  {uploadResult.message}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Previous Score</p>
                  <p className="text-2xl font-bold text-gray-900">{uploadResult.old_score?.toFixed(1)}</p>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-gray-600">New Score</p>
                  <p className="text-2xl font-bold text-blue-600">{uploadResult.new_score?.toFixed(1)}</p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-gray-600">Improvement</p>
                  <p className={`text-2xl font-bold ${uploadResult.score_improvement >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {uploadResult.score_improvement >= 0 ? '+' : ''}{uploadResult.score_improvement?.toFixed(1)}
                  </p>
                </div>
              </div>

              {!uploadResult.threshold_achieved && !uploadResult.final_rejection && (
                <div className="text-center">
                  <p className="text-sm text-gray-600">
                    You have <strong>{uploadResult.attempts_remaining}</strong> more attempt(s) remaining.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Resume Improvement Guidelines */}
        {guidelines && status?.eligible_for_update && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Resume Improvement Guidelines</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-3 text-blue-600">Formatting Tips</h4>
                <ul className="space-y-2 text-sm">
                  {guidelines.guidelines.formatting.map((tip, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 bg-blue-600 rounded-full mt-2 flex-shrink-0"></span>
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold mb-3 text-green-600">Content Tips</h4>
                <ul className="space-y-2 text-sm">
                  {guidelines.guidelines.content.map((tip, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 bg-green-600 rounded-full mt-2 flex-shrink-0"></span>
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            
            <div className="mt-6 p-4 bg-red-50 rounded-lg">
              <h4 className="font-semibold mb-2 text-red-600">Common Mistakes to Avoid</h4>
              <ul className="space-y-1 text-sm">
                {guidelines.guidelines.common_mistakes.map((mistake, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <XCircleIcon className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                    {mistake}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResumeUpdate;