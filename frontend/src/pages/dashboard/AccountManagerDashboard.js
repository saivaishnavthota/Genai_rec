import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { jobService } from '../../services/jobService';
import { 
  PlusIcon, 
  BriefcaseIcon, 
  DocumentTextIcon,
  ChartBarIcon,
  ClockIcon,
  SparklesIcon,
  ArrowUpRightIcon
} from '@heroicons/react/24/outline';

const AccountManagerDashboard = () => {
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({
    totalJobs: 0,
    draftJobs: 0,
    pendingApproval: 0,
    publishedJobs: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const jobsData = await jobService.getJobs({ created_by_me: true, limit: 10 });
      setJobs(jobsData);
      
      // Calculate stats
      const stats = jobsData.reduce((acc, job) => {
        acc.totalJobs++;
        switch (job.status) {
          case 'draft':
            acc.draftJobs++;
            break;
          case 'pending_approval':
            acc.pendingApproval++;
            break;
          case 'published':
            acc.publishedJobs++;
            break;
          default:
            break;
        }
        return acc;
      }, { totalJobs: 0, draftJobs: 0, pendingApproval: 0, publishedJobs: 0 });
      
      setStats(stats);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'pending_approval':
        return 'bg-yellow-100 text-yellow-800';
      case 'approved':
        return 'bg-blue-100 text-blue-800';
      case 'published':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Accent border color per status for visual emphasis
  const getStatusAccent = (status) => {
    switch (status) {
      case 'draft':
        return 'border-l-4 border-gray-300';
      case 'pending_approval':
        return 'border-l-4 border-yellow-400';
      case 'approved':
        return 'border-l-4 border-blue-400';
      case 'published':
        return 'border-l-4 border-green-500';
      default:
        return 'border-l-4 border-gray-300';
    }
  };

  const totalCount = stats.totalJobs || 0;
  const getPercent = (count) => (totalCount ? Math.round((count / totalCount) * 100) : 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card overflow-hidden relative">
        <div className="absolute inset-0 bg-gradient-to-r from-primary-50 via-blue-50 to-indigo-50" aria-hidden="true"></div>
        <div className="relative flex flex-col md:flex-row md:items-center md:justify-between p-2 gap-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center">
              <SparklesIcon className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-xl md:text-xl font-semibold text-gray-900">Account Manager Overview</h3>
              <p className="text-gray-600 text-sm md:text-base">Manage your job postings and track their progress</p>
            </div>
          </div>
          <Link
            to="/jobs/create"
            className="bg-purple-600 text-white flex items-center px-4 py-2 rounded-md shadow hover:bg-purple-700 hover:shadow-md transition"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Create New Job
            <ArrowUpRightIcon className="h-4 w-4 ml-2" />
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Jobs */}
        <Link to="/jobs" className="card group transition hover:shadow-lg hover:-translate-y-0.5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BriefcaseIcon className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Jobs</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalJobs}</p>
              <div className="mt-3">
                <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-2 bg-primary-600 rounded-full" style={{ width: `${getPercent(stats.totalJobs)}%` }}></div>
                </div>
                <p className="mt-1 text-xs text-gray-500">{getPercent(stats.totalJobs)}% of all postings</p>
              </div>
            </div>
          </div>
        </Link>

        {/* Draft Jobs */}
        <Link to="/jobs?status=draft" className="card group transition hover:shadow-lg hover:-translate-y-0.5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DocumentTextIcon className="h-8 w-8 text-gray-600 group-hover:text-gray-700" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Draft Jobs</p>
              <p className="text-2xl font-bold text-gray-900">{stats.draftJobs}</p>
              <div className="mt-3">
                <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-2 bg-gray-400 rounded-full" style={{ width: `${getPercent(stats.draftJobs)}%` }}></div>
                </div>
                <p className="mt-1 text-xs text-gray-500">{getPercent(stats.draftJobs)}% in draft</p>
              </div>
            </div>
          </div>
        </Link>

        {/* Pending Approval */}
        <Link to="/jobs?status=pending_approval" className="card group transition hover:shadow-lg hover:-translate-y-0.5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ClockIcon className="h-8 w-8 text-yellow-600 group-hover:text-yellow-700" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pending Approval</p>
              <p className="text-2xl font-bold text-gray-900">{stats.pendingApproval}</p>
              <div className="mt-3">
                <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-2 bg-yellow-400 rounded-full" style={{ width: `${getPercent(stats.pendingApproval)}%` }}></div>
                </div>
                <p className="mt-1 text-xs text-gray-500">{getPercent(stats.pendingApproval)}% awaiting review</p>
              </div>
            </div>
          </div>
        </Link>

        {/* Published */}
        <Link to="/jobs?status=published" className="card group transition hover:shadow-lg hover:-translate-y-0.5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-8 w-8 text-green-600 group-hover:text-green-700" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Published</p>
              <p className="text-2xl font-bold text-gray-900">{stats.publishedJobs}</p>
              <div className="mt-3">
                <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-2 bg-green-500 rounded-full" style={{ width: `${getPercent(stats.publishedJobs)}%` }}></div>
                </div>
                <p className="mt-1 text-xs text-gray-500">{getPercent(stats.publishedJobs)}% live</p>
              </div>
            </div>
          </div>
        </Link>
      </div>

      {/* Recent Jobs */}
      <div className="card">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-gray-900">Recent Jobs</h2>
          <Link
            to="/jobs"
            className="text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            View All Jobs
          </Link>
        </div>

        {jobs.length > 0 ? (
          <div className="grid grid-cols-2 gap-3 sm:gap-4">
            {jobs.slice(0, 5).map((job) => (
              <div key={job.id} className={`border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition ${getStatusAccent(job.status)}`}>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-base font-medium text-gray-900">{job.title}</h3>
                      <span className={`status-badge ${getStatusColor(job.status)} shadow-sm`}> 
                        {job.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-600 mt-1">{job.department} • {job.location}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Created: {new Date(job.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <Link
                      to={`/jobs/${job.id}`}
                      className="inline-flex items-center px-2.5 py-1 rounded-md text-primary-700 hover:text-primary-800 hover:bg-primary-50 text-xs font-medium transition"
                    >
                      View
                      <ArrowUpRightIcon className="h-4 w-4 ml-1" />
                    </Link>
                    <Link
                      to={`/jobs/${job.id}/edit`}
                      className="inline-flex items-center px-2.5 py-1 rounded-md text-gray-700 hover:text-gray-800 hover:bg-gray-100 text-xs font-medium transition"
                    >
                      Edit
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <BriefcaseIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs yet</h3>
            <p className="text-gray-600 mb-4">Start by creating your first job posting</p>
            <Link
              to="/jobs/create"
              className="bg-purple-600 text-white px-4 py-2 rounded-md shadow hover:bg-purple-700 transition"
            >
              Create New Job
            </Link>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/jobs/create"
            className="flex items-center p-4 rounded-lg border border-primary-100 bg-primary-50 hover:bg-primary-100 hover:shadow-md transition"
          >
            <PlusIcon className="h-6 w-6 text-primary-600 mr-3" />
            <span className="font-medium text-primary-900">Create New Job</span>
          </Link>
          
          <Link
            to="/jobs?status=draft"
            className="flex items-center p-4 rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100 hover:shadow-md transition"
          >
            <DocumentTextIcon className="h-6 w-6 text-gray-600 mr-3" />
            <span className="font-medium">Review Drafts</span>
          </Link>
          
          <Link
            to="/jobs?status=pending_approval"
            className="flex items-center p-4 rounded-lg border border-yellow-100 bg-yellow-50 hover:bg-yellow-100 hover:shadow-md transition"
          >
            <ClockIcon className="h-6 w-6 text-yellow-600 mr-3" />
            <span className="font-medium">Pending Approval</span>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AccountManagerDashboard;
