import React, { useState, useMemo } from 'react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, ReferenceLine, Legend
} from 'recharts';

// 🎨 커스텀 툴팁 (기존 디자인 유지 + 라이트모드 대응)
const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        const data = payload[0];
        return (
            <div className="bg-white/90 dark:bg-gray-900/90 border border-gray-200 dark:border-gray-700 p-3 rounded-lg shadow-xl backdrop-blur-sm transition-colors duration-300">
                <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">{label}</p>
                <p className="text-lg font-bold" style={{ color: data.color }}>
                    {data.name}: {data.value}%
                </p>
            </div>
        );
    }
    return null;
};

const MacroChart = ({ title, data, color, showTarget = false, isDarkMode = true }) => {
    // 1. 기간 선택 상태 (기본값: 5년)
    const [timeRange, setTimeRange] = useState('5Y');

    // 2. 기간 필터링 로직 (데이터가 변경되거나 기간을 바꿀 때만 재계산)
    const filteredData = useMemo(() => {
        if (!data || data.length === 0) return [];
        if (timeRange === 'MAX') return data;

        const now = new Date();
        const cutoffDate = new Date();

        // 기간별 날짜 계산
        if (timeRange === '1Y') cutoffDate.setFullYear(now.getFullYear() - 1);
        else if (timeRange === '5Y') cutoffDate.setFullYear(now.getFullYear() - 5);
        else if (timeRange === '10Y') cutoffDate.setFullYear(now.getFullYear() - 10);

        return data.filter(item => new Date(item.date) >= cutoffDate);
    }, [data, timeRange]);

    if (!data || data.length === 0) {
        return <div className="h-[350px] bg-gray-200 dark:bg-gray-800 rounded-xl animate-pulse border border-gray-200 dark:border-gray-700"></div>;
    }

    const gradientId = `colorGradient-${color.replace('#', '')}`;
    const ranges = ['1Y', '5Y', '10Y', 'MAX'];

    // Grid Color Logic
    const gridColor = isDarkMode ? "#374151" : "#e5e7eb";

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg transition-all duration-300">

            {/* 🟢 헤더 영역: 제목(좌측) + 기간 버튼(우측) */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2 transition-colors duration-300">
                    {title}
                </h3>

                {/* 기간 선택 버튼 그룹 */}
                <div className="flex bg-gray-100 dark:bg-gray-900 rounded-lg p-1 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
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

            {/* 차트 영역 */}
            <div className="w-full h-[300px]">
                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                    <AreaChart data={filteredData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={color} stopOpacity={0.4} />
                                <stop offset="95%" stopColor={color} stopOpacity={0} />
                            </linearGradient>
                        </defs>

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

                        <YAxis
                            stroke="#9ca3af"
                            domain={['auto', 'auto']}
                            tick={{ fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                        />

                        <Tooltip content={<CustomTooltip />} />
                        <Legend />

                        <Area
                            type="monotone"
                            dataKey="value"
                            name={title}
                            stroke={color}
                            fill={`url(#${gradientId})`}
                            strokeWidth={2}
                            activeDot={{ r: 6, strokeWidth: 0, fill: color }}
                            animationDuration={500} // 기간 변경 시 부드럽게 애니메이션
                        />

                        {showTarget && (
                            <ReferenceLine
                                y={2.0}
                                stroke="#3B82F6"
                                strokeDasharray="3 3"
                                label={{ position: 'insideTopRight', value: '목표치 2%', fill: '#3B82F6', fontSize: 12 }}
                            />
                        )}

                        {/* ❌ <Brush /> 삭제됨 */}

                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default MacroChart;