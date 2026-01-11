// frontend/src/App.jsx (전체 업데이트)

import { useState, useEffect } from 'react';
import api from './api';
import MetricCard from './components/MetricCard';
import MacroChart from './components/MacroChart'; // 추가
import RiskChart from './components/RiskChart';   // 추가
import { Activity, RefreshCw } from 'lucide-react';

function App() {
  const [pulseData, setPulseData] = useState([]);
  const [cpiData, setCpiData] = useState(null);
  const [unrateData, setUnrateData] = useState(null);
  const [riskData, setRiskData] = useState([]);

  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

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
      api.get('/api/macro/risk-ratio')
    ]);

    // 결과 처리 (성공한 것만 상태에 넣기)
    const [cpiResult, unrateResult, riskResult] = results;

    if (cpiResult.status === 'fulfilled') setCpiData(cpiResult.value.data);
    if (unrateResult.status === 'fulfilled') setUnrateData(unrateResult.value.data);
    if (riskResult.status === 'fulfilled') setRiskData(riskResult.value.data);

    setLastUpdated(new Date().toLocaleTimeString());
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4 md:p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-12">

        {/* Header */}
        <header className="flex flex-col md:flex-row justify-between items-center border-b border-gray-800 pb-6">
          <div className="flex items-center gap-3 mb-4 md:mb-0">
            <div className="p-3 bg-indigo-600 rounded-lg shadow-lg shadow-indigo-500/30">
              <Activity size={28} className="text-white" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                Market Radar v2.0
              </h1>
              <p className="text-gray-400 text-sm">Real-time Global Market Monitoring</p>
            </div>
          </div>

          <button
            onClick={fetchAllData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-full text-sm font-medium transition-all border border-gray-700"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            {loading ? "Updating..." : `Updated: ${lastUpdated}`}
          </button>
        </header>

        {/* 1. Market Pulse */}
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-indigo-500 rounded-full"></span>
            Market Pulse
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
            {loading && pulseData.length === 0
              ? [...Array(8)].map((_, i) => <div key={i} className="h-40 bg-gray-800 rounded-xl animate-pulse"></div>)
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
                />
              ))
            }
          </div>
        </section>

        {/* 2. Macro Health (거시경제) */}
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-green-500 rounded-full"></span>
            Macro Health
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <MacroChart
              title="🇺🇸 US CPI (Consumer Price Index)"
              data={cpiData?.data}
              color="#10b981"
              showTarget={true} // 2% 타겟 라인 표시
            />
            <MacroChart
              title="🇺🇸 Unemployment Rate (%)"
              data={unrateData?.data}
              color="#f43f5e"
            />
          </div>
        </section>

        {/* 3. Risk Radar (위기 감지) */}
        <section>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-yellow-500 rounded-full"></span>
            Risk Radar
          </h2>
          <RiskChart data={riskData} />
        </section>

        <footer className="text-center text-gray-600 text-sm py-8">
          © 2026 Market Radar by Glen. Powered by React & FastAPI.
        </footer>
      </div>
    </div>
  );
}

export default App;