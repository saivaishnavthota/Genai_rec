import React from 'react';
import { Outlet, Link, NavLink } from 'react-router-dom';

const PublicLayout = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="w-full px-0 sm:px-2">
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-2">
              <img src="/images/Nxzen_logo.jpg" alt="nxzen" className="h-9 w-10 rounded-md ml-4" />
              <span className="text-lg font-semibold text-gray-900">nxzen</span>
              <span className="h-6 w-px bg-gray-300" />
              <Link to="/careers" className="text-lg sm:text-xl font-semibold text-gray-900">
                Careers
              </Link>
            </div>
            <nav className="flex space-x-8">
              <NavLink
                to="/careers"
                className={({ isActive }) =>
                  `relative inline-flex items-center px-3 py-2 text-sm font-medium border-b-2 transition-colors duration-200 ${
                    isActive
                      ? 'text-gray-900 border-[#39FF14]'
                      : 'text-gray-600 hover:text-gray-900 hover:border-gray-300 border-transparent'
                  }`
                }
              >
                Browse Jobs
              </NavLink>
              <NavLink
                to="/application-status"
                className={({ isActive }) =>
                  `relative inline-flex items-center px-3 py-2 text-sm font-medium border-b-2 transition-colors duration-200 ${
                    isActive
                      ? 'text-gray-900 border-[#39FF14]'
                      : 'text-gray-600 hover:text-gray-900 hover:border-gray-300 border-transparent'
                  }`
                }
              >
                Check Application
              </NavLink>
              <NavLink
                to="/login"
                className={({ isActive }) =>
                  `relative inline-flex items-center px-3 py-2 text-sm font-medium border-b-2 transition-colors duration-200 ${
                    isActive
                      ? 'text-gray-900 border-[#39FF14]'
                      : 'text-gray-600 hover:text-gray-900 hover:border-gray-300 border-transparent'
                  }`
                }
              >
                Staff Login
              </NavLink>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main>
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600">
            <p>&copy; 2024 GenAI Hiring System. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PublicLayout;
