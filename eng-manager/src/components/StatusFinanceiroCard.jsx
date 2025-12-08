import React from 'react';
import { TrendingUp, CheckCircle2, AlertCircle } from 'lucide-react';

const StatusFinanceiroCard = ({ dados }) => {
  // Valores padrão para evitar erro de divisão por zero se não houver dados
  const total = dados?.carteiraTotal || 0;
  const pago = dados?.totalPago || 0;
  const saldo = dados?.saldoDevedor || 0;

  // Cálculos de Porcentagem
  const percentualPago = total > 0 ? ((pago / total) * 100) : 0;
  const percentualPendente = total > 0 ? ((saldo / total) * 100) : 0;

  const formatCurrency = (val) => 
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
            {formatCurrency(pago)} acumulado
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
           <p className="text-xs text-gray-500 mt-1">Falta pagar {formatCurrency(saldo)}</p>
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

export default StatusFinanceiroCard;