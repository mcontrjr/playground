import { defineConfig } from 'vite'
import dotenv from 'dotenv';
import { resolve } from 'path';
import react from '@vitejs/plugin-react'

dotenv.config({ path: resolve(__dirname, '../.env') });

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: process.env.VITE_API_PORT || 3000,
  },
  define: {
    'process.env': process.env,
  },
})
