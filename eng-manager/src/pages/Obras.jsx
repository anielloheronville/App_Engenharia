import React, { useState, useEffect } from 'react';
import { Plus, Search, Filter, Pencil, Trash2, Building2, Calendar, HardHat } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import ModalNovaObra from '../components/ModalNovaObra';

const Obras = () => {
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [obras, setObras] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [obraParaEditar, setObraParaEditar] = useState(null);
  // NOVO: Estado para armazenar o Empreendimento ao adicionar um sub-serviço
  const [empreendimentoPai, setEmpreendimentoPai] = useState(null); 

  // --- BUSCAR DADOS (READ) ---
  const fetchObras = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/obras/');
      if (!response.ok) throw new Error('Falha ao buscar dados');
      const data = await response.json();
      setObras(data);
    } catch (error) {
      toast.error('Erro ao conectar com servidor Python.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchObras();
  }, []);

  // --- 2. SALVAR (CREATE ou UPDATE) ---
  const handleSaveObra = async (dadosFormulario) => {
    // 1. Prepara o objeto da Obra
    const payloadObra = {
      empreendimento: dadosFormulario.empreendimento,
      fornecedor: dadosFormulario.fornecedor,
      servico: dadosFormulario.servico,
      valor_total: parseFloat(dadosFormulario.valorTotal) || 0,
      valor_pago: parseFloat(dadosFormulario.valorPago) || 0,
      status: dadosFormulario.status,
      data_inicio: dadosFormulario.dataInicio,
      data_fim: dadosFormulario.dataFim || "",
      prazo_execucao_meses: parseInt(dadosFormulario.prazoExecucaoMeses) || 1,
      orcamento_projetado: parseFloat(dadosFormulario.orcamentoProjetado) || 0,
    };

    try {
      let url = 'http://127.0.0.1:8000/obras/';
      let method = 'POST';

      if (dadosFormulario.id) {
        url = `http://127.0.0.1:8000/obras/${dadosFormulario.id}`;
        method = 'PUT';
      }

      // --- A. SALVAR/ATUALIZAR A OBRA PRINCIPAL ---
      const responseObra = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadObra),
      });
      
      if (!responseObra.ok) throw new Error('Falha ao salvar obra');

      // --- B. ATUALIZAR O ORÇAMENTO PROJETADO (RATEIO MENSAL) ---
      const valorTotalFloat = payloadObra.valor_total;
      const dataInicioStr = dadosFormulario.dataInicio;
      const prazoExecucaoMeses = payloadObra.prazo_execucao_meses;
      const empreendimentoStr = dadosFormulario.empreendimento;
      const servicoStr = dadosFormulario.servico;
      
      if (valorTotalFloat > 0 && dataInicioStr && prazoExecucaoMeses > 0) {
          
          const projUrl = `http://127.0.0.1:8000/orcamento/projetar/?valor_total=${valorTotalFloat}&data_inicio=${dataInicioStr}&empreendimento=${encodeURIComponent(empreendimentoStr)}&servico=${encodeURIComponent(servicoStr)}&num_meses_manual=${prazoExecucaoMeses}`;
          
          await fetch(projUrl, { method: 'POST' });
      }

      toast.success(dadosFormulario.id ? 'Obra atualizada com sucesso!' : 'Novo Serviço Cadastrado!');
      fetchObras(); 
      setIsModalOpen(false);
      setObraParaEditar(null);
      setEmpreendimentoPai(null); // Limpa o estado pai

    } catch (error) {
      console.error(error);
      toast.error('Erro de conexão ou ao salvar dados.');
    }
  };

  // --- 3. DELETAR (DELETE) ---
  const handleDelete = async (id) => {
    if (window.confirm('Tem a certeza que deseja excluir esta obra permanentemente?')) {
        try {
            const response = await fetch(`http://127.0.0.1:8000/obras/${id}`, {
                method: 'DELETE',
            });
            
            if (response.ok) {
                toast.success('Obra excluída.');
                fetchObras();
            } else {
                toast.error('Erro ao excluir a obra.');
            }
        } catch (error) {
            toast.error('Erro de conexão ao tentar excluir.');
        }
    }
  };

  // --- FUNÇÕES DE AUXÍLIO (UI) ---
  const handleEditClick = (obra) => {
    setObraParaEditar(obra);
    setEmpreendimentoPai(null); // Não é sub-serviço
    setIsModalOpen(true);
  };

  const handleNewClick = () => {
    setObraParaEditar(null);
    setEmpreendimentoPai(null); // Novo empreendimento principal
    setIsModalOpen(true);
  };
  
  // NOVO: Função para Adicionar Serviço no Empreendimento Existente
  const handleAddSubService = (empreendimentoNome) => {
    setObraParaEditar(null); // Garante que é uma NOVA obra
    setEmpreendimentoPai(empreendimentoNome); // Define o nome do empreendimento pai
    setIsModalOpen(true);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };

  const getStatusStyle = (status) => {
    switch (status) {
      case 'Concluído': return 'bg-green-100 text-green-700 border border-green-200';
      case 'Pendente': return 'bg-yellow-50 text-yellow-700 border border-yellow-200';
      case 'Em Andamento': return 'bg-blue-50 text-blue-700 border border-blue-200';
      case 'Atrasado': return 'bg-red-50 text-red-700 border border-red-200';
      default: return 'bg-gray-100 text-gray-700 border border-gray-200';
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      
      {/* Cabeçalho */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Base de Dados</h1>
          <p className="text-gray-500">Gerenciamento de Contratos e Serviços</p>
        </div>
        
        <button 
          onClick={handleNewClick}
          className="bg-blue-600 text-white px-5 py-2.5 rounded-lg hover:bg-blue-700 transition flex items-center gap-2 shadow-lg shadow-blue-500/30 font-medium"
        >
          <Plus size={20} />
          Nova Obra / Serviço
        </button>
      </div>

      {/* Barra de Filtros (Visual) */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-6 flex flex-col md:flex-row gap-4 items-center">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input 
            type="text" 
            placeholder="Buscar por empreendimento, fornecedor..." 
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 transition"
          />
        </div>
        <button className="flex items-center gap-2 text-gray-600 hover:text-blue-600 px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition">
          <Filter size={18} /> Filtros
        </button>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        
        {loading ? (
           <div className="p-10 text-center text-gray-500 animate-pulse flex flex-col items-center">
             <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
             Carregando dados...
           </div>
        ) : obras.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="bg-gray-50 p-6 rounded-full mb-4">
              <HardHat size={48} className="text-gray-300" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">Nenhuma obra encontrada</h3>
            <p className="text-gray-500 max-w-sm mb-6">
              O banco de dados está vazio. Cadastre o primeiro serviço.
            </p>
            <button onClick={handleNewClick} className="text-blue-600 font-medium hover:underline">
              Cadastrar agora
            </button>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Empreendimento</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Fornecedor / Serviço</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Valores</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Datas</th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Ações</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {obras.map((obra) => (
                    <tr key={obra.id} className="hover:bg-gray-50 transition duration-150 group">
                      <td className="px-6 py-4 whitespace-nowrap cursor-pointer" onClick={() => navigate(`/obras/${obra.id}`)}>
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600 border border-blue-100">
                            <Building2 size={20} />
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-bold text-gray-900 hover:text-blue-600 transition">{obra.empreendimento}</div>
                            <div className="text-xs text-gray-500">ID: #{obra.id}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900 font-medium">{obra.fornecedor}</div>
                        <div className="text-sm text-gray-500">{obra.servico}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900 font-bold">{formatCurrency(obra.valor_total)}</div>
                        <div className="text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded-full w-fit mt-1 border border-green-100">
                          Pago: {formatCurrency(obra.valor_pago)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full shadow-sm ${getStatusStyle(obra.status)}`}>
                          {obra.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex items-center gap-1.5 bg-gray-50 px-2 py-1 rounded w-fit border border-gray-100">
                          <Calendar size={14} className="text-gray-400" />
                          {obra.data_inicio}
                        </div>
                      </td>
                      
                      {/* Coluna Ações (Editar/Excluir/Adicionar) */}
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end gap-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                            {/* NOVO BOTÃO: Adicionar Serviço */}
                            <button 
                                onClick={() => handleAddSubService(obra.empreendimento)}
                                className="text-green-600 hover:bg-green-50 p-2 rounded-lg transition border border-transparent hover:border-green-100" 
                                title="Adicionar Serviço a este Empreendimento"
                            >
                                <Plus size={18} />
                            </button>
                            {/* BOTÃO EDITAR */}
                            <button 
                                onClick={() => handleEditClick(obra)}
                                className="text-blue-600 hover:bg-blue-50 p-2 rounded-lg transition border border-transparent hover:border-blue-100" 
                                title="Editar Registro"
                            >
                                <Pencil size={18} />
                            </button>
                            {/* BOTÃO EXCLUIR */}
                            <button 
                                onClick={() => handleDelete(obra.id)}
                                className="text-red-500 hover:bg-red-50 p-2 rounded-lg transition border border-transparent hover:border-red-100" 
                                title="Excluir Registro"
                            >
                                <Trash2 size={18} />
                            </button>
                        </div>
                      </td>

                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Rodapé da Tabela */}
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-between items-center text-sm text-gray-500">
              <span className="font-medium">Mostrando {obras.length} registros</span>
              <div className="flex gap-2">
                <button className="px-3 py-1.5 border border-gray-300 rounded-md bg-white hover:bg-gray-50 disabled:opacity-50 text-xs font-medium transition shadow-sm">Anterior</button>
                <button className="px-3 py-1.5 border border-gray-300 rounded-md bg-white hover:bg-gray-50 text-xs font-medium transition shadow-sm">Próximo</button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Componente Modal de Criação/Edição */}
      <ModalNovaObra 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onSave={handleSaveObra}
        obraToEdit={obraParaEditar}
        empreendimentoPai={empreendimentoPai}
      />

    </div>
  );
};

export default Obras;