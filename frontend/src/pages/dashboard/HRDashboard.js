import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { jobService } from '../../services/jobService';
import { applicationService } from '../../services/applicationService';
import { useAuth } from '../../context/AuthContext';
import { 
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  EyeIcon,
  UserGroupIcon,
  BriefcaseIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CalendarDaysIcon
} from '@heroicons/react/24/outline';

const HRDashboard = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({
    pendingJobs: 0,
    totalJobs: 0,
    totalApplications: 0,
    todayApplications: 0,
    interviewsScheduled: 0
  });
  const [pendingJobs, setPendingJobs] = useState([]);
  const [recentApplications, setRecentApplications] = useState([]);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');

      // Load pending jobs (waiting for HR approval)
      const jobsResponse = await jobService.getJobs({ 
        status_filter: 'pending_approval',
        limit: 10 
      });
      
      setPendingJobs(jobsResponse || []);

      // Load recent applications
      const applicationsResponse = await applicationService.getApplications({
        limit: 10,
        sort: 'created_at',
        order: 'desc'
      });
      setRecentApplications(applicationsResponse || []);

      // Calculate stats
      const allJobs = await jobService.getJobs();
      const allApplications = await applicationService.getApplications();
      
      const pendingCount = (allJobs || []).filter(j => j.status === 'pending_approval').length;
      const today = new Date().toDateString();
      const todayApps = (allApplications || []).filter(app => new Date(app.created_at).toDateString() === today);

      setStats({
        pendingJobs: pendingCount,
        totalJobs: (allJobs || []).length,
        totalApplications: (allApplications || []).length,
        todayApplications: todayApps.length,
        interviewsScheduled: (allApplications || []).filter(app => app.status === 'interview_scheduled').length
      });

    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Error loading HR dashboard:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleJobApproval = async (jobId, approve) => {
    try {
      if (approve) {
        await jobService.approveJob(jobId);
      } else {
        // For rejection, we might need a separate endpoint
        // For now, we'll just update the job status to draft
        await jobService.updateJob(jobId, { status: 'draft' });
      }
      
      // Reload data
      loadDashboardData();
    } catch (err) {
      setError(`Failed to ${approve ? 'approve' : 'reject'} job`);
      console.error('Error handling job approval:', err);
    }
  };

  const getApplicationStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-amber-100 text-amber-700 ring-amber-200';
      case 'shortlisted':
        return 'bg-sky-100 text-sky-700 ring-sky-200';
      case 'availability_requested':
        // red color
        return 'bg-rose-100 text-rose-700 ring-rose-200';
      case 'selected':
        // green color
        return 'bg-emerald-100 text-emerald-700 ring-emerald-200';
      case 'slot_selected':
        // purple color
        return 'bg-violet-100 text-violet-700 ring-violet-200';
      case 'interview_completed':
        // lumen green (use lime)
        return 'bg-lime-100 text-lime-700 ring-lime-200';
      case 'interview_scheduled':
        return 'bg-violet-100 text-violet-700 ring-violet-200';
      case 'hired':
        return 'bg-emerald-100 text-emerald-700 ring-emerald-200';
      case 'rejected':
        return 'bg-rose-100 text-rose-700 ring-rose-200';
      case 'interview_confirmed':
        return 'bg-indigo-100 text-indigo-700 ring-indigo-200';
      case 'review_received':
        return 'bg-purple-100 text-purple-700 ring-purple-200';
      default:
        return 'bg-gray-100 text-gray-700 ring-gray-200';
    }
  };

  const getStatusText = (status) => {
    const normalized = (status || '').toLowerCase();
    switch (normalized) {
      case 'availability_requested':
        return 'Availability Requested';
      case 'selected':
        return 'Selected';
      case 'slot_selected':
        return 'Slot Selected';
      case 'interview_completed':
        return 'Interview Completed';
      case 'interview_scheduled':
        return 'Interview Scheduled';
      case 'under_review':
        return 'Under Review';
      case 'resume_update_requested':
        return 'Resume Update Requested';
      
      
      default: {
        // Generic formatting: replace underscores with spaces and title-case each word
        const pretty = normalized.replace(/_/g, ' ');
        return pretty.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
      }
    }
  };
  
  const getPercent = (count, total) => (total ? Math.round((count / total) * 100) : 0);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">HR Dashboard</h1>
          <p className="text-gray-600">Loading dashboard data...</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-2xl">
        <div className="relative z-10 flex items-center justify-between">
          <div>
    
            <p className="mt-1 text-gray-500">Manage job approvals and candidate applications</p>
          </div>
          {/* Welcome text removed as requested */}
        </div>
        <div className="absolute -right-10 -top-10 h-48 w-48 rounded-full bg-white/10 blur-2xl"></div>
        <div className="absolute -left-12 -bottom-12 h-56 w-56 rounded-full bg-white/10 blur-2xl"></div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-xl bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 shadow-sm">{error}</div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="group rounded-xl p-5 shadow-sm bg-gradient-to-br from-amber-50 to-orange-100 border border-orange-200 hover:shadow-md transition">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-orange-500/10 text-orange-600 flex items-center justify-center">
              <ExclamationTriangleIcon className="h-7 w-7" />
            </div>
            <div>
              <p className="text-sm font-medium text-orange-800/90">Pending Approvals</p>
              <p className="text-3xl font-bold text-orange-900">{stats.pendingJobs}</p>
              <div className="mt-3">
                <div className="h-2 w-full bg-white/50 rounded-full overflow-hidden">
                  <div className="h-2 bg-orange-500 rounded-full" style={{ width: `${getPercent(stats.pendingJobs, stats.totalJobs)}%` }}></div>
                </div>
                <p className="mt-1 text-xs text-orange-800/80">{getPercent(stats.pendingJobs, stats.totalJobs)}% of all jobs</p>
              </div>
            </div>
          </div>
        </div>
        <div className="group rounded-xl p-5 shadow-sm bg-gradient-to-br from-sky-50 to-blue-100 border border-blue-200 hover:shadow-md transition">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-sky-500/10 text-sky-600 flex items-center justify-center">
              <UserGroupIcon className="h-7 w-7" />
            </div>
            <div>
              <p className="text-sm font-medium text-sky-800/90">Total Applications</p>
              <p className="text-3xl font-bold text-sky-900">{stats.totalApplications}</p>
              <div className="mt-3">
                <div className="h-2 w-full bg-white/50 rounded-full overflow-hidden">
                  <div className="h-2 bg-sky-500 rounded-full" style={{ width: `${getPercent(stats.totalApplications, stats.totalApplications)}%` }}></div>
                </div>
                <p className="mt-1 text-xs text-sky-800/80">{getPercent(stats.totalApplications, stats.totalApplications)}% of all applications</p>
              </div>
            </div>
          </div>
        </div>
        <div className="group rounded-xl p-5 shadow-sm bg-gradient-to-br from-emerald-50 to-green-100 border border-emerald-200 hover:shadow-md transition">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
              <CalendarDaysIcon className="h-7 w-7" />
            </div>
            <div>
              <p className="text-sm font-medium text-emerald-800/90">Today's Applications</p>
              <p className="text-3xl font-bold text-emerald-900">{stats.todayApplications}</p>
              <div className="mt-3">
                <div className="h-2 w-full bg-white/50 rounded-full overflow-hidden">
                  <div className="h-2 bg-emerald-500 rounded-full" style={{ width: `${getPercent(stats.todayApplications, stats.totalApplications)}%` }}></div>
                </div>
                <p className="mt-1 text-xs text-emerald-800/80">{getPercent(stats.todayApplications, stats.totalApplications)}% today</p>
              </div>
            </div>
          </div>
        </div>
        <div className="group rounded-xl p-5 shadow-sm bg-gradient-to-br from-violet-50 to-purple-100 border border-violet-200 hover:shadow-md transition">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-violet-500/10 text-violet-600 flex items-center justify-center">
              <ClockIcon className="h-7 w-7" />
            </div>
            <div>
              <p className="text-sm font-medium text-violet-800/90">Interviews Scheduled</p>
              <p className="text-3xl font-bold text-violet-900">{stats.interviewsScheduled}</p>
              <div className="mt-3">
                <div className="h-2 w-full bg-white/50 rounded-full overflow-hidden">
                  <div className="h-2 bg-violet-500 rounded-full" style={{ width: `${getPercent(stats.interviewsScheduled, stats.totalApplications)}%` }}></div>
                </div>
                <p className="mt-1 text-xs text-violet-800/80">{getPercent(stats.interviewsScheduled, stats.totalApplications)}% scheduled</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Job Approvals */}
        <div className="rounded-2xl p-6 bg-gradient-to-br from-sky-50 to-indigo-50 border border-indigo-100 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-indigo-900">Pending Job Approvals</h2>
            <Link to="/jobs?status=pending_approval" className="text-indigo-600 hover:text-indigo-700 text-sm">
              View All
            </Link>
          </div>

          {pendingJobs.length > 0 ? (
            <div className="space-y-4">
              {pendingJobs.map((job) => (
                <div key={job.id} className="rounded-xl p-4 bg-white/80 backdrop-blur border border-gray-200 shadow-sm hover:shadow-md transition">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{job.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">{job.department} • {job.location}</p>
                      <p className="text-xs text-gray-500 mt-1">Created: {new Date(job.created_at).toLocaleDateString()}</p>
                    </div>
                    <div className="flex space-x-2 ml-4">
                      <Link
                        to={`/jobs/${job.id}`}
                        state={{ fromDashboard: 'hr' }}
                        className="p-2 text-sky-600 hover:text-sky-800 hover:bg-sky-50 rounded-md"
                        title="View Details"
                      >
                        <EyeIcon className="h-5 w-5" />
                      </Link>
                      <button
                        onClick={() => handleJobApproval(job.id, true)}
                        className="p-2 text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50 rounded-md"
                        title="Approve"
                      >
                        <CheckCircleIcon className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleJobApproval(job.id, false)}
                        className="p-2 text-rose-600 hover:text-rose-800 hover:bg-rose-50 rounded-md"
                        title="Reject"
                      >
                        <XCircleIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-10">
              <BriefcaseIcon className="h-12 w-12 text-indigo-300 mx-auto mb-3" />
              <p className="text-indigo-700">No jobs pending approval</p>
            </div>
          )}
        </div>

        {/* Recent Applications */}
        <div className="rounded-2xl p-6 bg-gradient-to-br from-rose-50 to-pink-50 border border-pink-100 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-pink-900">Recent Applications</h2>
            <Link to="/applications" className="text-pink-600 hover:text-pink-700 text-sm">
              View All
            </Link>
          </div>

          {recentApplications.length > 0 ? (
            <div className="space-y-4">
              {recentApplications.slice(0, 5).map((application) => (
                <div key={application.id} className="rounded-xl p-4 bg-white/80 backdrop-blur border border-gray-200 shadow-sm hover:shadow-md transition">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{application.candidate_name}</h3>
                      <p className="text-sm text-gray-600 mt-1">Applied for: {application.job_title}</p>
                      <div className="flex items-center mt-2">
                        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-semibold ring-1 ring-inset ${getApplicationStatusColor(application.status)}`}>
                          {getStatusText(application.status)}
                        </span>
                        {application.ai_score && (
                          <span className="ml-2 text-xs text-gray-500">AI Score: {application.ai_score}%</span>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 mt-1">Applied: {new Date(application.created_at).toLocaleDateString()}</p>
                    </div>
                    <div className="flex space-x-2 ml-4">
                      <Link
                        to={`/applications/${application.id}`}
                        state={{ fromDashboard: 'hr' }}
                        className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md"
                        title="View Application"
                      >
                        <EyeIcon className="h-5 w-5" />
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-10">
              <UserGroupIcon className="h-12 w-12 text-pink-300 mx-auto mb-3" />
              <p className="text-pink-700">No recent applications</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="rounded-2xl p-6 bg-gradient-to-br from-teal-50 to-cyan-50 border border-teal-100 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 text-teal-900">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/jobs?status=pending_approval"
            className="group rounded-xl p-4 bg-white/80 backdrop-blur shadow-sm hover:shadow-md transition flex items-center"
          >
            <div className="h-10 w-10 rounded-full bg-amber-500/10 text-amber-600 flex items-center justify-center mr-3 group-hover:bg-amber-500/20">
              <ExclamationTriangleIcon className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-medium">Review Job Approvals</h3>
              <p className="text-sm text-gray-600">Approve or reject job postings</p>
            </div>
          </Link>

          <Link
            to="/applications"
            className="group rounded-xl p-4 bg-white/80 backdrop-blur shadow-sm hover:shadow-md transition flex items-center"
          >
            <div className="h-10 w-10 rounded-full bg-sky-500/10 text-sky-600 flex items-center justify-center mr-3 group-hover:bg-sky-500/20">
              <UserGroupIcon className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-medium">Manage Applications</h3>
              <p className="text-sm text-gray-600">Review candidate applications</p>
            </div>
          </Link>

          <Link
            to="/jobs"
            className="group rounded-xl p-4 bg-white/80 backdrop-blur shadow-sm hover:shadow-md transition flex items-center"
          >
            <div className="h-10 w-10 rounded-full bg-emerald-500/10 text-emerald-600 flex items-center justify-center mr-3 group-hover:bg-emerald-500/20">
              <ChartBarIcon className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-medium">View Analytics</h3>
              <p className="text-sm text-gray-600">Job and application metrics</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HRDashboard;