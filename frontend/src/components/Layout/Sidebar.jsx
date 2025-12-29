import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Link, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  BeakerIcon, 
  DocumentDuplicateIcon,
  ChatBubbleLeftRightIcon,
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/app/dashboard', icon: HomeIcon },
  { name: 'Predictions', href: '/app/predictions', icon: BeakerIcon },
  { name: 'Batch Processing', href: '/app/batch', icon: DocumentDuplicateIcon },
  { name: 'AI Assistant', href: '/app/chat', icon: ChatBubbleLeftRightIcon },
];

const Sidebar = ({ open, setOpen, collapsed, setCollapsed }) => {
  const location = useLocation();

  const SidebarContent = ({ isDesktop = false }) => (
    <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gradient-to-b from-gray-950 via-gray-900 to-black px-6 pb-4">
      {/* Logo */}
      <div className="flex h-16 shrink-0 items-center justify-between">
        <Link to="/" className={clsx(
          "flex items-center space-x-3 hover:scale-105 transition-transform duration-300",
          collapsed && isDesktop && "justify-center"
        )}>
          <div className="relative">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-600 backdrop-blur-sm flex items-center justify-center shadow-lg shadow-primary-500/50">
              <BeakerIcon className="h-6 w-6 text-white" />
            </div>
          </div>
          {(!collapsed || !isDesktop) && (
            <div>
              <h1 className="text-lg font-bold text-white">DeNovo Platform</h1>
              <p className="text-xs text-gray-400">ADMET Prediction</p>
            </div>
          )}
        </Link>
        {isDesktop && (
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          >
            {collapsed ? (
              <ChevronRightIcon className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronLeftIcon className="h-5 w-5 text-gray-400" />
            )}
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col">
        <ul role="list" className="flex flex-1 flex-col gap-y-7">
          <li>
            <ul role="list" className="-mx-2 space-y-1">
              {navigation.map((item) => (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    title={collapsed && isDesktop ? item.name : ''}
                    className={clsx(
                      location.pathname === item.href
                        ? 'bg-gradient-to-r from-primary-600 to-accent-600 text-white shadow-lg shadow-primary-500/30'
                        : 'text-gray-400 hover:text-white hover:bg-white/5',
                      'group flex gap-x-3 rounded-xl p-3 text-sm leading-6 font-medium transition-all duration-300 ease-in-out cursor-pointer',
                      collapsed && isDesktop && 'justify-center'
                    )}
                  >
                    <item.icon
                      className={clsx(
                        location.pathname === item.href ? 'text-white' : 'text-gray-400 group-hover:text-white',
                        'h-5 w-5 shrink-0 transition-all duration-300'
                      )}
                      aria-hidden="true"
                    />
                    {(!collapsed || !isDesktop) && (
                      <span className="flex-1">{item.name}</span>
                    )}
                    {location.pathname === item.href && (!collapsed || !isDesktop) && (
                      <div className="ml-auto h-2 w-2 rounded-full bg-white"></div>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          </li>
        </ul>
      </nav>

      {/* Platform info */}
      {(!collapsed || !isDesktop) && (
        <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-primary-500/10 to-accent-500/10 backdrop-blur-sm border border-primary-500/20">
          <div className="flex items-center">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary-500 to-accent-600 flex items-center justify-center shadow-lg shadow-primary-500/30">
              <BeakerIcon className="h-5 w-5 text-white" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-white">5 Models Active</p>
              <p className="text-xs text-gray-400">Production Ready</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Mobile sidebar */}
      <Transition.Root show={open} as={Fragment}>
        <Dialog as="div" className="relative z-50 lg:hidden" onClose={setOpen}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-gray-900/80" />
          </Transition.Child>

          <div className="fixed inset-0 flex">
            <Transition.Child
              as={Fragment}
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                <Transition.Child
                  as={Fragment}
                  enter="ease-in-out duration-300"
                  enterFrom="opacity-0"
                  enterTo="opacity-100"
                  leave="ease-in-out duration-300"
                  leaveFrom="opacity-100"
                  leaveTo="opacity-0"
                >
                  <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                    <button
                      type="button"
                      className="-m-2.5 p-2.5"
                      onClick={() => setOpen(false)}
                    >
                      <span className="sr-only">Close sidebar</span>
                      <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
                    </button>
                  </div>
                </Transition.Child>
                <SidebarContent isDesktop={false} />
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition.Root>

      {/* Static sidebar for desktop */}
      <div className={clsx(
        "hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:flex-col transition-all duration-300",
        collapsed ? "lg:w-20" : "lg:w-72"
      )}>
        <SidebarContent isDesktop={true} />
      </div>
    </>
  );
};

export default Sidebar;