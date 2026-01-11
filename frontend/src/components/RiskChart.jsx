import React from 'react';
import {
    ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Legend
} from 'recharts';

// 🎨 커스텀 툴팁
const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-gray-900/90 border border-gray-700 p-3 rounded-lg shadow-xl backdrop-blur-sm">
                <p className="text-gray-400 text-xs mb-1">{label}</p>
                {payload.map((entry, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm font-bold" style={{ color: entry.color }}>
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }}></span>
                        <span>{entry.name}: {entry.value.toLocaleString()}</span>
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

const RiskChart = ({ data }) => {
    if (!data || data.length === 0) {
        return (
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 col-span-1 md:col-span-2 h-[400px] flex items-center justify-center text-gray-500 animate-pulse">
                Waiting for Market Data...
            </div>
        );
    }

    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-2xl col-span-1 md:col-span-2">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        ⚠️ Risk Radar
                    </h3>
                    <p className="text-xs text-gray-400 mt-1">S&P 500 Price vs Gold/Silver Ratio Divergence</p>
                </div>
            </div>

            <div className="w-full h-[350px]">
                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                    <ComposedChart data={data} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorSp500" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#818cf8" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#818cf8" stopOpacity={0} />
                            </linearGradient>
                        </defs>

                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />

                        <XAxis
                            dataKey="date"
                            stroke="#9ca3af"
                            tick={{ fontSize: 11 }}
                            tickFormatter={(str) => str ? str.substring(5) : ""}
                            minTickGap={40}
                            axisLine={false}
                            tickLine={false}
                            dy={10}
                        />

                        <YAxis
                            yAxisId="left"
                            orientation="left"
                            stroke="#818cf8"
                            domain={['auto', 'auto']}
                            tickFormatter={(val) => val.toLocaleString()}
                            tick={{ fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                        />

                        <YAxis
                            yAxisId="right"
                            orientation="right"
                            stroke="#f59e0b"
                            domain={['auto', 'auto']}
                            tick={{ fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                        />

                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ paddingTop: '20px' }} />

                        {/* ✅ S&P 500: 배경처럼 얇게 (strokeWidth 2 -> 1.5) */}
                        <Area
                            yAxisId="left"
                            type="monotone"
                            dataKey="sp500"
                            name="S&P 500"
                            fill="url(#colorSp500)"
                            stroke="#818cf8"
                            strokeWidth={1.5}
                            connectNulls={true}
                        />

                        {/* ✅ 금/은 비율: 샤프하게 (strokeWidth 3 -> 2) */}
                        <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="ratio"
                            name="Gold/Silver Ratio"
                            stroke="#f59e0b"
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 5, strokeWidth: 0, fill: '#f59e0b' }} // 점 크기도 살짝 줄임
                            connectNulls={true}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default RiskChart;