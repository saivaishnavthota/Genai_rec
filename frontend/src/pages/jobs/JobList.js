import React, { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { jobService } from '../../services/jobService';
import { CheckIcon, GlobeAltIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../context/AuthContext';
import { 
  PlusIcon, 
  EyeIcon, 
  PencilIcon,
  TrashIcon,
  FunnelIcon,
  CalendarDaysIcon,
  BuildingOfficeIcon,
  MapPinIcon,
  SparklesIcon,
  ArrowUpRightIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import Swal from 'sweetalert2';

const JobList = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    status: searchParams.get('status') || '',
    created_by_me: searchParams.get('created_by_me') === 'true' || false
  });

  const loadJobs = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const params = {
        limit: 50,
        created_by_me: filters.created_by_me,
        ...(filters.status ? { status_filter: filters.status } : {})
      };
      
      const data = await jobService.getJobs(params);
      setJobs(data);
    } catch (err) {
      setError('Failed to load jobs');
      console.error('Error loading jobs:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

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

  const handleDeleteJob = async (jobId) => {
    const result = await Swal.fire({
      title: 'Delete Job?',
      text: 'This action cannot be undone.',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Delete',
      cancelButtonText: 'Cancel',
      heightAuto: false,
    });
    if (!result.isConfirmed) return;

    try {
      await jobService.deleteJob(jobId);
      setJobs(jobs.filter(job => job.id !== jobId));
      Swal.fire({
        title: 'Deleted',
        text: 'Job deleted successfully.',
        icon: 'success',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
    } catch (err) {
      setError('Failed to delete job');
      console.error('Error deleting job:', err);
      Swal.fire({
        title: 'Error',
        text: err.response?.data?.detail || 'Failed to delete job',
        icon: 'error',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
    }
  };

  const handleApproveJob = async (jobId) => {
    const result = await Swal.fire({
      title: 'Approve Job?',
      text: 'This will mark the job as approved.',
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: 'Approve',
      cancelButtonText: 'Cancel',
      heightAuto: false,
    });
    if (!result.isConfirmed) return;

    try {
      await jobService.approveJob(jobId);
      // Reload jobs to get updated status
      loadJobs();
      Swal.fire({
        title: 'Approved',
        text: 'Job approved successfully. You can now publish it to the careers page.',
        icon: 'success',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
    } catch (err) {
      setError('Failed to approve job');
      console.error('Error approving job:', err);
      Swal.fire({
        title: 'Error',
        text: err.response?.data?.detail || 'Failed to approve job',
        icon: 'error',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
    }
  };

  const handlePublishJob = async (jobId) => {
    const result = await Swal.fire({
      title: 'Publish Job?',
      text: 'This will make the job visible on the careers page.',
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: 'Publish',
      cancelButtonText: 'Cancel',
      heightAuto: false,
    });
    if (!result.isConfirmed) return;

    try {
      await jobService.publishJob(jobId);
      // Reload jobs to get updated status
      loadJobs();
      Swal.fire({
        title: 'Published',
        text: 'Job published successfully. It is now visible on the careers page.',
        icon: 'success',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
    } catch (err) {
      setError('Failed to publish job');
      console.error('Error publishing job:', err);
      Swal.fire({
        title: 'Error',
        text: err.response?.data?.detail || 'Failed to publish job',
        icon: 'error',
        confirmButtonText: 'OK',
        heightAuto: false,
      });
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

  const getStatusText = (status) => {
    switch (status) {
      case 'pending_approval':
        return 'Pending Approval';
      default:
        return status.charAt(0).toUpperCase() + status.slice(1);
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

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Job Management</h1>
          <p className="text-gray-600">Manage and track your job postings</p>
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
      <div className="card overflow-hidden relative">
        <div className="absolute inset-0 bg-gradient-to-r from-primary-50 via-blue-50 to-indigo-50" aria-hidden="true"></div>
        <div className="relative flex flex-col md:flex-row md:items-center md:justify-between p-6 gap-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center">
              <SparklesIcon className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl md:text-xl font-semibold text-gray-900">{user?.user_type === 'account_manager' ? 'Jobs — Account Manager' : 'Job Management'}</h1>
              <p className="text-gray-600 text-sm md:text-base">{user?.user_type === 'account_manager' ? 'Review and manage the jobs you own or collaborate on' : 'Manage and track your job postings'}</p>
            </div>
          </div>
          {(user?.user_type === 'account_manager' || user?.user_type === 'admin') && (
            <Link
              to="/jobs/create"
               className="bg-purple-600 text-white flex items-center px-4 py-2 rounded-md shadow hover:bg-purple-700 hover:shadow-md transition"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Create New Job
              <ArrowUpRightIcon className="h-4 w-4 ml-2" />
            </Link>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-lg p-4 bg-white">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <FunnelIcon className="h-5 w-5 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">Filters</span>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <select
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="pending_approval">Pending Approval</option>
              <option value="approved">Approved</option>
              <option value="published">Published</option>
            </select>

            {user?.user_type === 'account_manager' && (
              <label className="flex items-center px-2 py-1 rounded-md hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  className="mr-2 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  checked={filters.created_by_me}
                  onChange={(e) => handleFilterChange('created_by_me', e.target.checked)}
                />
                <span className="text-sm text-gray-700">My Jobs Only</span>
              </label>
            )}

            <button
              onClick={() => {
                setFilters({ status: '', created_by_me: false });
                setSearchParams(new URLSearchParams());
              }}
              className="inline-flex items-center text-primary-700 hover:text-primary-800 hover:bg-primary-50 p-2 rounded-md transition"
              title="Clear Filters"
            >
              <ArrowPathIcon className="h-5 w-5" />
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

      {/* Jobs List */}
      <div className="card">
        {jobs.length > 0 ? (
            <div className="grid grid-cols-2 gap-4">
            {jobs.map((job) => (
              <div key={job.id} className={`bg-white border border-gray-200 rounded-lg p-4 hover:bg-gray-50 hover:shadow-sm transition ${getStatusAccent(job.status)} group`}>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                      <span className={`status-badge ${getStatusColor(job.status)} shadow-sm ring-1 ring-inset ring-gray-200`}>
                        {getStatusText(job.status)}
                      </span>
                      {user?.user_type === 'account_manager' && job.created_by === user.id && (
                        <span className="inline-flex items-center text-xs px-2 py-0.5 rounded-full bg-primary-100 text-primary-800 ring-1 ring-inset ring-primary-200">Mine</span>
                      )}
                    </div>
                    
                    <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-3">
                      {job.department && (
                        <div className="flex items-center">
                          <BuildingOfficeIcon className="h-4 w-4 mr-1" />
                          {job.department}
                        </div>
                      )}
                      {job.location && (
                        <div className="flex items-center">
                          <MapPinIcon className="h-4 w-4 mr-1" />
                          {job.location}
                        </div>
                      )}
                      <div className="flex items-center">
                        <CalendarDaysIcon className="h-4 w-4 mr-1" />
                        Created: {new Date(job.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    {/* Description removed per request */}

                    {job.key_skills && job.key_skills.length > 0 && (
                      <div className="mb-3">
                        <div className="flex flex-wrap gap-1">
                          {job.key_skills.slice(0, 5).map((skill, index) => (
                            <span
                              key={index}
                              className="inline-flex items-center bg-gray-100 text-gray-700 text-xs px-2.5 py-1 rounded-full ring-1 ring-inset ring-gray-200"
                            >
                              {skill}
                            </span>
                          ))}
                          {job.key_skills.length > 5 && (
                            <span className="inline-block text-gray-500 text-xs px-2 py-1">
{job.key_skills.length - 5} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex space-x-2 ml-4">
                    <Link
                      to={`/jobs/${job.id}`}
                      className="inline-flex items-center p-2 text-primary-700 hover:text-primary-800 hover:bg-primary-50 rounded-md transition"
                      title="View Job"
                    >
                      <EyeIcon className="h-5 w-5" />
                    </Link>
                    {(user?.user_type === 'hr' || user?.user_type === 'admin') && 
                     job.status === 'pending_approval' && (
                      <button
                        onClick={() => handleApproveJob(job.id)}
                        className="inline-flex items-center p-2 text-gray-700 hover:text-green-700 hover:bg-green-50 rounded-md transition"
                        title="Approve Job"
                      >
                        <CheckIcon className="h-5 w-5" />
                      </button>
                    )}
                    {(user?.user_type === 'hr' || user?.user_type === 'admin') && 
                     job.status === 'approved' && (
                      <button
                        onClick={() => handlePublishJob(job.id)}
                        className="inline-flex items-center p-2 text-gray-700 hover:text-blue-700 hover:bg-blue-50 rounded-md transition"
                        title="Publish to Careers Page"
                      >
                        <GlobeAltIcon className="h-5 w-5" />
                      </button>
                    )}
                    {(user?.user_type === 'admin' || 
                      (user?.user_type === 'account_manager' && job.created_by === user.id)) && (
                      <>
                        <Link
                          to={`/jobs/${job.id}/edit`}
                          className="inline-flex items-center p-2 text-primary-700 hover:text-primary-800 hover:bg-primary-50 rounded-md transition"
                          title="Edit Job"
                        >
                          <PencilIcon className="h-5 w-5" />
                        </Link>
                        <button
                          onClick={() => handleDeleteJob(job.id)}
                          className="inline-flex items-center p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition"
                          title="Delete Job"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <BuildingOfficeIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
            <p className="text-gray-600 mb-4">
              {filters.status || filters.created_by_me 
                ? 'No jobs match your current filters.' 
                : 'Start by creating your first job posting.'}
            </p>
            {(user?.user_type === 'account_manager' || user?.user_type === 'admin') && (
              <Link
                to="/jobs/create"
                className="btn-primary"
              >
                Create New Job
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default JobList;
