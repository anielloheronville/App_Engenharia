import React from 'react'
// MUDANÇA: Importamos apenas a função específica, sem usar "ReactDOM"
import { createRoot } from 'react-dom/client' 
import App from './App.jsx'
import './index.css'
import { BrowserRouter } from 'react-router-dom'

// MUDANÇA: Usamos createRoot direto. Se der erro agora, será outro, não aquele.
createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter basename="/App_Engenharia">
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)