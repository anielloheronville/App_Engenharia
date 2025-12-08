import React, { useState, useEffect } from 'react';
import { X, Save, DollarSign } from 'lucide-react';
import { toast } from 'sonner';

const ModalNovoLancamento = ({ isOpen, onClose, onSave, empreendimentos }) => {
    const [formData, setFormData] = useState({
        empreendimento: '',
        tipo: 'saida', // Padrão
        categoria: 'Mão de Obra', // Padrão
        descricao: '',
        fornecedor: '',
        valor: '',
        data_vencimento: new Date().toISOString().substring(0, 10), // Data de hoje
        status: 'Pendente',
        obra_id: null, // Deixamos como null, pois será vinculado via empreendimento
    });
    
    // Listas de Categorias e Empreendimentos (Carregadas do estado)
    // Se você usa uma lista fixa de categorias, defina aqui. Se for dinâmica (como o Configuracoes.jsx), use props.
    const categoriasCusto = ['Mão de Obra', 'Material', 'Equipamento', 'Administrativo', 'Impostos', 'Logística', 'Outros'];

    useEffect(() => {
        if (!isOpen) {
            // Resetar formulário ao fechar, se necessário
            setFormData({
                empreendimento: '',
                tipo: 'saida',
                categoria: 'Mão de Obra',
                descricao: '',
                fornecedor: '',
                valor: '',
                data_vencimento: new Date().toISOString().substring(0, 10),
                status: 'Pendente',
                obra_id: null,
            });
        }
    }, [isOpen]);


    if (!isOpen) return null;

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        const payload = {
            ...formData,
            valor: parseFloat(formData.valor) || 0,
            // Garantindo que obra_id seja null se não for definido
            obra_id: formData.obra_id || null, 
            empreendimento: formData.empreendimento || 'Geral'
        };

        if (payload.valor <= 0) {
             toast.error("O valor deve ser maior que zero.");
             return;
        }

        try {
            const response = await fetch('http://127.0.0.1:8000/financeiro/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                toast.success('Lançamento financeiro registrado com sucesso!');
                onSave(); // Dispara a função de atualização (fetchFinanceiro) no componente pai
                onClose();
            } else {
                const errorData = await response.json();
                toast.error(`Erro ao salvar: ${errorData.detail || response.statusText}`);
            }
        } catch (error) {
            toast.error('Erro de conexão ao salvar lançamento.');
        }
    };

    return (
        <div className="fixed inset-0 bg-black/60 flex justify-center items-center z-50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
                <div className="flex justify-between items-center p-5 border-b border-gray-100 bg-gray-50 rounded-t-xl">
                    <div className="flex items-center gap-3">
                        <div className={`bg-blue-100 p-2 rounded-lg text-blue-600`}>
                            <DollarSign size={24} />
                        </div>
                        <h2 className="text-xl font-bold text-gray-800">Novo Lançamento Financeiro</h2>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-red-500 hover:bg-red-50 p-2 rounded-full transition">
                        <X size={24} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    
                    {/* Linha 1: Tipo de Transação */}
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">Tipo de Transação</label>
                        <div className="flex gap-4">
                            {['saida', 'entrada'].map((tipoOption) => (
                                <label key={tipoOption} className="flex items-center gap-2 cursor-pointer border p-3 rounded-lg hover:bg-gray-50 flex-1 justify-center has-[:checked]:border-blue-500 has-[:checked]:bg-blue-50 has-[:checked]:text-blue-700 transition select-none capitalize">
                                    <input 
                                        type="radio" 
                                        name="tipo" 
                                        value={tipoOption}
                                        checked={formData.tipo === tipoOption}
                                        onChange={handleChange}
                                        className="hidden"
                                        required
                                    />
                                    <span className="text-sm font-medium">{tipoOption === 'saida' ? 'Saída (Gasto)' : 'Entrada (Receita)'}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Linha 2: Valor e Vencimento */}
                    <div className="grid grid-cols-2 gap-4">
                        {/* Valor */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">Valor (R$)</label>
                            <input
                                type="number"
                                name="valor"
                                placeholder="Ex: 100000.00"
                                step="0.01"
                                className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 transition"
                                onChange={handleChange}
                                value={formData.valor}
                                required
                            />
                        </div>
                        {/* Data de Vencimento */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">Data de Vencimento</label>
                            <input
                                type="date"
                                name="data_vencimento"
                                className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 text-gray-600 transition"
                                onChange={handleChange}
                                value={formData.data_vencimento}
                                required
                            />
                        </div>
                    </div>

                    {/* Linha 3: Empreendimento e Categoria */}
                    <div className="grid grid-cols-2 gap-4">
                        {/* Empreendimento (Vínculo) */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">Vincular Projeto</label>
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
                                <option value="Geral">Geral (Não vinculado a Obra)</option>
                            </select>
                        </div>
                        {/* Categoria */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">Categoria</label>
                            <select
                                name="categoria"
                                className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                                onChange={handleChange}
                                value={formData.categoria}
                                required
                            >
                                {categoriasCusto.map((cat) => (
                                    <option key={cat} value={cat}>{cat}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Linha 4: Descrição e Fornecedor */}
                    <div className="grid grid-cols-2 gap-4">
                        {/* Descrição */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">Descrição Curta</label>
                            <input
                                type="text"
                                name="descricao"
                                placeholder="Pagamento Nota Fiscal 123"
                                className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 transition"
                                onChange={handleChange}
                                value={formData.descricao}
                                required
                            />
                        </div>
                        {/* Fornecedor */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">Fornecedor / Origem</label>
                            <input
                                type="text"
                                name="fornecedor"
                                placeholder="Nome da Empreiteira / Banco"
                                className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 transition"
                                onChange={handleChange}
                                value={formData.fornecedor}
                                required
                            />
                        </div>
                    </div>

                    {/* Botões */}
                    <div className="flex justify-end pt-2">
                        <button
                            type="submit"
                            className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 transition shadow-lg shadow-green-500/30"
                        >
                            <Save size={18} />
                            Salvar Lançamento
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
};

export default ModalNovoLancamento;