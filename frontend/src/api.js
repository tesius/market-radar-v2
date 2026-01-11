import axios from 'axios';

// 1. Axios 인스턴스 생성 (공통 설정)
const api = axios.create({
    baseURL: 'http://127.0.0.1:8000', // 백엔드 주소 (Uvicorn)
    timeout: 5000, // 5초 안에 응답 없으면 에러 처리
    headers: {
        'Content-Type': 'application/json',
    },
});

// 2. 요청 인터셉터 (선택 사항) - 요청 나가기 전 로그 찍기
api.interceptors.request.use(
    (config) => {
        console.log(`[API 요청] ${config.method.toUpperCase()} ${config.url}`);
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default api;