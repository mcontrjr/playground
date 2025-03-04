import { defineConfig } from 'vite'
import dotenv from 'dotenv';
import { resolve } from 'path';
import react from '@vitejs/plugin-react'

dotenv.config({ path: resolve(__dirname, '../.env') });

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    watch: {
      usePolling: true,
    }
  },
  define: {
    'process.env': process.env
  }
})