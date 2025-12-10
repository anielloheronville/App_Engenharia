import flask
from flask import Flask, request, render_template_string, jsonify
import psycopg2
import os
import datetime
import requests
import logging

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuração da Aplicação ---
app = Flask(__name__)

def to_bool_flag(value):
    """Converte valores vindos do front/n8n para booleano."""
    if value is None:
        return False
    value_str = str(value).strip().lower()
    return value_str in ('1', 'true', 'sim', 'yes')

# --- CONFIGURAÇÕES DE PRODUÇÃO (RENDER) ---
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
DATABASE_URL = os.environ.get("DATABASE_URL")

# --- LISTA DE EMPREENDIMENTOS (Dropdown) ---
OPCOES_EMPREENDIMENTOS = [
    "Jardim dos Ipês", "Jardim Amazônia ET. 3", "Jardim Amazônia ET. 4", 
    "Jardim Amazônia ET. 5", "Jardim Paulista", "Jardim Mato Grosso", 
    "Jardim Florencia", "Benjamim Rossato", "Santa Felicidade", "Amazon Park", 
    "Santa Fé", "Colina Verde", "Res. Terra de Santa Cruz", "Consórcio Gran Ville", 
    "Consórcio Parque Cerrado", "Consórcio Recanto da Mata", "Jardim Vila Rica", 
    "Jardim Amazônia Et. I", "Jardim Amazônia Et. II", "Loteamento Luxemburgo", 
    "Loteamento Jardim Vila Bella", "Morada do Boque III", "Reserva Jardim", 
    "Residencial Cidade Jardim", "Residencial Florais da Mata", 
    "Residencial Jardim Imigrantes", "Residencial Vila Rica", 
    "Residencial Vila Rica SINOP", "Outro / Não Listado"
]

# --- LISTA DE CORRETORES ---
OPCOES_CORRETORES = [
    "4083 - NEURA.T.PAVAN SINIGAGLIA", "2796 - PEDRO LAERTE RABECINI", 
    "57 - Santos e Padilha Ltda - ME", "1376 - VALMIR MARIO TOMASI", 
    "1768 - SEGALA EMPREENDIMENTOS", "2436 - PAULO EDUARDO GONCALVES DIAS", 
    "2447 - GLAUBER BENEDITO FIGUEIREDO DE PINHO", "4476 - Priscila Canhet da Silveira", 
    "1531 - Walmir de Oliveira Queiroz", "4704 - MAYCON JEAN CAMPOS", 
    "4084 - JAIMIR COMPAGNONI", "4096 - THAYANE APARECIDA BORGES", 
    "4160 - SIMONE VALQUIRIA BELLO OLIVEIRA", "4587 - GABRIEL GALVÃO LOURENÇO", 
    "4802 - CESAR AUGUSTO PORTELA DA FONSECA JUNIOR", "4868 - LENE ENGLER DA SILVA", 
    "4087 - JOHNNY MIRANDA OJEDA", "4531 - MG EMPREENDIMENTOS LTDA", 
    "4826 - JEVIELI BELLO OLIVEIRA", "4825 - EVA VITORIA GALVAO LOURENCO", 
    "54 - Ronaldo Padilha dos Santos", "1137 - Moacir Blemer Olivoto", 
    "4872 - WQ CORRETORES LTDA", "720 - Luciane Bocchi ME", 
    "5154 - FELIPE JOSE MOREIRA ALMEIDA", "3063 - SILVANA SEGALA", 
    "2377 - Paulo Eduardo Gonçalves Dias", "Outro / Não Listado"
]

# --- BANCO DE DADOS (COM TODOS AS COLUNAS DO ANEXO) ---
def init_db():
    if not DATABASE_URL:
        logger.warning("⚠️ AVISO: DATABASE_URL não encontrada. O app não salvará dados.")
        return

    create_table_query = '''
    CREATE TABLE IF NOT EXISTS atendimentos (
        id SERIAL PRIMARY KEY,
        data_hora TIMESTAMPTZ NOT NULL,
        nome TEXT NOT NULL,
        telefone TEXT NOT NULL,
        rede_social TEXT,
        abordagem_inicial TEXT,
        esteve_plantao BOOLEAN,
        foi_atendido BOOLEAN,
        nome_corretor TEXT,
        autoriza_transmissao BOOLEAN,
        foto_cliente TEXT,
        assinatura TEXT,
        cidade TEXT,
        loteamento TEXT
    )
    '''
    # Migrações para garantir que o banco tenha espaço para TUDO
    migrations = [
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS comprou_1o_lote TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nivel_interesse TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS nota_atendimento INTEGER DEFAULT 0;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS quadra TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS lote TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS metragem TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS valor_m2 TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS valor_total TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS entrada_valor TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS num_parcelas TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS valor_parcelas TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS vencimento_parcelas TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS rg TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS orgao_emissor TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS estado_civil TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS cpf TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS filhos TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS endereco TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS email TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS tipo_residencia TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS valor_aluguel TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS possui_financiamento TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS empresa_trabalho TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS profissao TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS telefone_empresa TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS renda_mensal TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS conjuge_nome TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS conjuge_rg TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS conjuge_cpf TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS conjuge_empresa TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS conjuge_profissao TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS conjuge_renda TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS ref1_nome TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS ref1_tel TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS ref2_nome TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS ref2_tel TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS ref3_nome TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS ref3_tel TEXT;",
        "ALTER TABLE atendimentos ADD COLUMN IF NOT EXISTS fonte_midia TEXT;"
    ]

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        for migration in migrations:
            try:
                cursor.execute(migration)
            except Exception:
                pass 
        cursor.close()
        conn.close()
        logger.info("✅ Banco de dados atualizado.")
    except Exception as e:
        logger.error(f"❌ Erro crítico DB: {e}")

init_db()

# --- TEMPLATE HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Araguaia Imóveis - Ficha Digital</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    
    <style>
        :root {
            --cor-bg-fundo: #263318; 
            --cor-bg-form: #324221;
            --cor-acento: #8cc63f; 
            --cor-texto-claro: #ffffff;
            --cor-texto-cinza: #d1d5db;
            --cor-borda: #4a5e35;
        }

        body {
            background-color: var(--cor-bg-fundo);
            color: var(--cor-texto-claro);
            font-family: 'Montserrat', sans-serif;
        }

        .form-container {
            background-color: var(--cor-bg-form);
            border-radius: 0.75rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            border: 1px solid var(--cor-borda);
            transition: all 0.3s ease;
        }

        .logo-text { font-weight: 800; letter-spacing: -0.05em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .logo-line { height: 4px; background-color: var(--cor-acento); width: 100px; margin: 0.5rem auto; border-radius: 2px; }

        .form-input, .form-textarea, .form-select {
            background-color: #263318;
            border: 1px solid var(--cor-borda);
            color: var(--cor-texto-claro);
            border-radius: 0.5rem;
            padding: 0.75rem;
            width: 100%;
            transition: all 0.3s;
        }
        
        .form-input:focus, .form-textarea:focus, .form-select:focus {
            border-color: var(--cor-acento);
            outline: none;
            box-shadow: 0 0 0 2px rgba(140, 198, 63, 0.2);
        }

        .section-separator {
            border-top: 1px solid var(--cor-borda);
            margin-top: 2rem;
            padding-top: 2rem;
            margin-bottom: 1rem;
        }

        .section-title {
            color: var(--cor-acento);
            font-weight: 800;
            text-transform: uppercase;
            font-size: 1rem;
            letter-spacing: 0.05em;
            margin-bottom: 1.5rem;
        }

        .btn-salvar {
            background-color: var(--cor-acento);
            color: #1a2610;
            font-weight: 800;
            padding: 0.85rem 2rem;
            border-radius: 0.5rem;
            transition: all 0.2s;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .btn-salvar:hover { background-color: #7ab82e; transform: translateY(-1px); }
        .btn-salvar:disabled { opacity: 0.6; cursor: not-allowed; }

        .btn-pdf {
            background-color: #ffffff;
            color: #263318;
            font-weight: 700;
            padding: 0.85rem 1.5rem;
            border-radius: 0.5rem;
            transition: all 0.2s;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-right: 10px;
        }

        .signature-canvas, .photo-canvas, .video-preview {
            border: 2px dashed var(--cor-borda);
            border-radius: 0.5rem;
            background-color: rgba(0,0,0,0.2);
        }

        /* Animação para aparecer a ficha extra */
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); max-height: 0; }
            to { opacity: 1; transform: translateY(0); max-height: 2000px; }
        }
        .animate-expand {
            animation: slideDown 0.6s ease-out forwards;
            overflow: hidden;
        }
        
        .hidden { display: none; }
        
        /* PDF MODE */
        .pdf-mode {
            background-color: #ffffff !important;
            color: #000000 !important;
            padding: 20px !important;
        }
        .pdf-mode .form-input, .pdf-mode .form-textarea, .pdf-mode .form-select {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #ccc !important;
        }
        .pdf-mode label, .pdf-mode .section-title {
            color: #000000 !important;
        }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    <header class="w-full p-6 text-center">
        <h1 class="text-4xl md:text-5xl logo-text text-white">Araguaia</h1>
        <h2 class="text-xl md:text-2xl font-semibold text-white mt-1">Imóveis</h2>
        <div class="logo-line"></div>
        <p class="text-xs md:text-sm italic mt-2 tracking-wider" style="color: var(--cor-texto-cinza);">
            INVISTA EM SEUS SONHOS
        </p>
    </header>

    <main class="flex-grow flex items-center justify-center p-4">
        <div id="fichaContainer" class="form-container w-full max-w-4xl mx-auto p-6 md:p-10">
            <div id="pdfHeader" class="hidden text-center mb-4">
                <h1 class="text-3xl font-bold text-[#263318]">FICHA DE CADASTRO</h1>
                <hr class="border-[#8cc63f] my-2">
            </div>

            <form id="preAtendimentoForm">
                <!-- PARTE 1: DADOS BÁSICOS (Idêntico ao original) -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
                    <div class="flex flex-col gap-5">
                        <div>
                            <label for="nome" class="block text-sm font-semibold mb-2 text-white">Nome do Cliente*</label>
                            <input type="text" id="nome" name="nome" class="form-input" placeholder="Nome Completo" required>
                        </div>
                        <div>
                            <label for="telefone" class="block text-sm font-semibold mb-2 text-white">Telefone / WhatsApp*</label>
                            <input type="tel" id="telefone" name="telefone" class="form-input" placeholder="(XX) XXXXX-XXXX" required>
                        </div>
                        <div>
                            <label for="rede_social" class="block text-sm font-semibold mb-2 text-gray-300">Instagram / Facebook</label>
                            <input type="text" id="rede_social" name="rede_social" class="form-input" placeholder="@usuario">
                        </div>
                        <div>
                            <label for="cidade" class="block text-sm font-semibold mb-2 text-white">Cidade do Atendimento*</label>
                            <input type="text" id="cidade" name="cidade" class="form-input" required>
                        </div>
                        <div>
                            <label for="loteamento" class="block text-sm font-semibold mb-2 text-white">Loteamento / Empreendimento</label>
                            <select id="loteamento" name="loteamento" class="form-select">
                                <option value="" disabled selected>Selecione uma opção...</option>
                                {% for opcao in empreendimentos %}
                                    <option value="{{ opcao }}">{{ opcao }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <!-- GATILHO DA EXPANSÃO -->
                        <div class="p-3 border border-[#8cc63f] rounded bg-[#8cc63f]/5">
                            <label for="comprou_1o_lote" class="block text-sm font-bold mb-2 text-[#8cc63f]">Realizou o sonho da compra do 1º Lote?</label>
                            <select id="comprou_1o_lote" name="comprou_1o_lote" class="form-select font-bold text-[#8cc63f]" required>
                                <option value="" disabled selected>Selecione...</option>
                                <option value="Sim">Sim</option>
                                <option value="Não">Não</option>
                            </select>
                        </div>
                        
                        <div>
                            <label for="nivel_interesse" class="block text-sm font-semibold mb-2 text-white">Nível de Interesse</label>
                            <select id="nivel_interesse" name="nivel_interesse" class="form-select">
                                <option value="Alto">Alto</option>
                                <option value="Médio">Médio</option>
                                <option value="Baixo">Baixo</option>
                            </select>
                        </div>
                    </div>

                    <div class="flex flex-col gap-5">
                        <div class="p-4 rounded-lg bg-black/20 border border-white/10" id="photoContainer">
                            <label class="block text-sm font-semibold mb-3 text-white">Foto do Cliente</label>
                            <div class="flex flex-col items-center gap-3">
                                <div class="relative">
                                    <canvas id="photoCanvas" class="photo-canvas w-32 h-32 rounded-full object-cover"></canvas>
                                    <video id="videoPreview" class="video-preview w-32 h-32 rounded-full object-cover hidden" autoplay playsinline></video>
                                </div>
                                <div class="flex flex-wrap justify-center gap-2" data-html2canvas-ignore="true">
                                    <button type="button" id="startWebcam" class="text-xs bg-gray-700 text-white px-3 py-2 rounded hover:bg-gray-600 font-semibold uppercase">📷 Câmera</button>
                                    <button type="button" id="takePhoto" class="hidden text-xs bg-green-600 text-white px-3 py-2 rounded hover:bg-green-500 font-semibold uppercase">📸 Capturar</button>
                                    <button type="button" id="clearPhoto" class="hidden text-xs text-red-400 underline">Remover</button>
                                </div>
                            </div>
                            <input type="hidden" id="foto_cliente_base64" name="foto_cliente_base64">
                        </div>
                    </div>
                </div>

                <!-- PARTE 2: FICHA EXPANSÍVEL (Mantendo o Visual Escuro) -->
                <div id="fichaPreContrato" class="hidden section-separator">
                    <h3 class="section-title text-center border-b border-[#8cc63f] pb-2 mb-6">Cadastro de Pré-Contrato</h3>
                    
                    <!-- Dados do Lote -->
                    <h4 class="text-white text-sm font-bold mb-4 uppercase tracking-wide">Dados do Imóvel</h4>
                    <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                        <div><label class="text-xs text-gray-300 block mb-1">Quadra</label><input type="text" name="quadra" class="form-input"></div>
                        <div><label class="text-xs text-gray-300 block mb-1">Lote</label><input type="text" name="lote" class="form-input"></div>
                        <div><label class="text-xs text-gray-300 block mb-1">Metragem (M²)</label><input type="text" name="metragem" class="form-input"></div>
                        <div class="col-span-2 md:col-span-2"><label class="text-xs text-gray-300 block mb-1">Valor Total (R$)</label><input type="text" name="valor_total" class="form-input font-bold text-[#8cc63f]"></div>
                    </div>

                    <!-- Financeiro -->
                    <h4 class="text-white text-sm font-bold mb-4 uppercase tracking-wide">Plano de Pagamento</h4>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                        <div><label class="text-xs text-gray-300 block mb-1">Entrada (R$)</label><input type="text" name="entrada_valor" class="form-input"></div>
                        <div><label class="text-xs text-gray-300 block mb-1">Nº Parcelas</label><input type="number" name="num_parcelas" class="form-input"></div>
                        <div><label class="text-xs text-gray-300 block mb-1">Valor Parcela (R$)</label><input type="text" name="valor_parcelas" class="form-input"></div>
                        <div class="md:col-span-3">
                            <label class="text-xs text-gray-300 block mb-2">Vencimento:</label>
                            <div class="flex gap-6">
                                <label class="flex items-center text-white text-sm cursor-pointer"><input type="radio" name="vencimento_parcelas" value="10" class="accent-[#8cc63f] mr-2"> Dia 10</label>
                                <label class="flex items-center text-white text-sm cursor-pointer"><input type="radio" name="vencimento_parcelas" value="20" class="accent-[#8cc63f] mr-2"> Dia 20</label>
                                <label class="flex items-center text-white text-sm cursor-pointer"><input type="radio" name="vencimento_parcelas" value="30" class="accent-[#8cc63f] mr-2"> Dia 30</label>
                            </div>
                        </div>
                    </div>

                    <!-- Dados Pessoais -->
                    <h4 class="text-white text-sm font-bold mb-4 uppercase tracking-wide">Dados Pessoais Completos</h4>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                        <div><label class="text-xs text-gray-300 block mb-1">CPF</label><input type="text" name="cpf" class="form-input"></div>
                        <div><label class="text-xs text-gray-300 block mb-1">RG</label><input type="text" name="rg" class="form-input"></div>
                        <div><label class="text-xs text-gray-300 block mb-1">Org. Emissor</label><input type="text" name="orgao_emissor" class="form-input"></div>
                        <div><label class="text-xs text-gray-300 block mb-1">Estado Civil</label><input type="text" name="estado_civil" class="form-input"></div>
                        <div><label class="text-xs text-gray-300 block mb-1">Profissão</label><input type="text" name="profissao" class="form-input"></div>
                        <div><label class="text-xs text-gray-300 block mb-1">Renda Mensal</label><input type="text" name="renda_mensal" class="form-input"></div>
                        <div class="md:col-span-3"><label class="text-xs text-gray-300 block mb-1">Endereço Completo</label><input type="text" name="endereco" class="form-input"></div>
                    </div>

                    <!-- Dados Conjuge -->
                    <h4 class="text-white text-sm font-bold mb-4 uppercase tracking-wide">Dados do Cônjuge (Se houver)</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        <div><label class="text-xs text-gray-300 block mb-1">Nome Cônjuge</label><input type="text" name="conjuge_nome" class="form-input"></div>
                        <div><label class="text-xs text-gray-300 block mb-1">CPF Cônjuge</label><input type="text" name="conjuge_cpf" class="form-input"></div>
                    </div>

                    <!-- Referencias -->
                    <h4 class="text-white text-sm font-bold mb-4 uppercase tracking-wide">Referências</h4>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div><label class="text-xs text-gray-300 block mb-1">Nome Ref 1</label><input type="text" name="ref1_nome" class="form-input"></div>
                        <div><label class="text-xs text-gray-300 block mb-1">Nome Ref 2</label><input type="text" name="ref2_nome" class="form-input"></div>
                        <div><label class="text-xs text-gray-300 block mb-1">Nome Ref 3</label><input type="text" name="ref3_nome" class="form-input"></div>
                    </div>
                </div>

                <!-- PARTE 3: FINALIZAÇÃO (Mantido layout original) -->
                <div class="mt-8 space-y-4 pt-4 border-t border-[#4a5e35]">
                    <div>
                        <span class="block text-sm font-semibold mb-2 text-white">Já esteve em um plantão da Araguaia?*</span>
                        <div class="flex gap-4">
                            <label class="flex items-center cursor-pointer text-white"><input type="radio" name="esteve_plantao" value="sim" class="accent-[#8cc63f] mr-2" required> Sim</label>
                            <label class="flex items-center cursor-pointer text-white"><input type="radio" name="esteve_plantao" value="nao" class="accent-[#8cc63f] mr-2"> Não</label>
                        </div>
                    </div>
                    <div>
                        <span class="block text-sm font-semibold mb-2 text-white">Já possui corretor na Araguaia?*</span>
                        <div class="flex gap-4">
                            <label class="flex items-center cursor-pointer text-white"><input type="radio" name="foi_atendido" value="sim" id="atendido_sim" class="accent-[#8cc63f] mr-2" required> Sim</label>
                            <label class="flex items-center cursor-pointer text-white"><input type="radio" name="foi_atendido" value="nao" id="atendido_nao" class="accent-[#8cc63f] mr-2"> Não</label>
                        </div>
                    </div>
                    <div id="campoNomeCorretor" class="hidden animate-fade-in p-3 bg-[#8cc63f]/10 border border-[#8cc63f] rounded-md">
                        <label for="nome_corretor" class="block text-sm font-bold mb-1 text-[#8cc63f]">Selecione o Corretor:</label>
                        <select id="nome_corretor" name="nome_corretor" class="form-select font-semibold">
                            <option value="" disabled selected>Selecione um corretor...</option>
                            {% for corretor in corretores %}
                                <option value="{{ corretor }}">{{ corretor }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <span class="block text-sm font-semibold mb-2 text-white">Autoriza lista de transmissão?*</span>
                        <div class="flex gap-4">
                            <label class="flex items-center cursor-pointer text-white"><input type="radio" name="autoriza_transmissao" value="sim" class="accent-[#8cc63f] mr-2" required> Sim</label>
                            <label class="flex items-center cursor-pointer text-white"><input type="radio" name="autoriza_transmissao" value="nao" class="accent-[#8cc63f] mr-2"> Não</label>
                        </div>
                    </div>
                </div>
                
                <div class="mt-6">
                    <label for="abordagem_inicial" class="block text-sm font-semibold mb-2 text-white">Observações / Abordagem Inicial</label>
                    <textarea id="abordagem_inicial" name="abordagem_inicial" rows="3" class="form-textarea" placeholder="Detalhes importantes..."></textarea>
                </div>

                <div class="mt-6">
                    <label class="block text-sm font-semibold mb-2 text-white">Assinatura do Cliente</label>
                    <canvas id="signatureCanvas" class="signature-canvas w-full h-32 cursor-crosshair"></canvas>
                    <input type="hidden" id="assinatura_base64" name="assinatura_base64">
                    <div class="flex justify-end mt-1" data-html2canvas-ignore="true">
                        <button type="button" id="clearSignature" class="text-xs text-gray-400 underline hover:text-white">Limpar Assinatura</button>
                    </div>
                </div>

                <div class="flex flex-col md:flex-row justify-end items-center gap-4 mt-8 btn-area">
                    <span class="text-sm font-medium mr-auto" style="color: var(--cor-texto-cinza);" id="dataAtual">Sorriso/MT</span>
                    <button type="button" id="btnGerarPDF" class="btn-pdf w-full md:w-auto shadow-lg">📄 Baixar Cópia (PDF)</button>
                    <button type="submit" id="saveButton" class="btn-salvar w-full md:w-auto shadow-lg hover:shadow-xl">Salvar Ficha</button>
                </div>
                <div id="statusMessage" class="mt-4 text-center p-3 rounded font-bold hidden"></div>
            </form>
        </div>
    </main>
    <footer class="w-full p-6 text-center text-xs opacity-50">© <span id="currentYear"></span> Araguaia Imóveis. Todos os direitos reservados.</footer>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            // Data atual
            const today = new Date();
            document.getElementById('dataAtual').innerText = `Sorriso/MT, ${today.toLocaleDateString('pt-BR')}`;
            document.getElementById('currentYear').innerText = today.getFullYear();
            
            const form = document.getElementById('preAtendimentoForm');
            const statusMessage = document.getElementById('statusMessage');

            // --- Lógica Expansão Ficha Extra ---
            const selectCompra = document.getElementById('comprou_1o_lote');
            const fichaExtra = document.getElementById('fichaPreContrato');

            selectCompra.addEventListener('change', function() {
                if(this.value === 'Sim') {
                    fichaExtra.classList.remove('hidden');
                    fichaExtra.classList.add('animate-expand');
                    // Scroll suave para a nova área
                    setTimeout(() => fichaExtra.scrollIntoView({behavior: 'smooth', block: 'start'}), 100);
                } else {
                    fichaExtra.classList.add('hidden');
                    fichaExtra.classList.remove('animate-expand');
                }
            });

            // --- Lógica Corretor ---
            const atendidoSim = document.getElementById('atendido_sim');
            const atendidoNao = document.getElementById('atendido_nao');
            const campoNome = document.getElementById('campoNomeCorretor');
            const inputNomeCorretor = document.getElementById('nome_corretor');
            
            function toggleCorretor() {
                if(atendidoSim.checked) {
                    campoNome.classList.remove('hidden');
                    inputNomeCorretor.required = true;
                } else {
                    campoNome.classList.add('hidden');
                    inputNomeCorretor.required = false;
                    inputNomeCorretor.value = '';
                }
            }
            atendidoSim.addEventListener('change', toggleCorretor);
            atendidoNao.addEventListener('change', toggleCorretor);

            // --- PDF Logic ---
            document.getElementById('btnGerarPDF').addEventListener('click', function() {
                const btnPdf = this;
                const originalText = btnPdf.innerText;
                const element = document.getElementById('fichaContainer');
                const pdfHeader = document.getElementById('pdfHeader');

                let nomeCliente = document.getElementById('nome').value.trim() || "Cliente";
                const nomeArquivo = `Ficha_Araguaia_${nomeCliente.replace(/\s+/g, "_")}.pdf`;

                btnPdf.innerText = "Gerando..."; btnPdf.disabled = true;

                element.classList.add('pdf-mode'); 
                pdfHeader.classList.remove('hidden'); 
                
                // Ocultar botões para o PDF
                const botoes = document.querySelectorAll('.btn-area button, .btn-acao-secundaria, #photoContainer button, #clearSignature');
                botoes.forEach(b => b.style.display = 'none');

                html2pdf().set({
                    margin: 5, filename: nomeArquivo, image: { type: 'jpeg', quality: 0.95 },
                    html2canvas: { scale: 2, useCORS: true, backgroundColor: '#ffffff' },
                    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
                }).from(element).save().then(function(){
                    element.classList.remove('pdf-mode');
                    pdfHeader.classList.add('hidden');
                    botoes.forEach(b => b.style.display = '');
                    btnPdf.innerText = originalText; btnPdf.disabled = false;
                });
            });

            // --- Câmera e Assinatura ---
            const sigCv = document.getElementById('signatureCanvas'); const sigCtx = sigCv.getContext('2d');
            let drawing = false;
            function fitSig(){ sigCv.width=sigCv.offsetWidth; sigCv.height=sigCv.offsetHeight; sigCtx.lineWidth=2; sigCtx.strokeStyle="#263318"; }
            window.addEventListener('resize', fitSig); fitSig();
            const getPos=(e)=>{const r=sigCv.getBoundingClientRect(); const t=e.touches?e.touches[0]:e; return{x:t.clientX-r.left,y:t.clientY-r.top}};
            sigCv.addEventListener('mousedown',(e)=>{drawing=true;sigCtx.beginPath();sigCtx.moveTo(getPos(e).x,getPos(e).y)});
            sigCv.addEventListener('mousemove',(e)=>{if(drawing){sigCtx.lineTo(getPos(e).x,getPos(e).y);sigCtx.stroke()}});
            sigCv.addEventListener('mouseup',()=>drawing=false);
            sigCv.addEventListener('touchstart',(e)=>{drawing=true;sigCtx.beginPath();sigCtx.moveTo(getPos(e).x,getPos(e).y);e.preventDefault()});
            sigCv.addEventListener('touchmove',(e)=>{if(drawing){sigCtx.lineTo(getPos(e).x,getPos(e).y);sigCtx.stroke();e.preventDefault()}});
            sigCv.addEventListener('touchend',()=>drawing=false);
            document.getElementById('clearSignature').addEventListener('click', ()=>{sigCtx.clearRect(0,0,sigCv.width,sigCv.height);document.getElementById('assinatura_base64').value=''});

            const vid = document.getElementById('videoPreview'); const photoCv = document.getElementById('photoCanvas'); const phCtx = photoCv.getContext('2d');
            const fotoInput = document.getElementById('foto_cliente_base64');
            
            // Placeholder
            phCtx.fillStyle='#f4f4f4'; phCtx.fillRect(0,0,photoCv.width,photoCv.height);
            
            document.getElementById('startWebcam').addEventListener('click', async()=>{
                try{vid.srcObject=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}});vid.classList.remove('hidden');photoCv.classList.add('hidden');document.getElementById('takePhoto').classList.remove('hidden');document.getElementById('startWebcam').classList.add('hidden');document.getElementById('clearPhoto').classList.remove('hidden');}catch(e){alert("Erro Câmera: "+e)}
            });
            document.getElementById('takePhoto').addEventListener('click',()=>{
                photoCv.width=vid.videoWidth;photoCv.height=vid.videoHeight; phCtx.drawImage(vid,0,0);
                fotoInput.value=photoCv.toDataURL('image/jpeg',0.8);
                vid.classList.add('hidden'); photoCv.classList.remove('hidden');
                vid.srcObject.getTracks().forEach(t=>t.stop());
                document.getElementById('takePhoto').classList.add('hidden'); document.getElementById('startWebcam').classList.remove('hidden');
            });
            document.getElementById('clearPhoto').addEventListener('click', ()=>{
                fotoInput.value=''; phCtx.clearRect(0,0,photoCv.width,photoCv.height); phCtx.fillStyle='#f4f4f4'; phCtx.fillRect(0,0,photoCv.width,photoCv.height);
                if(vid.srcObject) vid.srcObject.getTracks().forEach(t=>t.stop());
                vid.classList.add('hidden'); photoCv.classList.remove('hidden');
                document.getElementById('startWebcam').classList.remove('hidden'); document.getElementById('takePhoto').classList.add('hidden'); document.getElementById('clearPhoto').classList.add('hidden');
            });

            // --- Submit ---
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                document.getElementById('assinatura_base64').value = sigCv.toDataURL();
                const btn = document.getElementById('saveButton'); btn.disabled=true; btn.innerText='SALVANDO...';
                
                const fd = new FormData(form); const data={}; fd.forEach((v,k)=>data[k]=v);
                
                // Conversão de booleanos
                data.esteve_plantao = (data.esteve_plantao==='sim')?1:0;
                data.foi_atendido = (data.foi_atendido==='sim')?1:0;
                data.autoriza_transmissao = (data.autoriza_transmissao==='sim')?1:0;

                try {
                    const r = await fetch('/', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
                    const res = await r.json();
                    if(res.success) {
                        statusMessage.innerText = "FICHA SALVA COM SUCESSO!"; 
                        statusMessage.className="mt-4 bg-[#8cc63f] text-[#1a2610] p-4 rounded shadow-lg block animate-bounce";
                        statusMessage.classList.remove('hidden');
                        form.reset(); sigCtx.clearRect(0,0,sigCv.width,sigCv.height);
                        document.getElementById('clearPhoto').click();
                        setTimeout(() => statusMessage.classList.add('hidden'), 5000);
                        // Reset da área expandida
                        fichaExtra.classList.add('hidden');
                    } else throw new Error(res.message);
                } catch(err) {
                    statusMessage.innerText = "ERRO: "+err.message; 
                    statusMessage.className="mt-4 bg-red-600 text-white p-4 rounded shadow-lg block";
                    statusMessage.classList.remove('hidden');
                } finally { btn.disabled=false; btn.innerText='SALVAR FICHA'; }
            });
        });
    </script>
</body>
</html>
"""

# --- AUXILIARES ---
def formatar_telefone_n8n(telefone_bruto):
    try:
        numeros = ''.join(filter(str.isdigit, telefone_bruto))
        if 10 <= len(numeros) <= 11:
            return f"+55{numeros}"
        return None
    except:
        return None

# --- ROTAS ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not DATABASE_URL:
            return jsonify({'success': False, 'message': 'Banco de dados não configurado.'}), 500
        try:
            data = request.json
            nome = data.get('nome')
            cidade = data.get('cidade')
            telefone = formatar_telefone_n8n(data.get('telefone'))
            
            if not telefone or not nome:
                return jsonify({'success': False, 'message': 'Nome e Telefone são obrigatórios.'}), 400

            # 1. PREPARA DADOS PARA O BANCO (COMPLETO)
            campos_db = {
                'data_hora': datetime.datetime.now(datetime.timezone.utc),
                'nome': nome,
                'telefone': telefone,
                'rede_social': data.get('rede_social'),
                'abordagem_inicial': data.get('abordagem_inicial'),
                'esteve_plantao': to_bool_flag(data.get('esteve_plantao')),
                'foi_atendido': to_bool_flag(data.get('foi_atendido')),
                'nome_corretor': data.get('nome_corretor') if to_bool_flag(data.get('foi_atendido')) else None,
                'autoriza_transmissao': to_bool_flag(data.get('autoriza_transmissao')),
                'foto_cliente': data.get('foto_cliente_base64'),
                'assinatura': data.get('assinatura_base64'),
                'cidade': cidade,
                'loteamento': data.get('loteamento'),
                'comprou_1o_lote': data.get('comprou_1o_lote'),
                'nivel_interesse': data.get('nivel_interesse'),
                # Campos Extras do Anexo
                'quadra': data.get('quadra'), 'lote': data.get('lote'), 'metragem': data.get('metragem'),
                'valor_m2': data.get('valor_m2'), 'valor_total': data.get('valor_total'),
                'entrada_valor': data.get('entrada_valor'), 'num_parcelas': data.get('num_parcelas'),
                'valor_parcelas': data.get('valor_parcelas'), 'vencimento_parcelas': data.get('vencimento_parcelas'),
                'rg': data.get('rg'), 'orgao_emissor': data.get('orgao_emissor'),
                'estado_civil': data.get('estado_civil'), 'cpf': data.get('cpf'),
                'filhos': data.get('filhos'), 'endereco': data.get('endereco'),
                'email': data.get('email'), 'tipo_residencia': data.get('tipo_residencia'),
                'valor_aluguel': data.get('valor_aluguel'), 'possui_financiamento': data.get('possui_financiamento'),
                'empresa_trabalho': data.get('empresa_trabalho'), 'profissao': data.get('profissao'),
                'telefone_empresa': data.get('telefone_empresa'), 'renda_mensal': data.get('renda_mensal'),
                'conjuge_nome': data.get('conjuge_nome'), 'conjuge_cpf': data.get('conjuge_cpf'),
                'conjuge_rg': data.get('conjuge_rg'), 'conjuge_empresa': data.get('conjuge_empresa'),
                'conjuge_profissao': data.get('conjuge_profissao'), 'conjuge_renda': data.get('conjuge_renda'),
                'ref1_nome': data.get('ref1_nome'), 'ref1_tel': data.get('ref1_tel'),
                'ref2_nome': data.get('ref2_nome'), 'ref2_tel': data.get('ref2_tel'),
                'ref3_nome': data.get('ref3_nome'), 'ref3_tel': data.get('ref3_tel'),
                'fonte_midia': data.get('fonte_midia')
            }

            cols = list(campos_db.keys())
            vals = list(campos_db.values())
            query = f"INSERT INTO atendimentos ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(cols))}) RETURNING id"

            ticket_id = None
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, tuple(vals))
                    ticket_id = cursor.fetchone()[0]

            logger.info(f"✅ Ficha salva no Banco! ID: {ticket_id}")

            # 2. PREPARA DADOS PARA O N8N (SOMENTE O NECESSÁRIO)
            if N8N_WEBHOOK_URL:
                try:
                    payload_n8n = {
                        "ticket_id": ticket_id,
                        "nome": nome,
                        "telefone": telefone,
                        "nome_corretor": campos_db['nome_corretor'],
                        "cidade": cidade,
                        "timestamp": str(campos_db['data_hora'])
                    }
                    requests.post(N8N_WEBHOOK_URL, json=payload_n8n, timeout=2)
                    logger.info("✅ Dados básicos enviados para o N8N.")
                except Exception as e:
                    logger.warning(f"Erro N8N: {e}")

            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Erro POST: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    return render_template_string(HTML_TEMPLATE, empreendimentos=OPCOES_EMPREENDIMENTOS, corretores=OPCOES_CORRETORES)

@app.route('/avaliar', methods=['POST'])
def avaliar_atendimento():
    if not DATABASE_URL: return jsonify({'success': False}), 500
    try:
        data = request.get_json(silent=True) or request.form.to_dict() or request.args.to_dict()
        if not data: return jsonify({'success': False}), 400
        
        ticket_id = data.get('ticket_id')
        nota = int(str(data.get('nota')).strip())
        
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE atendimentos SET nota_atendimento = %s WHERE id = %s", (nota, ticket_id))
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erro avaliar: {e}")
        return jsonify({'success': False}), 500

if __name__ == '__main__':
    # use_reloader=False é OBRIGATÓRIO para evitar erro de sinal de thread no Windows/IDEs
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)