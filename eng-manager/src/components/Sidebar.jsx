import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, HardHat, DollarSign, Settings, LogOut } from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  // REMOVIDO: Item 'Clientes'
  const menuItems = [
    { name: 'Resumo Global', icon: LayoutDashboard, path: '/' },
    { name: 'Projetos', icon: HardHat, path: '/obras' },
    { name: 'Financeiro', icon: DollarSign, path: '/financeiro' },
    { name: 'Configurações', icon: Settings, path: '/config' },
  ];

  return (
    <div className="bg-[#0f172a] text-white w-64 min-h-screen flex flex-col font-sans transition-all duration-300">
      <div className="p-6 flex items-center gap-3 border-b border-gray-800">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold shadow-lg shadow-blue-500/50">EM</div>
        <span className="text-xl font-bold tracking-tight">EngManager</span>
      </div>
      
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link 
              key={item.name} 
              to={item.path} 
              className={`flex items-center p-3 rounded-lg transition-all duration-200 group relative ${
                isActive 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/50 translate-x-1' 
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white hover:translate-x-1'
              }`}
            >
              <item.icon size={20} className={`mr-3 ${isActive ? 'text-white' : 'text-gray-400 group-hover:text-white'}`} />
              <span className="font-medium">{item.name}</span>
              {isActive && <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-l-full opacity-20"></div>}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-800">
        <button className="flex items-center text-gray-400 hover:text-red-400 transition w-full p-2 hover:bg-gray-800/50 rounded-lg">
          <LogOut size={20} className="mr-3" />
          <span>Sair</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;