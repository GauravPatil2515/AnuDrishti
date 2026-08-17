import React from 'react';
import { Link } from 'react-router-dom';
import { BeakerIcon, CheckBadgeIcon, SignalIcon, SparklesIcon, ArrowRightIcon } from '@heroicons/react/24/outline';

const Dashboard = () => (
  <div className="container-wide py-12 animate-fade-in">
    <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
      <div>
        <h1 className="text-3xl font-display font-bold text-text-primary">Dashboard</h1>
        <p className="text-text-secondary mt-1">
          System overview and recent analysis activity.
        </p>
      </div>
      <Link 
        to="/app/pharmaguard" 
        className="btn btn-primary"
      >
        <SparklesIcon className="h-4 w-4" />
        PharmaGuard Workbench
        <ArrowRightIcon className="h-4 w-4" />
      </Link>
    </div>
    
    {/* KPI Cards */}
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
      <div className="surface p-5 hover:-translate-y-1 transition-transform hover:shadow-card-hover">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-accent-green/10 text-accent-green border border-accent-green/20">
            <BeakerIcon className="h-5 w-5" />
          </div>
          <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">Analyzed Today</h3>
        </div>
        <div className="flex items-end gap-2">
          <p className="text-3xl font-black text-text-primary font-mono">1,247</p>
          <span className="pill pill-green mb-1">+12%</span>
        </div>
      </div>

      <div className="surface p-5 hover:-translate-y-1 transition-transform hover:shadow-card-hover">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/20">
            <CheckBadgeIcon className="h-5 w-5" />
          </div>
          <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">Avg EFS Score</h3>
        </div>
        <div className="flex items-end gap-2">
          <p className="text-3xl font-black text-text-primary font-mono">0.82</p>
          <span className="pill pill-green mb-1">Excellent</span>
        </div>
      </div>

      <div className="surface p-5 hover:-translate-y-1 transition-transform hover:shadow-card-hover">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-accent-amber/10 text-accent-amber border border-accent-amber/20">
            <SignalIcon className="h-5 w-5" />
          </div>
          <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">Novel Compounds</h3>
        </div>
        <div className="flex items-end gap-2">
          <p className="text-3xl font-black text-text-primary font-mono">23</p>
          <span className="pill pill-yellow mb-1">Flagged</span>
        </div>
      </div>
      
      <div className="surface p-5 hover:-translate-y-1 transition-transform hover:shadow-card-hover">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-accent-rose/10 text-accent-rose border border-accent-rose/20">
            <CheckBadgeIcon className="h-5 w-5" />
          </div>
          <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">High Toxicity</h3>
        </div>
        <div className="flex items-end gap-2">
          <p className="text-3xl font-black text-text-primary font-mono">18</p>
          <span className="pill pill-red mb-1">Critical</span>
        </div>
      </div>
    </div>
    
    <div className="grid md:grid-cols-3 gap-6">
      {/* Recent Activity */}
      <div className="md:col-span-2">
        <h2 className="text-lg font-bold text-text-primary mb-4 font-display">Recent Activity</h2>
        <div className="surface overflow-hidden">
          <div className="divide-y divide-border">
            <div className="flex items-center gap-4 p-4 hover:bg-surface-hover transition-colors">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent-green/10 text-accent-green border border-accent-green/20">
                <BeakerIcon className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold text-text-primary">Aspirin Analysis Completed</h3>
                <p className="text-xs text-text-secondary truncate mt-0.5">
                  Safety profile verified with EFS 0.91 - Non-toxic
                </p>
              </div>
              <div className="text-right shrink-0">
                <span className="pill pill-green">Verified</span>
                <p className="text-[10px] text-text-muted mt-1">2 min ago</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 hover:bg-surface-hover transition-colors">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent-amber/10 text-accent-amber border border-accent-amber/20">
                <CheckBadgeIcon className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold text-text-primary">Batch Processing Finished</h3>
                <p className="text-xs text-text-secondary truncate mt-0.5">
                  50 molecules screened - 3 flagged for review
                </p>
              </div>
              <div className="text-right shrink-0">
                <span className="pill pill-yellow">Complete</span>
                <p className="text-[10px] text-text-muted mt-1">15 min ago</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 hover:bg-surface-hover transition-colors">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent-rose/10 text-accent-rose border border-accent-rose/20">
                <SignalIcon className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold text-text-primary">OOD Detection Alert</h3>
                <p className="text-xs text-text-secondary truncate mt-0.5">
                  High epistemic uncertainty detected for novel compound structure.
                </p>
              </div>
              <div className="text-right shrink-0">
                <span className="pill pill-red">Review</span>
                <p className="text-[10px] text-text-muted mt-1">1 hr ago</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* System Status */}
      <div>
        <h2 className="text-lg font-bold text-text-primary mb-4 font-display">System Status</h2>
        <div className="surface p-4 space-y-4">
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold text-text-secondary">GNN Models</span>
              <span className="text-xs text-accent-emerald font-bold">Online</span>
            </div>
            <div className="h-1.5 w-full bg-surface-elevated rounded-full overflow-hidden">
              <div className="h-full bg-accent-emerald w-full"></div>
            </div>
          </div>
          
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold text-text-secondary">LLM Generation (Groq)</span>
              <span className="text-xs text-accent-emerald font-bold">Online</span>
            </div>
            <div className="h-1.5 w-full bg-surface-elevated rounded-full overflow-hidden">
              <div className="h-full bg-accent-emerald w-full"></div>
            </div>
          </div>
          
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold text-text-secondary">TDC Endpoints</span>
              <span className="text-xs text-accent-amber font-bold">Offline</span>
            </div>
            <div className="h-1.5 w-full bg-surface-elevated rounded-full overflow-hidden">
              <div className="h-full bg-border w-full"></div>
            </div>
            <p className="text-[10px] text-text-muted mt-1">Established panels currently unavailable.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
);

export default Dashboard;