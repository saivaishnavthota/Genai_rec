import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import PrivateRoute from './components/PrivateRoute';
import PublicRoute from './components/PublicRoute';

// Auth Pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';

// Dashboard Pages
import AccountManagerDashboard from './pages/dashboard/AccountManagerDashboard';
import HRDashboard from './pages/dashboard/HRDashboard';
import AdminDashboard from './pages/dashboard/AdminDashboard';

// Job Pages
import JobList from './pages/jobs/JobList';
import CreateJob from './pages/jobs/CreateJob';
import EditJob from './pages/jobs/EditJob';
import JobDetails from './pages/jobs/JobDetails';

// Application Pages
import ApplicationList from './pages/applications/ApplicationList';
import ApplicationDetails from './pages/applications/ApplicationDetails';

// Public Pages
import CareersPage from './pages/public/CareersPage';
import JobDetailsPublic from './pages/public/JobDetailsPublic';
import ApplyJob from './pages/public/ApplyJob';
import ApplicationStatus from './pages/public/ApplicationStatus';
import SlotSelection from './pages/public/SlotSelection';
import InterviewerReview from './pages/public/InterviewerReview';
import ResumeUpdate from './pages/ResumeUpdate';
// AI Interview Pages
import AIInterviewRoomPage from './pages/AIInterviewRoomPage';
import AIInterviewReviewPage from './pages/AIInterviewReviewPage';
// Layout
import DashboardLayout from './components/layout/DashboardLayout';
import PublicLayout from './components/layout/PublicLayout';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public Routes */}
            <Route element={<PublicLayout />}>
              <Route path="/careers" element={<CareersPage />} />
              <Route path="/careers/job/:jobId" element={<JobDetailsPublic />} />
              <Route path="/careers/apply/:jobId" element={<ApplyJob />} />
              <Route path="/application-status" element={<ApplicationStatus />} />
              <Route path="/select-slot/:applicationId" element={<SlotSelection />} />
              <Route path="/interviewer-review/:token" element={<InterviewerReview />} />
              <Route path="/update-resume/:referenceNumber" element={<ResumeUpdate />} />
              <Route path="/ai-interview/:sessionId" element={<AIInterviewRoomPage />} />
            </Route>

            {/* Auth Routes */}
            <Route path="/login" element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } />
            <Route path="/register" element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            } />

            {/* Protected Dashboard Routes */}
            <Route element={
              <PrivateRoute>
                <DashboardLayout />
              </PrivateRoute>
            }>
              {/* Account Manager Routes */}
              <Route path="/dashboard" element={<AccountManagerDashboard />} />
              <Route path="/jobs" element={<JobList />} />
              <Route path="/jobs/create" element={<CreateJob />} />
              <Route path="/jobs/:jobId/edit" element={<EditJob />} />
              <Route path="/jobs/:jobId" element={<JobDetails />} />
              <Route path="/applications" element={<ApplicationList />} />
              <Route path="/applications/:applicationId" element={<ApplicationDetails />} />

              {/* HR Routes */}
              <Route path="/hr-dashboard" element={<HRDashboard />} />
              <Route path="/applications" element={<ApplicationList />} />
              <Route path="/applications/:applicationId" element={<ApplicationDetails />} />
              <Route path="/review/ai-interview/:sessionId" element={<AIInterviewReviewPage />} />

              {/* Admin Routes */}
              <Route path="/admin-dashboard" element={<AdminDashboard />} />
            </Route>

            {/* Redirects */}
            <Route path="/" element={<Navigate to="/careers" replace />} />
            <Route path="*" element={<Navigate to="/careers" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
