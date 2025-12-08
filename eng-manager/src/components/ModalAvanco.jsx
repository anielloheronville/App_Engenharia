import React, { useState } from 'react';
import { X, CheckCircle, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';

const ModalAvanco = ({ isOpen, onClose, empreendimentos, onAvancoSalvo }) => {
    const [formData, setFormData] = useState({
        empreendimento: '',
        atividade: 'DRENAGEM', // Padrão
        mesAno: '',
        percentual: 0
    });
    
    // Lista de atividades (para padronização)
    const tiposServico = [
        "DRENAGEM", "ÁGUA E ESGOTO", "TERRAPLANAGEM", "PAVIMENTAÇÃO", 
        "SINALIZAÇÃO", "REDE ELÉTRICA", "OUTROS"
    ];

    if (!isOpen) return null;

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        const payload = {
            empreendimento: formData.empreendimento,
            atividade: formData.atividade,
            mes_ano: formData.mesAno,
            percentual_avanco: parseFloat(formData.percentual) || 0
        };

        if (payload.percentual_avanco < 0 || payload.percentual_avanco > 100) {
             toast.error("O percentual deve estar entre 0 e 100.");
             return;
        }

        try {
            const response = await fetch('http://127.0.0.1:8000/avanco/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                toast.success('Avanço físico registrado com sucesso!');
                onAvancoSalvo(); // Dispara atualização do Dashboard
                onClose();
            } else {
                toast.error('Erro ao salvar avanço.');
            }
        } catch (error) {
            toast.error('Erro de conexão ao salvar avanço.');
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 flex justify-center items-center z-50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
                <div className="flex justify-between items-center p-5 border-b border-gray-100 bg-gray-50 rounded-t-xl">
                    <div className="flex items-center gap-3">
                        <div className="bg-green-100 p-2 rounded-lg text-green-600">
                            <TrendingUp size={24} />
                        </div>
                        <h2 className="text-xl font-bold text-gray-800">Lançar Avanço Físico</h2>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-red-500 hover:bg-red-50 p-2 rounded-full transition">
                        <X size={24} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    
                    {/* Empreendimento */}
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Projeto</label>
                        <select
                            name="empreendimento"
                            className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                            onChange={handleChange}
                            value={formData.empreendimento}
                            required
                        >
                            <option value="" disabled>Selecione o projeto...</option>
                            {empreendimentos.map((item, index) => (
                                <option key={index} value={item}>{item}</option>
                            ))}
                        </select>
                    </div>

                    {/* Atividade */}
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Atividade</label>
                        <select
                            name="atividade"
                            className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                            onChange={handleChange}
                            value={formData.atividade}
                            required
                        >
                            {tiposServico.map((tipo) => (
                                <option key={tipo} value={tipo}>{tipo}</option>
                            ))}
                        </select>
                    </div>

                    {/* Mês de Referência */}
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Mês de Referência</label>
                        <input
                            type="month"
                            name="mesAno"
                            className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 text-gray-600"
                            onChange={handleChange}
                            value={formData.mesAno}
                            required
                        />
                    </div>

                    {/* Percentual de Avanço */}
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Percentual Concluído (%)</label>
                        <input
                            type="number"
                            name="percentual"
                            placeholder="Ex: 50.5"
                            step="0.1"
                            min="0"
                            max="100"
                            className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-green-500"
                            onChange={handleChange}
                            value={formData.percentual}
                            required
                        />
                    </div>

                    <div className="flex justify-end pt-2">
                        <button
                            type="submit"
                            className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 transition shadow-lg shadow-green-500/30"
                        >
                            <CheckCircle size={18} />
                            Salvar Avanço
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
};

export default ModalAvanco;