import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { jobService } from '../../services/jobService';
import { 
  SparklesIcon, 
  DocumentTextIcon,
  PlusIcon,
  ExclamationTriangleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const CreateJob = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [similarJobs, setSimilarJobs] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);

  // Step 1: Basic Details
  const [basicDetails, setBasicDetails] = useState({
    project_name: '',
    role_title: '',
    role_description: ''
  });

  // Step 2: AI Generated Fields
  const [aiFields, setAiFields] = useState({
    key_skills: [],
    required_experience: '',
    certifications: [],
    additional_requirements: []
  });

  // Step 3: Final Job Description
  const [jobDescription, setJobDescription] = useState({
    description: '',
    short_description: ''
  });

  // Step 4: Additional Details
  const [additionalDetails, setAdditionalDetails] = useState({
    department: '',
    location: '',
    job_type: 'full-time',
    experience_level: '',
    salary_range: ''
  });

  const handleBasicDetailsChange = (e) => {
    const { name, value } = e.target;
    setBasicDetails(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const handleGenerateFields = async () => {
    if (!basicDetails.project_name || !basicDetails.role_title || !basicDetails.role_description) {
      setError('Please fill in all basic details before generating AI fields');
      return;
    }

    try {
      setLoading(true);
      setError('');
      const response = await jobService.generateJobFields(basicDetails);
      setAiFields(response);
      setCurrentStep(2);
    } catch (err) {
      console.error('AI Generation Error:', err);
      if (err.response?.data?.detail) {
        setError(`Failed to generate AI fields: ${err.response.data.detail}`);
      } else if (err.response?.status === 401) {
        setError('You are not authorized to use AI features. Please log in as an Account Manager or Admin.');
      } else if (err.response?.status === 403) {
        setError('You do not have permission to use AI features. Only Account Managers and Admins can generate AI fields.');
      } else {
        setError('Failed to generate AI fields. Please try again or continue manually.');
      }
      // Allow user to proceed manually
      setCurrentStep(2);
    } finally {
      setLoading(false);
    }
  };

  const handleAiFieldsChange = (field, value) => {
    setAiFields(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleArrayFieldChange = (field, index, value) => {
    setAiFields(prev => ({
      ...prev,
      [field]: prev[field].map((item, i) => i === index ? value : item)
    }));
  };

  const addArrayItem = (field) => {
    setAiFields(prev => ({
      ...prev,
      [field]: [...prev[field], '']
    }));
  };

  const removeArrayItem = (field, index) => {
    setAiFields(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }));
  };

  const handleGenerateDescription = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await jobService.generateJobDescription({
        ...basicDetails,
        ...aiFields
      });
      setJobDescription(response);
      setCurrentStep(3);
    } catch (err) {
      console.error('Description Generation Error:', err);
      if (err.response?.data?.detail) {
        setError(`Failed to generate job description: ${err.response.data.detail}`);
      } else if (err.response?.status === 401) {
        setError('You are not authorized to use AI features. Please log in as an Account Manager or Admin.');
      } else if (err.response?.status === 403) {
        setError('You do not have permission to use AI features. Only Account Managers and Admins can generate job descriptions.');
      } else {
        setError('Failed to generate job description. Please write it manually.');
      }
      setCurrentStep(3);
    } finally {
      setLoading(false);
    }
  };

  const handleDescriptionChange = (field, value) => {
    setJobDescription(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAdditionalDetailsChange = (e) => {
    const { name, value } = e.target;
    setAdditionalDetails(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Load similar jobs when department, job_type, or experience_level changes
    if (['department', 'job_type', 'experience_level'].includes(name) && value) {
      // Use setTimeout to avoid calling immediately (wait for state update)
      setTimeout(() => {
        loadSimilarJobs(name, value);
      }, 100);
    }
  };

  const loadSimilarJobs = async (changedField = null, changedValue = null) => {
    try {
      setLoadingSimilar(true);
      const filters = { ...additionalDetails };
      if (changedField && changedValue) {
        filters[changedField] = changedValue;
      }
      
      // Only load if we have at least one filter
      if (filters.department || filters.job_type || filters.experience_level) {
        const jobs = await jobService.getJobs({ ...filters, limit: 5 });
        setSimilarJobs(jobs);
      } else {
        setSimilarJobs([]);
      }
    } catch (err) {
      console.error('Error loading similar jobs:', err);
      setSimilarJobs([]);
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
      setAiFields(prev => ({
        ...prev,
        [field]: combined
      }));
    } else {
      // For text fields, use the first non-empty value
      const firstValue = values.find(v => v && v.trim() !== '');
      if (firstValue) {
        setAiFields(prev => ({
          ...prev,
          [field]: firstValue
        }));
      }
    }
  };

  const handleSubmitJob = async () => {
    try {
      setLoading(true);
      setError('');
      
      const jobData = {
        title: basicDetails.role_title,
        description: jobDescription.description || basicDetails.role_description,
        short_description: jobDescription.short_description || '',
        department: additionalDetails.department || '',
        location: additionalDetails.location || '',
        job_type: additionalDetails.job_type || 'full-time',
        experience_level: additionalDetails.experience_level || '',
        salary_range: additionalDetails.salary_range || '',
        key_skills: aiFields.key_skills || [],
        required_experience: aiFields.required_experience || '',
        certifications: aiFields.certifications || [],
        additional_requirements: aiFields.additional_requirements || []
      };

      const response = await jobService.createJob(jobData);
      navigate(`/jobs/${response.id}`);
    } catch (err) {
      console.error('Job Creation Error:', err);
      if (err.response?.data?.detail) {
        setError(`Failed to create job: ${err.response.data.detail}`);
      } else if (err.response?.status === 401) {
        setError('You are not authorized to create jobs. Please log in as an Account Manager or Admin.');
      } else if (err.response?.status === 403) {
        setError('You do not have permission to create jobs. Only Account Managers and Admins can create jobs.');
      } else {
        setError('Failed to create job. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const stepTitles = [
    'Basic Details',
    'AI Generated Fields',
    'Job Description', 
    'Additional Details'
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
<div className="rounded-xl p-6 bg-gradient-to-r from-primary-50 via-white to-primary-50 border border-primary-100 shadow-sm">
<div className="flex items-start justify-between">
<div>
<h1 className="text-2xl font-bold text-gray-900">Create New Job</h1>
<p className="text-gray-600">Create a new job posting with AI assistance</p>
</div>
<SparklesIcon className="h-6 w-6 text-primary-600" />
</div>
</div>

      {/* Progress Steps */}
<div className="rounded-lg p-6 bg-white/80 backdrop-blur-sm shadow-sm ring-1 ring-inset ring-gray-100">
<div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          {stepTitles.map((title, index) => (
            <div key={index} className="flex items-center">
<div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
index + 1 <= currentStep 
? 'bg-primary-600 text-white ring-1 ring-inset ring-primary-300 shadow-sm' 
: 'bg-gray-100 text-gray-600 ring-1 ring-inset ring-gray-200'
}`}>
                {index + 1}
              </div>
<span className={`ml-2 text-sm ${
index + 1 <= currentStep ? 'text-primary-700 font-medium' : 'text-gray-500'
}`}>
                {title}
              </span>
              {index < stepTitles.length - 1 && (
<div className={`w-12 h-0.5 mx-4 ${
index + 1 < currentStep ? 'bg-primary-500' : 'bg-gray-200'
}`} />
              )}
            </div>
          ))}
        </div>

        {/* Error Message */}
{error && (
<div className="mb-6 bg-red-50 border border-red-200 ring-1 ring-inset ring-red-100 text-red-700 px-4 py-3 rounded-md flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
            {error}
          </div>
        )}

        {/* Step 1: Basic Details */}
        {currentStep === 1 && (
          <div className="space-y-6 rounded-xl p-6 bg-white/80 backdrop-blur-sm shadow ring-1 ring-inset ring-gray-100">
            <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-700 to-indigo-700 bg-clip-text text-transparent">Basic Job Details</h2>
            
            <div className="grid grid-cols-1 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-800 mb-2">
                  Project Name
                </label>
<input
                  type="text"
                  name="project_name"
className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow"
                  placeholder="e.g., Mobile App Development, Website Redesign"
                  value={basicDetails.project_name}
                  onChange={handleBasicDetailsChange}
                  required
                />
              </div>

              <div>
<label className="block text-sm font-medium text-gray-800 mb-2">
                  Role Title
                </label>
                <input
                  type="text"
                  name="role_title"
className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow"
                  placeholder="e.g., Senior Frontend Developer, UI/UX Designer"
                  value={basicDetails.role_title}
                  onChange={handleBasicDetailsChange}
                  required
                />
              </div>

              <div>
<label className="block text-sm font-medium text-gray-800 mb-2">
                  Role Description
                </label>
                <textarea
                  name="role_description"
                  rows={4}
className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow"
                  placeholder="Briefly describe the role, key responsibilities, and what the candidate will be working on..."
                  value={basicDetails.role_description}
                  onChange={handleBasicDetailsChange}
                  required
                />
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleGenerateFields}
                disabled={loading}
                className="btn-primary flex items-center shadow hover:shadow-md transition bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-700 hover:to-indigo-700"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : (
                  <SparklesIcon className="h-5 w-5 mr-2" />
                )}
                {loading ? 'Generating...' : 'Generate Draft Fields'}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: AI Generated Fields */}
        {currentStep === 2 && (
          <div className="space-y-6 rounded-xl p-6 bg-white/80 backdrop-blur-sm shadow ring-1 ring-inset ring-gray-100">
            <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-700 to-indigo-700 bg-clip-text text-transparent">AI Generated Fields</h2>
            <p className="text-gray-600">Review and edit the AI-generated fields below:</p>

            {/* Key Skills */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-800">
                  Key Skills (comma-separated)
                </label>
                {similarJobs.length > 0 && (
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
                value={Array.isArray(aiFields.key_skills) ? aiFields.key_skills.join(', ') : ''}
                onChange={(e) => {
                  const skills = e.target.value.split(',').map(skill => skill.trim()).filter(skill => skill);
                  handleAiFieldsChange('key_skills', skills);
                }}
                className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow mb-2"
                placeholder="React, Node.js, JavaScript, Python, AWS"
              />
              {aiFields.key_skills && aiFields.key_skills.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {aiFields.key_skills.map((skill, index) => (
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

            {/* Required Experience */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-800">
                  Required Experience
                </label>
                {similarJobs.length > 0 && (
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
className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow"
                rows={3}
                value={aiFields.required_experience}
                onChange={(e) => handleAiFieldsChange('required_experience', e.target.value)}
                placeholder="Describe the required experience..."
              />
            </div>

            {/* Certifications */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-800">
                  Certifications (comma-separated)
                </label>
                {similarJobs.length > 0 && (
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
                value={Array.isArray(aiFields.certifications) ? aiFields.certifications.join(', ') : ''}
                onChange={(e) => {
                  const items = e.target.value.split(',').map(item => item.trim()).filter(item => item);
                  handleAiFieldsChange('certifications', items);
                }}
                className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow"
                placeholder="AWS Certified Developer, PMP, etc."
              />
            </div>

            {/* Additional Requirements */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-800">
                  Additional Requirements (comma-separated)
                </label>
                {similarJobs.length > 0 && (
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
                value={Array.isArray(aiFields.additional_requirements) ? aiFields.additional_requirements.join(', ') : ''}
                onChange={(e) => {
                  const items = e.target.value.split(',').map(item => item.trim()).filter(item => item);
                  handleAiFieldsChange('additional_requirements', items);
                }}
                className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow"
                placeholder="On-call availability, travel, specific tooling, etc."
              />
            </div>

            {/* Additional Details Section */}
<div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 pt-6 border-t border-gray-100">
              <div>
                <label className="block text-sm font-medium text-gray-800 mb-2">
                  Department
                </label>
                <input
                  type="text"
                  name="department"
className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow"
                  placeholder="e.g., Engineering, Marketing"
                  value={additionalDetails.department}
                  onChange={handleAdditionalDetailsChange}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 mb-2">
                  Location
                </label>
                <input
                  type="text"
                  name="location"
className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow"
                  placeholder="e.g., Remote, New York"
                  value={additionalDetails.location}
                  onChange={handleAdditionalDetailsChange}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 mb-2">
                  Job Type
                </label>
                <select
                  name="job_type"
className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow"
                  value={additionalDetails.job_type}
                  onChange={handleAdditionalDetailsChange}
                >
                  <option value="full-time">Full Time</option>
                  <option value="part-time">Part Time</option>
                  <option value="contract">Contract</option>
                  <option value="internship">Internship</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 mb-2">
                  Experience Level
                </label>
                <select
                  name="experience_level"
className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow"
                  value={additionalDetails.experience_level}
                  onChange={handleAdditionalDetailsChange}
                >
                  <option value="">Select Level</option>
                  <option value="entry">Entry Level</option>
                  <option value="mid">Mid Level</option>
                  <option value="senior">Senior Level</option>
                  <option value="lead">Lead/Principal</option>
                </select>
              </div>

            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setCurrentStep(1)}
className="btn-secondary shadow-sm hover:shadow transition"
              >
                Back
              </button>
              <button
                onClick={handleGenerateDescription}
                disabled={loading}
className="btn-primary flex items-center shadow hover:shadow-md transition"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : (
                  <DocumentTextIcon className="h-5 w-5 mr-2" />
                )}
                {loading ? 'Generating...' : 'Generate Job Description'}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Job Description & Submit */}
        {currentStep === 3 && (
          <div className="space-y-6 rounded-xl p-6 bg-white/80 backdrop-blur-sm shadow ring-1 ring-inset ring-gray-100">
            <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-700 to-indigo-700 bg-clip-text text-transparent">Job Description</h2>
            <p className="text-gray-600">Review and edit the AI-generated job description:</p>

            <div>
              <label className="block text-sm font-medium text-gray-800 mb-2">
                Short Description
              </label>
              <textarea
className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow"
                rows={3}
                value={jobDescription.short_description}
                onChange={(e) => handleDescriptionChange('short_description', e.target.value)}
                placeholder="Brief summary of the role (2-3 sentences)"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-800 mb-2">
                Full Job Description
              </label>
              {/* Optional: Preview markdown below the textarea to help users see formatting */}
              <textarea
                className="input-field focus:ring-primary-500 focus:border-primary-500 transition-shadow"
                rows={12}
                value={jobDescription.description}
                onChange={(e) => handleDescriptionChange('description', e.target.value)}
                placeholder="Complete job description with responsibilities, requirements, and benefits"
              />
              {/* Preview */}
              {jobDescription.description?.trim() && (
                <div className="mt-4 p-4 bg-gray-50 rounded-md ring-1 ring-inset ring-gray-200">
                  <div className="text-sm text-gray-600 mb-2">Preview</div>
                  <div className="prose max-w-none">
                    {/* keep plain here unless we import markdown; skip rendering in CreateJob for now */}
                    {/* You asked for frontend markdown rendering primarily for Job Details; preview can be enabled later if desired */}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setCurrentStep(2)}
className="btn-secondary shadow-sm hover:shadow transition bg-white/80 backdrop-blur-sm ring-1 ring-gray-200"
              >
                Back
              </button>
              <button
                onClick={handleSubmitJob}
                disabled={loading}
className="btn-primary shadow hover:shadow-md transition bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-700 hover:to-indigo-700"
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Creating Job...
                  </div>
                ) : (
                  'Create Job'
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CreateJob;
