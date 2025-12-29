import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    LineChart,
    Line
} from 'recharts';

/**
 * Premium chart components with pink-purple theme
 * Consistent with MedToXAi design system
 * No emojis - professional visualization
 */

// Theme colors matching your design
const COLORS = {
    primary: '#ec4899', // pink-500
    secondary: '#9333ea', // purple-600
    success: '#10b981', // green-500
    danger: '#ef4444', // red-500
    warning: '#f59e0b', // amber-500
    info: '#3b82f6', // blue-500
    gray: '#6b7280', // gray-500
};

const GRADIENT_COLORS = [
    '#ec4899', // pink-500
    '#db2777', // pink-600
    '#a855f7', // purple-500
    '#9333ea', // purple-600
    '#7c3aed', // violet-600
];

/**
 * Toxicity Bar Chart
 * Shows toxicity predictions across endpoints
 */
export const ToxicityChart = ({ data, title = "Toxicity Analysis" }) => {
    if (!data || Object.keys(data).length === 0) {
        return (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <p className="text-center text-gray-500 dark:text-gray-400">No data available</p>
            </div>
        );
    }

    const chartData = Object.entries(data).map(([endpoint, result]) => ({
        name: endpoint.replace('NR-', '').replace('SR-', ''),
        probability: (result.probability * 100).toFixed(1),
        toxic: result.prediction === 'Toxic' ? result.probability * 100 : 0,
        safe: result.prediction === 'Safe' ? result.probability * 100 : 0,
        prediction: result.prediction
    }));

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
            <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                        dataKey="name"
                        angle={-45}
                        textAnchor="end"
                        height={100}
                        tick={{ fill: '#6b7280', fontSize: 12 }}
                    />
                    <YAxis
                        label={{ value: 'Probability (%)', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                        tick={{ fill: '#6b7280' }}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#ffffff',
                            border: '1px solid #e5e7eb',
                            borderRadius: '0.5rem',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                    />
                    <Legend wrapperStyle={{ paddingTop: '20px' }} />
                    <Bar dataKey="toxic" fill={COLORS.danger} name="Toxic" radius={[8, 8, 0, 0]} />
                    <Bar dataKey="safe" fill={COLORS.success} name="Safe" radius={[8, 8, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};

/**
 * Stats Pie Chart
 * Shows distribution of toxic vs safe predictions
 */
export const StatsPieChart = ({ toxic = 0, safe = 0, title = "Prediction Distribution" }) => {
    const total = toxic + safe;

    if (total === 0) {
        return (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
                <p className="text-center text-gray-500 dark:text-gray-400">No predictions yet</p>
            </div>
        );
    }

    const data = [
        { name: 'Toxic', value: toxic, color: COLORS.danger },
        { name: 'Safe', value: safe, color: COLORS.success }
    ];

    const RADIAN = Math.PI / 180;
    const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);

        return (
            <text
                x={x}
                y={y}
                fill="white"
                textAnchor={x > cx ? 'start' : 'end'}
                dominantBaseline="central"
                className="font-semibold"
            >
                {`${(percent * 100).toFixed(0)}%`}
            </text>
        );
    };

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
            <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={renderCustomizedLabel}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#ffffff',
                            border: '1px solid #e5e7eb',
                            borderRadius: '0.5rem'
                        }}
                    />
                    <Legend />
                </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="text-center">
                    <div className="text-2xl font-bold text-red-500">{toxic}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Toxic</div>
                </div>
                <div className="text-center">
                    <div className="text-2xl font-bold text-green-500">{safe}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Safe</div>
                </div>
            </div>
        </div>
    );
};

/**
 * Endpoint Performance Chart
 * Shows accuracy across different endpoints
 */
export const EndpointPerformanceChart = ({ data, title = "Endpoint Performance" }) => {
    if (!data || data.length === 0) {
        return (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
                <p className="text-center text-gray-500 dark:text-gray-400">No data available</p>
            </div>
        );
    }

    const chartData = data.map((item, index) => ({
        ...item,
        name: item.endpoint?.replace('NR-', '').replace('SR-', '') || item.name,
        color: GRADIENT_COLORS[index % GRADIENT_COLORS.length]
    }));

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
            <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                        dataKey="name"
                        angle={-45}
                        textAnchor="end"
                        height={100}
                        tick={{ fill: '#6b7280', fontSize: 12 }}
                    />
                    <YAxis
                        label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                        tick={{ fill: '#6b7280' }}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#ffffff',
                            border: '1px solid #e5e7eb',
                            borderRadius: '0.5rem'
                        }}
                    />
                    <Bar dataKey="accuracy" radius={[8, 8, 0, 0]}>
                        {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};

/**
 * Trend Line Chart
 * Shows prediction trends over time
 */
export const TrendChart = ({ data, title = "Prediction Trends" }) => {
    if (!data || data.length === 0) {
        return (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
                <p className="text-center text-gray-500 dark:text-gray-400">No data available</p>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                        dataKey="date"
                        tick={{ fill: '#6b7280' }}
                    />
                    <YAxis
                        tick={{ fill: '#6b7280' }}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#ffffff',
                            border: '1px solid #e5e7eb',
                            borderRadius: '0.5rem'
                        }}
                    />
                    <Legend />
                    <Line
                        type="monotone"
                        dataKey="toxic"
                        stroke={COLORS.danger}
                        strokeWidth={2}
                        dot={{ fill: COLORS.danger, r: 4 }}
                        activeDot={{ r: 6 }}
                    />
                    <Line
                        type="monotone"
                        dataKey="safe"
                        stroke={COLORS.success}
                        strokeWidth={2}
                        dot={{ fill: COLORS.success, r: 4 }}
                        activeDot={{ r: 6 }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};

export default {
    ToxicityChart,
    StatsPieChart,
    EndpointPerformanceChart,
    TrendChart
};
