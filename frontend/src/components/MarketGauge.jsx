import React from 'react';
import { Target, TrendingUp, AlertTriangle, ShieldCheck, Zap } from 'lucide-react';

const MarketGauge = ({ data, loading }) => {
    if (loading || !data) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[1, 2].map((i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-xl h-48 animate-pulse text-gray-400 flex items-center justify-center">
                        지표 분석 중...
                    </div>
                ))}
            </div>
        );
    }

    const { us, kr } = data;

    const GaugeCard = ({ title, marketData, type }) => {
        const { current, avg, status, pe, yield: bondYield } = marketData;

        // Judgment color mapping
        const getStatusStyles = (status) => {
            if (["저평가", "적극 매수"].includes(status)) return "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border-blue-200 dark:border-blue-800";
            if (["고평가(과열)", "매도"].includes(status)) return "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300 border-red-200 dark:border-red-800";
            return "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600";
        };

        const getIcon = (status) => {
            if (["저평가", "적극 매수"].includes(status)) return <Zap size={18} className="text-blue-500" />;
            if (["고평가(과열)", "매도"].includes(status)) return <AlertTriangle size={18} className="text-red-500" />;
            return <ShieldCheck size={18} className="text-gray-500" />;
        };

        // Calculate position percentage for the bar (range: -2% to +8%)
        const min = -2;
        const max = 8;
        const getPos = (val) => Math.min(Math.max(((val - min) / (max - min)) * 100, 0), 100);

        return (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-xl transition-all duration-300 hover:shadow-2xl hover:border-indigo-500/30">
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                            {title}
                        </h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">이익수익률(1/PER) - 국채금리</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusStyles(status)} transition-colors duration-300 flex items-center gap-1.5`}>
                        {getIcon(status)}
                        {status}
                    </span>
                </div>

                {/* Gauge Bar */}
                <div className="space-y-4 mb-6">
                    <div className="relative h-3 w-full bg-gray-100 dark:bg-gray-900 rounded-full overflow-hidden border border-gray-200 dark:border-gray-700">
                        {/* 5Y Avg Marker Area */}
                        <div
                            className="absolute h-full bg-indigo-500/20 dark:bg-indigo-400/10 border-x border-indigo-500/30"
                            style={{ left: `${getPos(avg - 0.5)}%`, width: `${getPos(avg + 0.5) - getPos(avg - 0.5)}%` }}
                        ></div>

                        {/* Current Value Pointer */}
                        <div
                            className="absolute top-0 h-full w-1.5 bg-indigo-600 dark:bg-indigo-400 rounded-full shadow-[0_0_10px_rgba(79,70,229,0.5)] z-10 transition-all duration-1000 ease-out"
                            style={{ left: `${getPos(current)}%`, transform: 'translateX(-50%)' }}
                        ></div>
                    </div>

                    <div className="flex justify-between text-[10px] text-gray-400 dark:text-gray-500 font-medium px-1">
                        <span>-2.0%</span>
                        <div className="flex items-center gap-1">
                            <div className="w-2 h-2 rounded-full bg-indigo-500/40"></div>
                            <span>5년 평균 ({avg.toFixed(2)}%)</span>
                        </div>
                        <span>8.0%</span>
                    </div>
                </div>

                <div className="grid grid-cols-3 gap-4 border-t border-gray-100 dark:border-gray-700 pt-5">
                    <div className="text-center">
                        <p className="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-1">일드갭</p>
                        <p className="text-lg font-bold text-gray-900 dark:text-white">{current.toFixed(2)}%</p>
                    </div>
                    <div className="text-center border-x border-gray-100 dark:border-gray-700">
                        <p className="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-1">PER</p>
                        <p className="text-lg font-bold text-gray-900 dark:text-white">{pe}</p>
                    </div>
                    <div className="text-center">
                        <p className="text-[10px] text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-1">국채금리</p>
                        <p className="text-lg font-bold text-gray-900 dark:text-white">{bondYield}%</p>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <GaugeCard title="🇺🇸 US Market Gauge" marketData={us} type="US" />
            <GaugeCard title="🇰🇷 KR Market Gauge" marketData={kr} type="KR" />
        </div>
    );
};

export default MarketGauge;
