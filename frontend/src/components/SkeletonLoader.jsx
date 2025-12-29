import React from 'react';

/**
 * Premium skeleton loader components matching pink-purple theme
 * No emojis - clean, professional design
 */

const SkeletonLoader = ({ type = 'card', count = 1 }) => {
    const loaders = Array.from({ length: count }, (_, i) => i);

    if (type === 'card') {
        return (
            <>
                {loaders.map((i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                        <div className="animate-pulse space-y-4">
                            <div className="h-4 bg-gradient-to-r from-pink-200 to-purple-200 dark:from-pink-900 dark:to-purple-900 rounded w-3/4"></div>
                            <div className="space-y-2">
                                <div className="h-3 bg-gradient-to-r from-pink-100 to-purple-100 dark:from-pink-800 dark:to-purple-800 rounded w-full"></div>
                                <div className="h-3 bg-gradient-to-r from-pink-100 to-purple-100 dark:from-pink-800 dark:to-purple-800 rounded w-5/6"></div>
                            </div>
                        </div>
                    </div>
                ))}
            </>
        );
    }

    if (type === 'stats') {
        return (
            <>
                {loaders.map((i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                        <div className="animate-pulse">
                            <div className="flex items-center justify-between mb-4">
                                <div className="h-8 w-16 bg-gradient-to-r from-pink-200 to-purple-200 dark:from-pink-900 dark:to-purple-900 rounded"></div>
                                <div className="h-12 w-12 bg-gradient-to-r from-pink-200 to-purple-200 dark:from-pink-900 dark:to-purple-900 rounded-full"></div>
                            </div>
                            <div className="h-3 bg-gradient-to-r from-pink-100 to-purple-100 dark:from-pink-800 dark:to-purple-800 rounded w-24"></div>
                        </div>
                    </div>
                ))}
            </>
        );
    }

    if (type === 'table') {
        return (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="animate-pulse">
                    {/* Table header */}
                    <div className="bg-gray-50 dark:bg-gray-900 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                        <div className="flex space-x-4">
                            <div className="h-4 bg-gradient-to-r from-pink-200 to-purple-200 dark:from-pink-900 dark:to-purple-900 rounded w-1/4"></div>
                            <div className="h-4 bg-gradient-to-r from-pink-200 to-purple-200 dark:from-pink-900 dark:to-purple-900 rounded w-1/4"></div>
                            <div className="h-4 bg-gradient-to-r from-pink-200 to-purple-200 dark:from-pink-900 dark:to-purple-900 rounded w-1/4"></div>
                            <div className="h-4 bg-gradient-to-r from-pink-200 to-purple-200 dark:from-pink-900 dark:to-purple-900 rounded w-1/4"></div>
                        </div>
                    </div>
                    {/* Table rows */}
                    {loaders.map((i) => (
                        <div key={i} className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                            <div className="flex space-x-4">
                                <div className="h-3 bg-gradient-to-r from-pink-100 to-purple-100 dark:from-pink-800 dark:to-purple-800 rounded w-1/4"></div>
                                <div className="h-3 bg-gradient-to-r from-pink-100 to-purple-100 dark:from-pink-800 dark:to-purple-800 rounded w-1/4"></div>
                                <div className="h-3 bg-gradient-to-r from-pink-100 to-purple-100 dark:from-pink-800 dark:to-purple-800 rounded w-1/4"></div>
                                <div className="h-3 bg-gradient-to-r from-pink-100 to-purple-100 dark:from-pink-800 dark:to-purple-800 rounded w-1/4"></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (type === 'list') {
        return (
            <div className="space-y-3">
                {loaders.map((i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700">
                        <div className="animate-pulse flex items-center space-x-4">
                            <div className="h-10 w-10 bg-gradient-to-r from-pink-200 to-purple-200 dark:from-pink-900 dark:to-purple-900 rounded-full"></div>
                            <div className="flex-1 space-y-2">
                                <div className="h-3 bg-gradient-to-r from-pink-200 to-purple-200 dark:from-pink-900 dark:to-purple-900 rounded w-3/4"></div>
                                <div className="h-2 bg-gradient-to-r from-pink-100 to-purple-100 dark:from-pink-800 dark:to-purple-800 rounded w-1/2"></div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    if (type === 'chart') {
        return (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="animate-pulse">
                    <div className="h-4 bg-gradient-to-r from-pink-200 to-purple-200 dark:from-pink-900 dark:to-purple-900 rounded w-1/3 mb-6"></div>
                    <div className="space-y-3">
                        {[100, 80, 60, 90, 70].map((width, i) => (
                            <div key={i} className="flex items-center space-x-3">
                                <div className="h-2 bg-gradient-to-r from-pink-100 to-purple-100 dark:from-pink-800 dark:to-purple-800 rounded w-16"></div>
                                <div
                                    className="h-8 bg-gradient-to-r from-pink-300 to-purple-300 dark:from-pink-700 dark:to-purple-700 rounded"
                                    style={{ width: `${width}%` }}
                                ></div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    // Default spinner
    return (
        <div className="flex items-center justify-center py-12">
            <div className="relative">
                <div className="h-16 w-16 rounded-full border-4 border-gray-200 dark:border-gray-700"></div>
                <div className="absolute top-0 left-0 h-16 w-16 rounded-full border-4 border-transparent border-t-pink-500 border-r-purple-500 animate-spin"></div>
            </div>
        </div>
    );
};

export default SkeletonLoader;
