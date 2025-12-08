import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const data = [
  { name: 'Jan', Desembolso: 4000, Orcado: 2400 },
  { name: 'Fev', Desembolso: 3000, Orcado: 1398 },
  { name: 'Mar', Desembolso: 2000, Orcado: 9800 },
  { name: 'Abr', Desembolso: 2780, Orcado: 3908 },
  { name: 'Mai', Desembolso: 1890, Orcado: 4800 },
  { name: 'Jun', Desembolso: 2390, Orcado: 3800 },
];

const FinancialChart = () => {
  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
          <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#9ca3af'}} />
          <YAxis axisLine={false} tickLine={false} tick={{fill: '#9ca3af'}} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
          />
          <Legend />
          <Bar dataKey="Orcado" fill="#e2e8f0" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Desembolso" fill="#2563eb" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default FinancialChart;