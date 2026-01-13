import React, { useState } from 'react';
import { Copy, Check, MessageSquare } from 'lucide-react';

const PromptGenerator = ({ pulseData, cpiData, unrateData, riskData }) => {
    const [copied, setCopied] = useState(false);

    const formatDataForPrompt = () => {
        const getMetric = (ticker) => pulseData.find(item => item.ticker === ticker) || {};

        // Tickers from market_data.py
        const tnx = getMetric('^TNX');     // 미국 10년물 금리
        const usdKrw = getMetric('KRW=X');  // 원/달러 환율
        const vix = getMetric('^VIX');     // VIX
        const nasdaq = getMetric('^NDX');  // 나스닥 100
        const sp500 = getMetric('^GSPC');   // S&P 500
        const nikkei = getMetric('^N225');  // 닛케이 225
        const eem = getMetric('EEM');       // 신흥국 ETF
        const kospi = getMetric('^KS11');   // 코스피 지수

        const latestCpi = cpiData?.data?.[cpiData.data.length - 1]?.value || 'N/A';
        const latestUnrate = unrateData?.data?.[unrateData.data.length - 1]?.value || 'N/A';

        // Risk Data (Gold/Silver Ratio)
        let gsRatio = 'N/A';
        let gsChange = 'N/A';
        if (riskData && riskData.length >= 2) {
            const currentRisk = riskData[riskData.length - 1];
            const prevRisk = riskData[riskData.length - 2];
            gsRatio = currentRisk.ratio.toFixed(2);
            gsChange = (currentRisk.ratio - prevRisk.ratio).toFixed(2);
        }

        const today = new Date().toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        }).replace(/\. /g, '-').replace('.', '');

        const formatChange = (val, pct) => {
            const v = typeof val === 'number' ? val.toFixed(2) : '0.00';
            const p = typeof pct === 'number' ? pct.toFixed(2) : '0.00';
            return `${v > 0 ? '+' : ''}${v} / ${p > 0 ? '+' : ''}${p}%`;
        };

        const promptText = `[역할]
당신은 월가에서 20년 경력을 가진 거시경제 애널리스트이자, 나의 친절한 투자 멘토입니다.

[상황]
오늘은 ${today}입니다. 수집된 최신 시장 데이터는 아래와 같습니다.

[데이터 리포트]
- 🇺🇸 미국 10년물 금리: ${tnx.price?.toFixed(2) || 'N/A'}% (전일대비: ${formatChange(tnx.change, tnx.change_percent)})
- 🇰🇷 원/달러 환율: ${usdKrw.price?.toLocaleString() || 'N/A'}원 (전일대비: ${formatChange(usdKrw.change, usdKrw.change_percent)})
- 😨 VIX (공포지수): ${vix.price?.toFixed(2) || 'N/A'} (등락: ${vix.change_percent?.toFixed(2) || '0.00'}%) -> [오늘예상변동: ±${((vix.price || 0) / 16).toFixed(2)}%]
- 🇺🇸 나스닥 100: ${nasdaq.price?.toLocaleString() || 'N/A'} (전일대비: ${formatChange(nasdaq.change, nasdaq.change_percent)})
- 🇺🇸 S&P 500: ${sp500.price?.toLocaleString() || 'N/A'} (전일대비: ${formatChange(sp500.change, sp500.change_percent)})
- 🇯🇵 닛케이 225: ${nikkei.price?.toLocaleString() || 'N/A'} (전일대비: ${formatChange(nikkei.change, nikkei.change_percent)})
- 🌏 신흥국 ETF (EEM): ${eem.price?.toFixed(2) || 'N/A'} (전일대비: ${formatChange(eem.change, eem.change_percent)})
- 🇰🇷 코스피 지수: ${kospi.price?.toLocaleString() || 'N/A'} (전일대비: ${formatChange(kospi.change, kospi.change_percent)})
- 미국 소비자 물가 지수(CPI, YoY): ${latestCpi}%
- 미국 실업률: ${latestUnrate}%
- 금/은 비율(Gold/Silver Ratio): ${gsRatio} (전일대비: ${gsChange > 0 ? '+' : ''}${gsChange})
  (참고: 금/은 비율이 80을 넘으면 경기 침체 우려, 급등 시 주식 시장 조정 가능성 높음)

[요청사항]
1. 시장 분위기 3줄 요약: 현재 시장이 탐욕 구간인지, 공포 구간인지, 관망세인지 명확히 진단해줘.
2. 핵심 지표 해석: 국채 금리와 환율의 움직임이 현재 주식 시장(S&P 500)에 어떤 압력을 주고 있는지 분석해줘.
3. 리스크 점검: 물가와 실업률 추세를 볼 때 '연준(Fed)'의 정책 방향이 어떻게 될지 예측해줘.
4. 투자 조언: 주식 시장 전체에 대한 투자 조언을 해줘. 주식,채권, 원자재 등등 지금 시점에서 개인 투자자는 '현금 비중'을 늘려야 할지 아니면 '매수'를 하는게 좋을지.

전문 용어를 쓰되 이해하기 쉽게 존대말로 설명해줘.`;

        return promptText;
    };

    const handleCopy = () => {
        const text = formatDataForPrompt();
        navigator.clipboard.writeText(text).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        });
    };

    return (
        <button
            onClick={handleCopy}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all border shadow-sm ${copied
                    ? 'bg-green-500 border-green-500 text-white shadow-green-500/20'
                    : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 border-gray-300 dark:border-gray-700'
                }`}
            title="AI 분석용 프롬프트 복사"
        >
            {copied ? (
                <><Check size={16} className="text-white" /> 복사 완료</>
            ) : (
                <><MessageSquare size={16} className="text-indigo-500" /> AI 분석 복사</>
            )}
        </button>
    );
};

export default PromptGenerator;
