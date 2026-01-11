import React from 'react';
import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

const MetricCard = ({ title, name, ticker, value, change, changePercent, change_percent, displayChange, history }) => {
    // 1. 데이터 안전장치 & 포맷팅
    // 이름이 없으면 티커라도 보여주고, 그것도 없으면 Loading
    const displayName = title || name || ticker || "Loading...";

    // 값이 없을 경우를 대비한 방어 로직
    const safeValue = typeof value === 'number' ? value : 0;
    const safeChange = typeof change === 'number' ? change : 0;
    const safePercent = typeof changePercent === 'number' ? changePercent : (typeof change_percent === 'number' ? change_percent : 0);
    const safeHistory = history || [];

    // 2. 숫자 예쁘게 다듬기 (소수점 2자리, 콤마 찍기)
    const formattedValue = safeValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const formattedChange = Math.abs(safeChange).toFixed(2); // 절대값으로 변환 후 포맷팅
    const formattedPercent = Math.abs(safePercent).toFixed(2);

    // 3. 상태 판단 (양수/음수/보합)
    const isPositive = safeChange > 0;
    const isNegative = safeChange < 0;
    const isNeutral = safeChange === 0;

    // 4. 색상 설정
    let color = '#9CA3AF'; // 기본 회색 (Neutral)
    if (isPositive) color = '#10B981'; // Emerald (상승)
    if (isNegative) color = '#EF4444'; // Red (하락)

    // 그라데이션 ID (고유값 보장)
    const gradientId = `gradient-${(ticker || 'unknown').replace(/\W/g, '')}-${Math.random()}`;

    return (
        <div className="bg-gray-800 rounded-xl p-5 border border-gray-700 shadow-lg flex flex-col justify-between h-[180px] relative overflow-hidden group hover:border-gray-600 transition-all">

            {/* 텍스트 정보 영역 */}
            <div className="z-10 pointer-events-none">
                <h3 className="text-gray-400 text-sm font-medium mb-1 truncate">{displayName}</h3>

                {/* 메인 가격 */}
                <div className="text-2xl font-bold text-white mb-2 tracking-tight">
                    {formattedValue}
                </div>

                {/* 등락률 표시 (아이콘 + 숫자) */}
                <div className="flex items-center text-sm font-bold" style={{ color: color }}>
                    {isPositive && <ArrowUpRight size={16} className="mr-1" />}
                    {isNegative && <ArrowDownRight size={16} className="mr-1" />}
                    {isNeutral && <Minus size={16} className="mr-1" />}

                    <span>
                        {isPositive ? '+' : isNegative ? '-' : ''}{formattedChange} ({formattedPercent}%)
                    </span>
                </div>
            </div>

            {/* 배경 미니 차트 */}
            <div className="absolute bottom-0 left-0 right-0 w-full opacity-40 group-hover:opacity-70 transition-opacity" style={{ height: '100px' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={safeHistory}>
                        <defs>
                            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={color} stopOpacity={0.5} />
                                <stop offset="95%" stopColor={color} stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <YAxis domain={['auto', 'auto']} hide />
                        <Area
                            type="monotone"
                            dataKey="value"
                            stroke={color}
                            strokeWidth={2}
                            fill={`url(#${gradientId})`}
                            animationDuration={1500}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default MetricCard;