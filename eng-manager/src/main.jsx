import React from 'react'
import { createRoot } from 'react-dom/client' // <--- MUDANÇA AQUI
import App from './App.jsx'
import './index.css'
import { BrowserRouter } from 'react-router-dom'

// <--- MUDANÇA AQUI: Removemos "ReactDOM." e usamos direto "createRoot"
createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter basename="/App_Engenharia">
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)