
import React from 'react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';
import { useState, useMemo } from 'react';

const CreditSpreadChart = ({ data, loading }) => {
    // data 형식: [{ date: '2024-01', value: 0.6 }, ...]
    const [timeRange, setTimeRange] = useState('1Y'); // 1Y, 5Y, 10Y, MAX

    // 데이터 필터링 로직
    const filteredData = useMemo(() => {
        if (!data || data.length === 0) return [];

        if (timeRange === 'MAX') return data;

        const now = new Date();
        const cutoffDate = new Date(); // 복사본 생성

        if (timeRange === '1Y') cutoffDate.setFullYear(now.getFullYear() - 1);
        else if (timeRange === '5Y') cutoffDate.setFullYear(now.getFullYear() - 5);
        else if (timeRange === '10Y') cutoffDate.setFullYear(now.getFullYear() - 10);

        return data.filter(d => new Date(d.date) >= cutoffDate);
    }, [data, timeRange]);

    if (loading || !data || data.length === 0) {
        return <div className="h-64 bg-gray-800 rounded-xl animate-pulse border border-gray-700"></div>;
    }

    // 현재 값 (마지막 데이터)
    const lastItem = data[data.length - 1];
    const currentSpread = lastItem.spread;

    // Gradient Offset Calculation
    // 1.3% 이상은 빨간색으로 칠하기 위한 오프셋 계산
    const gradientOffset = () => {
        if (!filteredData || filteredData.length === 0) return 0;

        const dataMax = Math.max(...filteredData.map((d) => d.spread));
        const dataMin = Math.min(...filteredData.map((d) => d.spread));

        if (dataMax <= 1.3) return 0;
        if (dataMin >= 1.3) return 1;

        return (dataMax - 1.3) / (dataMax - dataMin);
    };

    const off = gradientOffset();

    // Spread Change Calculation
    const prevItem = data.length > 1 ? data[data.length - 2] : lastItem;
    const change = currentSpread - prevItem.spread;

    // 상태 메시지 결정
    let statusColor = "text-green-400";
    let statusText = "안정적 (Stable)";
    let borderColor = "border-gray-700";

    if (currentSpread >= 1.3) {
        statusColor = "text-red-500";
        statusText = "위험 (Danger)";
        borderColor = "border-red-500/50";
    } else if (currentSpread >= 1.0) {
        statusColor = "text-yellow-400";
        statusText = "주의 (Caution)";
        borderColor = "border-yellow-500/50";
    }

    return (
        <div className={`bg-gray-800 p-6 rounded-xl border ${borderColor} shadow-lg transition-colors duration-300`}>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                <div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2 transition-colors duration-300">
                        Credit Spread Trend
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">회사채(AA-) - 국고채(3년) 금리 차이</p>
                </div>

                <div className="flex items-center gap-4">
                    {/* Range Buttons moved to header */}
                    <div className="flex bg-gray-700 rounded-lg p-1 border border-gray-600 transition-colors duration-300">
                        {['1Y', '5Y', '10Y', 'MAX'].map((range) => (
                            <button
                                key={range}
                                onClick={() => setTimeRange(range)}
                                className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${timeRange === range
                                    ? 'bg-gray-600 text-white shadow'
                                    : 'text-gray-400 hover:text-white'
                                    }`}
                            >
                                {range}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <div className="flex justify-between items-end mb-4">
                {/* Status Indicator (moved below header) */}
                <div className="flex-1">
                    {/* Placeholder for left-side metrics if needed later */}
                </div>

                <div className="text-right">
                    <div className={`text-2xl font-bold ${statusColor} flex items-center justify-end gap-2`}>
                        {currentSpread.toFixed(2)}%p
                        <span className="text-sm font-normal text-gray-500 flex items-center">
                            {change > 0 ? <TrendingUp size={14} className="text-red-400" /> : <TrendingDown size={14} className="text-green-400" />}
                            {Math.abs(change).toFixed(2)}%p
                        </span>
                    </div>
                    <div className={`text-xs text-gray-400 mt-1`}>
                        Threshold: 1.3% (Danger)
                    </div>
                    <div className={`text-xs font-medium ${statusColor} flex items-center justify-end gap-1 mt-1`}>
                        {currentSpread >= 1.0 && <AlertTriangle size={12} />}
                        {statusText}
                    </div>
                </div>
            </div>

            <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={filteredData}>
                        <defs>
                            <linearGradient id="splitColor" x1="0" y1="0" x2="0" y2="1">
                                <stop offset={off} stopColor="#ef4444" stopOpacity={0.3} />
                                <stop offset={off} stopColor="#6366f1" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                        <XAxis
                            dataKey="date"
                            stroke="#9ca3af"
                            fontSize={12}
                            tickFormatter={(str) => {
                                if (timeRange === '1Y') return str.substring(5); // 01-15
                                // 5Y, 10Y, MAX: '2024-01-15' -> '24.01' (YY.MM)
                                return str.substring(2, 7).replace('-', '.');
                            }}
                            minTickGap={timeRange === '1Y' ? 30 : 40}
                        />
                        <YAxis
                            domain={[0, 'auto']}
                            stroke="#9ca3af"
                            fontSize={12}
                            unit="%"
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                            itemStyle={{ color: '#818cf8' }}
                            formatter={(value) => [`${value}%p`, 'Spread']}
                            labelFormatter={(label) => `Date: ${label}`}
                        />

                        {/* 핵심: 위험 기준선 표시 */}
                        <ReferenceLine y={1.0} stroke="#fbbf24" strokeDasharray="3 3" label={{ position: 'right', value: '주의(1.0)', fill: '#fbbf24', fontSize: 10 }} />
                        <ReferenceLine y={1.3} stroke="#ef4444" strokeDasharray="3 3" label={{ position: 'right', value: '위험(1.3)', fill: '#ef4444', fontSize: 10 }} />

                        <Area
                            type="monotone"
                            dataKey="spread"
                            stroke="#6366f1"
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#splitColor)"
                            isAnimationActive={false}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            <p className="text-xs text-gray-500 mt-4 text-center">
                * 그래프가 빨간 점선(1.3%)을 돌파하면 적극적인 현금화가 필요합니다.
            </p>
        </div >
    );
};

export default CreditSpreadChart;
