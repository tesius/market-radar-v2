// frontend/src/App.jsx (전체 업데이트)

import { useState, useEffect } from 'react';
import api from './api';
import MetricCard from './components/MetricCard';
import MacroChart from './components/MacroChart'; // 추가
import RiskChart from './components/RiskChart';   // 추가
import CreditSpreadChart from './components/CreditSpreadChart'; // 추가
import RateSpreadChart from './components/RateSpreadChart'; // 추가
import USRateSpreadChart from './components/USRateSpreadChart'; // 추가
import { Activity, RefreshCw } from 'lucide-react';
import PromptGenerator from './components/PromptGenerator';
import MarketGauge from './components/MarketGauge';

function App() {
  const [pulseData, setPulseData] = useState([]);
  const [cpiData, setCpiData] = useState(null);
  const [unrateData, setUnrateData] = useState(null);
  const [riskData, setRiskData] = useState([]);
  const [creditSpreadData, setCreditSpreadData] = useState([]);
  const [yieldGapData, setYieldGapData] = useState(null);

  // Theme Management (Default: Dark)
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined' && localStorage.getItem('theme')) {
      return localStorage.getItem('theme');
    }
    if (window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    return 'dark';
  });

  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const isDarkMode = theme === 'dark';

  useEffect(() => {
    fetchAllData();
  }, []);

  // frontend/src/App.jsx 안의 fetchAllData 함수 수정

  const fetchAllData = async () => {
    setLoading(true);

    // 1. 주식 데이터 (Pulse) - 이건 무조건 성공해야 함
    try {
      const pulseRes = await api.get('/api/market/pulse');
      setPulseData(pulseRes.data);
    } catch (err) {
      console.error("주식 데이터 로딩 실패:", err);
    }

    // 2. 거시경제 데이터 (Macro & Risk) - 실패해도 괜찮음 (개별 처리)
    // Promise.allSettled를 쓰면 실패한 놈만 무시하고 나머지는 다 가져옴
    const results = await Promise.allSettled([
      api.get('/api/macro/cpi'),
      api.get('/api/macro/unrate'),
      api.get('/api/macro/risk-ratio'),
      api.get('/api/market/credit-spread'),
      api.get('/api/market/yield-gap')
    ]);

    // 결과 처리 (성공한 것만 상태에 넣기)
    const [cpiResult, unrateResult, riskResult, creditResult, yieldGapResult] = results;

    if (cpiResult.status === 'fulfilled') setCpiData(cpiResult.value.data);
    if (unrateResult.status === 'fulfilled') setUnrateData(unrateResult.value.data);
    if (riskResult.status === 'fulfilled') setRiskData(riskResult.value.data);
    if (creditResult.status === 'fulfilled') setCreditSpreadData(creditResult.value.data);
    if (yieldGapResult.status === 'fulfilled') setYieldGapData(yieldGapResult.value.data);

    setLastUpdated(new Date().toLocaleTimeString());
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white p-4 md:p-8 font-sans transition-colors duration-300">
      <div className="max-w-7xl mx-auto space-y-12">

        {/* Header */}
        <header className="flex flex-col md:flex-row justify-between items-center border-b border-gray-300 dark:border-gray-800 pb-6 transition-colors duration-300">
          <div className="flex items-center gap-3 mb-4 md:mb-0">
            <div className="p-3 bg-indigo-600 rounded-lg shadow-lg shadow-indigo-500/30">
              <Activity size={28} className="text-white" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400">
                Market Radar v2.0
              </h1>
              <p className="text-gray-600 dark:text-gray-400 text-sm">실시간 글로벌 시장 모니터링</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Theme Toggle Button */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-full bg-gray-200 dark:bg-gray-800 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-700 transition-all"
              aria-label="Toggle Theme"
            >
              {isDarkMode ? '🌞' : '🌙'}
            </button>

            {/* AI Prompt Copy Button */}
            <PromptGenerator
              pulseData={pulseData}
              cpiData={cpiData}
              unrateData={unrateData}
              riskData={riskData}
              yieldGapData={yieldGapData}
              creditSpreadData={creditSpreadData}
            />

            <button
              onClick={fetchAllData}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full text-sm font-medium transition-all border border-gray-300 dark:border-gray-700 shadow-sm"
            >
              <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
              {loading ? "업데이트 중..." : `업데이트 시간: ${lastUpdated}`}
            </button>
          </div>
        </header>

        {/* 1. Market Pulse */}
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-indigo-500 rounded-full"></span>
            실시간 시장 현황
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
            {loading && pulseData.length === 0
              ? [...Array(8)].map((_, i) => <div key={i} className="h-40 bg-gray-200 dark:bg-gray-800 rounded-xl animate-pulse"></div>)
              : pulseData.map((item) => (
                <MetricCard
                  key={item.ticker}
                  ticker={item.ticker}
                  title={item.name}
                  value={item.display_value || item.price}
                  change={item.change}
                  changePercent={item.change_percent}
                  displayChange={item.display_change}
                  history={item.history}
                  isDarkMode={isDarkMode}
                />
              ))
            }
          </div>
        </section>

        {/* 2. Market Gauge (일드갭) */}
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-blue-500 rounded-full"></span>
            시장 밸류에이션 (Yield Gap)
          </h2>
          <MarketGauge data={yieldGapData} loading={loading} />
        </section>

        {/* 3. Macro Health (거시경제) */}
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-green-500 rounded-full"></span>
            거시 경제 지표
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <MacroChart
              title="🇺🇸 미국 소비자물가지수 (CPI)"
              data={cpiData?.data}
              color="#F59E0B"
              showTarget={true} // 2% 타겟 라인 표시
              isDarkMode={isDarkMode}
            />
            <MacroChart
              title="🇺🇸 고용지표 (실업률)"
              data={unrateData?.data}
              color="#6366F1"
              isDarkMode={isDarkMode}
            />
          </div>
        </section>

        {/* 3. Risk Radar (위기 감지) */}
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-yellow-500 rounded-full"></span>
            위험 신호 탐지
          </h2>
          <RiskChart data={riskData} isDarkMode={isDarkMode} />
        </section>

        {/* 4. Credit Market (크레딧 스프레드) */}
        <section>
          <CreditSpreadChart data={creditSpreadData} loading={loading} isDarkMode={isDarkMode} />
        </section>

        {/* 5. Short-term Rate (금리 스프레드) */}
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-red-500 rounded-full"></span>
            단기 자금 동향 (Call vs Base)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <RateSpreadChart isDarkMode={isDarkMode} />
            <USRateSpreadChart isDarkMode={isDarkMode} />
          </div>
        </section>

        <footer className="text-center text-gray-500 dark:text-gray-600 text-sm py-8 transition-colors duration-300">
          © 2026 Market Radar by Glen. React와 FastAPI로 제작되었습니다.
        </footer>
      </div>
    </div>
  );
}

export default App;