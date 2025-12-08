// src/config.js
export const API_URL = import.meta.env.MODE === 'development'
  ? 'http://127.0.0.1:8000'             // Usa Localhost se estiver no seu PC
  : 'https://app-engenharia.onrender.com';    // Usa a URL do Render se estiver no site

export default API_URL;