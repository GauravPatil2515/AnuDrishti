import React, { Fragment, useState } from 'react';
import { Menu, Transition, Popover } from '@headlessui/react';
import { useNavigate } from 'react-router-dom';
import {
  MagnifyingGlassIcon,
  BellIcon,
  Bars3Icon,
  UserCircleIcon,
  CogIcon,
  ArrowRightOnRectangleIcon,
  SunIcon,
  MoonIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { useTheme, useAnalysis } from '../../App';
import api from '../../api';
import { toast } from 'react-hot-toast';

const TopNavbar = ({ setSidebarOpen, pageTitle = 'Dashboard' }) => {
  const { theme, toggleTheme } = useTheme();
  const { addAnalysis } = useAnalysis();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);

  const handleSearchSubmit = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim() || searching) return;
    const term = searchQuery.trim();
    setSearching(true);
    toast.loading(`Searching compound "${term}"...`, { id: 'search-toast' });

    try {
      let smiles = term;
      // If term is not a raw SMILES string (simple heuristic: contains spaces or no standard SMILES characters)
      const isSmiles = /[()\[\]=#@\/\.0-9]/.test(term) && !term.includes(' ');
      if (!isSmiles) {
        const lookupRes = await api.post('/api/lookup/smiles', { name: term });
        if (lookupRes.data?.canonical_smiles) {
          smiles = lookupRes.data.canonical_smiles;
        } else {
          toast.error(`Could not resolve drug name "${term}"`, { id: 'search-toast' });
          setSearching(false);
          return;
        }
      }

      // Run analysis
      const analysisRes = await api.post('/api/analyze/single', { smiles, include_explanation: true });
      if (analysisRes.data?.analysis) {
        addAnalysis(analysisRes.data.analysis);
        toast.success(`Analyzed ${term}`, { id: 'search-toast' });
        setSearchQuery('');
        navigate('/app/safety');
      } else {
        toast.error(`Analysis failed for "${term}"`, { id: 'search-toast' });
      }
    } catch (err) {
      toast.error(`Search error for "${term}"`, { id: 'search-toast' });
    } finally {
      setSearching(false);
    }
  };

  const notifications = [
    { id: 1, title: 'Model Training Complete', message: 'Attention-GIN model loaded with 16 active ADMET targets', time: '2 min ago', type: 'success' },
    { id: 2, title: 'Batch Processing', message: 'Library screening pipeline ready', time: '5 min ago', type: 'info' },
    { id: 3, title: 'Faithfulness Gatekeeper', message: 'EFS scoring engine operational (threshold ≥ 0.70)', time: '1 hour ago', type: 'update' },
  ];

  const getNotificationDot = (type) => {
    switch (type) {
      case 'success': return 'bg-accent-emerald';
      case 'info': return 'bg-accent-green';
      case 'update': return 'bg-accent-amber';
      default: return 'bg-text-muted';
    }
  };

  return (
    <div className="sticky top-0 z-40 flex h-14 shrink-0 items-center gap-x-4 border-b border-border bg-canvas-overlay px-4 backdrop-blur-md sm:px-6 transition-colors duration-200">
      <button
        type="button"
        className="-m-2.5 p-2.5 text-text-muted hover:text-text-primary lg:hidden"
        onClick={() => setSidebarOpen(true)}
      >
        <span className="sr-only">Open sidebar</span>
        <Bars3Icon className="h-6 w-6" aria-hidden="true" />
      </button>

      <div className="flex flex-1 items-center gap-x-3 self-stretch">
        <h1 className="truncate text-base font-bold text-text-primary font-display">{pageTitle}</h1>
        <form className="relative hidden flex-1 md:flex max-w-md" onSubmit={handleSearchSubmit}>
          <label htmlFor="search-field" className="sr-only">Search</label>
          <MagnifyingGlassIcon className="pointer-events-none absolute inset-y-0 left-0 h-full w-5 text-text-muted pl-3" aria-hidden="true" />
          <input
            id="search-field"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            disabled={searching}
            className="block h-full w-full border-0 bg-transparent py-0 pl-10 pr-0 text-sm text-text-primary placeholder:text-text-muted focus:ring-0 focus:outline-none"
            placeholder="Search drug (e.g. Aspirin, Warfarin) or SMILES..."
            type="search"
            name="search"
          />
        </form>
      </div>

      <div className="flex items-center gap-x-3">
        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface transition-colors"
          title="Toggle Light / Dark Theme"
        >
          {theme === 'dark' ? <SunIcon className="h-5 w-5" /> : <MoonIcon className="h-5 w-5" />}
        </button>

        {/* Notifications Popover */}
        <Popover className="relative">
          <Popover.Button className="relative rounded-lg bg-surface p-2 text-text-muted transition-colors hover:bg-surface-hover hover:text-text-primary border border-border">
            <span className="sr-only">View notifications</span>
            <BellIcon className="h-5 w-5" aria-hidden="true" />
            <div className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-accent-green text-[10px] font-bold text-white shadow-sm">
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
            <Popover.Panel className="absolute right-0 z-50 mt-2 w-80 origin-top-right rounded-xl border border-border bg-surface p-2 shadow-dropdown backdrop-blur-xl">
              <div className="px-3 py-2 border-b border-border">
                <h3 className="text-sm font-semibold text-text-primary">Notifications</h3>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {notifications.map((notification) => (
                  <div key={notification.id} className="flex items-start gap-3 rounded-lg px-3 py-3 transition-colors hover:bg-surface-hover">
                    <div className={clsx('mt-1.5 h-2 w-2 shrink-0 rounded-full', getNotificationDot(notification.type))} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-text-primary">{notification.title}</p>
                      <p className="mt-0.5 text-xs text-text-secondary">{notification.message}</p>
                      <p className="mt-1 text-xs text-text-muted">{notification.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Popover.Panel>
          </Transition>
        </Popover>
      </div>
    </div>
  );
};

export default TopNavbar;
