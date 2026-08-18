import React from 'react';
import { clsx } from 'clsx';

/**
 * Skeleton loading components for better perceived performance
 * Uses shimmer animation for modern feel
 */

// Base skeleton with shimmer animation
const SkeletonBase = ({ className, ...props }) => (
  <div
    className={clsx(
      'relative overflow-hidden rounded bg-surface-hover',
      'animate-shimmer',
      className
    )}
    {...props}
  >
    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer-sweep" />
  </div>
);

// Text line skeleton
export const SkeletonText = ({ lines = 1, className, ...props }) => (
  <div className={clsx('space-y-2', className)} {...props}>
    {Array.from({ length: lines }, (_, i) => (
      <SkeletonBase
        key={i}
        className={clsx('h-4 rounded', i === lines - 1 && 'w-3/4')}
      />
    ))}
  </div>
);

// Card skeleton
export const SkeletonCard = ({ className, ...props }) => (
  <div className={clsx('rounded-xl border border-border bg-surface p-5 space-y-4', className)} {...props}>
    <SkeletonText lines={2} className="max-w-xs" />
    <SkeletonBase className="h-32 w-full rounded-lg" />
    <SkeletonText lines={3} />
  </div>
);

// Metric card skeleton (for KPI cards)
export const SkeletonMetricCard = ({ className, ...props }) => (
  <div className={clsx('rounded-xl border border-border bg-surface p-4 space-y-2', className)} {...props}>
    <SkeletonBase className="h-4 w-1/3 rounded" />
    <SkeletonBase className="h-8 w-1/2 rounded" />
    <SkeletonBase className="h-4 w-2/3 rounded" />
  </div>
);

// Endpoint row skeleton (for endpoint table)
export const SkeletonEndpointRow = ({ className, ...props }) => (
  <div className={clsx('flex items-center gap-4 p-3 rounded-lg border border-border bg-surface/50', className)} {...props}>
    <SkeletonBase className="h-6 w-24 rounded" />
    <SkeletonBase className="flex-1 h-4 rounded" />
    <SkeletonBase className="h-6 w-16 rounded" />
    <SkeletonBase className="h-6 w-16 rounded" />
  </div>
);

// Dashboard skeleton (full layout)
export const SkeletonDashboard = ({ className, ...props }) => (
  <div className={clsx('space-y-6', className)} {...props}>
    {/* Top banner */}
    <SkeletonBase className="h-28 w-full rounded-xl" />
    {/* Metrics row */}
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <SkeletonMetricCard />
      <SkeletonMetricCard />
      <SkeletonMetricCard />
      <SkeletonMetricCard />
    </div>
    {/* Endpoints table */}
    <div className="space-y-2">
      <SkeletonText lines={1} className="max-w-xs" />
      {Array.from({ length: 8 }, (_, i) => (
        <SkeletonEndpointRow key={i} />
      ))}
    </div>
    {/* Uncertainty section */}
    <SkeletonCard />
  </div>
);

// Inline skeleton for small areas
export const SkeletonInline = ({ width = 'full', height = 16, className, ...props }) => (
  <SkeletonBase
    className={clsx(
      'rounded',
      width === 'full' ? 'w-full' : width,
      height === 16 ? 'h-4' : `h-${height}`
    )}
    {...props}
  />
);

export default {
  Base: SkeletonBase,
  Text: SkeletonText,
  Card: SkeletonCard,
  MetricCard: SkeletonMetricCard,
  EndpointRow: SkeletonEndpointRow,
  Dashboard: SkeletonDashboard,
  Inline: SkeletonInline,
};