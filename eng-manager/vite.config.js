import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 1000, // Aumenta o limite do aviso para 1000kb (opcional, para silenciar o aviso)
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Se o módulo vier de node_modules, cria um chunk separado
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },
      },
    },
  },
})