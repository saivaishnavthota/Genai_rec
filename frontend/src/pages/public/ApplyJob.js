import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { jobService } from '../../services/jobService';
import { applicationService } from '../../services/applicationService';
import { 
  ArrowLeftIcon,
  DocumentArrowUpIcon,
  CheckCircleIcon,
  XMarkIcon,
  SparklesIcon,
  UserIcon,
  EnvelopeIcon,
  PhoneIcon,
  PaperClipIcon
} from '@heroicons/react/24/outline';

const ApplyJob = () => {
  const { jobId } = useParams();
  const id = jobId; // For backward compatibility with existing code
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [applicationReference, setApplicationReference] = useState('');

  const [formData, setFormData] = useState({
    candidate_name: '',
    candidate_email: '',
    candidate_phone: '',
    cover_letter: '',
    additional_info: ''
  });
  const [resumeFile, setResumeFile] = useState(null);

  const loadJob = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await jobService.getPublicJob(id);
      setJob(data);
    } catch (err) {
      setError('Failed to load job details');
      console.error('Error loading job:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadJob();
  }, [loadJob]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (!allowedTypes.includes(file.type)) {
        setError('Please upload a PDF or Word document');
        return;
      }
      
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('File size must be less than 5MB');
        return;
      }
      
      setResumeFile(file);
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.candidate_name.trim()) {
      setError('Name is required');
      return;
    }
    
    if (!formData.candidate_email.trim()) {
      setError('Email is required');
      return;
    }
    
    if (!resumeFile) {
      setError('Resume is required');
      return;
    }

    try {
      setSubmitting(true);
      setError('');

      // Create FormData for file upload
      const submitData = new FormData();
      submitData.append('job_id', id);
      submitData.append('candidate_name', formData.candidate_name);
      submitData.append('candidate_email', formData.candidate_email);
      submitData.append('candidate_phone', formData.candidate_phone || '');
      submitData.append('cover_letter', formData.cover_letter || '');
      submitData.append('additional_info', formData.additional_info || '');
      submitData.append('resume', resumeFile);

      const response = await applicationService.submitApplication(submitData);
      
      setSuccess(true);
      setApplicationReference(response.reference_number || 'N/A');
      
      // Reset form
      setFormData({
        candidate_name: '',
        candidate_email: '',
        candidate_phone: '',
        cover_letter: '',
        additional_info: ''
      });
      setResumeFile(null);

    } catch (err) {
      setError('Failed to submit application. Please try again.');
      console.error('Error submitting application:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-primary-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !job) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-primary-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="card bg-white/90 backdrop-blur border border-gray-200 rounded-2xl shadow-sm">
            <div className="text-center py-12">
              <XMarkIcon className="h-16 w-16 text-red-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Job Not Found</h3>
              <p className="text-gray-600 mb-4">{error}</p>
              <Link to="/careers" className="btn-primary">
                Browse All Jobs
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-primary-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="card bg-white/90 backdrop-blur border border-gray-200 rounded-2xl shadow-sm">
            <div className="text-center py-12">
              <CheckCircleIcon className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Application Submitted!</h3>
              <p className="text-gray-600 mb-4">
                Thank you for applying to <strong>{job?.title}</strong>. 
                Your application has been received and will be processed by our AI system.
              </p>
              {applicationReference && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                  <p className="text-sm text-green-700">
                    <strong>Reference Number:</strong> {applicationReference}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    Please save this reference number for future correspondence.
                  </p>
                </div>
              )}
              <div className="flex items-center justify-center flex-wrap gap-3 sm:gap-4">
                <Link to={`/careers/job/${job?.id}`} className="btn-secondary inline-flex items-center gap-2">
                  <ArrowLeftIcon className="h-5 w-5" />
                  Back to Job Details
                </Link>
                <Link to="/careers" className="btn-primary inline-flex items-center gap-2">
                  Browse More Jobs
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-100 dark:from-slate-900 dark:via-slate-950 dark:to-slate-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center mb-6">
          <button onClick={() => navigate(`/careers/job/${job?.id}`)} className="mr-3 bg-gray-100 text-gray-600 px-3 py-2 rounded-md">
            <ArrowLeftIcon className="h-6 w-6 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-primary-800 dark:text-primary-200">Apply for {job?.title}</h1>
            <p className="text-gray-600 text-sm dark:text-gray-300">Please fill out the form below to submit your application.</p>
          </div>
        </div>
    
        <div className="card bg-gradient-to-br from-white to-primary-50 dark:from-slate-800 dark:to-slate-900 backdrop-blur border border-primary-200 dark:border-slate-700 rounded-2xl shadow-xl ring-1 ring-primary-100/60 dark:ring-slate-700/60 p-6">
          <div className="mb-6 -mx-6 -mt-6 px-6 py-4 rounded-t-2xl bg-gradient-to-r from-primary-600 via-indigo-600 to-sky-500 text-white shadow-sm">
            <div className="flex items-center gap-2">
              <SparklesIcon className="h-5 w-5" />
              <span className="font-semibold">Start your application</span>
            </div>
          </div>
          {error && (
            <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-900/40 border border-red-200 dark:border-red-700 px-4 py-3 text-red-700 dark:text-red-200">
              {error}
            </div>
          )}
    
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">Full Name</label>
                <div className="relative">
                  <UserIcon className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-primary-400 dark:text-primary-300" />
                  <input
                    type="text"
                    name="candidate_name"
                    value={formData.candidate_name}
                    onChange={handleInputChange}
                    required
                    placeholder="Your full name"
                    className="block w-full rounded-xl border border-primary-200 dark:border-slate-700 bg-white/95 dark:bg-slate-800 px-3 pl-10 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 shadow-sm transition focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1 focus:border-primary-500 hover:border-primary-300"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">Email</label>
                <div className="relative">
                  <EnvelopeIcon className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-primary-400 dark:text-primary-300" />
                  <input
                    type="email"
                    name="candidate_email"
                    value={formData.candidate_email}
                    onChange={handleInputChange}
                    required
                    placeholder="you@example.com"
                    className="block w-full rounded-xl border border-primary-200 dark:border-slate-700 bg-white/95 dark:bg-slate-800 px-3 pl-10 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 shadow-sm transition focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1 focus:border-primary-500 hover:border-primary-300"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">Phone</label>
                <div className="relative">
                  <PhoneIcon className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-primary-400 dark:text-primary-300" />
                  <input
                    type="text"
                    name="candidate_phone"
                    value={formData.candidate_phone}
                    onChange={handleInputChange}
                    placeholder="e.g., +1 555-1234"
                    className="block w-full rounded-xl border border-primary-200 dark:border-slate-700 bg-white/95 dark:bg-slate-800 px-3 pl-10 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 shadow-sm transition focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1 focus:border-primary-500 hover:border-primary-300"
                  />
                </div>
              </div>
            </div>
    
              <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Resume</label>
              <div className="mt-1 flex items-center gap-3">
                <PaperClipIcon className="h-5 w-5 text-primary-400 dark:text-primary-300" />
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.doc,.docx"
                  className="block w-full text-sm  file:mr-4 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-semibold file:text-dark  dark:file:text-slate-100 hover:file:bg-gray-400"
                />
                {resumeFile && (
                  <span className="text-sm text-gray-600 dark:text-gray-300">{resumeFile.name}</span>
                )}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Accepted formats: PDF or Word (DOC/DOCX), up to 5MB</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cover Letter</label>
              <textarea
                name="cover_letter"
                value={formData.cover_letter}
                onChange={handleInputChange}
                rows={4}
                placeholder="Briefly describe why you're a great fit"
                className="block w-full rounded-xl border border-primary-200 dark:border-slate-700 bg-white/95 dark:bg-slate-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 shadow-sm transition focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 hover:border-primary-300"
              />
            </div>
    
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Additional Info</label>
              <textarea
                name="additional_info"
                value={formData.additional_info}
                onChange={handleInputChange}
                rows={3}
                placeholder="Any notes you'd like us to consider (optional)"
                className="block w-full rounded-xl border border-primary-200 dark:border-slate-700 bg-white/95 dark:bg-slate-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 shadow-sm transition focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 hover:border-primary-300"
              />
            </div>
    
           
    
            <div className="flex items-center justify-between gap-3 sm:gap-4">
              <Link to={`/careers/job/${job?.id}`} className="btn-secondary inline-flex items-center gap-2">
                <ArrowLeftIcon className="h-5 w-5" />
                Back to Job Details
              </Link>
              <button
                type="submit"
                disabled={submitting}
                className="btn-primary inline-flex items-center gap-2"
              >
                <DocumentArrowUpIcon className="h-5 w-5" />
                {submitting ? 'Submitting...' : 'Submit Application'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ApplyJob;