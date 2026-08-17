import React from 'react';
import { Link } from 'react-router-dom';
import { BeakerIcon, CheckBadgeIcon } from '@heroicons/react/24/outline';

const Dashboard = () => (
  <div className="mx-auto max-w-3xl px-6 py-16">
    <div className="rounded-lg border border-white/5 bg-white/5 p-6 backdrop-blur">
      <h1 className="text-2xl font-bold text-white mb-4">Dashboard</h1>
      <p className="text-white/50">
        Overview panels are being consolidated into the
        <Link to="/app/pharmaguard" className="font-medium text-indigo-400 hover:text-indigo-300 transition-colors">
          PharmaGuard AI Workbench
        </Link>
        .
      </p>
      
      {/* Quick Stats - Linear style dense data tables */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-white mb-4">Quick Overview</h2>
        <div className="overflow-x-auto rounded-lg border border-white/5 bg-white/5">
          <table className="min-w-full divide-y divide-white/5">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-white/40 uppercase tracking-wider">
                  Metric
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-white/40 uppercase tracking-wider">
                  Value
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-white/40 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              <tr className="hover:bg-white/5">
                <td className="px-4 py-3 text-white/70 font-mono">
                  Molecules Analyzed Today
                </td>
                <td className="px-4 py-3 text-white/70 font-mono">
                  1,247
                </td>
                <td className="px-4 py-3">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400">
                    Active
                  </span>
                </td>
              </tr>
              <tr className="hover:bg-white/5">
                <td className="px-4 py-3 text-white/70 font-mono">
                  Average EFS Score
                </td>
                <td className="px-4 py-3 text-white/70 font-mono">
                  0.82
                </td>
                <td className="px-4 py-3">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400">
                    Excellent
                  </span>
                </td>
              </tr>
              <tr className="hover:bg-white/5">
                <td className="px-4 py-3 text-white/70 font-mono">
                  Novel Compounds Detected
                </td>
                <td className="px-4 py-3 text-white/70 font-mono">
                  23
                </td>
                <td className="px-4 py-3">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400">
                    Review
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Recent Activity */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-white mb-4">Recent Activity</h2>
        <div className="space-y-4">
          <div className="flex items-center gap-3 p-3 rounded-lg border border-white/5 bg-white/2 hover:bg-white/5 transition-colors">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-indigo-600/10 text-indigo-400">
              <BeakerIcon className="h-4 w-4" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-white">Aspirin Analysis Completed</h3>
              <p className="mt-1 text-xs text-white/50">
                Safety profile verified with EFS 0.91 - Non-toxic
              </p>
            </div>
            <span className="text-xs text-white/40">2 min ago</span>
          </div>
          
          <div className="flex items-center gap-3 p-3 rounded-lg border border-white/5 bg-white/2 hover:bg-white/5 transition-colors">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-indigo-600/10 text-indigo-400">
              <CheckBadgeIcon className="h-4 w-4" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-white">Batch Processing Finished</h3>
              <p className="mt-1 text-xs text-white/50">
                50 molecules screened - 3 flagged for review
              </p>
            </div>
            <span className="text-xs text-white/40">15 min ago</span>
          </div>
        </div>
      </div>
    </div>
  </div>
);

export default Dashboard;