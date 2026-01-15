import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // [중요] 레포지토리 이름 앞뒤로 슬래시(/)를 꼭 붙여야 합니다.
  base: '/market-radar-v2/',
})