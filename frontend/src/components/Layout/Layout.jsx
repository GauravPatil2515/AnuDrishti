import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopNavbar from './TopNavbar';

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  // Get page title based on current route
  const getPageTitle = (pathname) => {
    switch (pathname) {
      case '/':
        return 'Dashboard';
      case '/predictions':
        return 'Molecular Predictions';
      case '/batch':
        return 'Batch Processing';
      case '/results':
        return 'Results & Analytics';
      case '/analytics':
        return 'Advanced Analytics';
      case '/settings':
        return 'Settings';
      case '/help':
        return 'Help & Documentation';
      case '/contact':
        return 'Contact Support';
      default:
        return 'DeNovo';
    }
  };

  return (
    <div className="min-h-screen bg-black">
      {/* Sidebar */}
      <Sidebar 
        open={sidebarOpen} 
        setOpen={setSidebarOpen}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
      />
      
      {/* Main content */}
      <div className={sidebarCollapsed ? "lg:pl-20" : "lg:pl-72"} style={{ transition: 'padding 300ms' }}>
        {/* Top navbar */}
        <TopNavbar 
          setSidebarOpen={setSidebarOpen} 
          pageTitle={getPageTitle(location.pathname)}
        />
        
        {/* Page content */}
        <main className="py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;