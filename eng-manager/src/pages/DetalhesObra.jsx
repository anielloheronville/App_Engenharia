import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Building2, DollarSign, Calendar, PieChart, Wallet } from 'lucide-react';
import { toast } from 'sonner';

const DetalhesObra = () => {
  const { id } = useParams(); // Captura o ID da obra na URL (ex: /obras/1)
  const navigate = useNavigate();
  
  const [obra, setObra] = useState(null);
  const [financeiro, setFinanceiro] = useState([]);
  const [loading, setLoading] = useState(true);

  // --- BUSCAR DADOS COMPLETOS ---
  useEffect(() => {
    const fetchData = async () => {
      try {
        // 1. Buscar os dados da Obra
        const resObra = await fetch(`http://127.0.0.1:8000/obras/${id}`);
        
        if (!resObra.ok) {
          throw new Error('Obra não encontrada');
        }
        
        const dadosObra = await resObra.json();
        setObra(dadosObra);

        // 2. Buscar o financeiro DESTA obra específica
        // (Requer que o Backend tenha a rota /financeiro/obra/{id} implementada)
        const resFin = await fetch(`http://127.0.0.1:8000/financeiro/obra/${id}`);
        
        if (resFin.ok) {
            const dadosFin = await resFin.json();
            setFinanceiro(dadosFin);
        } else {
            console.warn("Rota de financeiro por obra não encontrada ou erro no servidor.");
            setFinanceiro([]); // Segue sem falhar se não houver financeiro
        }

      } catch (error) {
        console.error(error);
        toast.error('Erro ao carregar os detalhes da obra.');
        navigate('/obras'); // Volta para a lista se der erro grave
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, navigate]);

  const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  if (loading) {
    return (
        <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
            <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
            <p className="text-gray-500">A carregar detalhes do projeto...</p>
        </div>
    );
  }

  if (!obra) return null;

  // --- CÁLCULOS LOCAIS ---
  // Soma apenas as saídas (gastos)
  const totalGasto = financeiro
    .filter(f => f.tipo === 'saida')
    .reduce((acc, curr) => acc + (curr.valor || 0), 0);
  
  const saldoContrato = (obra.valor_total || 0) - totalGasto;
  
  // Evita divisão por zero
  const percentualConcluido = obra.valor_total > 0 
    ? (totalGasto / obra.valor_total) * 100 
    : 0;

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      
      {/* Botão Voltar */}
      <button 
        onClick={() => navigate('/obras')} 
        className="flex items-center text-gray-500 hover:text-blue-600 mb-6 transition group"
      >
        <ArrowLeft size={20} className="mr-2 group-hover:-translate-x-1 transition-transform" /> 
        Voltar para Projetos
      </button>

      {/* Cabeçalho da Obra */}
      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 mb-8">
        <div className="flex flex-col md:flex-row justify-between items-start gap-4">
          <div className="flex items-center gap-4">
            <div className="p-4 bg-blue-50 rounded-xl text-blue-600">
              <Building2 size={32} />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-800">{obra.empreendimento}</h1>
              <p className="text-gray-500 text-lg flex items-center gap-2">
                {obra.servico} <span className="text-gray-300">|</span> {obra.fornecedor}
              </p>
            </div>
          </div>
          <div className={`px-4 py-2 rounded-full text-sm font-bold border ${obra.status === 'Em Andamento' ? 'bg-blue-100 text-blue-700 border-blue-200' : 'bg-gray-100 text-gray-700'}`}>
            {obra.status}
          </div>
        </div>

        {/* Grid de Resumo Financeiro da Obra */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-8">
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
            <p className="text-sm text-gray-500 mb-1">Valor do Contrato</p>
            <p className="text-xl font-bold text-gray-800">{formatCurrency(obra.valor_total)}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
            <p className="text-sm text-gray-500 mb-1">Total Gasto (Real)</p>
            <p className="text-xl font-bold text-blue-600">{formatCurrency(totalGasto)}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
            <p className="text-sm text-gray-500 mb-1">Saldo em Caixa</p>
            <p className={`text-xl font-bold ${saldoContrato < 0 ? 'text-red-500' : 'text-green-600'}`}>
              {formatCurrency(saldoContrato)}
            </p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-100">
            <p className="text-sm text-gray-500 mb-1">Avanço Financeiro</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500" style={{ width: `${Math.min(percentualConcluido, 100)}%` }}></div>
              </div>
              <span className="text-sm font-bold text-blue-600">{percentualConcluido.toFixed(1)}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Extrato Financeiro da Obra */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <h3 className="font-bold text-gray-700 flex items-center gap-2">
            <Wallet size={18} /> Extrato de Custos
          </h3>
        </div>
        
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
                <tr>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Data</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Descrição</th>
                <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Categoria</th>
                <th className="px-6 py-3 text-right text-xs font-bold text-gray-500 uppercase">Valor</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
                {financeiro.length === 0 ? (
                <tr>
                    <td colSpan="4" className="px-6 py-10 text-center text-gray-400">
                    <p>Nenhum custo lançado para esta obra ainda.</p>
                    <p className="text-xs mt-1">Os lançamentos feitos no menu Financeiro aparecerão aqui se vinculados.</p>
                    </td>
                </tr>
                ) : (
                financeiro.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4 text-sm text-gray-600">{item.data_vencimento}</td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-800">{item.descricao}</td>
                    <td className="px-6 py-4 text-sm">
                        <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600 border border-gray-200">
                        {item.categoria}
                        </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-right font-mono text-red-600">
                        - {formatCurrency(item.valor)}
                    </td>
                    </tr>
                ))
                )}
            </tbody>
            </table>
        </div>
      </div>

    </div>
  );
};

export default DetalhesObra;