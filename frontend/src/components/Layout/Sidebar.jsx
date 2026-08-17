import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Link, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  BeakerIcon, 
  ChatBubbleLeftRightIcon,
  ShieldCheckIcon,
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

const navigation = [
  { name: 'PharmaGuard Workbench', href: '/app/pharmaguard', icon: ShieldCheckIcon, highlight: true },
  { name: 'Dashboard', href: '/app/dashboard', icon: HomeIcon },
  { name: 'AI Assistant', href: '/app/chat', icon: ChatBubbleLeftRightIcon },
];

const Sidebar = ({ open, setOpen, collapsed, setCollapsed }) => {
  const location = useLocation();

  const SidebarContent = ({ isDesktop = false }) => (
    <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-canvas-elevated border-r border-border px-4 pb-4 transition-colors duration-200">
      {/* Logo */}
      <div className="flex h-16 shrink-0 items-center justify-between border-b border-border">
        <Link to="/" className={clsx(
          "flex items-center space-x-3 hover:opacity-90 transition-opacity",
          collapsed && isDesktop && "justify-center"
        )}>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-green/10 text-accent-green border border-accent-green/20">
            <ShieldCheckIcon className="h-5 w-5" />
          </div>
          {(!collapsed || !isDesktop) && (
            <div>
              <h1 className="text-sm font-bold text-text-primary font-display tracking-tight">PharmaGuard AI</h1>
              <p className="text-[10px] text-text-muted font-medium">Toxicity Decision Support</p>
            </div>
          )}
        </Link>
        {isDesktop && (
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface transition-colors"
          >
            {collapsed ? (
              <ChevronRightIcon className="h-4 w-4" />
            ) : (
              <ChevronLeftIcon className="h-4 w-4" />
            )}
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col pt-2">
        <ul role="list" className="flex flex-1 flex-col gap-y-6">
          <li>
            <div className={clsx("text-[10px] font-bold uppercase tracking-wider text-text-muted mb-2 px-2", collapsed && isDesktop && "sr-only")}>
              Platform Navigation
            </div>
            <ul role="list" className="space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href || (item.href === '/app/pharmaguard' && location.pathname === '/app');
                return (
                  <li key={item.name}>
                    <Link
                      to={item.href}
                      title={collapsed && isDesktop ? item.name : ''}
                      className={clsx(
                        isActive
                          ? 'bg-accent-green/10 text-accent-green border-accent-green/30 font-semibold'
                          : 'text-text-secondary hover:text-text-primary hover:bg-surface border-transparent',
                        'group flex items-center gap-x-3 rounded-lg px-3 py-2.5 text-xs border transition-all duration-150',
                        collapsed && isDesktop && 'justify-center'
                      )}
                    >
                      <item.icon
                        className={clsx(
                          isActive ? 'text-accent-green' : 'text-text-muted group-hover:text-text-primary',
                          'h-4 w-4 shrink-0 transition-colors'
                        )}
                        aria-hidden="true"
                      />
                      {(!collapsed || !isDesktop) && (
                        <span className="flex-1 truncate">{item.name}</span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </li>
        </ul>
      </nav>

      {/* Status card */}
      {(!collapsed || !isDesktop) && (
        <div className="p-3 rounded-xl bg-surface border border-border mt-auto">
          <div className="flex items-center gap-3">
            <div className="h-2 w-2 rounded-full bg-accent-emerald animate-pulse"></div>
            <div>
              <p className="text-xs font-bold text-text-primary">5 Models Active</p>
              <p className="text-[10px] text-text-muted">Attention-GIN Ensemble</p>
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
            <div className="fixed inset-0 bg-canvas/80 backdrop-blur-sm" />
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
                  leaveFrom="opacity-0"
                  leaveTo="opacity-100"
                >
                  <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                    <button
                      type="button"
                      className="-m-2.5 p-2.5 text-text-primary"
                      onClick={() => setOpen(false)}
                    >
                      <span className="sr-only">Close sidebar</span>
                      <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                    </button>
                  </div>
                </Transition.Child>
                <SidebarContent isDesktop={false} />
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition.Root>

      {/* Desktop sidebar */}
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