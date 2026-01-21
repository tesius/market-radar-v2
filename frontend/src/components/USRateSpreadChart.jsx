import React, { useState, useEffect, useMemo } from 'react';
import {
    ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, Legend, ReferenceLine, Cell
} from 'recharts';
import api from '../api';

const getSpreadStatus = (spread) => {
    if (spread >= 0.10) return { status: '안전', color: '#10b981', message: '충분한 유동성' };
    if (spread > 0.05) return { status: '양호', color: '#34d399', message: '정상 범위' };
    if (spread > 0.02) return { status: '경계', color: '#f59e0b', message: '유동성 축소 주의' }; // 5bp 이내 (2bp 초과)
    return { status: '위험', color: '#ef4444', message: '유동성 경색 신호!' }; // 2bp 이하
};

// 🎨 커스텀 툴팁
const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        // spread 값을 찾기
        const spreadItem = payload.find(p => p.dataKey === 'spread');
        const spreadVal = spreadItem ? spreadItem.value : 0;
        const status = getSpreadStatus(spreadVal);

        return (
            <div className="bg-white/95 dark:bg-gray-900/95 border border-gray-200 dark:border-gray-700 p-3 rounded-lg shadow-xl backdrop-blur-sm transition-colors duration-300 z-50">
                <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">{label}</p>
                {payload.map((entry, index) => (
                    <p key={index} className="text-sm font-bold flex items-center gap-2" style={{ color: entry.dataKey === 'spread' ? status.color : entry.color }}>
                        <span>{entry.name}:</span>
                        <span>{entry.value}%</span>
                    </p>
                ))}
                <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs font-semibold flex items-center gap-1" style={{ color: status.color }}>
                        <span>● {status.status}:</span>
                        <span>{status.message}</span>
                    </p>
                </div>
            </div>
        );
    }
    return null;
};

const USRateSpreadChart = ({ isDarkMode = true }) => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState('1Y');

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

    // 최신 상태 (마지막 데이터 기준)
    const currentStatus = useMemo(() => {
        if (!data || data.length === 0) return null;
        const last = data[data.length - 1];
        return {
            val: last.spread,
            ...getSpreadStatus(last.spread)
        };
    }, [data]);

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
                        {currentStatus && (
                            <span className={`px-2 py-0.5 text-xs rounded-full border flex items-center gap-1`}
                                style={{
                                    borderColor: currentStatus.color,
                                    color: currentStatus.color,
                                    backgroundColor: `${currentStatus.color}20` // Hex Transparency (approx 12%)
                                }}>
                                <span>{currentStatus.status}</span>
                            </span>
                        )}
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
                            domain={[-0.1, 0.5]} // 범위 고정하여 변화 잘 보이게
                            stroke="#9ca3af"
                            tick={{ fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                            label={{ value: 'Spread (%p)', angle: 90, position: 'insideRight', style: { fill: '#9ca3af', fontSize: 10 } }}
                        />

                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ paddingTop: '10px' }} />

                        {/* Reference Lines (Thresholds) */}
                        <ReferenceLine y={0.10} stroke="#10b981" strokeDasharray="3 3" yAxisId="right" label={{ value: 'Safe (10bp)', position: 'right', fill: '#10b981', fontSize: 10 }} />
                        <ReferenceLine y={0.05} stroke="#f59e0b" strokeDasharray="3 3" yAxisId="right" label={{ value: 'Warning (5bp)', position: 'right', fill: '#f59e0b', fontSize: 10 }} />
                        <ReferenceLine y={0.02} stroke="#ef4444" strokeDasharray="3 3" yAxisId="right" label={{ value: 'Danger (2bp)', position: 'right', fill: '#ef4444', fontSize: 10 }} />
                        <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="3 3" yAxisId="right" />

                        {/* Bar: Spread (Right Axis) */}
                        <Bar
                            yAxisId="right"
                            dataKey="spread"
                            name="Spread (FFTR - EFFR)"
                            barSize={20}
                            isAnimationActive={false} // 성능 최적화
                        >
                            {filteredData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={getSpreadStatus(entry.spread).color} opacity={0.7} />
                            ))}
                        </Bar>

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
