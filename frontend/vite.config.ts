import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const apiTarget = process.env.API_TARGET ?? 'http://127.0.0.1:8765'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/exceptions': apiTarget,
    },
  },
})