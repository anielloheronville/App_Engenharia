import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "/App_Engenharia/",

  // --- MUDANÇA CRUCIAL AQUI ---
  // Isso injeta a data/hora no código, garantindo que o arquivo final
  // seja sempre diferente do anterior (mata o cache).
  
  define: {
    'process.env.BUILD_TIME': JSON.stringify(new Date().toISOString()),
  },
  // ---------------------------

  build: {
    chunkSizeWarningLimit: 1000,
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