import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { jobService } from '../../services/jobService';
import { 
  BriefcaseIcon, 
  MapPinIcon, 
  ClockIcon,
  MagnifyingGlassIcon,
  FunnelIcon 
} from '@heroicons/react/24/outline';

const CareersPage = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    department: '',
    location: '',
    job_type: ''
  });

  useEffect(() => {
    loadJobs();
  }, [filters]);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const data = await jobService.getPublicJobs(filters);
      setJobs(data);
    } catch (error) {
      console.error('Error loading jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredJobs = jobs.filter(job =>
    job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    job.description.toLowerCase().includes(searchTerm.toLowerCase())
  );
  // Unique filter options derived from loaded jobs
  const departments = useMemo(() => Array.from(new Set(jobs.map(j => j.department).filter(Boolean))), [jobs]);
  const locations = useMemo(() => Array.from(new Set(jobs.map(j => j.location).filter(Boolean))), [jobs]);
  const jobTypes = useMemo(() => Array.from(new Set(jobs.map(j => j.job_type).filter(Boolean))), [jobs]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Hero theme: set to 'purple' or 'green'
  const heroTheme = 'black'
  const heroGradient = 'bg-black'
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-primary-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className={`absolute inset-0 ${heroGradient}`} />
        {/* Disable glow overlays for pure black background */}
        <div className="hidden" />
        <div className="hidden" />
        <div className="relative py-5">
          <div className="w-full px-0 sm:px-2">
            <div className="text-center text-white">
              <h1 className="text-2xl font-bold mb-4 drop-shadow-sm">Build the Future with Us</h1>
              <p className="text-xl text-primary-100 mb-8">Join our team where innovation meets integrity</p>
              <div className="flex justify-center gap-3 flex-wrap mb-6">
                <span className="px-3 py-1 text-xs rounded-full bg-white/10 border border-[#39FF14]/30 text-white">Empowered Teams</span>
                <span className="px-3 py-1 text-xs rounded-full bg-white/10 border border-[#39FF14]/30 text-white">Inclusive Culture</span>
                <span className="px-3 py-1 text-xs rounded-full bg-white/10 border border-[#39FF14]/30 text-white">Growth Together</span>
              </div>
              <div className="flex justify-center gap-4 mb-8">
                <a href="#open-roles" className="inline-flex items-center px-4 py-2 rounded-md bg-[#39FF14] text-black font-medium shadow-sm ring-1 ring-[#39FF14] hover:shadow-lg">Browse Open Roles</a>
                <Link to="/application-status" className="inline-flex items-center px-4 py-2 rounded-md border border-white/40 text-white hover:bg-white/10">Check Application Status</Link>
              </div>
              <div className="max-w-2xl mx-auto">
                <div className="relative">
                  {/* Search icon inside the input */}
                  <MagnifyingGlassIcon className="pointer-events-none absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search jobs..."
                    className="w-full pl-10 pr-4 py-3 bg-white text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-white shadow-sm"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* Explore Jobs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar Filters */}
          <aside className="lg:col-span-1 space-y-4">
            <div className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50 to-white shadow-sm">
              <div className="p-5 border-b border-emerald-100 bg-emerald-50/50 rounded-t-2xl">
                <div className="flex items-center gap-2">
                  <FunnelIcon className="h-5 w-5 text-primary-600" />
                  <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
                </div>
              </div>
              <div className="p-5 space-y-5">
                {/* Department */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1.5">Department</label>
                  <select
                    className="w-full border border-gray-200 rounded-md text-sm p-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
                    value={filters.department}
                    onChange={(e) => handleFilterChange('department', e.target.value)}
                  >
                    <option value="">All</option>
                    {departments.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                </div>
                {/* Location */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1.5">Location</label>
                  <select
                    className="w-full border border-gray-200 rounded-md text-sm p-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
                    value={filters.location}
                    onChange={(e) => handleFilterChange('location', e.target.value)}
                  >
                    <option value="">All</option>
                    {locations.map((l) => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </div>
                {/* Job Type */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1.5">Job Type</label>
                  <select
                    className="w-full border border-gray-200 rounded-md text-sm p-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
                    value={filters.job_type}
                    onChange={(e) => handleFilterChange('job_type', e.target.value)}
                  >
                    <option value="">All</option>
                    {jobTypes.map((t) => (
                      <option key={t} value={t}>{t.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Helpful CTA */}
            
          </aside>

          {/* Jobs Grid */}
          <div id="open-roles" className="lg:col-span-3">
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading jobs...</p>
              </div>
            ) : filteredJobs.length > 0 ? (
              <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                {filteredJobs.map((job, index) => (
                  <div key={job.id} className={`group h-full flex flex-col rounded-2xl border border-gray-100 ${getCardTheme(job, index)} backdrop-blur-sm shadow-sm hover:shadow-xl hover:-translate-y-0.5 transition-all`}>
                    <div className="p-5 flex-1">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-primary-700 transition-colors">
                            {job.title}
                          </h3>
                          <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                            {job.short_description || job.description.substring(0, 150) + '...'}
                          </p>
                        </div>
                      </div>
                      <div className="space-y-2 mb-3">
                        {job.department && (
                          <div className="flex items-center text-sm text-gray-500">
                            <BriefcaseIcon className="h-4 w-4 mr-2" />
                            {job.department}
                          </div>
                        )}
                        {job.location && (
                          <div className="flex items-center text-sm text-gray-500">
                            <MapPinIcon className="h-4 w-4 mr-2" />
                            {job.location}
                          </div>
                        )}
                        {job.job_type && (
                          <div className="flex items-center text-sm text-gray-500">
                            <ClockIcon className="h-4 w-4 mr-2" />
                            {job.job_type.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </div>
                        )}
                      </div>
                      {job.key_skills && job.key_skills.length > 0 && (
                        <div className="mb-3">
                          <div className="flex flex-wrap gap-1.5">
                            {job.key_skills.slice(0, 3).map((skill, index) => (
                              <span key={index} className="inline-block bg-primary-100 text-primary-800 text-xs px-2.5 py-1 rounded">
                                {skill}
                              </span>
                            ))}
                            {job.key_skills.length > 3 && (
                              <span className="inline-block text-gray-500 text-xs px-2.5 py-1">+{job.key_skills.length - 3} more</span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="px-5 pb-5 pt-0 flex items-center justify-between">
                      <Link to={`/careers/job/${job.id}`} className="text-purple-500 hover:text-purple-700 text-sm font-medium">
                        View Details
                      </Link>
                      <Link to={`/careers/apply/${job.id}`} className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 text-sm font-medium rounded-md transition-colors">
                        Apply Now
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <BriefcaseIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
                <p className="text-gray-600">{searchTerm ? 'Try adjusting your search or filters.' : 'Check back later for new opportunities.'}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CareersPage;

// Light theme palette for job cards
const cardThemes = [
  'from-emerald-50 to-white',
  'from-sky-50 to-white',
  'from-rose-50 to-white',
  'from-amber-50 to-white',
  'from-indigo-50 to-white',
  'from-fuchsia-50 to-white'
];
const getCardTheme = (job, idx) => `bg-gradient-to-br ${cardThemes[((job?.id ?? idx) % cardThemes.length + cardThemes.length) % cardThemes.length]}`;
