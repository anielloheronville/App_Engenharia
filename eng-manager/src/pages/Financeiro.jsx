import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingDown, TrendingUp, Filter, Search, Calendar, ArrowUpRight, ArrowDownRight, AlertCircle, X, Save } from 'lucide-react';
import { toast } from 'sonner';
import ModalNovoLancamento from "../components/ModalNovoLancamento";

const Financeiro = () => {
  const [lancamentos, setLancamentos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false); // NOVO: Estado do Modal
  const [empreendimentos, setEmpreendimentos] = useState([]); // NOVO: Lista para o modal

  // --- BUSCAR DADOS DO SERVIDOR ---
  const fetchFinanceiro = async () => {
    try {
      // Busca lançamentos
      const response = await fetch('http://127.0.0.1:8000/financeiro/');
      if (response.ok) {
        const data = await response.json();
        setLancamentos(data);
      } else {
        toast.error('Falha ao buscar dados financeiros.');
      }
      
      // Busca empreendimentos (para o modal)
      const resEmpreendimentos = await fetch('http://127.0.0.1:8000/empreendimentos/');
      if (resEmpreendimentos.ok) {
        const listaEmpreendimentos = await resEmpreendimentos.json();
        setEmpreendimentos(listaEmpreendimentos);
      } else {
         console.warn("Não foi possível carregar a lista de empreendimentos.");
      }

    } catch (error) {
      console.error("Erro ao carregar financeiro:", error);
      toast.error('Erro ao conectar com servidor financeiro.');
    } finally {
      setLoading(false);
    }
  };
  
  // Função que o modal chama após salvar para atualizar a lista
  const handleLancamentoSalvo = () => {
      fetchFinanceiro();
      setIsModalOpen(false);
  };


  useEffect(() => {
    fetchFinanceiro();
  }, []);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };

  // Cálculos Automáticos baseados nos dados reais
  const entradas = lancamentos.filter(l => l.tipo === 'entrada').reduce((acc, curr) => acc + curr.valor, 0);
  const saidas = lancamentos.filter(l => l.tipo === 'saida').reduce((acc, curr) => acc + curr.valor, 0);
  const saldo = entradas - saidas;

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      
      {/* Cabeçalho */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Financeiro</h1>
          <p className="text-gray-500">Fluxo de Caixa em Tempo Real</p>
        </div>
        <div className="flex gap-2">
            {/* CORREÇÃO: Adicionar o onClick para abrir o modal */}
            <button 
                onClick={() => setIsModalOpen(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 shadow flex items-center gap-2"
            >
                <DollarSign size={18} /> Novo Lançamento
            </button>
        </div>
      </div>

      {/* Cards de KPIs Dinâmicos */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* ... (Cards de KPI) ... */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-gray-500">Saldo Atual</p>
              <h3 className={`text-2xl font-bold ${saldo >= 0 ? 'text-gray-800' : 'text-red-600'}`}>
                {formatCurrency(saldo)}
              </h3>
            </div>
            <div className="p-2 bg-blue-50 rounded-lg text-blue-600"><DollarSign size={20} /></div>
          </div>
          <span className={`text-xs px-2 py-1 rounded-full ${saldo >= 0 ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50'}`}>
            {saldo >= 0 ? '+ Fluxo Positivo' : 'Atenção: Negativo'}
          </span>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-gray-500">Entradas</p>
              <h3 className="text-2xl font-bold text-green-600">{formatCurrency(entradas)}</h3>
            </div>
            <div className="p-2 bg-green-50 rounded-lg text-green-600"><TrendingUp size={20} /></div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-gray-500">Saídas</p>
              <h3 className="text-2xl font-bold text-red-600">{formatCurrency(saidas)}</h3>
            </div>
            <div className="p-2 bg-red-50 rounded-lg text-red-600"><TrendingDown size={20} /></div>
          </div>
        </div>
      </div>

      {/* Tabela de Lançamentos */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {loading ? (
            <div className="p-8 text-center text-gray-500">Carregando financeiro...</div>
        ) : lancamentos.length === 0 ? (
            <div className="p-8 text-center text-gray-500">Nenhum lançamento encontrado.</div>
        ) : (
            <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
                <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Descrição / Fornecedor</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Categoria</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Vencimento</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Valor</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
                {lancamentos.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4">
                        <div className="flex items-center">
                            <div className={`p-2 rounded-lg mr-3 ${item.tipo === 'entrada' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                                {item.tipo === 'entrada' ? <ArrowUpRight size={18} /> : <ArrowDownRight size={18} />}
                            </div>
                            <div>
                                <p className="text-sm font-medium text-gray-900">{item.descricao}</p>
                                <p className="text-xs text-gray-500">{item.fornecedor}</p>
                            </div>
                        </div>
                    </td>
                    <td className="px-6 py-4">
                    <p className="text-sm text-gray-800">{item.categoria}</p>
                    </td>
                    <td className="px-6 py-4">
                    <div className="flex items-center text-sm text-gray-600">
                        <Calendar size={14} className="mr-2" />
                        {item.data_vencimento}
                    </div>
                    </td>
                    <td className="px-6 py-4">
                    <span className={`text-sm font-bold ${item.tipo === 'entrada' ? 'text-green-600' : 'text-gray-800'}`}>
                        {item.tipo === 'entrada' ? '+' : '-'} {formatCurrency(item.valor)}
                    </span>
                    </td>
                    <td className="px-6 py-4">
                    {item.status === 'Pago' || item.status === 'Confirmado' ? (
                        <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full font-medium">Pago</span>
                    ) : item.status === 'Atrasado' ? (
                        <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full font-medium flex items-center w-fit gap-1">
                            <AlertCircle size={10} /> Atrasado
                        </span>
                    ) : (
                        <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full font-medium">Pendente</span>
                    )}
                    </td>
                </tr>
                ))}
            </tbody>
            </table>
        )}
      </div>
      
      {/* NOVO: Renderização condicional do Modal */}
      <ModalNovoLancamento
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSave={handleLancamentoSalvo}
          empreendimentos={empreendimentos}
      />

    </div>
  );
};

export default Financeiro;