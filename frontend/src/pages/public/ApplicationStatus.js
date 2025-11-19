import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { applicationService } from '../../services/applicationService';
import { 
  MagnifyingGlassIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  CalendarDaysIcon,
  UserIcon,
  BriefcaseIcon,
  StarIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';

const ApplicationStatus = () => {
  const [referenceNumber, setReferenceNumber] = useState('');
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!referenceNumber.trim()) {
      setError('Please enter a reference number');
      return;
    }

    try {
      setLoading(true);
      setError('');
      const data = await applicationService.getApplicationByReference(referenceNumber.trim());
      setApplication(data);
    } catch (err) {
      setError('Application not found. Please check your reference number.');
      setApplication(null);
      console.error('Error finding application:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-gradient-to-br from-yellow-50 to-amber-100 text-amber-800 border-amber-200';
      case 'shortlisted':
        return 'bg-gradient-to-br from-sky-50 to-blue-100 text-blue-800 border-blue-200';
      case 'interview_scheduled':
        return 'bg-gradient-to-br from-violet-50 to-fuchsia-100 text-purple-800 border-purple-200';
      case 'hired':
        return 'bg-gradient-to-br from-green-50 to-emerald-100 text-green-800 border-green-200';
      case 'rejected':
        return 'bg-gradient-to-br from-rose-50 to-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gradient-to-br from-gray-50 to-zinc-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="h-6 w-6" />;
      case 'under_review':
        return <ClockIcon className="h-6 w-6" />;
      case 'shortlisted':
        return <CheckCircleIcon className="h-6 w-6" />;
      case 'interview_scheduled':
        return <CalendarDaysIcon className="h-6 w-6" />;
      case 'hired':
        return <CheckCircleIcon className="h-6 w-6" />;
      case 'rejected':
        return <XCircleIcon className="h-6 w-6" />;
      default:
        return <ClockIcon className="h-6 w-6" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending':
        return 'Application Under Review';
      case 'shortlisted':
        return 'Application Shortlisted';
      case 'interview_scheduled':
        return 'Interview Scheduled';
      case 'hired':
        return 'Congratulations! You\'re Hired';
      case 'rejected':
        return 'Application Not Selected';
      default:
        return 'Application Submitted';
    }
  };

  const getStatusDescription = (status) => {
    switch (status) {
      case 'pending':
        return 'Your application is being reviewed by our AI system and HR team. We\'ll update you soon!';
      case 'shortlisted':
        return 'Great news! Your application has been shortlisted. Our HR team will contact you soon.';
      case 'interview_scheduled':
        return 'You\'ve been selected for an interview! Check your email for details and scheduling information.';
      case 'hired':
        return 'Welcome to the team! Our HR department will contact you with next steps and onboarding information.';
      case 'rejected':
        return 'Thank you for your interest. While we won\'t be moving forward with your application at this time, we encourage you to apply for other positions.';
      default:
        return 'Your application has been submitted successfully.';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-700 bg-gradient-to-br from-green-50 to-emerald-100 border-green-200';
    if (score >= 60) return 'text-yellow-700 bg-gradient-to-br from-yellow-50 to-amber-100 border-yellow-200';
    return 'text-red-700 bg-gradient-to-br from-rose-50 to-red-100 border-red-200';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-primary-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link 
            to="/careers" 
            className="inline-flex items-center text-primary-600 hover:text-primary-700 mb-4"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Back to Careers
          </Link>
          
          <div className="text-center">
            <h1 className="text-3xl font-bold text-primary-900 mb-2 drop-shadow-sm">Check Application Status</h1>
            <p className="text-gray-700">Enter your reference number to track your application progress</p>
          </div>
        </div>

        {/* Search Form */}
        <div className="card bg-gradient-to-br from-indigo-50 to-blue-100 backdrop-blur border border-blue-200 rounded-2xl shadow-sm mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Application Reference Number</label>
              <div className="flex gap-4">
                <input
                  type="text"
                  value={referenceNumber}
                  onChange={(e) => setReferenceNumber(e.target.value)}
                  className="flex-1 border border-blue-200 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white/80"
                  placeholder="Enter your reference number (e.g., APP-12345-67890)"
                />
                <button type="submit" disabled={loading} className="btn-primary flex items-center px-6">
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  ) : (
                    <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
                  )}
                  Search
                </button>
              </div>
            </div>

            {error && (
              <div className="bg-gradient-to-br from-red-50 to-rose-100 border border-rose-300 text-rose-800 px-4 py-3 rounded-md text-sm">
                {error}
              </div>
            )}
          </form>
        </div>

        {/* Application Results */}
        {application && (
          <div className="space-y-6">
            {/* Status Overview */}
            <div className={`card backdrop-blur rounded-2xl shadow-sm border-2 ${getStatusColor(application.status)}`}>
              <div className="flex items-center">
                <div className="flex-shrink-0 mr-4">
                  {getStatusIcon(application.status)}
                </div>
                <div className="flex-1">
                  <h2 className="text-xl font-bold mb-1">
                    {getStatusText(application.status)}
                  </h2>
                  <p className="text-sm opacity-90">
                    {getStatusDescription(application.status)}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Application Details */}
              <div className="lg:col-span-2 space-y-6">
                {/* Basic Information */}
                <div className="card bg-gradient-to-br from-rose-50 to-pink-100 backdrop-blur border border-pink-200 rounded-2xl shadow-sm">
                  <h3 className="text-lg font-semibold mb-4">Application Details</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-center">
                      <UserIcon className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <div className="text-sm text-gray-500">Candidate</div>
                        <div className="font-medium">{application.candidate_name}</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center">
                      <BriefcaseIcon className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <div className="text-sm text-gray-500">Position</div>
                        <div className="font-medium">{application.job_title}</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center">
                      <CalendarDaysIcon className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <div className="text-sm text-gray-500">Applied Date</div>
                        <div className="font-medium">
                          {new Date(application.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center">
                      <div className="w-5 h-5 mr-3 flex items-center justify-center">
                        <div className="w-3 h-3 bg-primary-600 rounded-full"></div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">Reference</div>
                        <div className="font-medium font-mono text-sm">
                          {application.reference_number}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* AI Analysis Results */}
                {(application.ai_score || application.match_score || application.ats_score) && (
                  <div className="card bg-gradient-to-br from-amber-50 to-orange-100 backdrop-blur border border-orange-200 rounded-2xl shadow-sm">
                    <h3 className="text-lg font-semibold mb-4">AI Analysis Results</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {application.ai_score && (
                        <div className={`p-4 rounded-lg border ${getScoreColor(application.ai_score)}`}>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">Overall Score</span>
                            <StarIcon className="h-5 w-5" />
                          </div>
                          <div className="text-2xl font-bold">{application.ai_score}%</div>
                        </div>
                      )}
                      
                      {application.match_score && (
                        <div className={`p-4 rounded-lg border ${getScoreColor(application.match_score)}`}>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">Skills Match</span>
                            <CheckCircleIcon className="h-5 w-5" />
                          </div>
                          <div className="text-2xl font-bold">{application.match_score}%</div>
                        </div>
                      )}
                      
                      {application.ats_score && (
                        <div className={`p-4 rounded-lg border ${getScoreColor(application.ats_score)}`}>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">ATS Score</span>
                            <div className="w-5 h-5 bg-current rounded opacity-20"></div>
                          </div>
                          <div className="text-2xl font-bold">{application.ats_score}%</div>
                        </div>
                      )}
                    </div>
                    
                    {application.ai_summary && (
                      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                        <h4 className="font-medium mb-2">AI Summary</h4>
                        <p className="text-gray-700 text-sm leading-relaxed">
                          {application.ai_summary}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Timeline */}
                <div className="card bg-gradient-to-br from-purple-50 to-violet-100 backdrop-blur border border-violet-200 rounded-2xl shadow-sm">
                  <h3 className="text-lg font-semibold mb-4">Application Timeline</h3>
                  <div className="space-y-4">
                    <div className="flex items-start">
                      <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center mr-4">
                        <CheckCircleIcon className="h-4 w-4 text-white" />
                      </div>
                      <div>
                        <div className="font-medium">Application Submitted</div>
                        <div className="text-sm text-gray-600">
                          {new Date(application.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    
                    {application.processed_at && (
                      <div className="flex items-start">
                        <div className="flex-shrink-0 w-8 h-8 bg-yellow-600 rounded-full flex items-center justify-center mr-4">
                          <StarIcon className="h-4 w-4 text-white" />
                        </div>
                        <div>
                          <div className="font-medium">AI Processing Complete</div>
                          <div className="text-sm text-gray-600">
                            {new Date(application.processed_at).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {application.updated_at !== application.created_at && (
                      <div className="flex items-start">
                        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mr-4 ${
                          application.status === 'hired' ? 'bg-green-600' : 
                          application.status === 'rejected' ? 'bg-red-600' : 'bg-purple-600'
                        }`}>
                          {getStatusIcon(application.status)}
                        </div>
                        <div>
                          <div className="font-medium">Status Updated to "{getStatusText(application.status)}"</div>
                          <div className="text-sm text-gray-600">
                            {new Date(application.updated_at).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Next Steps */}
                <div className="card bg-gradient-to-br from-sky-50 to-cyan-100 backdrop-blur border border-cyan-200 rounded-2xl shadow-sm">
                  <h3 className="text-lg font-semibold mb-3">What's Next?</h3>
                  <div className="space-y-3 text-sm">
                    {application.status === 'pending' && (
                      <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                        <div className="font-medium text-yellow-800 mb-1">Under Review</div>
                        <div className="text-yellow-700">
                          Our team is reviewing your application. This typically takes 3-5 business days.
                        </div>
                      </div>
                    )}
                    
                    {application.status === 'shortlisted' && (
                      <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                        <div className="font-medium text-blue-800 mb-1">Interview Invitation</div>
                        <div className="text-blue-700">
                          Congratulations! Our HR team will contact you within 2-3 business days to schedule an interview.
                        </div>
                      </div>
                    )}
                    
                    {application.status === 'interview_scheduled' && (
                      <div className="p-3 bg-purple-50 border border-purple-200 rounded">
                        <div className="font-medium text-purple-800 mb-1">Interview Scheduled</div>
                        <div className="text-purple-700">
                          Check your email for interview details including date, time, and format.
                        </div>
                      </div>
                    )}
                    
                    {application.status === 'hired' && (
                      <div className="p-3 bg-green-50 border border-green-200 rounded">
                        <div className="font-medium text-green-800 mb-1">Welcome Aboard!</div>
                        <div className="text-green-700">
                          Our HR team will send you onboarding information and next steps.
                        </div>
                      </div>
                    )}
                    
                    {application.status === 'rejected' && (
                      <div className="p-3 bg-gray-50 border border-gray-200 rounded">
                        <div className="font-medium text-gray-800 mb-1">Keep Exploring</div>
                        <div className="text-gray-700">
                          We encourage you to apply for other positions that match your skills.
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Contact Information */}
                <div className="card bg-gradient-to-br from-lime-50 to-green-100 backdrop-blur border border-lime-200 rounded-2xl shadow-sm">
                  <h3 className="text-lg font-semibold mb-3">Need Help?</h3>
                  <div className="text-sm space-y-2">
                    <p className="text-gray-600">
                      If you have questions about your application, please contact our HR team:
                    </p>
                    <div className="space-y-1">
                      <div>📧 careers@company.com</div>
                      <div>📞 (555) 123-4567</div>
                    </div>
                    <p className="text-xs text-gray-500 mt-3">
                      Please include your reference number when contacting us.
                    </p>
                  </div>
                </div>

                {/* Related Jobs */}
                <div className="card bg-gradient-to-br from-zinc-50 to-stone-100 backdrop-blur border border-stone-200 rounded-2xl shadow-sm">
                  <h3 className="text-lg font-semibold mb-3">More Opportunities</h3>
                  <Link to="/careers" className="btn-secondary w-full text-center">
                    Browse Open Positions
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* How to Find Reference Number */}
        {!application && (
          <div className="card bg-gradient-to-br from-zinc-50 to-stone-100 backdrop-blur border border-stone-200 rounded-2xl shadow-sm">
            <h3 className="text-lg font-semibold mb-3">How to Find Your Reference Number</h3>
            <div className="text-sm text-gray-700 space-y-2">
              <p>Your application reference number was provided when you submitted your application. You can find it:</p>
              <ul className="list-disc ml-5 space-y-1">
                <li>In the confirmation email sent to your registered email address</li>
                <li>On the application confirmation page after submission</li>
                <li>It follows the format: APP-XXXXX-XXXXX</li>
              </ul>
              <p className="mt-3">If you can't find your reference number, please contact our HR team at careers@company.com</p>
            </div>
          </div>
          )}
      </div>
    </div>
  );
};

export default ApplicationStatus;