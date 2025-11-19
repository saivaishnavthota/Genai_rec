import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  HomeIcon,
  BriefcaseIcon,
  UsersIcon,
  DocumentTextIcon,
  ChartBarIcon,
  CogIcon,
  PowerIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

const DashboardLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getNavigationItems = () => {
    const baseItems = [];

    if (user?.user_type === 'account_manager') {
      baseItems.push(
        { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
        { name: 'Jobs', href: '/jobs', icon: BriefcaseIcon },
      );
    }

    if (user?.user_type === 'hr') {
      baseItems.push(
        { name: 'HR Dashboard', href: '/hr-dashboard', icon: HomeIcon },
        { name: 'Applications', href: '/applications', icon: DocumentTextIcon },
        { name: 'Jobs', href: '/jobs', icon: BriefcaseIcon },
      );
    }

    if (user?.user_type === 'admin') {
      baseItems.push(
        { name: 'Admin Dashboard', href: '/admin-dashboard', icon: HomeIcon },
        { name: 'Applications', href: '/applications', icon: DocumentTextIcon },
        { name: 'Jobs', href: '/jobs', icon: BriefcaseIcon },
        { name: 'Users', href: '/users', icon: UsersIcon },
        { name: 'Companies', href: '/companies', icon: CogIcon },
        { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
      );
    }

    return baseItems;
  };

  const navigation = getNavigationItems();

  const isActive = (href) => {
    return location.pathname === href || location.pathname.startsWith(href + '/');
  };

  return (
    <>
      {user?.user_type === 'hr' || user?.user_type === 'account_manager' || user?.user_type === 'admin' ? (
        <div className="min-h-screen bg-white flex flex-col">
          {/* Header bar (matches first image layout) */}
          <header className="w-full border-b border-gray-200 bg-white">
            <div className="flex items-center justify-between px-6 py-3">
              {/* Left: Brand + Title */}
              <div className="flex items-center gap-3">
                <img src="/images/Nxzen_logo.jpg" alt="nxzen" className="h-8 w-8 rounded-md" />
                <span className="text-lg font-semibold text-gray-900">nxzen</span>
                <span className="h-6 w-px bg-gray-300" />
                <h1 className="text-lg sm:text-xl font-semibold text-gray-900">
                  {user?.user_type === 'hr' ? 'HR GenAI-Hiring' : user?.user_type === 'admin' ? 'Admin Dashboard' : 'Account Manager Dashboard'}
                </h1>
              </div>

              {/* Right: User info + Logout */}
              <div className="flex items-center gap-4">
                <div className="flex flex-col items-end">
                  <span className="text-sm font-medium text-gray-900">{user?.full_name}</span>
                  <span className="text-xs text-gray-500">{user?.email}</span>
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="inline-flex items-center rounded-lg p-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100"
                  title="Logout"
                  aria-label="Logout"
                >
                  <PowerIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          </header>

          {/* Horizontal navigation (matches second image layout, using sidebar items) */}
          <nav className="w-full  bg-gray-50">
            <div className="max-w-7xl mx-auto flex flex-wrap justify-center items-center gap-6 px-8 py-3">
              {navigation.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`group inline-flex items-center justify-center gap-2 text-sm px-6 py-2 rounded-md min-w-[180px] transition-colors duration-200 ${
                      active ? 'text-blue-700 border-b-2 border-blue-600' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </nav>

          {/* Page content */}
          <main className="flex-1 overflow-y-auto focus:outline-none">
            <div className="py-6  bg-gray-50">
              <div className="max-w-7xl mx-auto px-6">
                <Outlet />
              </div>
            </div>
          </main>
        </div>
      ) : (
        <div className="min-h-screen bg-gray-50 flex">
          {/* Mobile sidebar */}
          <div className={`fixed inset-0 z-40 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
            <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)}></div>
            <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
              <div className="absolute top-0 right-0 -mr-12 pt-2">
                <button
                  className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                  onClick={() => setSidebarOpen(false)}
                >
                  <XMarkIcon className="h-6 w-6 text-white" />
                </button>
              </div>
              <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
                <div className="flex-shrink-0 flex items-center px-4">
                  <h1 className="text-xl font-bold text-gray-900">GenAI Hiring</h1>
                </div>
                <nav className="mt-5 px-2 space-y-1">
                  {navigation.map((item) => {
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.name}
                        to={item.href}
                        className={`${
                          isActive(item.href)
                            ? 'bg-primary-100 text-primary-700'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        } group flex items-center px-2 py-2 text-base font-medium rounded-md`}
                        onClick={() => setSidebarOpen(false)}
                      >
                        <Icon className="mr-4 h-6 w-6" />
                        {item.name}
                      </Link>
                    );
                  })}
                </nav>
              </div>
            </div>
          </div>

          {/* Desktop sidebar */}
          <div className="hidden lg:flex lg:flex-shrink-0">
            <div className="flex flex-col w-64 bg-white border-r border-gray-200">
              <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
                <div className="flex items-center flex-shrink-0 px-4">
                  <h1 className="text-xl font-bold text-gray-900">GenAI Hiring</h1>
                </div>
                <nav className="mt-5 flex-1 px-2 space-y-1">
                  {navigation.map((item) => {
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.name}
                        to={item.href}
                        className={`${
                          isActive(item.href)
                            ? 'bg-primary-100 text-primary-700'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        } group flex items-center px-2 py-2 text-sm font-medium rounded-md`}
                      >
                        <Icon className="mr-3 h-5 w-5" />
                        {item.name}
                      </Link>
                    );
                  })}
                </nav>
              </div>
            </div>
          </div>

          {/* Main content */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {/* Top navigation */}
            <div className="bg-white shadow-sm border-b border-gray-200">
              <div className="flex justify-between h-16 px-4 sm:px-6 lg:px-8">
                <div className="flex items-center">
                  <button
                    className="lg:hidden -ml-2 mr-2 h-12 w-12 inline-flex items-center justify-center rounded-md text-gray-500 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
                    onClick={() => setSidebarOpen(true)}
                  >
                    <Bars3Icon className="h-6 w-6" />
                  </button>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-sm text-gray-600">
                    Welcome, {user?.full_name}
                  </div>
                  <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    {user?.user_type?.replace('_', ' ').toUpperCase()}
                  </div>
                  <button
                    onClick={handleLogout}
                    className="text-gray-500 hover:text-gray-700 inline-flex items-center p-2 rounded-md hover:bg-gray-100"
                    title="Logout"
                    aria-label="Logout"
                  >
                    <PowerIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Page content */}
            <main className="flex-1 overflow-y-auto focus:outline-none">
              <div className="py-6">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                  <Outlet />
                </div>
              </div>
            </main>
          </div>
        </div>
      )}
    </>
  );
};

export default DashboardLayout;
