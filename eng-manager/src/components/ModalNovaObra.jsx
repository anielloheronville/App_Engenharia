import React, { useState, useEffect, useCallback } from 'react';
import { X, Save, HardHat, CalendarCheck } from 'lucide-react';

const ModalNovaObra = ({ isOpen, onClose, onSave, obraToEdit, empreendimentoPai }) => {
  
  // --- LISTAS DE DROPDOWN ---
  const listaEmpreendimentos = [
    "Jardim dos Ipês", "Jardim Amazônia ET. 3", "Jardim Amazônia ET. 4", 
    "Jardim Amazônia ET. 5", "Jardim Paulista", "Jardim Mato Grosso", "Jardim Florencia", 
    "Benjamim Rossato", "Santa Felicidade", "Amazon Park", "Santa Fé", 
    "Colina Verde", "Res. Terra de Santa Cruz", "Consórcio Gran Ville", 
    "Consórcio Parque Cerrado", "Consórcio Recanto da Mata", "Jardim Vila Rica", 
    "Jardim Amazônia Et. I", "Jardim Amazônia Et. II", "Loteamento Luxemburgo", 
    "Loteamento Jardim Vila Bella", "Morada do Boque III", "Reserva Jardim", 
    "Residencial Cidade Jardim", "Residencial Florais da Mata", "Residencial Jardim Imigrantes", 
    "Residencial Vila Rica", "Residencial Vila Rica SINOP", "Outro / Não Listado"
  ];

  const tiposServico = [
    "DRENAGEM", "ÁGUA E ESGOTO", "TERRAPLANAGEM", "PAVIMENTAÇÃO", 
    "SINALIZAÇÃO", "REDE ELÉTRICA", "OUTROS"
  ];

  const [formData, setFormData] = useState({
    empreendimento: '',
    fornecedor: '',
    servico: '',
    valorTotal: '',
    valorPago: '',
    dataInicio: '',
    dataFim: '',
    prazoExecucaoMeses: 1, 
    orcamentoProjetado: '', 
    status: 'Em Andamento'
  });

  // Função de Lógica: Calcula o orçamento mensal projetado
  const calculateProjetado = useCallback((total, prazo) => {
    const valor = parseFloat(total) || 0;
    const meses = parseInt(prazo) || 1; 
    
    if (valor <= 0 || meses <= 0) {
      return '0.00'; 
    }
    
    return (valor / meses).toFixed(2);
  }, []);

  // EFEITO 1: Preenche o formulário se for Edição OU Sub-Serviço
  useEffect(() => {
    if (isOpen) {
      if (obraToEdit) {
        // MODO EDIÇÃO (PUT): Carrega valores persistidos
        setFormData({
            empreendimento: obraToEdit.empreendimento || '',
            fornecedor: obraToEdit.fornecedor || '',
            servico: obraToEdit.servico || '',
            valorTotal: obraToEdit.valor_total || '',
            valorPago: obraToEdit.valor_pago || '',
            dataInicio: obraToEdit.data_inicio || '',
            dataFim: obraToEdit.data_fim || '',
            status: obraToEdit.status || 'Em Andamento',
            prazoExecucaoMeses: obraToEdit.prazo_execucao_meses || 1, 
            orcamentoProjetado: obraToEdit.orcamento_projetado || '',
        });
      } else if (empreendimentoPai) {
        // MODO NOVO SUB-SERVIÇO (POST): Preenche o empreendimento pai
        setFormData(prev => ({
            empreendimento: empreendimentoPai,
            fornecedor: '', servico: '', valorTotal: '', valorPago: '', orcamentoProjetado: '',
            prazoExecucaoMeses: 1, 
            dataInicio: '', dataFim: '', 
            status: 'Em Andamento'
        }));
      } else {
        // MODO CRIAÇÃO (POST): Limpa tudo
        setFormData(prev => ({
            empreendimento: '', fornecedor: '', servico: '', valorTotal: '',
            valorPago: '', dataInicio: '', dataFim: '', orcamentoProjetado: '',
            prazoExecucaoMeses: 1, 
            status: 'Em Andamento'
        }));
      }
    }
  }, [isOpen, obraToEdit, empreendimentoPai]);

  // EFEITO 2: Roda o cálculo automático sempre que o Valor Total ou Prazo muda
  useEffect(() => {
    const { valorTotal, prazoExecucaoMeses, orcamentoProjetado } = formData;
    
    // Roda o cálculo apenas para novos registros ou se o valor total ou prazo for alterado
    const novoProjetado = calculateProjetado(valorTotal, prazoExecucaoMeses);
    
    if (orcamentoProjetado === '' || 
        parseFloat(orcamentoProjetado).toFixed(2) === novoProjetado ||
        orcamentoProjetado === '0.00') {
        
        setFormData(prev => ({
            ...prev,
            orcamentoProjetado: novoProjetado
        }));
    }
  }, [formData.valorTotal, formData.prazoExecucaoMeses, formData.orcamentoProjetado, calculateProjetado]);


  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'prazoExecucaoMeses' && value !== '') {
        // Garante valor mínimo de 1 para prazo
        setFormData(prev => ({ ...prev, [name]: Math.max(1, parseInt(value) || 1) }));
    } else {
        setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({ ...formData, id: obraToEdit?.id });
    onClose();
  };

  // Se for edição OU sub-serviço, o dropdown do empreendimento é desabilitado
  const isEmpreendimentoDisabled = !!obraToEdit || !!empreendimentoPai; 

  return (
    <div className="fixed inset-0 bg-black/60 flex justify-center items-center z-50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-in fade-in zoom-in duration-200">
        
        <div className="flex justify-between items-center p-6 border-b border-gray-100 bg-gray-50 rounded-t-xl">
          <div className="flex items-center gap-3">
            <div className="bg-blue-100 p-2 rounded-lg text-blue-600">
                <HardHat size={24} />
            </div>
            <div>
                <h2 className="text-xl font-bold text-gray-800">
                    {obraToEdit ? 'Editar Obra / Serviço' : (empreendimentoPai ? 'Adicionar Novo Serviço' : 'Nova Obra Principal')}
                </h2>
                <p className="text-sm text-gray-500">
                    {isEmpreendimentoDisabled ? `Empreendimento: ${formData.empreendimento}` : 'Selecione o Empreendimento Principal'}
                </p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-red-500 hover:bg-red-50 p-2 rounded-full transition">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* CAMPO EMPREENDIMENTO (DROPDOWN/TEXTO) */}
          <div className="col-span-2">
            <label className="block text-sm font-semibold text-gray-700 mb-2">Nome do Empreendimento</label>
            <div className="relative">
                <select
                  name="empreendimento"
                  className={`w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 ${isEmpreendimentoDisabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white focus:ring-blue-500'}`}
                  onChange={handleChange}
                  value={formData.empreendimento}
                  required
                  disabled={isEmpreendimentoDisabled}
                >
                  <option value="" disabled>Selecione o empreendimento...</option>
                  {listaEmpreendimentos.map((item, index) => (
                    <option key={index} value={item}>{item}</option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-gray-500">
                  {/* Ícone de seta */}
                  {!isEmpreendimentoDisabled && <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/></svg>}
                </div>
            </div>
            {isEmpreendimentoDisabled && <p className="text-xs text-gray-500 mt-1">Este campo está bloqueado porque o serviço pertence a um empreendimento existente.</p>}
          </div>

          {/* Fornecedor */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Fornecedor / Empreiteira</label>
            <input
              type="text"
              name="fornecedor"
              className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 transition"
              onChange={handleChange}
              value={formData.fornecedor}
              required
            />
          </div>

          {/* Serviço */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Atividade Principal</label>
            <div className="relative">
                <select
                name="servico"
                className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 bg-white transition"
                onChange={handleChange}
                value={formData.servico}
                required
                >
                <option value="" disabled>Selecione...</option>
                {tiposServico.map((tipo) => (
                    <option key={tipo} value={tipo}>{tipo}</option>
                ))}
                </select>
            </div>
          </div>

          {/* VALOR TOTAL */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Valor Total do Contrato (R$)</label>
            <input
              type="number"
              name="valorTotal"
              step="0.01"
              className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-green-500 transition"
              onChange={handleChange}
              value={formData.valorTotal}
              required
            />
          </div>
          
          {/* CAMPO: PRAZO DE EXECUÇÃO */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-1">
              Prazo de Execução (Meses)
              <CalendarCheck size={16} className="text-gray-500" />
            </label>
            <input
              type="number"
              name="prazoExecucaoMeses"
              min="1"
              max="60"
              className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 transition"
              onChange={handleChange}
              value={formData.prazoExecucaoMeses}
              required
            />
          </div>

          {/* CAMPO ORÇAMENTO PROJETADO MENSAL (Cálculo Automático/Editável) */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Orçamento Mensal Projetado (R$)</label>
            <input
              type="number"
              name="orcamentoProjetado"
              placeholder="Ex: 50000"
              step="0.01"
              className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-purple-500 transition"
              onChange={handleChange}
              value={formData.orcamentoProjetado}
            />
          </div>

          {/* VALOR PAGO */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Valor Pago (R$)</label>
            <input
              type="number"
              name="valorPago"
              step="0.01"
              className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-green-500 transition"
              onChange={handleChange}
              value={formData.valorPago}
            />
          </div>

          {/* Datas */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Data de Início</label>
            <input
              type="date"
              name="dataInicio"
              className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 text-gray-600 transition"
              onChange={handleChange}
              value={formData.dataInicio}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Previsão de Término</label>
            <input
              type="date"
              name="dataFim"
              className="w-full border border-gray-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-blue-500 text-gray-600 transition"
              onChange={handleChange}
              value={formData.dataFim}
            />
          </div>

          {/* Status */}
           <div className="col-span-2">
            <label className="block text-sm font-semibold text-gray-700 mb-2">Status</label>
            <div className="flex gap-4">
                {['Em Andamento', 'Pendente', 'Concluído'].map((statusOption) => (
                    <label key={statusOption} className="flex items-center gap-2 cursor-pointer border p-3 rounded-lg hover:bg-gray-50 flex-1 justify-center has-[:checked]:border-blue-500 has-[:checked]:bg-blue-50 has-[:checked]:text-blue-700 transition select-none">
                        <input 
                            type="radio" 
                            name="status" 
                            value={statusOption}
                            checked={formData.status === statusOption}
                            onChange={handleChange}
                            className="hidden"
                        />
                        <span className="text-sm font-medium">{statusOption}</span>
                    </label>
                ))}
            </div>
          </div>

          {/* Botões */}
          <div className="col-span-2 flex justify-end gap-3 mt-6 pt-6 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2.5 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 shadow-lg shadow-blue-500/30 font-medium active:scale-95 transition-transform"
            >
              <Save size={18} />
              {obraToEdit ? 'Atualizar Dados' : 'Salvar Registro'}
            </button>
          </div>

        </form>
      </div>
    </div>
  );
};

export default ModalNovaObra;