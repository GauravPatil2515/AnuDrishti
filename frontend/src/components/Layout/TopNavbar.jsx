import React, { Fragment } from 'react';
import { Menu, Transition, Popover } from '@headlessui/react';
import { 
  MagnifyingGlassIcon,
  BellIcon,
  Bars3Icon,
  ChevronDownIcon,
  UserCircleIcon,
  CogIcon,
  ArrowRightOnRectangleIcon,
  SunIcon,
  MoonIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

const TopNavbar = ({ setSidebarOpen, pageTitle = 'Dashboard' }) => {
  const [darkMode, setDarkMode] = React.useState(false);

  const userNavigation = [
    { name: 'Your Profile', href: '/app/profile', icon: UserCircleIcon },
    { name: 'Settings', href: '/app/settings', icon: CogIcon },
    { name: 'Sign out', href: '/', icon: ArrowRightOnRectangleIcon },
  ];

  const notifications = [
    {
      id: 1,
      title: 'Model Training Complete',
      message: 'XGBoost model has finished training with 94% accuracy',
      time: '2 min ago',
      type: 'success'
    },
    {
      id: 2,
      title: 'Batch Processing',
      message: '250 molecules processed successfully',
      time: '5 min ago',
      type: 'info'
    },
    {
      id: 3,
      title: 'System Update',
      message: 'New features available in prediction pipeline',
      time: '1 hour ago',
      type: 'update'
    }
  ];

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success':
        return 'bg-success-100 text-success-600';
      case 'info':
        return 'bg-primary-100 text-primary-600';
      case 'update':
        return 'bg-warning-100 text-warning-600';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-2 sm:gap-x-4 border-b border-cyan-500/30 bg-black backdrop-blur-sm px-2 sm:px-4 shadow-soft sm:px-6 lg:px-8">
      {/* Mobile menu button */}
      <button
        type="button"
        className="-m-2.5 p-2.5 text-cyan-400 lg:hidden"
        onClick={() => setSidebarOpen(true)}
      >
        <span className="sr-only">Open sidebar</span>
        <Bars3Icon className="h-6 w-6" aria-hidden="true" />
      </button>

      {/* Separator */}
      <div className="h-6 w-px bg-cyan-500/20 lg:hidden" aria-hidden="true" />

      {/* Page title */}
      <div className="flex flex-1 gap-x-2 sm:gap-x-4 self-stretch lg:gap-x-6">
        <div className="flex items-center">
          <h1 className="text-base sm:text-xl font-semibold text-cyan-400 truncate">{pageTitle}</h1>
        </div>
        
        {/* Search - Hidden on mobile, visible on tablet+ */}
        <form className="relative hidden md:flex flex-1 max-w-md" action="#" method="GET">
          <label htmlFor="search-field" className="sr-only">
            Search
          </label>
          <MagnifyingGlassIcon
            className="pointer-events-none absolute inset-y-0 left-0 h-full w-5 text-gray-500 pl-3"
            aria-hidden="true"
          />
          <input
            id="search-field"
            className="block h-full w-full border-0 py-0 pl-10 pr-0 text-gray-300 placeholder:text-gray-600 focus:ring-0 sm:text-sm bg-transparent"
            placeholder="Search molecules, results, or models..."
            type="search"
            name="search"
          />
        </form>
      </div>

      <div className="flex items-center gap-x-1 sm:gap-x-2 lg:gap-x-4">
        {/* Notifications dropdown */}
        <Popover className="relative">
          <Popover.Button className="relative rounded-full bg-gray-900 p-2 text-cyan-400 hover:text-cyan-300 hover:bg-gray-800 hover:scale-110 transition-all duration-300 ease-in-out">
            <span className="sr-only">View notifications</span>
            <BellIcon className="h-5 w-5" aria-hidden="true" />
            {/* Notification badge */}
            <div className="absolute -top-0.5 -right-0.5 h-4 w-4 bg-danger-500 rounded-full flex items-center justify-center">
              <span className="text-xs font-medium text-white">{notifications.length}</span>
            </div>
          </Popover.Button>

          <Transition
            as={Fragment}
            enter="transition ease-out duration-200"
            enterFrom="opacity-0 translate-y-1"
            enterTo="opacity-100 translate-y-0"
            leave="transition ease-in duration-150"
            leaveFrom="opacity-100 translate-y-0"
            leaveTo="opacity-0 translate-y-1"
          >
            <Popover.Panel className="absolute right-0 z-10 mt-2 w-80 origin-top-right rounded-xl bg-white py-2 shadow-luxury ring-1 ring-gray-900/5">
              <div className="px-4 py-3 border-b border-gray-100">
                <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {notifications.map((notification) => (
                  <div key={notification.id} className="px-4 py-3 hover:bg-gray-50 hover:scale-105 cursor-pointer transition-all duration-300 ease-in-out">
                    <div className="flex items-start space-x-3">
                      <div className={clsx(
                        'flex-shrink-0 w-2 h-2 rounded-full mt-2',
                        getNotificationIcon(notification.type)
                      )} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {notification.title}
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          {notification.time}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="px-4 py-3 border-t border-gray-100">
                <button className="text-sm font-medium text-primary-600 hover:text-primary-500">
                  View all notifications
                </button>
              </div>
            </Popover.Panel>
          </Transition>
        </Popover>
      </div>
    </div>
  );
};

export default TopNavbar;