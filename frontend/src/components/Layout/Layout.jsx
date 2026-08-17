import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopNavbar from './TopNavbar';

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  const getPageTitle = (pathname) => {
    switch (pathname) {
      case '/app':
      case '/app/dashboard':
        return 'Dashboard';
      case '/app/pharmaguard':
        return 'PharmaGuard AI Workbench';
      case '/app/chat':
        return 'AI Assistant';
      case '/app/predictions':
        return 'Molecular Predictions';
      case '/app/batch':
        return 'Batch Processing';
      case '/app/settings':
        return 'Settings';
      case '/app/help':
        return 'Help & Documentation';
      case '/app/contact':
        return 'Contact Support';
      default:
        return 'PharmaGuard AI';
    }
  };

  return (
    <div className="min-h-screen bg-canvas text-text-primary transition-colors duration-200 flex flex-col">
      {/* Sidebar */}
      <Sidebar 
        open={sidebarOpen} 
        setOpen={setSidebarOpen}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
      />
      
      {/* Main content wrapper */}
      <div className={`flex-1 flex flex-col ${sidebarCollapsed ? "lg:pl-20" : "lg:pl-72"} transition-all duration-300`}>
        {/* Top navbar */}
        <TopNavbar 
          setSidebarOpen={setSidebarOpen} 
          pageTitle={getPageTitle(location.pathname)}
        />
        
        {/* Page content */}
        <main className="flex-1 bg-canvas">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;