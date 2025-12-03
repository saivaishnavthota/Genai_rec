import React, { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { applicationService } from '../../services/applicationService';
import { jobService } from '../../services/jobService';
import { useAuth } from '../../context/AuthContext';
import { 
  EyeIcon,
  FunnelIcon,
  CalendarDaysIcon,
  UserIcon,
  BriefcaseIcon,
  StarIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

const ApplicationList = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [applications, setApplications] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    status: searchParams.get('status') || '',
    job_id: searchParams.get('job_id') || '',
    sort: searchParams.get('sort') || 'created_at',
    order: searchParams.get('order') || 'desc'
  });

  const loadApplications = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const params = {
        ...filters,
        limit: 50
      };
      
      const data = await applicationService.getApplications(params);
      setApplications(data);
    } catch (err) {
      setError('Failed to load applications');
      console.error('Error loading applications:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadApplications();
  }, [loadApplications]);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setJobsLoading(true);
        const data = await jobService.getJobs({ limit: 200, sort: 'title', order: 'asc' });
        if (Array.isArray(data)) {
          setJobs(data);
        } else if (Array.isArray(data?.jobs)) {
          setJobs(data.jobs);
        } else {
          setJobs([]);
        }
      } catch (err) {
        console.error('Failed to load jobs for filter:', err);
        setJobs([]);
      } finally {
        setJobsLoading(false);
      }
    };

    fetchJobs();
  }, []);

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    
    // Update URL params
    const params = new URLSearchParams();
    Object.entries(newFilters).forEach(([k, v]) => {
      if (v) params.set(k, v.toString());
    });
    setSearchParams(params);
  };

  const handleStatusUpdate = async (applicationId, newStatus) => {
    try {
      await applicationService.updateApplicationStatus(applicationId, newStatus);
      loadApplications(); // Reload data
    } catch (err) {
      setError('Failed to update application status');
      console.error('Error updating application:', err);
    }
  };

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
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  // New: Card theme backgrounds for vibrant grid
  const getCardTheme = (status, index) => {
    const palettes = [
      'bg-gradient-to-br from-rose-50 to-pink-100',
      'bg-gradient-to-br from-sky-50 to-indigo-100',
      'bg-gradient-to-br from-amber-50 to-orange-100',
      'bg-gradient-to-br from-emerald-50 to-green-100',
      'bg-gradient-to-br from-violet-50 to-purple-100',
      'bg-gradient-to-br from-gray-50 to-slate-100',
    ];
    return `${palettes[index % palettes.length]} backdrop-blur`;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
          <p className="text-gray-600">Loading applications...</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Applications</h1>
        <p className="text-gray-600">Manage candidate applications</p>
      </div>

      {/* Filters */}
      <div className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50 to-white shadow-sm">
        <div className="p-5 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <FunnelIcon className="h-5 w-5 text-primary-600" />
            <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
          </div>

          <div className="flex items-center gap-4 overflow-x-auto whitespace-nowrap">
            {/* Status */}
            <div className="inline-flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Status</span>
              <select
                id="filter-status"
                className="h-9 border border-gray-200 rounded-md px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="under_review">Under Review</option>
                <option value="shortlisted">Shortlisted</option>
                <option value="selected">Selected</option>
                <option value="availability_requested">Availability Requested</option>
                <option value="slot_selected">Slot Selected</option>
                <option value="interview_confirmed">Interview Confirmed</option>
                <option value="interview_completed">Interview Completed</option>
                <option value="review_received">Review Received</option>
                <option value="interview_scheduled">Interview Scheduled</option>
                <option value="hired">Hired</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>

            {/* Job */}
            <div className="inline-flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Job</span>
              <select
                id="filter-job"
                className="h-9 border border-gray-200 rounded-md px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 min-w-[180px]"
                value={filters.job_id}
                onChange={(e) => handleFilterChange('job_id', e.target.value)}
              >
                <option value="">All Jobs</option>
                {jobs.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.title}
                  </option>
                ))}
              </select>
              {jobsLoading && (
                <span className="text-xs text-gray-500">Loading…</span>
              )}
            </div>

            {/* Sort */}
            <div className="inline-flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Sort</span>
              <select
                id="filter-sort"
                className="h-9 border border-gray-200 rounded-md px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                value={filters.sort}
                onChange={(e) => handleFilterChange('sort', e.target.value)}
              >
                <option value="created_at">Sort by Date</option>
                <option value="ai_score">Sort by AI Score</option>
                <option value="candidate_name">Sort by Name</option>
              </select>
            </div>

            {/* Order */}
            <div className="inline-flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Order</span>
              <select
                id="filter-order"
                className="h-9 border border-gray-200 rounded-md px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                value={filters.order}
                onChange={(e) => handleFilterChange('order', e.target.value)}
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>

            {/* Reset filters icon button */}
            <button
              onClick={() => {
                setFilters({ status: '', job_id: '', sort: 'created_at', order: 'desc' });
                setSearchParams(new URLSearchParams());
              }}
              className="inline-flex items-center justify-center p-2 rounded-md text-primary-600 hover:text-primary-700 hover:bg-primary-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
              title="Reset filters"
              aria-label="Reset filters"
            >
              <ArrowPathIcon className="h-5 w-5" />
              <span className="sr-only">Reset filters</span>
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {/* Applications List */}
      <div>
        {applications.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {applications.map((application, index) => (
              <div
                key={application.id}
                className={`relative rounded-2xl p-4 border border-gray-200 shadow-sm ${getCardTheme(application.status, index)}`}
              >
                {/* Action icons */}
                <div className="absolute top-3 right-3 flex flex-col space-y-1">
                  <Link
                    to={`/applications/${application.id}`}
                    className="p-2 text-blue-700 hover:text-blue-900 hover:bg-blue/50 rounded-md"
                    title="View Application"
                  >
                    <EyeIcon className="h-4 w-4" />
                  </Link>
                  {(user?.user_type === 'hr' || user?.user_type === 'admin') && (
                    <>
                      {(application.status === 'pending' || application.status === 'under_review') && (
                        <>
                          <button
                            onClick={() => handleStatusUpdate(application.id, 'shortlisted')}
                            className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md"
                            title="Shortlist"
                          >
                            <CheckCircleIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleStatusUpdate(application.id, 'rejected')}
                            className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md"
                            title="Reject"
                          >
                            <XCircleIcon className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      {application.status === 'shortlisted' && (
                        <>
                          <button
                            onClick={() => handleStatusUpdate(application.id, 'interview_scheduled')}
                            className="p-2 text-purple-600 hover:text-purple-800 hover:bg-purple-50 rounded-md"
                            title="Schedule Interview"
                          >
                            <ClockIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleStatusUpdate(application.id, 'rejected')}
                            className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md"
                            title="Reject"
                          >
                            <XCircleIcon className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      {application.status === 'interview_scheduled' && (
                        <>
                          <button
                            onClick={() => handleStatusUpdate(application.id, 'hired')}
                            className="p-2 text-green-600 hover:text-green-800 hover:bg-green-50 rounded-md"
                            title="Mark Hired"
                          >
                            <CheckCircleIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleStatusUpdate(application.id, 'rejected')}
                            className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md"
                            title="Reject"
                          >
                            <XCircleIcon className="h-4 w-4" />
                          </button>
                        </>
                      )}
                    </>
                  )}
                </div>

                {/* Card body */}
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 rounded-full bg-white/40 flex items-center justify-center text-gray-800 font-bold">
                    {(application.candidate_name || 'A').charAt(0)}
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-gray-900">{application.candidate_name}</h3>
                    <div className="flex items-center text-xs text-gray-700">
                      <BriefcaseIcon className="h-4 w-4 mr-1" />
                      {application.job_title}
                    </div>
                  </div>
                </div>

                <div className="mt-3 flex items-center justify-between">
                  <span className={`status-badge ${getStatusColor(application.status)} rounded-full px-2 py-1 text-xs`}>
                    {getStatusText(application.status)}
                  </span>
                  {application.ai_score && (
                    <span className={`text-xs font-medium ${getScoreColor(application.ai_score)}`}>AI {application.ai_score}%</span>
                  )}
                </div>

                {application.ai_summary && (
                  <p className="mt-3 text-sm text-gray-800 line-clamp-3">{application.ai_summary}</p>
                )}

                <div className="mt-3 text-xs text-gray-700 flex items-center">
                  <CalendarDaysIcon className="h-4 w-4 mr-1" />
                  Applied: {new Date(application.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-10 text-gray-600">No applications found</div>
        )}
      </div>
    </div>
  );
};

export default ApplicationList;