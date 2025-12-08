import React from 'react';
// src/main.jsx (ou App.jsx)
import { BrowserRouter } from 'react-router-dom';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* ADICIONE O BASENAME AQUI: */}
    <BrowserRouter basename="/App_Engenharia">
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)

import { Toaster } from 'sonner';

// Componentes de Layout
import Sidebar from './components/Sidebar';

// Páginas do Sistema
import Dashboard from './pages/Dashboard';
import Obras from './pages/Obras';
import DetalhesObra from './pages/DetalhesObra'; // <--- Nova Página de Detalhes
import Financeiro from './pages/Financeiro';
import Configuracoes from './pages/Configuracoes';

function App() {
  return (
    <BrowserRouter>
      <div className="flex bg-gray-100 min-h-screen font-sans text-gray-900">
        
        {/* --- MENU LATERAL (FIXO) --- */}
        <Sidebar />
        
        {/* --- ÁREA PRINCIPAL (DINÂMICA) --- */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto h-screen relative scroll-smooth">
          
          {/* Componente Global de Notificações 
            - position="top-right": Aparece no canto superior direito
            - richColors: Usa verde para sucesso e vermelho para erro
            - closeButton: Permite fechar a notificação manualmente
          */}
          <Toaster position="top-right" richColors expand={true} closeButton />
          
          {/* Gestor de Rotas */}
          <Routes>
            {/* Rota Inicial (Dashboard) */}
            <Route path="/" element={<Dashboard />} />
            
            {/* Base de Dados de Obras (Lista) */}
            <Route path="/obras" element={<Obras />} />
            
            {/* Detalhes de uma Obra Específica (Dinâmica pelo ID) */}
            <Route path="/obras/:id" element={<DetalhesObra />} />
            
            {/* Gestão Financeira Global */}
            <Route path="/financeiro" element={<Financeiro />} />
            
            {/* Configurações do Sistema */}
            <Route path="/config" element={<Configuracoes />} />
            
            {/* Rota de "Catch-all" (Página 404) */}
            <Route path="*" element={
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <h1 className="text-4xl font-bold mb-2">404</h1>
                <p>Página não encontrada.</p>
              </div>
            } />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;