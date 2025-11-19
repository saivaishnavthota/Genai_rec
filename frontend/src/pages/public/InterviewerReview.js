import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import api from '../../services/api';

const InterviewerReview = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    candidate_name: '',
    candidate_email: '',
    job_title: '',
    interviewer_name: '',
    interviewer_type: '',
    review_submitted: false,
    token_expires_at: ''
  });
  
  const [reviewData, setReviewData] = useState({
    technical_skills: 5,
    communication: 5,
    problem_solving: 5,
    cultural_fit: 5,
    leadership_potential: 5,
    overall_rating: 5,
    strengths: '',
    areas_for_improvement: '',
    recommendation: 'maybe',
    additional_comments: ''
  });

  useEffect(() => {
    fetchFormData();
  }, [token]);

  const fetchFormData = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/interviewer/review-form/${token}`);
      const data = response.data;
      setFormData(data);
      
      if (data.review_submitted) {
        setSuccess(true);
      }
      
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load review form');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setReviewData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSubmitting(true);
      setError('');
      
      const response = await api.post(`/api/interviewer/submit-review/${token}`, reviewData);
      
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit review');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading review form...</p>
        </div>
      </div>
    );
  }

  if (error && !formData.candidate_name) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <XCircleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Access Error</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <p className="text-sm text-gray-500">
              This link may have expired or already been used. Please contact HR for assistance.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (success || formData.review_submitted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <CheckCircleIcon className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Review Submitted</h2>
            <p className="text-gray-600 mb-6">
              Thank you for submitting your interview review for <strong>{formData.candidate_name}</strong>.
            </p>
            <p className="text-sm text-gray-500">
              Your feedback has been recorded and will be reviewed by the hiring team.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-lg">
          {/* Header */}
          <div className="bg-blue-600 text-white px-6 py-4 rounded-t-lg">
            <h1 className="text-2xl font-bold">Interview Review</h1>
            <p className="text-blue-100">
              Candidate: <span className="font-medium">{formData.candidate_name}</span> | 
              Position: <span className="font-medium">{formData.job_title}</span>
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6">
            {error && (
              <div className="mb-6 bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-md">
                {error}
              </div>
            )}

            {/* Interviewer Info */}
            <div className="mb-6 bg-gray-50 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Interviewer Information</h3>
              <p className="text-gray-900">
                <span className="font-medium">{formData.interviewer_name}</span>
                <span className="ml-2 text-sm text-gray-600">
                  ({formData.interviewer_type === 'primary' ? 'Primary Interviewer' : 'Backup Interviewer'})
                </span>
              </p>
            </div>

            {/* Rating Scales */}
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Evaluation Criteria</h3>
              
              {[
                { key: 'technical_skills', label: 'Technical Skills & Knowledge' },
                { key: 'communication', label: 'Communication & Presentation' },
                { key: 'problem_solving', label: 'Problem-Solving Ability' },
                { key: 'cultural_fit', label: 'Cultural Fit & Team Collaboration' },
                { key: 'leadership_potential', label: 'Leadership Potential' }
              ].map(({ key, label }) => (
                <div key={key} className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    {label} <span className="text-red-500">*</span>
                  </label>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-500">Poor</span>
                    <div className="flex space-x-2">
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                        <button
                          key={num}
                          type="button"
                          onClick={() => handleInputChange(key, num)}
                          className={`w-8 h-8 rounded-full text-sm font-medium transition-colors ${
                            reviewData[key] === num
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          }`}
                        >
                          {num}
                        </button>
                      ))}
                    </div>
                    <span className="text-sm text-gray-500">Excellent</span>
                    <span className="text-sm font-medium text-blue-600 min-w-[60px]">
                      Score: {reviewData[key]}
                    </span>
                  </div>
                </div>
              ))}

              {/* Overall Rating */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">
                  Overall Rating <span className="text-red-500">*</span>
                </label>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-500">Poor</span>
                  <div className="flex space-x-2">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                      <button
                        key={num}
                        type="button"
                        onClick={() => handleInputChange('overall_rating', num)}
                        className={`w-8 h-8 rounded-full text-sm font-medium transition-colors ${
                          reviewData.overall_rating === num
                            ? 'bg-green-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        {num}
                      </button>
                    ))}
                  </div>
                  <span className="text-sm text-gray-500">Excellent</span>
                  <span className="text-sm font-medium text-green-600 min-w-[60px]">
                    Score: {reviewData.overall_rating}
                  </span>
                </div>
              </div>

              {/* Text Fields */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Key Strengths <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={reviewData.strengths}
                    onChange={(e) => handleInputChange('strengths', e.target.value)}
                    rows={3}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Describe the candidate's key strengths and positive qualities..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Areas for Improvement <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={reviewData.areas_for_improvement}
                    onChange={(e) => handleInputChange('areas_for_improvement', e.target.value)}
                    rows={3}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Describe areas where the candidate could improve or develop..."
                  />
                </div>

                {/* Recommendation */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Overall Recommendation <span className="text-red-500">*</span>
                  </label>
                  <div className="flex space-x-4">
                    {[
                      { value: 'hire', label: 'Hire', color: 'green' },
                      { value: 'maybe', label: 'Maybe', color: 'yellow' },
                      { value: 'reject', label: 'Reject', color: 'red' }
                    ].map(({ value, label, color }) => (
                      <button
                        key={value}
                        type="button"
                        onClick={() => handleInputChange('recommendation', value)}
                        className={`px-4 py-2 rounded-md font-medium transition-colors ${
                          reviewData.recommendation === value
                            ? `bg-${color}-600 text-white`
                            : `bg-${color}-100 text-${color}-800 hover:bg-${color}-200`
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Additional Comments
                  </label>
                  <textarea
                    value={reviewData.additional_comments}
                    onChange={(e) => handleInputChange('additional_comments', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Any additional comments or observations..."
                  />
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="mt-8 flex justify-end">
              <button
                type="submit"
                disabled={submitting}
                className="bg-blue-600 text-white px-6 py-3 rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Submitting...
                  </div>
                ) : (
                  'Submit Review'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default InterviewerReview;
