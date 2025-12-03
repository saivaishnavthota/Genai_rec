import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate,useLocation } from 'react-router-dom';
import { jobService } from '../../services/jobService';
import { useAuth } from '../../context/AuthContext';
import { 
  ArrowLeftIcon,
  SparklesIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const EditJob = () => {
  const { jobId } = useParams();
  const id = jobId; // For backward compatibility with existing code
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const location = useLocation();

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    short_description: '',
    description: '',
    department: '',
    location: '',
    job_type: '',
    experience_level: '',
    salary_range: '',
    key_skills: [],
    required_experience: '',
    certifications: [],
    additional_requirements: [],
    status: 'draft'
  });

  const [isPublished, setIsPublished] = useState(false);
  const [similarJobs, setSimilarJobs] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);

  const loadJob = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const job = await jobService.getJob(id);
      
      // Check if job is published
      if (job.status === 'published') {
        setIsPublished(true);
        setError('This job is published and cannot be edited. Please unpublish it first or create a new job posting.');
      }
      
      // Check permissions
      if (user?.user_type !== 'admin' && 
          !(user?.user_type === 'account_manager' && job.created_by === user.id)) {
        setError('You do not have permission to edit this job.');
        return;
      }

      // Populate form
      setFormData({
        title: job.title || '',
        short_description: job.short_description || '',
        description: job.description || '',
        department: job.department || '',
        location: job.location || '',
        job_type: job.job_type || '',
        experience_level: job.experience_level || '',
        salary_range: job.salary_range || '',
        key_skills: job.key_skills || [],
        required_experience: job.required_experience || '',
        certifications: job.certifications || [],
        additional_requirements: job.additional_requirements || [],
        status: job.status || 'draft'
      });

      // Load similar jobs for autofill
      if (job.status !== 'published') {
        loadSimilarJobs();
      }
    } catch (err) {
      setError('Failed to load job details');
      console.error('Error loading job:', err);
    } finally {
      setLoading(false);
    }
  }, [id, user?.user_type, user?.id]);

  const loadSimilarJobs = async () => {
    try {
      setLoadingSimilar(true);
      const jobs = await jobService.getSimilarJobs(id);
      setSimilarJobs(jobs);
    } catch (err) {
      console.error('Error loading similar jobs:', err);
    } finally {
      setLoadingSimilar(false);
    }
  };

  const handleAutofill = (field) => {
    if (similarJobs.length === 0) return;
    
    // Find the most common value from similar jobs
    const values = similarJobs
      .map(job => {
        if (field === 'key_skills') return job.key_skills || [];
        if (field === 'certifications') return job.certifications || [];
        if (field === 'additional_requirements') return job.additional_requirements || [];
        return job[field] || '';
      })
      .filter(v => v && (Array.isArray(v) ? v.length > 0 : v.trim() !== ''));
    
    if (values.length === 0) return;
    
    if (Array.isArray(values[0])) {
      // For array fields, combine unique values
      const combined = [...new Set(values.flat())];
      setFormData(prev => ({
        ...prev,
        [field]: combined
      }));
    } else {
      // For text fields, use the first non-empty value
      const firstValue = values.find(v => v && v.trim() !== '');
      if (firstValue) {
        setFormData(prev => ({
          ...prev,
          [field]: firstValue
        }));
      }
    }
  };

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

  const handleSkillsChange = (skillsText) => {
    const skills = skillsText.split(',').map(skill => skill.trim()).filter(skill => skill);
    setFormData(prev => ({
      ...prev,
      key_skills: skills
    }));
  };

  const handleListChange = (field, text) => {
    const items = text.split(',').map(item => item.trim()).filter(item => item);
    setFormData(prev => ({
      ...prev,
      [field]: items
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title.trim()) {
      setError('Job title is required');
      return;
    }

    try {
      setSaving(true);
      setError('');
      setSuccess('');

      const jobData = {
        title: formData.title,
        short_description: formData.short_description,
        description: formData.description,
        department: formData.department,
        location: formData.location,
        job_type: formData.job_type,
        experience_level: formData.experience_level,
        salary_range: formData.salary_range,
        key_skills: formData.key_skills,
        required_experience: formData.required_experience,
        certifications: formData.certifications,
        additional_requirements: formData.additional_requirements,
        status: formData.status
      };

      await jobService.updateJob(id, jobData);
      setSuccess('Job updated successfully!');
      
      // Navigate back to job details after a brief delay
      setTimeout(() => {
        navigate(`/jobs/${id}`);
      }, 1500);
    } catch (err) {
      setError('Failed to update job. Please try again.');
      console.error('Error updating job:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center">
          <button onClick={() => navigate(`/jobs/${id}`)} className="mr-4">
            <ArrowLeftIcon className="h-6 w-6 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Edit Job</h1>
            <p className="text-gray-600">Loading job information...</p>
          </div>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (error && !formData.title) {
    return (
      <div className="space-y-6">
        <div className="flex items-center">
          <button onClick={() => navigate(location.state?.fromDashboard === 'hr' ? '/hr-dashboard' : '/jobs')} className="mr-4">
            <ArrowLeftIcon className="h-6 w-6 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Edit Job</h1>
            <p className="text-gray-600">Error loading job</p>
          </div>
        </div>
        <div className="card-themed-red">
          <h2 className="text-lg font-semibold mb-3 heading-gradient">Error</h2>
          <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button onClick={() => navigate(`/jobs/${id}`)} className="mr-4">
            <ArrowLeftIcon className="h-6 w-6 text-gray-600 hover:text-gray-800" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Edit Job</h1>
            <p className="text-gray-600">Update job posting details</p>
          </div>
        </div>
      </div>

      {/* Success/Error Messages */}
      {error && (
        <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-300 text-green-700 px-4 py-3 rounded-md">
          {success}
        </div>
      )}

      {isPublished && (
        <div className="bg-yellow-50 border border-yellow-300 text-yellow-800 px-4 py-3 rounded-md">
          <strong>⚠️ Published Job:</strong> This job is published and cannot be edited. Please unpublish it first or create a new job posting.
        </div>
      )}

      {/* Edit Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Information */}
            <div className="card-themed-yellow">
              <h2 className="text-lg font-semibold mb-4 heading-gradient">Basic Information</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Job Title *
                  </label>
                  <input
                    type="text"
                    name="title"
                    value={formData.title}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="e.g. Senior Software Engineer"
                    required
                    disabled={isPublished}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Short Description
                  </label>
                  <textarea
                    name="short_description"
                    value={formData.short_description}
                    onChange={handleInputChange}
                    rows={2}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="Brief summary of the role..."
                    disabled={isPublished}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Job Description
                  </label>
                  <textarea
                    name="description"
                    value={formData.description}
                    onChange={handleInputChange}
                    rows={6}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="Detailed job description..."
                    disabled={isPublished}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-sm font-medium text-gray-700">
                      Required Experience
                    </label>
                    {similarJobs.length > 0 && !isPublished && (
                      <button
                        type="button"
                        onClick={() => handleAutofill('required_experience')}
                        className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                        title="Autofill from similar jobs"
                      >
                        🔄 Autofill
                      </button>
                    )}
                  </div>
                  <textarea
                    name="required_experience"
                    value={formData.required_experience}
                    onChange={handleInputChange}
                    rows={4}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="Describe the required experience (years, areas, levels)..."
                    disabled={isPublished}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-sm font-medium text-gray-700">
                      Key Skills (comma-separated)
                    </label>
                    {similarJobs.length > 0 && !isPublished && (
                      <button
                        type="button"
                        onClick={() => handleAutofill('key_skills')}
                        className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                        title="Autofill from similar jobs"
                      >
                        🔄 Autofill
                      </button>
                    )}
                  </div>
                  <input
                    type="text"
                    value={formData.key_skills.join(', ')}
                    onChange={(e) => handleSkillsChange(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="React, Node.js, JavaScript, Python, AWS"
                    disabled={isPublished}
                  />
                  {formData.key_skills.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {formData.key_skills.map((skill, index) => (
                        <span
                          key={index}
                          className="inline-block bg-primary-100 text-primary-800 text-xs px-2 py-1 rounded ring-1 ring-inset ring-primary-200"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-sm font-medium text-gray-700">
                      Certifications (comma-separated)
                    </label>
                    {similarJobs.length > 0 && !isPublished && (
                      <button
                        type="button"
                        onClick={() => handleAutofill('certifications')}
                        className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                        title="Autofill from similar jobs"
                      >
                        🔄 Autofill
                      </button>
                    )}
                  </div>
                  <input
                    type="text"
                    value={formData.certifications.join(', ')}
                    onChange={(e) => handleListChange('certifications', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="AWS Certified Developer, PMP, etc."
                    disabled={isPublished}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-sm font-medium text-gray-700">
                      Additional Requirements (comma-separated)
                    </label>
                    {similarJobs.length > 0 && !isPublished && (
                      <button
                        type="button"
                        onClick={() => handleAutofill('additional_requirements')}
                        className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                        title="Autofill from similar jobs"
                      >
                        🔄 Autofill
                      </button>
                    )}
                  </div>
                  <input
                    type="text"
                    value={formData.additional_requirements.join(', ')}
                    onChange={(e) => handleListChange('additional_requirements', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="On-call availability, travel, specific tooling, etc."
                    disabled={isPublished}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar Form */}
          <div className="space-y-6">
            {/* Job Details */}
            <div className="card-themed-cyan">
              <h3 className="text-lg font-semibold mb-4 heading-gradient">Job Details</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Department
                  </label>
                  <input
                    type="text"
                    name="department"
                    value={formData.department}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="Engineering"
                    disabled={isPublished}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Location
                  </label>
                  <input
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="San Francisco, CA"
                    disabled={isPublished}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Job Type
                  </label>
                  <select
                    name="job_type"
                    value={formData.job_type}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    disabled={isPublished}
                  >
                    <option value="">Select job type</option>
                    <option value="full-time">Full-time</option>
                    <option value="part-time">Part-time</option>
                    <option value="contract">Contract</option>
                    <option value="internship">Internship</option>
                    <option value="freelance">Freelance</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Experience Level
                  </label>
                  <select
                    name="experience_level"
                    value={formData.experience_level}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    disabled={isPublished}
                  >
                    <option value="">Select experience level</option>
                    <option value="entry">Entry Level</option>
                    <option value="junior">Junior</option>
                    <option value="mid">Mid Level</option>
                    <option value="senior">Senior</option>
                    <option value="lead">Lead</option>
                    <option value="principal">Principal</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Salary Range
                  </label>
                  <input
                    type="text"
                    name="salary_range"
                    value={formData.salary_range}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="e.g., ₹12–15 LPA or 50000-80000"
                    disabled={isPublished}
                  />
                </div>

                

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Status
                  </label>
                  <select
                    name="status"
                    value={formData.status}
                    onChange={handleInputChange}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    disabled={isPublished}
                  >
                    <option value="draft">Draft</option>
                    <option value="pending_approval">Pending Approval</option>
                    {user?.user_type === 'admin' && (
                      <>
                        <option value="approved">Approved</option>
                        <option value="published">Published</option>
                      </>
                    )}
                  </select>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
           
              <div className="space-y-4">
                <button
                  type="submit"
                  disabled={saving || isPublished}
                  className="w-full btn-primary flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? (
                    <>
                      <ClockIcon className="h-4 w-4 mr-2 animate-spin" />
                      Updating Job...
                    </>
                  ) : (
                    <>
                      <SparklesIcon className="h-4 w-4 mr-2" />
                      {isPublished ? 'Cannot Update Published Job' : 'Update Job'}
                    </>
                  )}
                </button>
                
                <button
                  type="button"
                  onClick={() => navigate(`/jobs/${id}`)}
                  className="w-full btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
       
        </div>
      </form>
    </div>
  );
};

export default EditJob;