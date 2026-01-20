import React, { useState, useEffect, useMemo } from 'react';
import {
    ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, Legend, ReferenceLine
} from 'recharts';
import api from '../api';

// 🎨 커스텀 툴팁
const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white/90 dark:bg-gray-900/90 border border-gray-200 dark:border-gray-700 p-3 rounded-lg shadow-xl backdrop-blur-sm transition-colors duration-300">
                <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">{label}</p>
                {payload.map((entry, index) => (
                    <p key={index} className="text-sm font-bold flex items-center gap-2" style={{ color: entry.color }}>
                        <span>{entry.name}:</span>
                        <span>{entry.value}%</span>
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

const USRateSpreadChart = ({ isDarkMode = true }) => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState('ALL');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await api.get('/api/macro/us-rate-spread');
                setData(response.data);
            } catch (error) {
                console.error("Failed to fetch US rate spread data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // 기간 필터링 및 데이터 최적화 (Downsampling)
    const filteredData = useMemo(() => {
        if (!data || data.length === 0) return [];

        let targetData = data;

        // 1. 기간 필터링
        if (timeRange !== 'ALL') {
            const now = new Date();
            const cutoffDate = new Date();
            if (timeRange === '1Y') cutoffDate.setFullYear(now.getFullYear() - 1);
            else if (timeRange === '5Y') cutoffDate.setFullYear(now.getFullYear() - 5);

            targetData = data.filter(item => new Date(item.date) >= cutoffDate);
        }

        // 2. 데이터 다운샘플링 (렌더링 성능 최적화)
        // 포인트가 너무 많으면(예: 500개 이상) Recharts 렌더링 부하 발생
        // 그래프 형상을 유지하면서 포인트 수를 줄임
        if (targetData.length > 500) {
            const step = Math.ceil(targetData.length / 500);
            return targetData.filter((_, index) => index % step === 0);
        }

        return targetData;
    }, [data, timeRange]);

    if (loading) {
        return <div className="h-[350px] bg-gray-200 dark:bg-gray-800 rounded-xl animate-pulse border border-gray-200 dark:border-gray-700"></div>;
    }

    const gridColor = isDarkMode ? "#374151" : "#e5e7eb";
    const ranges = ['1Y', '5Y', 'ALL'];

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg transition-all duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                <div className="flex flex-col">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <span>🇺🇸 US Rate Spread (FFTR vs EFFR)</span>
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        기준금리(FFTR Upper)와 실효연방기금금리(EFFR)의 차이
                    </p>
                </div>

                {/* Range Selector */}
                <div className="flex bg-gray-100 dark:bg-gray-900 rounded-lg p-1 border border-gray-200 dark:border-gray-700">
                    {ranges.map((range) => (
                        <button
                            key={range}
                            onClick={() => setTimeRange(range)}
                            className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${timeRange === range
                                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow'
                                : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-300'
                                }`}
                        >
                            {range}
                        </button>
                    ))}
                </div>
            </div>

            {/* Chart */}
            <div className="w-full h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={filteredData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
                        <XAxis
                            dataKey="date"
                            stroke="#9ca3af"
                            tick={{ fontSize: 11 }}
                            tickFormatter={(str) => str.substring(0, 4)}
                            minTickGap={30}
                            axisLine={false}
                            tickLine={false}
                            dy={10}
                        />
                        {/* Left Y-Axis: Rates (Base/Call) */}
                        <YAxis
                            yAxisId="left"
                            domain={['auto', 'auto']}
                            stroke="#9ca3af"
                            tick={{ fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                            label={{ value: 'Rate (%)', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af', fontSize: 10 } }}
                        />
                        {/* Right Y-Axis: Spread */}
                        <YAxis
                            yAxisId="right"
                            orientation="right"
                            domain={['auto', 'auto']}
                            stroke="#9ca3af"
                            tick={{ fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                            label={{ value: 'Spread (%p)', angle: 90, position: 'insideRight', style: { fill: '#9ca3af', fontSize: 10 } }}
                        />

                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ paddingTop: '10px' }} />

                        <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="3 3" yAxisId="right" />

                        {/* Bar: Spread (Right Axis) */}
                        <Bar
                            yAxisId="right"
                            dataKey="spread"
                            name="Spread (FFTR - EFFR)"
                            fill="#10b981"
                            opacity={0.6}
                            barSize={20}
                            isAnimationActive={false} // 성능 최적화
                        />

                        {/* Line: Base Rate (FFTR) (Left Axis) */}
                        <Line
                            yAxisId="left"
                            type="stepAfter"
                            dataKey="base_rate"
                            name="FFTR (Upper)"
                            stroke="#6366f1"
                            strokeWidth={2}
                            dot={false}
                            isAnimationActive={false} // 성능 최적화
                        />

                        {/* Line: Call Rate (EFFR) (Left Axis) */}
                        <Line
                            yAxisId="left"
                            type="monotone"
                            dataKey="call_rate"
                            name="EFFR"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            dot={false}
                            strokeDasharray="5 5"
                            isAnimationActive={false} // 성능 최적화
                        />

                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default USRateSpreadChart;
