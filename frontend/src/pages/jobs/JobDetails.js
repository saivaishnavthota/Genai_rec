import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom';
import { jobService } from '../../services/jobService';
import { useAuth } from '../../context/AuthContext';
import { 
  PencilIcon,
  TrashIcon,
  ArrowLeftIcon,
  CalendarDaysIcon,
  BuildingOfficeIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  ClockIcon,
  UserIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Swal from 'sweetalert2';

const JobDetails = () => {
  const { jobId } = useParams();
  const id = jobId; // For backward compatibility with existing code
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadJob = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      
      // Validate job ID
      if (!id || id === 'undefined' || id === 'null') {
        throw new Error(`Invalid job ID: ${id}`);
      }
      
      const data = await jobService.getJob(id);
      setJob(data);
    } catch (err) {
      const errorMessage = err.message?.includes('Invalid job ID') 
        ? `Invalid job ID provided: ${id}. Please check the URL or go back to the job list.`
        : 'Failed to load job details';
      setError(errorMessage);
      console.error('Error loading job:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadJob();
  }, [loadJob]);

  const handleDeleteJob = async () => {
    try {
      const result = await Swal.fire({
        title: 'Delete Job',
        text: 'Are you sure you want to delete this job? This action cannot be undone.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        confirmButtonColor: '#dc2626', // Tailwind red-600
        focusCancel: true,
        showLoaderOnConfirm: true,
        allowOutsideClick: () => !Swal.isLoading(),
        preConfirm: async () => {
          try {
            await jobService.deleteJob(id);
          } catch (err) {
            const msg = err.response?.data?.detail || 'Failed to delete job';
            Swal.showValidationMessage(msg);
            throw err;
          }
        }
      });

      if (result.isConfirmed) {
        await Swal.fire({
          title: 'Deleted',
          text: 'Job deleted successfully',
          icon: 'success',
          timer: 1200,
          showConfirmButton: false,
          heightAuto: false,
        });
        navigate('/jobs');
      }
    } catch (err) {
      console.error('Error deleting job:', err);
      setError('Failed to delete job');
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

  const canEdit = user?.user_type === 'admin' || 
                  (user?.user_type === 'account_manager' && job?.created_by === user.id);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center">
          <button onClick={() => navigate('/jobs')} className="mr-4">
            <ArrowLeftIcon className="h-6 w-6 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Job Details</h1>
            <p className="text-gray-600">Loading job information...</p>
          </div>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center">
          <button onClick={() => navigate(location.state?.fromDashboard === 'hr' ? '/hr-dashboard' : '/jobs')} className="mr-4">
            <ArrowLeftIcon className="h-6 w-6 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Job Details</h1>
            <p className="text-gray-600">Error loading job</p>
          </div>
        </div>
        <div className="card">
          <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="space-y-6">
        <div className="flex items-center">
          <button onClick={() => navigate(location.state?.fromDashboard === 'hr' ? '/hr-dashboard' : '/jobs')} className="mr-4">
            <ArrowLeftIcon className="h-6 w-6 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Job Details</h1>
            <p className="text-gray-600">Job not found</p>
          </div>
        </div>
        <div className="card">
          <p className="text-gray-600">The requested job could not be found.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex items-center">
          <button onClick={() => navigate(location.state?.fromDashboard === 'hr' ? '/hr-dashboard' : '/jobs')} className="mr-4">
            <ArrowLeftIcon className="h-6 w-6 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
            <div className="flex items-center mt-2">
              <span className={`status-badge ${getStatusColor(job.status)}`}>
                {getStatusText(job.status)}
              </span>
            </div>
          </div>
        </div>

        {canEdit && (
          <div className="flex space-x-2">
            <Link
              to={`/jobs/${job.id}/edit`}
              className="btn-secondary flex items-center"
            >
              <PencilIcon className="h-4 w-4 mr-2" />
              Edit Job
            </Link>
            <button
              onClick={handleDeleteJob}
              className="btn-danger flex items-center"
            >
              <TrashIcon className="h-4 w-4 mr-2" />
              Delete Job
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Job Description */}
          <div className="card-themed-yellow">
            <h2 className="text-lg font-semibold mb-4 heading-gradient">Job Description</h2>
            <div className="prose max-w-none text-gray-700">
              {/* Render markdown with GFM for bold, lists, etc. */}
              {typeof job.description === 'string' && job.description.trim() ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {job.description}
                </ReactMarkdown>
               ) : (
                 <div className="text-gray-700">No description available.</div>
               )}
            </div>
          </div>

          {/* Required Experience */}
          {job.required_experience && (
            <div className="card-themed-yellow">
              <h2 className="text-lg font-semibold mb-4 heading-gradient">Required Experience</h2>
              <div className="prose max-w-none">
                <div className="whitespace-pre-wrap text-gray-700">
                  {job.required_experience}
                </div>
              </div>
            </div>
          )}

          {/* Certifications */}
          {job.certifications && Array.isArray(job.certifications) && job.certifications.length > 0 && (
            <div className="card-themed-cyan">
              <h2 className="text-lg font-semibold mb-4 heading-gradient">Certifications</h2>
              <div className="flex flex-wrap gap-2">
                {job.certifications.map((cert, index) => (
                  <span
                    key={index}
                    className="inline-block bg-primary-100 text-primary-800 text-sm px-3 py-1 rounded-full ring-1 ring-inset ring-primary-200"
                  >
                    {cert}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Additional Requirements */}
          {job.additional_requirements && Array.isArray(job.additional_requirements) && job.additional_requirements.length > 0 && (
            <div className="card-themed-yellow">
              <h2 className="text-lg font-semibold mb-4 heading-gradient">Additional Requirements</h2>
              <div className="flex flex-wrap gap-2">
                {job.additional_requirements.map((req, index) => (
                  <span
                    key={index}
                    className="inline-block bg-amber-100 text-amber-800 text-sm px-3 py-1 rounded-full ring-1 ring-inset ring-amber-200"
                  >
                    {req}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Key Skills */}
          {job.key_skills && job.key_skills.length > 0 && (
            <div className="card-themed-cyan">
              <h2 className="text-lg font-semibold mb-4 heading-gradient">Key Skills Required</h2>
              <div className="flex flex-wrap gap-2">
                {job.key_skills.map((skill, index) => (
                  <span
                    key={index}
                    className="inline-block bg-primary-100 text-primary-800 text-sm px-3 py-1 rounded-full ring-1 ring-inset ring-primary-200"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Job Info */}
          <div className="card-themed-cyan">
            <h3 className="text-lg font-semibold mb-4 heading-gradient">Job Information</h3>
            <div className="space-y-3">
              {/* Department */}
              {job.department && (
                <div className="flex items-center">
                  <BuildingOfficeIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <div className="text-sm text-gray-500">Department</div>
                    <div className="font-medium">{job.department}</div>
                  </div>
                </div>
              )}
              {/* Location */}
              {job.location && (
                <div className="flex items-center">
                  <MapPinIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <div className="text-sm text-gray-500">Location</div>
                    <div className="font-medium">{job.location}</div>
                  </div>
                </div>
              )}
              {/* Job Type */}
              {job.job_type && (
                <div className="flex items-center">
                  <ClockIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <div className="text-sm text-gray-500">Job Type</div>
                    <div className="font-medium">{job.job_type}</div>
                  </div>
                </div>
              )}
              {/* Experience Level */}
              {job.experience_level && (
                <div className="flex items-center">
                  <UserIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <div className="text-sm text-gray-500">Experience Level</div>
                    <div className="font-medium">{job.experience_level}</div>
                  </div>
                </div>
              )}
              {/* Salary Range */}
              {(job.salary_range || job.salary_min || job.salary_max) && (
                <div className="flex items-center">
                  <CurrencyDollarIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <div className="text-sm text-gray-500">Salary Range</div>
                    <div className="font-medium">
                      {job.salary_range
                        ? job.salary_range
                        : job.salary_min && job.salary_max
                        ? `$${job.salary_min.toLocaleString()} - $${job.salary_max.toLocaleString()}`
                        : job.salary_min
                        ? `From $${job.salary_min.toLocaleString()}`
                        : job.salary_max
                        ? `Up to $${job.salary_max.toLocaleString()}`
                        : 'Not specified'}
                    </div>
                  </div>
                </div>
              )}
              {/* Created Date */}
              <div className="flex items-center">
                <CalendarDaysIcon className="h-5 w-5 text-gray-400 mr-3" />
                <div>
                  <div className="text-sm text-gray-500">Created Date</div>
                  <div className="font-medium">{new Date(job.created_at).toLocaleDateString()}</div>
                </div>
              </div>
              {/* Deadline */}
              {job.deadline && (
                <div className="flex items-center">
                  <TagIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <div className="text-sm text-gray-500">Application Deadline</div>
                    <div className="font-medium">{new Date(job.deadline).toLocaleDateString()}</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Additional Info */}
         {typeof job.short_description === 'string' && job.short_description.trim() && (
             <div className="card-themed-red">
               <h3 className="text-lg font-semibold mb-3 heading-gradient">Summary</h3>
               <div className="prose max-w-none text-gray-700 text-sm leading-relaxed">
                 <ReactMarkdown remarkPlugins={[remarkGfm]}>
                   {job.short_description}
                 </ReactMarkdown>
               </div>
             </div>
           )}
        </div>
      </div>
    </div>
  );
};

export default JobDetails;