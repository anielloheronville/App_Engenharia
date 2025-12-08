import React, { useState } from 'react';
import { User, Bell, Shield, Database, Save, Plus, X, Moon, Sun } from 'lucide-react';
import { toast } from 'sonner';

const Configuracoes = () => {
  // Estado para simular as configurações
  const [user, setUser] = useState({ name: 'Admin', role: 'Gestor de Engenharia', email: 'admin@engmanager.com' });
  const [notifications, setNotifications] = useState({ email: true, push: false, weeklyReport: true });
  const [darkMode, setDarkMode] = useState(false);
  
  // Gestão de Categorias (Isso alimentaria os Dropdowns do sistema)
  const [newCategory, setNewCategory] = useState('');
  const [categories, setCategories] = useState(['Mão de Obra', 'Material', 'Equipamento', 'Administrativo', 'Impostos']);

  const handleSave = () => {
    toast.success('Configurações atualizadas com sucesso!');
  };

  const addCategory = (e) => {
    e.preventDefault();
    if (newCategory && !categories.includes(newCategory)) {
      setCategories([...categories, newCategory]);
      setNewCategory('');
      toast.success('Categoria adicionada!');
    }
  };

  const removeCategory = (catToRemove) => {
    setCategories(categories.filter(c => c !== catToRemove));
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      
      {/* Cabeçalho */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Configurações</h1>
          <p className="text-gray-500">Gerencie as preferências e parâmetros do sistema</p>
        </div>
        <button 
          onClick={handleSave}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition flex items-center gap-2 shadow-lg shadow-blue-500/30"
        >
          <Save size={18} /> Salvar Alterações
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* COLUNA DA ESQUERDA (Perfil e Aparência) */}
        <div className="space-y-8">
          
          {/* Card Perfil */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center gap-2 mb-6 text-gray-800">
              <User className="text-blue-600" size={20} />
              <h3 className="font-bold text-lg">Perfil de Utilizador</h3>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-center mb-6">
                <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center text-3xl font-bold text-gray-400 border-4 border-white shadow-md">
                  {user.name.charAt(0)}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome Completo</label>
                <input 
                  type="text" 
                  value={user.name} 
                  onChange={e => setUser({...user, name: e.target.value})}
                  className="w-full border border-gray-200 rounded-lg p-2 outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cargo / Função</label>
                <input 
                  type="text" 
                  value={user.role} 
                  onChange={e => setUser({...user, role: e.target.value})}
                  className="w-full border border-gray-200 rounded-lg p-2 outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">E-mail</label>
                <input 
                  type="email" 
                  value={user.email} 
                  disabled
                  className="w-full border border-gray-200 rounded-lg p-2 bg-gray-50 text-gray-500 cursor-not-allowed"
                />
              </div>
            </div>
          </div>

          {/* Card Aparência */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center gap-2 mb-6 text-gray-800">
              <Moon className="text-purple-600" size={20} />
              <h3 className="font-bold text-lg">Aparência</h3>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                {darkMode ? <Moon size={18} className="text-gray-600"/> : <Sun size={18} className="text-yellow-500"/>}
                <span className="text-sm font-medium text-gray-700">Modo Escuro</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" checked={darkMode} onChange={() => setDarkMode(!darkMode)} className="sr-only peer" />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>

        </div>

        {/* COLUNA DO MEIO (Categorias e Parâmetros) */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Card Categorias */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2 text-gray-800">
                <Database className="text-green-600" size={20} />
                <h3 className="font-bold text-lg">Categorias de Custo</h3>
              </div>
              <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-full border border-green-100">
                Usado no Financeiro
              </span>
            </div>

            <p className="text-sm text-gray-500 mb-4">
              Defina as categorias que aparecerão nos formulários de lançamento. Isso padroniza os relatórios.
            </p>

            {/* Input Nova Categoria */}
            <form onSubmit={addCategory} className="flex gap-2 mb-6">
              <input 
                type="text" 
                placeholder="Nova categoria (ex: Logística)..." 
                value={newCategory}
                onChange={e => setNewCategory(e.target.value)}
                className="flex-1 border border-gray-200 rounded-lg p-2 outline-none focus:ring-2 focus:ring-green-500"
              />
              <button type="submit" className="bg-gray-800 text-white p-2 rounded-lg hover:bg-gray-900 transition">
                <Plus size={20} />
              </button>
            </form>

            {/* Lista de Tags */}
            <div className="flex flex-wrap gap-2">
              {categories.map((cat) => (
                <div key={cat} className="group flex items-center gap-2 px-3 py-1.5 bg-gray-50 text-gray-700 rounded-full border border-gray-200 hover:border-red-200 hover:bg-red-50 transition cursor-pointer">
                  <span className="text-sm font-medium">{cat}</span>
                  <button onClick={() => removeCategory(cat)} className="text-gray-400 group-hover:text-red-500">
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Card Notificações */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center gap-2 mb-6 text-gray-800">
              <Bell className="text-orange-500" size={20} />
              <h3 className="font-bold text-lg">Alertas e Notificações</h3>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between py-2 border-b border-gray-50">
                <div>
                  <p className="text-sm font-medium text-gray-800">Alertas de Atraso</p>
                  <p className="text-xs text-gray-500">Notificar quando uma obra exceder a data prevista</p>
                </div>
                <input type="checkbox" className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" defaultChecked />
              </div>

              <div className="flex items-center justify-between py-2 border-b border-gray-50">
                <div>
                  <p className="text-sm font-medium text-gray-800">Estouro de Orçamento</p>
                  <p className="text-xs text-gray-500">Avisar se o gasto ultrapassar 90% do orçado</p>
                </div>
                <input type="checkbox" className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" defaultChecked />
              </div>

              <div className="flex items-center justify-between py-2">
                <div>
                  <p className="text-sm font-medium text-gray-800">Relatório Semanal</p>
                  <p className="text-xs text-gray-500">Receber resumo por e-mail toda segunda-feira</p>
                </div>
                <input type="checkbox" className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" checked={notifications.weeklyReport} onChange={() => setNotifications({...notifications, weeklyReport: !notifications.weeklyReport})} />
              </div>
            </div>
          </div>

          {/* Card Zona de Perigo (Dados) */}
          <div className="bg-red-50 p-6 rounded-xl border border-red-100">
            <div className="flex items-center gap-2 mb-4 text-red-800">
              <Shield size={20} />
              <h3 className="font-bold text-lg">Zona de Dados</h3>
            </div>
            <p className="text-sm text-red-600 mb-4">
              Ações irreversíveis relacionadas à base de dados do sistema.
            </p>
            <div className="flex gap-4">
              <button className="bg-white border border-red-200 text-red-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-100 transition">
                Limpar Cache
              </button>
              <button className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700 transition">
                Resetar Base de Dados
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Configuracoes;