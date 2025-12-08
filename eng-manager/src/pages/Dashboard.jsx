import React, { useState, useEffect } from 'react';
import { API_URL } from '../../config'; // (Ajuste os pontos conforme a pasta)
import { 
  TrendingUp, 
  AlertCircle, 
  CheckCircle2, 
  DollarSign, 
  Activity, 
  Wallet, 
  Target,
  Clock, // Adicionado para StatusCard
  TrendingDown // Adicionado para StatusCard
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer, 
  Legend, 
  LineChart, 
  Line 
} from 'recharts';
import { toast } from 'sonner';

// --- FUNÇÕES DE UTILIDADE ---
const formatCurrency = (value) => 
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0 }).format(value);

const formatPercentage = (value) => `${value.toFixed(1)}%`;


// 1. Gráfico Financeiro (Desembolso Mensal Real vs Orçado)
const FinancialChart = ({ chartData }) => { 
  if (!chartData || chartData.length === 0) {
    return (
        <div className="flex items-center justify-center h-full text-gray-400">
            Sem dados de desembolso para o gráfico.
        </div>
    );
  }
  
  return (
    <div className="h-full w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis dataKey="mesAno" axisLine={false} tickLine={false} tick={{fill: '#9ca3af', fontSize: '12px'}} />
          <YAxis 
            axisLine={false} 
            tickLine={false} 
            tick={{fill: '#9ca3af', fontSize: '12px'}} 
            tickFormatter={val => `R$ ${Intl.NumberFormat('pt-BR', { notation: 'compact', maximumFractionDigits: 1 }).format(val)}`}
          />
          <RechartsTooltip 
            formatter={(value) => [formatCurrency(value), 'Valor']} 
            labelFormatter={(label) => `Mês: ${label}`}
            contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
          />
          <Legend />
          <Bar dataKey="Orçado Mensal" name="Orçado" fill="#e2e8f0" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Desembolso Mensal" fill="#2563eb" name="Desembolso" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

// 2. Gráfico Curva S (Acumulado)
const CurvaSChart = ({ chartData }) => {
    if (!chartData || chartData.length === 0) {
        return (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 min-h-[400px] flex items-center justify-center text-gray-400">
                Sem dados para Curva S.
            </div>
        );
    }
    
    const maxVal = Math.max(...chartData.map(d => Math.max(d["Orçado Acumulado"] || 0, d["Desembolso Acumulado"] || 0)));
    const domainMax = maxVal > 0 ? maxVal * 1.1 : 10000; 
    
    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 min-h-[400px]">
            <div className="flex items-center gap-2 mb-1">
                <Target size={20} className="text-blue-600"/>
                <h3 className="text-lg font-bold text-gray-800">Curva S - Acumulado</h3>
            </div>
            <p className="text-sm text-gray-500 mb-6">Comparativo Planejado vs Realizado (Acumulado)</p>
            
            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                    <XAxis dataKey="mesAno" axisLine={false} tickLine={false} tick={{fill: '#9ca3af'}} />
                    <YAxis 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{fill: '#9ca3af', fontSize: '12px'}} 
                        domain={[0, domainMax]}
                        tickFormatter={val => `R$ ${Intl.NumberFormat('pt-BR', { notation: 'compact', maximumFractionDigits: 1 }).format(val)}`}
                    />
                    <RechartsTooltip />
                    <Legend iconType="circle" />
                    
                    <Line 
                        type="monotone" 
                        dataKey="Orçado Acumulado" 
                        name="Planejado" 
                        stroke="#94a3b8" 
                        strokeWidth={2} 
                        dot={false}
                        activeDot={{ r: 6 }} 
                    />
                    
                    <Line 
                        type="monotone" 
                        dataKey="Desembolso Acumulado" 
                        name="Realizado" 
                        stroke="#2563eb" 
                        strokeWidth={3} 
                        dot={{r: 4, fill: '#2563eb', strokeWidth: 2, stroke: '#fff'}} 
                        activeDot={{ r: 8 }} 
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};


// 3. Card Status Financeiro (ORIGINALMENTE StatusFinanceiroCard.jsx)
const StatusFinanceiroCard = ({ dados }) => {
    const total = dados?.carteiraTotal || 0;
    const pago = dados?.totalPago || 0;
    const saldo = dados?.saldoDevedor || 0;

    const percentualPago = total > 0 ? ((pago / total) * 100) : 0;
    const percentualPendente = total > 0 ? ((saldo / total) * 100) : 0;
    
    const formatCurrencyNoDec = (val) => 
        new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(val);

    return (
        <div className="bg-[#1e293b] p-6 rounded-xl shadow-sm text-white flex flex-col justify-between h-full min-h-[380px]">
            <div>
                <div className="flex items-center gap-2 mb-8">
                    <div className="p-2 bg-gray-700/50 rounded-lg">
                        <TrendingUp className="text-green-400" size={20} />
                    </div>
                    <h3 className="text-lg font-bold">Estado Financeiro</h3>
                </div>

                {/* Barra 1: Executado / Pago */}
                <div className="mb-6">
                    <div className="flex justify-between text-sm mb-2 text-gray-300">
                        <span>Realizado (Pago)</span>
                        <span className="font-bold text-white">{percentualPago.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                        <div 
                        className="bg-green-500 h-2 rounded-full shadow-[0_0_10px_rgba(34,197,94,0.5)] transition-all duration-1000" 
                        style={{ width: `${percentualPago}%` }}
                        ></div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                        {formatCurrencyNoDec(pago)} acumulado
                    </p>
                </div>

                {/* Barra 2: Saldo Pendente */}
                <div className="mb-6">
                    <div className="flex justify-between text-sm mb-2 text-gray-300">
                        <span>A Realizar (Saldo)</span>
                        <span className="font-bold text-white">{percentualPendente.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                        <div 
                        className="bg-purple-500 h-2 rounded-full shadow-[0_0_10px_rgba(168,85,247,0.5)] transition-all duration-1000" 
                        style={{ width: `${percentualPendente}%` }}
                        ></div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Falta pagar {formatCurrencyNoDec(saldo)}</p>
                </div>
            </div>

            {/* Card Inferior: Análise de Fluxo */}
            <div className={`p-4 rounded-lg mt-4 border backdrop-blur-sm ${saldo > 0 ? 'bg-gray-800/50 border-gray-700' : 'bg-green-900/20 border-green-800'}`}>
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">
                    {saldo > 0 ? "Saldo Contratual Restante" : "Status do Contrato"}
                </p>
                <p className="text-2xl font-bold text-white">
                    {formatCurrency(saldo)}
                </p>
                
                <div className="flex items-center gap-1 mt-2 text-xs">
                    {saldo > 0 ? (
                        <>
                            <AlertCircle size={12} className="text-purple-400" /> 
                            <span className="text-gray-400">Fluxo futuro previsto</span>
                        </>
                    ) : (
                        <>
                            <CheckCircle2 size={12} className="text-green-500" /> 
                            <span className="text-green-400">Contratos Quitado / Finalizado</span>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};


// 4. Card de KPI Simples
const KpiCard = ({ title, value, icon: Icon, colorClass, description }) => (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 relative overflow-hidden group hover:shadow-md transition-all">
        <div className="flex justify-between items-start">
            <div>
                <p className="text-sm font-medium text-gray-500 mb-1">{title}</p>
                <h3 className="text-2xl font-bold text-gray-800">
                    {value}
                </h3>
            </div>
            <div className={`p-2 rounded-lg text-white ${colorClass} group-hover:bg-opacity-80 transition-colors`}>
                <Icon size={20} />
            </div>
        </div>
        <div className="mt-4 text-xs text-gray-400">{description}</div>
    </div>
);


// 5. Tabela de Progresso Financeiro Simples (NOVO COMPONENTE)
const SimpleProgressTable = ({ data }) => {
    
  if (!data || data.length === 0) {
    return (
        <div className="p-6 text-center text-gray-500">
            Nenhum projeto cadastrado na base de dados.
        </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <div className="flex items-center gap-2 mb-4">
        <Activity size={20} className="text-blue-600" />
        <h3 className="text-lg font-bold text-gray-800">Progresso Financeiro Simples</h3>
      </div>
      <p className="text-sm text-gray-500 mb-6">
        Progresso baseado em Valor Pago / Valor Total do Contrato.
      </p>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Empreendimento</th>
              <th className="px-4 py-2 text-right text-xs font-semibold text-gray-500 uppercase">Valor Total (R$)</th>
              <th className="px-4 py-2 text-right text-xs font-semibold text-gray-500 uppercase">Valor Pago (R$)</th>
              <th className="px-4 py-2 text-center text-xs font-semibold text-gray-500 uppercase">% da Obra</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((item, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-4 py-2 text-sm font-medium text-gray-800">{item.empreendimento}</td>
                <td className="px-4 py-2 text-sm text-right font-mono text-gray-600">
                    {formatCurrency(item.valor_total)}
                </td>
                <td className="px-4 py-2 text-sm text-right font-bold text-green-600">
                    {formatCurrency(item.valor_pago)}
                </td>
                <td className="px-4 py-2 text-sm text-center font-bold">
                    <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs">
                        {item.percentual_progresso.toFixed(1)}%
                    </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};


// --- COMPONENTE PRINCIPAL (DASHBOARD) ---
const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState({});
  const [simpleProgressData, setSimpleProgressData] = useState([]);
  const [chartData, setChartData] = useState([]); // Restaurado para os gráficos


  // --- Função para buscar dados completos (KPIs, Progresso, Gráficos) ---
 const fetchCompletedData = async () => {
  try {
    // 1. Busca KPIs (Use crase ` e ${API_URL})
    const resKpis = await fetch(`${API_URL}/kpis/`); 
    const dadosKpis = await resKpis.json();
    setKpis(dadosKpis);

    // 2. Busca Progresso Simples
    const resProgresso = await fetch(`${API_URL}/financeiro/progresso_simples`);
    const dadosProgresso = await resProgresso.json();
    setSimpleProgressData(dadosProgresso);

    // 3. Busca Dados para Gráficos
    const resChart = await fetch(`${API_URL}/desembolso/dados`);
    if (resChart.ok) {
        const dadosChart = await resChart.json();
        setChartData(dadosChart);
    } else {
          console.warn("Falha ao carregar dados do gráfico /desembolso/dados. Carregando dados básicos.");
          setChartData([]);
      }
      
    } catch (error) {
        console.error("Erro fatal ao carregar Dashboard. Verifique logs do backend.", error);
        toast.error('Erro ao carregar dados completos do Dashboard. Verifique o servidor.');
    } finally {
        setLoading(false);
    }
  };


  // --- Efeito: Carrega dados (Roda 1 vez) ---
  useEffect(() => {
    fetchCompleteData();
  }, []);
  

  if (loading) {
    return (
      <div className="p-8 text-center text-gray-500 flex flex-col items-center h-screen bg-gray-50">
        <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
        <p>A carregar Dashboard e dados do Backend...</p>
      </div>
    );
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      
      {/* --- CABEÇALHO --- */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Resumo Geral</h1>
          <p className="text-gray-500">Visão geral e indicadores de desempenho</p>
        </div>
        <div className="flex gap-2">
            <span className="bg-white px-4 py-2 rounded-full text-sm border border-gray-200 text-gray-600 shadow-sm flex items-center gap-2">
                <Activity size={16} className="text-blue-600"/>
                Setor de Engenharia
            </span>
        </div>
      </div>
      
      {/* --- LINHA 1: KPIs FINANCEIROS --- */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <KpiCard 
          title="Carteira Total Contratada"
          value={formatCurrency(kpis.carteiraTotal)}
          icon={DollarSign}
          colorClass="bg-blue-600"
          description="Valor total dos serviços contratados."
        />
        <KpiCard 
          title="Total Pago"
          value={formatCurrency(kpis.totalPago)}
          icon={CheckCircle2}
          colorClass="bg-green-600"
          description="Soma dos valores já liquidados."
        />
        <KpiCard 
          title="Saldo a Pagar (Devedor)"
          value={formatCurrency(kpis.saldoDevedor)}
          icon={Wallet}
          colorClass="bg-purple-600"
          description="Total restante para quitação da carteira."
        />
        <KpiCard 
          title="Atraso Financeiro"
          value={formatCurrency(kpis.atrasoFinanceiro)}
          icon={AlertCircle}
          colorClass="bg-red-600"
          description="Valor de pendências com vencimento ultrapassado."
        />
      </div>
      
      {/* --- LINHA 2: GRÁFICOS E CARDS ORIGINAIS --- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8 h-[400px]">
        
        {/* Coluna Esquerda: Gráfico de Barras (Desembolso Real) */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center gap-2 mb-4">
                <DollarSign size={20} className="text-blue-600" />
                <h3 className="text-lg font-bold text-gray-800">Desembolso Mensal (Real x Orçado)</h3>
            </div>
            <div className="h-[300px] w-full">
                <FinancialChart chartData={chartData} />
            </div>
        </div>

        {/* Coluna Direita: Card Status Financeiro */}
        <div className="lg:col-span-1">
           <StatusFinanceiroCard dados={kpis} />
        </div>
      </div>

      {/* --- LINHA 3: TABELA DE PROGRESSO SIMPLES E CURVA S --- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          
          {/* Coluna Esquerda: Tabela de Progresso Simples (Nova) */}
          <SimpleProgressTable data={simpleProgressData} />
          
          {/* Coluna Direita: Curva S */}
          <CurvaSChart chartData={chartData} />
      </div>

    </div>
  );
};

export default Dashboard;