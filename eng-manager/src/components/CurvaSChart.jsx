import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area } from 'recharts';

const data = [
  { mes: 'Jan', planejado: 10, realizado: 10 },
  { mes: 'Fev', planejado: 25, realizado: 22 },
  { mes: 'Mar', planejado: 45, realizado: 35 }, // Começou a atrasar
  { mes: 'Abr', planejado: 60, realizado: 48 },
  { mes: 'Mai', planejado: 80, realizado: 65 },
  { mes: 'Jun', planejado: 100, realizado: null }, // Futuro
];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-4 rounded-lg shadow-xl border border-gray-100">
        <p className="font-bold text-gray-800 mb-2">{label}</p>
        <p className="text-sm text-gray-500">
          Planejado: <span className="font-bold text-gray-800">{payload[0].value}%</span>
        </p>
        {payload[1] && (
            <p className="text-sm text-blue-600">
            Realizado: <span className="font-bold">{payload[1].value}%</span>
            </p>
        )}
        {payload[1] && payload[0].value > payload[1].value && (
            <div className="mt-2 text-xs text-red-500 font-bold bg-red-50 p-1 rounded">
                ⚠️ Desvio: {(payload[0].value - payload[1].value).toFixed(1)}%
            </div>
        )}
      </div>
    );
  }
  return null;
};

const CurvaSChart = () => {
  return (
    <div className="h-[350px] w-full bg-white p-4 rounded-xl shadow-sm border border-gray-100">
      <h3 className="text-lg font-bold text-gray-800 mb-1">Curva S - Avanço Físico</h3>
      <p className="text-sm text-gray-500 mb-6">Comparativo Planejado vs Realizado (Acumulado)</p>
      
      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
          <XAxis dataKey="mes" axisLine={false} tickLine={false} tick={{fill: '#9ca3af'}} />
          <YAxis unit="%" axisLine={false} tickLine={false} tick={{fill: '#9ca3af'}} domain={[0, 100]} />
          <Tooltip content={<CustomTooltip />} />
          <Legend iconType="circle" />
          
          {/* Linha de Planejamento (Cinza/Neutra) */}
          <Line 
            type="monotone" 
            dataKey="planejado" 
            name="Planejado" 
            stroke="#94a3b8" 
            strokeWidth={2} 
            dot={{r: 4, fill: '#94a3b8'}} 
            strokeDasharray="5 5" 
            activeDot={{ r: 6 }} 
          />
          
          {/* Linha de Realizado (Azul/Destaque) */}
          <Line 
            type="monotone" 
            dataKey="realizado" 
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

export default CurvaSChart;