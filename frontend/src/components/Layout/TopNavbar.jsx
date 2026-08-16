import React, { Fragment } from 'react';
import { Menu, Transition, Popover } from '@headlessui/react';
import {
  MagnifyingGlassIcon,
  BellIcon,
  Bars3Icon,
  UserCircleIcon,
  CogIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

const TopNavbar = ({ setSidebarOpen, pageTitle = 'Dashboard' }) => {
  const userNavigation = [
    { name: 'Your Profile', href: '/app/profile', icon: UserCircleIcon },
    { name: 'Settings', href: '/app/settings', icon: CogIcon },
    { name: 'Sign out', href: '/', icon: ArrowRightOnRectangleIcon },
  ];

  const notifications = [
    { id: 1, title: 'Model Training Complete', message: 'XGBoost model finished training with 94% accuracy', time: '2 min ago', type: 'success' },
    { id: 2, title: 'Batch Processing', message: '250 molecules processed successfully', time: '5 min ago', type: 'info' },
    { id: 3, title: 'System Update', message: 'New features available in prediction pipeline', time: '1 hour ago', type: 'update' },
  ];

  const getNotificationDot = (type) => {
    switch (type) {
      case 'success': return 'bg-emerald-400';
      case 'info': return 'bg-indigo-400';
      case 'update': return 'bg-amber-400';
      default: return 'bg-white/40';
    }
  };

  return (
    <div className="sticky top-0 z-40 flex h-14 shrink-0 items-center gap-x-2 border-b border-border bg-canvas-elevated/80 px-3 backdrop-blur-md sm:px-6">
      <button
        type="button"
        className="-m-2.5 p-2.5 text-muted hover:text-primary lg:hidden"
        onClick={() => setSidebarOpen(true)}
      >
        <span className="sr-only">Open sidebar</span>
        <Bars3Icon className="h-6 w-6" aria-hidden="true" />
      </button>

      <div className="flex flex-1 items-center gap-x-3 self-stretch">
        <h1 className="truncate text-sm font-semibold text-primary sm:text-base">{pageTitle}</h1>
        <form className="relative hidden flex-1 md:flex max-w-md" action="#" method="GET">
          <label htmlFor="search-field" className="sr-only">Search</label>
          <MagnifyingGlassIcon className="pointer-events-none absolute inset-y-0 left-0 h-full w-5 text-muted pl-3" aria-hidden="true" />
          <input
            id="search-field"
            className="block h-full w-full border-0 bg-transparent py-0 pl-10 pr-0 text-sm text-primary placeholder:text-muted focus:ring-0"
            placeholder="Search molecules, results, or models..."
            type="search"
            name="search"
          />
        </form>
      </div>

      <div className="flex items-center gap-x-2">
        <Popover className="relative">
          <Popover.Button className="relative rounded-lg bg-surface p-2 text-muted transition-colors hover:bg-surface-hover hover:text-primary">
            <span className="sr-only">View notifications</span>
            <BellIcon className="h-5 w-5" aria-hidden="true" />
            <div className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-accent-indigo text-[10px] font-medium text-white">
              {notifications.length}
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
            <Popover.Panel className="absolute right-0 z-10 mt-2 w-80 origin-top-right rounded-xl border border-border bg-canvas-elevated p-2 shadow-card backdrop-blur-xl">
              <div className="px-3 py-2 border-b border-border">
                <h3 className="text-sm font-semibold text-primary">Notifications</h3>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {notifications.map((notification) => (
                  <div key={notification.id} className="flex items-start gap-3 rounded-lg px-3 py-3 transition-colors hover:bg-surface">
                    <div className={clsx('mt-1.5 h-2 w-2 shrink-0 rounded-full', getNotificationDot(notification.type))} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-primary">{notification.title}</p>
                      <p className="mt-0.5 text-xs text-secondary">{notification.message}</p>
                      <p className="mt-1 text-xs text-muted">{notification.time}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="border-t border-border px-3 py-2">
                <button className="text-sm font-medium text-accent-indigo hover:text-accent-indigoHover">View all notifications</button>
              </div>
            </Popover.Panel>
          </Transition>
        </Popover>
      </div>
    </div>
  );
};

export default TopNavbar;
