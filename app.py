import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table, ALL
import dash_bootstrap_components as dbc
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# --- 1. CONFIGURAÇÃO E SEGURANÇA ---
# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

db_url = os.getenv("DATABASE_URL")

# Fallback apenas para evitar crash se a variável não estiver setada (mas avisa no log)
if not db_url:
    print("⚠️ AVISO: Variável DATABASE_URL não encontrada. Usando banco SQLite local para testes.")
    db_url = "sqlite:///local_test.db" # Fallback seguro para dev local
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)

# --- 2. INICIALIZAÇÃO DO BANCO (COM HISTÓRICO) ---
def init_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS projetos (id SERIAL PRIMARY KEY, nome VARCHAR(255));"))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cronograma_etapas (
                    id SERIAL PRIMARY KEY, projeto_id INTEGER REFERENCES projetos(id),
                    etapa VARCHAR(100), data_inicio DATE, data_fim DATE,
                    valor_estimado NUMERIC(15,2) DEFAULT 0, status VARCHAR(50) DEFAULT 'A Fazer'
                );
            """))
            # Garante coluna percentual (caso banco antigo)
            try: conn.execute(text("ALTER TABLE cronograma_etapas ADD COLUMN IF NOT EXISTS percentual INTEGER DEFAULT 0;"))
            except: pass

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS despesas (
                    id SERIAL PRIMARY KEY, projeto_id INTEGER REFERENCES projetos(id),
                    categoria VARCHAR(100), descricao VARCHAR(255),
                    valor NUMERIC(15,2), data_pagamento DATE, status VARCHAR(50) DEFAULT 'Pago'
                );
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS permutas (
                    id SERIAL PRIMARY KEY, projeto_id INTEGER REFERENCES projetos(id),
                    descricao VARCHAR(255), data_permuta DATE, valor NUMERIC(15,2) DEFAULT 0
                );
            """))

            # --- NOVA TABELA: HISTÓRICO FÍSICO ---
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS historico_fisico (
                    id SERIAL PRIMARY KEY,
                    etapa_id INTEGER REFERENCES cronograma_etapas(id) ON DELETE CASCADE,
                    data_registro DATE DEFAULT CURRENT_DATE,
                    percentual_novo INTEGER
                );
            """))
            
            conn.commit()
    except Exception as e:
        print(f"Erro DB Init: {e}")

init_db()

def update_db_schema():
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE projetos ADD COLUMN IF NOT EXISTS empresa VARCHAR(100) DEFAULT 'Própria';"))
            conn.commit()
    except: pass

update_db_schema()

# --- 3. MODEL E DADOS ---

def get_projetos():
    try: return pd.read_sql("SELECT id, nome, empresa FROM projetos ORDER BY id DESC", engine)
    except: return pd.DataFrame(columns=['id', 'nome', 'empresa'])

def get_cronograma():
    try:
        sql = """SELECT p.nome as projeto, e.projeto_id, e.id as id_etapa, e.etapa, e.data_inicio, e.data_fim, e.valor_estimado, e.status, e.percentual 
                 FROM cronograma_etapas e JOIN projetos p ON e.projeto_id = p.id ORDER BY p.nome, e.data_inicio"""
        return pd.read_sql(sql, engine)
    except: return pd.DataFrame()

def get_despesas_realizadas():
    try:
        sql = """SELECT d.id, p.nome as projeto, d.projeto_id, d.categoria, d.descricao, d.valor, d.data_pagamento, d.status 
                 FROM despesas d JOIN projetos p ON d.projeto_id = p.id ORDER BY d.data_pagamento DESC"""
        return pd.read_sql(sql, engine)
    except: return pd.DataFrame()

def get_permutas():
    try:
        sql = """SELECT pm.id, p.nome as projeto, pm.projeto_id, pm.descricao, pm.valor, pm.data_permuta 
                 FROM permutas pm JOIN projetos p ON pm.projeto_id = p.id ORDER BY pm.data_permuta DESC"""
        return pd.read_sql(sql, engine)
    except: return pd.DataFrame()

def get_dados_historico_tendencia(filtro_id=None):
    # Busca o histórico de alterações para montar a curva S realizada
    try:
        sql = """
            SELECT h.data_registro, p.nome as projeto, e.valor_estimado, h.percentual_novo, p.id as projeto_id
            FROM historico_fisico h
            JOIN cronograma_etapas e ON h.etapa_id = e.id
            JOIN projetos p ON e.projeto_id = p.id
            ORDER BY h.data_registro ASC
        """
        df = pd.read_sql(sql, engine)
        
        if df.empty: return pd.DataFrame()

        if filtro_id and str(filtro_id) != 'todos':
            df = df[df['projeto_id'] == int(filtro_id)]
            
        # Logica Simplificada de Tendência:
        # Agrupa por data e calcula a "Média Ponderada da Evolução" registrada naquele dia
        # Para um sistema perfeito, precisaria recalcular o estado total da obra dia a dia.
        # Aqui vamos mostrar os "Pontos de Evolução".
        df['valor_realizado'] = df['valor_estimado'] * (df['percentual_novo'] / 100)
        
        # Agrupa por Data e Projeto para somar o que foi realizado acumulado
        # Nota: Isso é uma aproximação baseada nos registros de UPDATE.
        df_agrupado = df.groupby(['data_registro', 'projeto'])['percentual_novo'].mean().reset_index()
        
        return df_agrupado
    except: return pd.DataFrame()

def get_tabela_resumo_financeiro():
    df_crono = get_cronograma()
    if not df_crono.empty:
        df_orcado = df_crono.groupby(['projeto', 'projeto_id'])['valor_estimado'].sum().reset_index()
        df_orcado.rename(columns={'valor_estimado': 'vl_contrato'}, inplace=True)
    else:
        df_orcado = pd.DataFrame(columns=['projeto', 'projeto_id', 'vl_contrato'])

    df_desp = get_despesas_realizadas()
    if not df_desp.empty:
        df_pago = df_desp.groupby('projeto')['valor'].sum().reset_index()
        df_pago.rename(columns={'valor': 'vl_pago'}, inplace=True)
    else:
        df_pago = pd.DataFrame(columns=['projeto', 'vl_pago'])

    df_perm = get_permutas()
    if not df_perm.empty:
        df_perm_g = df_perm.groupby('projeto')['valor'].sum().reset_index()
        df_perm_g.rename(columns={'valor': 'vl_permuta'}, inplace=True)
    else:
        df_perm_g = pd.DataFrame(columns=['projeto', 'vl_permuta'])

    df_proj = get_projetos()
    if 'empresa' not in df_proj.columns: df_proj['empresa'] = 'Própria' 

    df_final = pd.merge(df_proj, df_orcado, left_on='id', right_on='projeto_id', how='left')
    df_final = pd.merge(df_final, df_pago, left_on='nome', right_on='projeto', how='left')
    df_final = pd.merge(df_final, df_perm_g, left_on='nome', right_on='projeto', how='left')
    
    df_final['vl_contrato'] = df_final['vl_contrato'].fillna(0).astype(float)
    df_final['vl_pago'] = df_final['vl_pago'].fillna(0).astype(float)
    df_final['vl_permuta'] = df_final['vl_permuta'].fillna(0).astype(float)
    
    df_final['saldo'] = df_final['vl_contrato'] - df_final['vl_pago'] - df_final['vl_permuta']
    df_final['perc_pago'] = df_final.apply(lambda x: ((x['vl_pago'] + x['vl_permuta']) / x['vl_contrato'] * 100) if x['vl_contrato'] > 0 else 0, axis=1)
    
    df_final = df_final[(df_final['vl_contrato'] > 0) | (df_final['vl_pago'] > 0) | (df_final['vl_permuta'] > 0)]
    return df_final

def get_kpis_globais(filtro_id=None):
    try:
        df_crono = get_cronograma()
        df_desp = get_despesas_realizadas()
        df_permuta = get_permutas()

        if filtro_id and str(filtro_id) != 'todos':
            fid = int(filtro_id)
            if not df_crono.empty: df_crono = df_crono[df_crono['projeto_id'] == fid]
            if not df_desp.empty: df_desp = df_desp[df_desp['projeto_id'] == fid]
            if not df_permuta.empty: df_permuta = df_permuta[df_permuta['projeto_id'] == fid]

        total_contratado = df_crono['valor_estimado'].sum() if not df_crono.empty else 0
        total_pago = df_desp['valor'].sum() if not df_desp.empty else 0
        total_permuta = df_permuta['valor'].sum() if not df_permuta.empty else 0
        saldo = total_contratado - total_pago - total_permuta
        atraso = 0
        
        if not df_crono.empty:
            df_crono['data_fim'] = pd.to_datetime(df_crono['data_fim'])
            mask_atraso = (df_crono['data_fim'] < pd.Timestamp.now()) & (df_crono['percentual'] < 100)
            df_crono['valor_pendente'] = df_crono['valor_estimado'] * (1 - (df_crono['percentual'] / 100))
            atraso = df_crono.loc[mask_atraso, 'valor_pendente'].sum()

        # --- FÍSICO vs FINANCEIRO ---
        perc_fisico = 0
        perc_financeiro = 0
        if total_contratado > 0:
            valor_fisico_executado = (df_crono['valor_estimado'] * (df_crono['percentual'] / 100)).sum()
            perc_fisico = (valor_fisico_executado / total_contratado) * 100
            perc_financeiro = ((total_pago + total_permuta) / total_contratado) * 100

        return total_contratado, total_permuta, total_pago, saldo, atraso, perc_fisico, perc_financeiro
    except: return 0, 0, 0, 0, 0, 0, 0

def get_dados_pareto_resumo(filtro_id=None):
    df_desp = get_despesas_realizadas()
    df_perm = get_permutas()

    if filtro_id and str(filtro_id) != 'todos':
        fid = int(filtro_id)
        if not df_desp.empty: df_desp = df_desp[df_desp['projeto_id'] == fid]
        if not df_perm.empty: df_perm = df_perm[df_perm['projeto_id'] == fid]

    if not df_desp.empty:
        df_desp = df_desp[df_desp['status'] == 'Pago']
        df_cat = df_desp.groupby('categoria')['valor'].sum().reset_index()
    else:
        df_cat = pd.DataFrame(columns=['categoria', 'valor'])

    val_permuta = df_perm['valor'].sum() if not df_perm.empty else 0
    if val_permuta > 0:
        row_permuta = pd.DataFrame({'categoria': ['Permuta'], 'valor': [val_permuta]})
        df_cat = pd.concat([df_cat, row_permuta], ignore_index=True)

    if df_cat.empty: return pd.DataFrame()

    df_cat = df_cat.sort_values(by='valor', ascending=False)
    if len(df_cat) > 5:
        top_5 = df_cat.iloc[:5]
        outros_val = df_cat.iloc[5:]['valor'].sum()
        row_outros = pd.DataFrame({'categoria': ['Outros'], 'valor': [outros_val]})
        df_final = pd.concat([top_5, row_outros], ignore_index=True)
    else:
        df_final = df_cat

    total = df_final['valor'].sum()
    df_final['perc'] = (df_final['valor'] / total) * 100
    df_final['acum'] = df_final['perc'].cumsum()
    return df_final

def calcular_orcado_vs_realizado():
    df_crono = get_cronograma()
    lista_orcado = []
    if not df_crono.empty:
        df_crono['data_inicio'] = pd.to_datetime(df_crono['data_inicio'])
        df_crono['data_fim'] = pd.to_datetime(df_crono['data_fim'])
        for _, row in df_crono.iterrows():
            inicio, fim = row['data_inicio'].replace(day=1), row['data_fim'].replace(day=1)
            valor_total = float(row['valor_estimado'])
            meses = (fim.year - inicio.year) * 12 + (fim.month - inicio.month) + 1
            if meses < 1: meses = 1
            valor_mensal = valor_total / meses
            curr = inicio
            for _ in range(meses):
                lista_orcado.append({'projeto': row['projeto'], 'data_ref': curr, 'valor_orcado': valor_mensal, 'valor_realizado': 0.0})
                curr += relativedelta(months=1)
    
    lista_realizado = []
    df_desp = get_despesas_realizadas()
    if not df_desp.empty:
        df_desp['data_pagamento'] = pd.to_datetime(df_desp['data_pagamento'])
        for _, row in df_desp.iterrows():
            lista_realizado.append({'projeto': row['projeto'], 'data_ref': row['data_pagamento'].replace(day=1), 'valor_orcado': 0.0, 'valor_realizado': float(row['valor'])})

    df_perm = get_permutas()
    if not df_perm.empty:
        df_perm['data_permuta'] = pd.to_datetime(df_perm['data_permuta'])
        for _, row in df_perm.iterrows():
            lista_realizado.append({'projeto': row['projeto'], 'data_ref': row['data_permuta'].replace(day=1), 'valor_orcado': 0.0, 'valor_realizado': float(row['valor'])})

    df_final = pd.concat([pd.DataFrame(lista_orcado), pd.DataFrame(lista_realizado)])
    if df_final.empty: return pd.DataFrame()
    return df_final.groupby(['data_ref', 'projeto'])[['valor_orcado', 'valor_realizado']].sum().reset_index().sort_values(by='data_ref')

def get_detalhes_atraso():
    try:
        sql = """SELECT p.nome as projeto, e.etapa, e.data_fim, e.valor_estimado, e.percentual FROM cronograma_etapas e JOIN projetos p ON e.projeto_id = p.id WHERE e.data_fim < CURRENT_DATE AND e.percentual < 100 ORDER BY e.data_fim ASC"""
        return pd.read_sql(sql, engine)
    except: return pd.DataFrame()

def calcular_projecao_futura():
    df = get_cronograma()
    if df.empty: return pd.DataFrame()
    df['percentual'] = pd.to_numeric(df['percentual'], errors='coerce').fillna(0)
    df_aberto = df[(df['status'] != 'Concluído') & (df['percentual'] < 100)].copy()
    df_aberto['data_inicio'] = pd.to_datetime(df_aberto['data_inicio'])
    df_aberto['data_fim'] = pd.to_datetime(df_aberto['data_fim'])
    
    lista_projecao = []
    today = pd.Timestamp.now().normalize()
    for _, row in df_aberto.iterrows():
        start_date = max(today, row['data_inicio'])
        end_date = row['data_fim']
        valor_restante = float(row['valor_estimado']) * (1 - (float(row['percentual']) / 100))
        if valor_restante <= 0: continue

        if end_date <= start_date:
            lista_projecao.append({'Data': today.replace(day=1), 'Projeto': row['projeto'], 'Valor Projetado': valor_restante})
        else:
            meses = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
            if meses < 1: meses = 1
            valor_mensal = valor_restante / meses
            curr = start_date.replace(day=1)
            for _ in range(meses):
                lista_projecao.append({'Data': curr, 'Projeto': row['projeto'], 'Valor Projetado': valor_mensal})
                curr += relativedelta(months=1)
            
    if not lista_projecao: return pd.DataFrame()
    return pd.DataFrame(lista_projecao).groupby(['Data', 'Projeto'])['Valor Projetado'].sum().reset_index()

# --- FUNÇÕES GRÁFICAS ---

def gerar_figura_gantt(filtro_obra_id=None):
    df_crono = get_cronograma()
    if df_crono.empty: return px.bar(title="Sem cronograma cadastrado", template="plotly_white")
    
    df_crono['data_inicio'] = pd.to_datetime(df_crono['data_inicio'])
    df_crono['data_fim'] = pd.to_datetime(df_crono['data_fim'])
    df_chart = df_crono.copy()
    
    if filtro_obra_id and str(filtro_obra_id).lower() not in ['none', 'todos', '']:
        df_chart = df_chart[df_chart['projeto_id'] == int(filtro_obra_id)]
        title_text = f"Cronograma: {df_chart.iloc[0]['projeto'] if not df_chart.empty else ''}"
    else:
        title_text = "Visão Geral: Todas as Obras"

    if df_chart.empty: return px.bar(title="Nenhum dado encontrado para o filtro.", template="plotly_white")

    df_chart['tarefa_label'] = df_chart['projeto'] + " - " + df_chart['etapa']
    df_chart = df_chart.sort_values(by=['projeto', 'data_inicio'], ascending=[True, True])
    altura_calc = 300 + (len(df_chart) * 60)

    fig = px.timeline(df_chart, x_start="data_inicio", x_end="data_fim", y="tarefa_label", color="percentual", color_continuous_scale="RdYlGn", range_color=[0, 100], template="plotly_white", height=altura_calc)
    
    df_chart['data_inicio_str'] = df_chart['data_inicio'].dt.strftime('%Y-%m-%d')
    df_chart['data_fim_str'] = df_chart['data_fim'].dt.strftime('%Y-%m-%d')
    
    fig.update_traces(customdata=df_chart[['id_etapa', 'valor_estimado', 'percentual', 'data_inicio_str', 'data_fim_str', 'etapa', 'projeto_id']], marker=dict(line=dict(width=1, color='black'), opacity=0.9), width=0.8)
    fig.update_layout(title=dict(text=title_text, font=dict(size=24, color="black", family="Arial Black")), xaxis=dict(title="Linha do Tempo", side="top", tickfont=dict(size=14, family="Arial Black", color="black"), gridcolor="#e5e7eb"), yaxis=dict(title="", autorange="reversed", tickfont=dict(size=14, family="Arial Black", color="black"), dtick=1), legend=dict(orientation="h", y=1.05), margin=dict(l=10, r=10, t=120, b=50), autosize=True)
    return fig

def gerar_grafico_descompasso(fisico_pct, financeiro_pct):
    cor_fin = "#ef4444" if financeiro_pct > (fisico_pct + 2) else "#10b981"
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[fisico_pct], y=["Progresso"], name='Avanço Físico (Obra)', orientation='h', marker_color='#2563eb', text=f"{fisico_pct:.1f}%", textposition='auto', width=0.6))
    fig.add_trace(go.Bar(x=[financeiro_pct], y=["Progresso"], name='Avanço Financeiro (Pago)', orientation='h', marker_color=cor_fin, text=f"{financeiro_pct:.1f}%", textposition='auto', width=0.3))
    fig.update_layout(title="<b>Físico vs Financeiro (O Descompasso)</b>", template="plotly_white", barmode='overlay', xaxis=dict(range=[0, 100], showgrid=True, title="%"), yaxis=dict(showticklabels=False), legend=dict(orientation="h", y=-0.2), height=200, margin=dict(l=20, r=20, t=50, b=20))
    diff = fisico_pct - financeiro_pct
    msg = "✅ Eficiente" if diff >= 0 else "⚠️ Atenção"
    fig.add_annotation(x=50, y=1, text=msg, showarrow=False, font=dict(size=12, color="gray"), yshift=20)
    return fig

# --- 4. APP SETUP ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

# --- LAYOUT WRAPPERS ---
sidebar = html.Div([
    html.Div([html.Span("EM", style={"backgroundColor": "#2563eb", "color": "white", "padding": "4px 8px", "borderRadius": "6px", "fontWeight": "bold", "marginRight": "8px"}), html.Span("EngManager", style={"fontWeight": "600", "fontSize": "1.2rem", "color": "white"})], style={"marginBottom": "2rem", "display": "flex", "alignItems": "center"}),
    dbc.Nav([
        dbc.NavLink([html.I(className="bi bi-grid-fill me-2"), "Resumo Global"], href="/", active="exact", style={"color": "#d1d5db"}),
        dbc.NavLink([html.I(className="bi bi-building me-2"), "Projetos / Obras"], href="/projetos", active="exact", style={"color": "#d1d5db"}),
        dbc.NavLink([html.I(className="bi bi-cash-coin me-2"), "Financeiro"], href="/financeiro", active="exact", style={"color": "#d1d5db"}),
        dbc.NavLink([html.I(className="bi bi-table me-2"), "Relatórios & Tabelas"], href="/tabelas", active="exact", style={"color": "#d1d5db"}),
    ], vertical=True, pills=True)
], style={"position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "16rem", "padding": "2rem 1rem", "backgroundColor": "#0e1621", "color": "white"})

content = html.Div(id="page-content", style={"marginLeft": "16rem", "padding": "2rem", "backgroundColor": "#f3f4f6", "minHeight": "100vh"})
app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

# --- HELPER DE UI ---
def create_kpi_card(title, value, icon_class, color_bg):
    return dbc.Card(dbc.CardBody([
        html.Div([
            html.Div([html.P(title, style={"color": "#6b7280", "fontSize": "0.85rem", "marginBottom": "5px"}), html.H4(value, style={"fontWeight": "bold", "color": "#111827"}), html.Small("Atualizado", style={"fontSize": "0.7rem", "color": "#9ca3af"})]),
            html.Div(html.I(className=icon_class, style={"fontSize": "1.5rem", "color": "white"}), style={"backgroundColor": color_bg, "width": "48px", "height": "48px", "borderRadius": "12px", "display": "flex", "alignItems": "center", "justifyContent": "center"})
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"})
    ]), style={"border": "none", "borderRadius": "12px", "boxShadow": "0 4px 6px -1px rgba(0,0,0,0.1)"})

# --- LAYOUTS DAS PÁGINAS ---

def serve_resumo_global():
    df_proj = get_projetos()
    opcoes = [{'label': 'Todas as Obras', 'value': 'todos'}] + [{'label': row['nome'], 'value': row['id']} for i, row in df_proj.iterrows()]

    return html.Div([
        dbc.Row([
            dbc.Col(html.H3("Painel de Controle", style={"fontWeight": "bold", "color": "#111827"}), width=8),
            dbc.Col(dcc.Dropdown(id='filtro-global-obra', options=opcoes, value='todos', clearable=False, placeholder="Filtrar por Obra", style={"borderRadius": "8px"}), width=4)
        ], className="mb-4 align-items-center"),

        html.Div(id='conteudo-resumo-global'),

        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("⚠️ Detalhamento de Itens em Atraso"), close_button=True), 
            dbc.ModalBody(id="body-modal-risk"), 
            dbc.ModalFooter(dbc.Button("Fechar", id="btn-close-risk", className="ms-auto", n_clicks=0))
        ], id="modal-risk", size="lg", scrollable=True)
    ])

def serve_projetos():
    df_proj = get_projetos()
    opcoes_obras = [{'label': r['nome'], 'value': r['id']} for i, r in df_proj.iterrows()]
    opcoes_etapas = [{"label": x, "value": x} for x in ["TERRAPLANAGEM", "DRENAGEM", "REDE DE ÁGUA", "REDE DE ESGOTO", "PAVIMENTAÇÃO", "MEIO-FIO / SARJETA", "SINALIZAÇÃO", "ILUMINAÇÃO PÚBLICA", "ADMINISTRAÇÃO"]]
    return html.Div([
        dcc.Store(id="stored-etapa-id", data=None),
        dbc.Row([dbc.Col(html.H2("Gestão de Obras", style={"color": "#111827", "fontWeight": "bold"}), width=8), dbc.Col(dbc.Button("🤝 Gerenciar Permutas", id="btn-open-permuta", color="info", className="w-100", style={"color":"white", "fontWeight": "bold"}), width=4)], className="align-items-center mb-4"),
        dbc.Row([
            dbc.Col(dbc.Card([dbc.CardHeader("🏗️ Cadastrar Nova Obra", style={"fontWeight": "bold"}), dbc.CardBody([dbc.Label("Nome"), dbc.Input(id="input-nova-obra"), dbc.Button("Criar", id="btn-criar-obra", color="primary", className="mt-3 w-100"), html.Div(id="msg-obra", className="mt-2")])], style={"height": "100%"}), width=3),
            dbc.Col(dbc.Card([dbc.CardHeader("📅 Etapas do Cronograma", style={"fontWeight": "bold"}), dbc.CardBody([
                    dbc.Row([dbc.Col([dbc.Label("Obra"), dbc.InputGroup([dbc.Select(id="select-obra", options=opcoes_obras), dbc.Button("🗑", id="btn-ask-delete-obra", color="danger", outline=True)])], width=6), dbc.Col([dbc.Label("Etapa"), dbc.Select(id="select-etapa", options=opcoes_etapas)], width=6)], className="mb-2"), dcc.ConfirmDialog(id='confirm-delete-obra', message='Excluir Obra e Histórico?'),
                    dbc.Row([dbc.Col([dbc.Label("R$"), dbc.Input(id="input-valor", type="number")], width=4), dbc.Col([dbc.Label("%"), dbc.Input(id="input-percent", type="number", min=0, max=100)], width=4), dbc.Col([dbc.Label("Ações"), html.Div([dbc.Button("Salvar", id="btn-salvar-etapa", color="success", className="me-2"), dbc.Button("Del", id="btn-excluir-etapa", color="danger", disabled=True), dbc.Button("Limpar", id="btn-limpar-form", color="secondary", outline=True)], className="d-flex")], width=4)], className="mb-2"),
                    dbc.Row([dbc.Col([dbc.Label("Início"), dbc.Input(id="input-inicio", type="date")], width=6), dbc.Col([dbc.Label("Fim"), dbc.Input(id="input-fim", type="date")], width=6)], className="mb-3"),
                    html.Div(id="msg-etapa", className="mt-2"), html.Hr(), dash_table.DataTable(id='tabela-etapas-crud', columns=[{'name': i, 'id': j} for i,j in [('Etapa','etapa'),('Início','data_inicio'),('Fim','data_fim'),('Valor','valor_estimado'),('%','percentual')]], data=[], row_selectable='single', style_table={'overflowX': 'auto'}, style_header={'backgroundColor': '#f3f4f6', 'fontWeight': 'bold'}, page_size=5)
            ])], style={"height": "100%"}), width=9)
        ]), html.Hr(className="my-4"),
        dbc.Card([dbc.CardHeader([dbc.Row([dbc.Col("Gantt Físico-Financeiro", width=8, className="fw-bold"), dbc.Col(dbc.Button([html.I(className="bi bi-arrows-fullscreen me-2"), "Tela Cheia"], id="btn-gantt-fullscreen", color="secondary", size="sm", outline=True, className="float-end"), width=4)])]), dbc.CardBody([dcc.Loading(html.Div(dcc.Graph(id="grafico-gantt"), style={"overflowX": "auto", "width": "100%"}))])], style={"border": "none", "borderRadius": "12px"}),
        dbc.Modal([dbc.ModalHeader("Visão Geral do Cronograma"), dbc.ModalBody(dcc.Graph(id="grafico-gantt-modal", style={"height": "85vh"})), dbc.ModalFooter(dbc.Button("Fechar", id="btn-close-fullscreen", className="ms-auto"))], id="modal-gantt-fullscreen", fullscreen=True),
        dbc.Modal([dbc.ModalHeader("Cadastrar Permuta"), dbc.ModalBody([dbc.Row([dbc.Col([dbc.Label("Projeto"), dbc.Select(id="modal-permuta-projeto", options=opcoes_obras)], width=12)], className="mb-3"), dbc.Row([dbc.Col([dbc.Label("Descrição"), dbc.Input(id="modal-permuta-desc")], width=12)], className="mb-3"), dbc.Row([dbc.Col([dbc.Label("Valor"), dbc.Input(id="modal-permuta-valor", type="number")], width=6), dbc.Col([dbc.Label("Data"), dbc.Input(id="modal-permuta-data", type="date")], width=6)], className="mb-3"), html.Div(id="msg-permuta-save")]), dbc.ModalFooter([dbc.Button("Fechar", id="btn-close-permuta", className="ms-auto"), dbc.Button("Salvar", id="btn-save-permuta", color="success")])], id="modal-permuta", is_open=False, size="lg")
    ])

def serve_financeiro():
    df_proj = get_projetos()
    opcoes_proj = [{'label': r['nome'], 'value': r['id']} for i, r in df_proj.iterrows()]
    opcoes_filtro = [{'label': 'Todos os Projetos', 'value': 'todos'}] + [{'label': r['nome'], 'value': r['nome']} for i, r in df_proj.iterrows()]
    cats = ["Mat/ Água", "Diesel", "Imprimação", "Emulsão", "Pedra 01", "Frete Emulsão", "Obra Baixa Tensão", "MÃO DE OBRA", "IPITHERM", "Outros"]
    return html.Div([
        dbc.Row([dbc.Col([html.H3("Fluxo de Caixa & Custos", style={"fontWeight": "bold"}), html.P("Orçado vs Realizado", style={"color": "#6b7280"})], width=8), dbc.Col([dbc.Button("➕ Nova Despesa", id="btn-open-modal", color="danger", className="w-100")], width=4)]), html.Hr(),
        dbc.Row([dbc.Col([dbc.Label("Filtrar Projeto:"), dbc.Select(id="filtro-fin", options=opcoes_filtro, value="todos")], width=4)], className="mb-4"),
        dbc.Card([dbc.CardHeader("🔮 Projeção de Caixa Futuro", style={"backgroundColor": "white", "fontWeight": "bold"}), dbc.CardBody([dcc.Loading(dcc.Graph(id="grafico-projecao"))])], style={"border": "none", "borderRadius": "12px", "marginBottom": "20px"}),
        dbc.Card(dbc.CardBody([dcc.Loading(dcc.Graph(id="grafico-financeiro"))]), style={"border": "none", "borderRadius": "12px", "marginBottom": "20px"}),
        dbc.Card([dbc.CardHeader([dbc.Row([dbc.Col(html.H5("📉 Curva ABC"), width=6), dbc.Col(dbc.RadioItems(id="switch-pareto", options=[{"label": "Orçado", "value": "orcado"}, {"label": "Realizado", "value": "realizado"}], value="orcado", inline=True), width=6, className="d-flex justify-content-end")])]), dbc.CardBody([dcc.Loading(dcc.Graph(id="grafico-pareto"))])], style={"border": "none", "borderRadius": "12px"}),
        dbc.Modal([dbc.ModalHeader("Lançar Despesa"), dbc.ModalBody([dbc.Row([dbc.Col([dbc.Label("Projeto"), dbc.Select(id="modal-projeto", options=opcoes_proj)], width=12)], className="mb-3"), dbc.Row([dbc.Col([dbc.Label("Categoria"), dbc.Select(id="modal-categoria", options=[{'label': c, 'value': c} for c in cats])], width=12)], className="mb-3"), dbc.Row([dbc.Col([dbc.Label("Descrição"), dbc.Input(id="modal-desc")], width=12)], className="mb-3"), dbc.Row([dbc.Col([dbc.Label("Valor"), dbc.Input(id="modal-valor", type="number")], width=6), dbc.Col([dbc.Label("Data"), dbc.Input(id="modal-data", type="date")], width=6)], className="mb-3"), html.Div(id="msg-modal-save")]), dbc.ModalFooter([dbc.Button("Cancelar", id="btn-close-modal", className="ms-auto"), dbc.Button("Salvar", id="btn-save-despesa", color="success")])], id="modal-despesa", is_open=False, size="lg")
    ])

def serve_tabelas():
    df_proj = get_projetos()
    opcoes_proj = [{'label': r['nome'], 'value': r['id']} for i, r in df_proj.iterrows()]
    cats = ["Mat/ Água", "Diesel", "Imprimação", "Emulsão", "Pedra 01", "Frete Emulsão", "Obra Baixa Tensão", "MÃO DE OBRA", "IPITHERM", "Outros"]
    return html.Div([
        dcc.Store(id="stored-despesa-id", data=None), dcc.Store(id="stored-permuta-id", data=None),
        html.H2("Gerenciamento Detalhado", style={"color": "#111827", "fontWeight": "bold", "marginBottom": "20px"}),
        dbc.Card([dbc.CardHeader("📋 Gerenciar Despesas", style={"fontWeight": "bold"}), dbc.CardBody([
                dbc.Row([dbc.Col([dbc.Label("Projeto"), dbc.Select(id="input-desp-projeto", options=opcoes_proj)], width=3), dbc.Col([dbc.Label("Categoria"), dbc.Select(id="input-desp-cat", options=[{'label': c, 'value': c} for c in cats])], width=3), dbc.Col([dbc.Label("Descrição"), dbc.Input(id="input-desp-desc")], width=4), dbc.Col([dbc.Label("Status"), dbc.Select(id="input-desp-status", options=[{'label': 'Pago', 'value': 'Pago'}, {'label': 'Pendente', 'value': 'Pendente'}], value='Pago')], width=2)], className="mb-2"),
                dbc.Row([dbc.Col([dbc.Label("Valor"), dbc.Input(id="input-desp-valor", type="number")], width=3), dbc.Col([dbc.Label("Data"), dbc.Input(id="input-desp-data", type="date")], width=3), dbc.Col([dbc.Label("Ações"), html.Div([dbc.Button("Salvar", id="btn-save-desp-crud", color="success", className="me-2"), dbc.Button("Del", id="btn-del-desp-crud", color="danger", className="me-2", disabled=True), dbc.Button("Limpar", id="btn-clean-desp-crud", color="secondary", outline=True)], className="d-flex")], width=6)], className="mb-3"),
                html.Div(id="msg-desp-crud"), html.Hr(), dash_table.DataTable(id='tabela-despesas-crud', columns=[{'name': i, 'id': j} for i,j in [('Projeto','projeto'),('Categoria','categoria'),('Descrição','descricao'),('Valor','valor'),('Data','data_pagamento'),('Status','status')]], data=[], row_selectable='single', page_size=10, style_table={'overflowX': 'auto'}), html.Div(dbc.Button("📥 Exportar Excel", id="btn-xls-despesas", color="success", size="sm", className="mt-2"))
        ])], className="mb-5"),
        dbc.Card([dbc.CardHeader("🤝 Gerenciar Permutas", style={"fontWeight": "bold"}), dbc.CardBody([
                dbc.Row([dbc.Col([dbc.Label("Projeto"), dbc.Select(id="input-perm-projeto", options=opcoes_proj)], width=4), dbc.Col([dbc.Label("Descrição"), dbc.Input(id="input-perm-desc")], width=8)], className="mb-2"),
                dbc.Row([dbc.Col([dbc.Label("Valor"), dbc.Input(id="input-perm-valor", type="number")], width=4), dbc.Col([dbc.Label("Data"), dbc.Input(id="input-perm-data", type="date")], width=4), dbc.Col([dbc.Label("Ações"), html.Div([dbc.Button("Salvar", id="btn-save-perm-crud", color="success", className="me-2"), dbc.Button("Del", id="btn-del-perm-crud", color="danger", className="me-2", disabled=True), dbc.Button("Limpar", id="btn-clean-perm-crud", color="secondary", outline=True)], className="d-flex")], width=4)], className="mb-3"),
                html.Div(id="msg-perm-crud"), html.Hr(), dash_table.DataTable(id='tabela-permutas-crud', columns=[{'name': i, 'id': j} for i,j in [('Projeto','projeto'),('Descrição','descricao'),('Valor','valor'),('Data','data_permuta')]], data=[], row_selectable='single', page_size=10, style_table={'overflowX': 'auto'}), html.Div(dbc.Button("📥 Exportar Excel", id="btn-xls-permutas", color="success", size="sm", className="mt-2"))
        ])]), dcc.Download(id="download-despesas"), dcc.Download(id="download-permutas")
    ])

# --- 5. CALLBACKS ---

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page(path):
    if path == "/financeiro": return serve_financeiro()
    elif path == "/projetos": return serve_projetos()
    elif path == "/tabelas": return serve_tabelas()
    return serve_resumo_global()

# --- ATUALIZAÇÃO DO PAINEL GLOBAL ---
@app.callback(
    Output('conteudo-resumo-global', 'children'),
    Input('filtro-global-obra', 'value')
)
def update_resumo_global_content(filtro_id):
    # 1. KPIs
    tot_contratado, tot_permuta, tot_pago_em_dinheiro, saldo, atraso, perc_fisico, perc_financeiro = get_kpis_globais(filtro_id)
    fmt = lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # 2. Tabela Resumo
    df_resumo = get_tabela_resumo_financeiro()
    if filtro_id and filtro_id != 'todos':
        df_resumo = df_resumo[df_resumo['id'] == int(filtro_id)]

    table_rows = []
    for index, row in df_resumo.iterrows():
        color_bar = "success" if row['perc_pago'] >= 90 else "primary"
        table_rows.append(html.Tr([
            html.Td(html.B(row['nome'])), 
            html.Td(row.get('empresa', 'Própria'), style={"color": "#6b7280"}),
            html.Td(fmt(row['vl_contrato'])), 
            html.Td(fmt(row['vl_pago'] + row['vl_permuta']), style={"color": "#10b981", "fontWeight": "bold"}),
            html.Td(fmt(row['saldo']), style={"color": "#ef4444"}),
            html.Td([html.Div(f"{row['perc_pago']:.1f}%", style={"fontSize": "12px", "marginBottom": "2px"}), dbc.Progress(value=row['perc_pago'], color=color_bar, style={"height": "8px"}, className="mb-0")], style={"width": "150px", "verticalAlign": "middle"})
        ]))
    if len(df_resumo) > 0:
        table_rows.append(html.Tr([html.Td("TOTAIS", colSpan=2, style={"textAlign": "right", "fontWeight": "bold"}), html.Td(html.B(fmt(df_resumo['vl_contrato'].sum()))), html.Td(html.B(fmt(df_resumo['vl_pago'].sum() + df_resumo['vl_permuta'].sum())), style={"color": "#10b981"}), html.Td(html.B(fmt(df_resumo['saldo'].sum())), style={"color": "#ef4444"}), html.Td("")], style={"backgroundColor": "#f9fafb"}))

    # 3. Gráficos
    # A) Gráfico Descompasso
    fig_descompasso = gerar_grafico_descompasso(perc_fisico, perc_financeiro)
    
    # B) Gráfico Tendência (Histórico)
    df_hist = get_dados_historico_tendencia(filtro_id)
    if not df_hist.empty:
        fig_trend = px.line(df_hist, x='data_registro', y='percentual_novo', color='projeto', title="Evolução Física Registrada (Tendência)", template="plotly_white", markers=True)
        graph_trend = dcc.Graph(figure=fig_trend, config={'displayModeBar': False}, style={"height": "300px"})
    else:
        graph_trend = html.Div("Sem histórico de evolução registrado.", className="text-center text-muted p-4")

    # C) Gráfico Pareto (Custos)
    df_pareto = get_dados_pareto_resumo(filtro_id)
    if not df_pareto.empty:
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(x=df_pareto['categoria'], y=df_pareto['valor'], name='Valor (R$)', marker_color='#2563eb', text=df_pareto['valor'].apply(lambda x: f"R$ {x:,.0f}".replace(",", ".")), textposition='auto'))
        fig_pareto.add_trace(go.Scatter(x=df_pareto['categoria'], y=df_pareto['acum'], name='% Acumulado', yaxis='y2', mode='lines+markers', line=dict(color='#ef4444', width=3)))
        fig_pareto.update_layout(title="<b>Composição de Custos (Pareto)</b>", template="plotly_white", legend=dict(orientation="h", y=1.1), yaxis=dict(title="R$"), yaxis2=dict(title="%", overlaying='y', side='right', range=[0, 110], showgrid=False), height=300, margin=dict(l=20, r=20, t=50, b=20))
        graph_pareto = dcc.Graph(figure=fig_pareto, config={'displayModeBar': False})
    else:
        graph_pareto = html.Div("Sem dados financeiros.", className="text-center text-muted p-4")

    # --- LAYOUT FINAL ---
    return html.Div([
        # KPIs
        dbc.Row([
            dbc.Col(create_kpi_card("Carteira Contratada", fmt(tot_contratado), "bi bi-currency-dollar", "#3b82f6"), width=12, md=6, lg=3),
            dbc.Col(create_kpi_card("Total Pago + Permuta", fmt(tot_pago_em_dinheiro + tot_permuta), "bi bi-check-lg", "#10b981"), width=12, md=6, lg=3),
            dbc.Col(create_kpi_card("Saldo a Pagar", fmt(saldo), "bi bi-wallet2", "#8b5cf6"), width=12, md=6, lg=3),
            # Correção do ID do botão de Risco
            dbc.Col(html.Div(create_kpi_card("Risco / Atraso", fmt(atraso), "bi bi-exclamation-circle", "#ef4444"), id={'type': 'btn-open-risk', 'index': 0}, n_clicks=0, style={"cursor": "pointer"}), width=12, md=6, lg=3),
        ], className="mb-4"),

        # LINHA DE INTELIGÊNCIA (Descompasso + Tendência)
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_descompasso, config={'displayModeBar': False}, style={"height": "250px"})), style={"border": "none", "borderRadius": "12px", "boxShadow": "0 4px 6px -1px rgba(0,0,0,0.1)"}), width=12, lg=4, className="mb-4"),
            dbc.Col(dbc.Card(dbc.CardBody(graph_trend), style={"border": "none", "borderRadius": "12px", "boxShadow": "0 4px 6px -1px rgba(0,0,0,0.1)"}), width=12, lg=8, className="mb-4")
        ]),

        # TABELA GERAL
        dbc.Card([dbc.CardHeader("📊 Status Financeiro Detalhado", style={"backgroundColor": "white", "fontWeight": "bold"}), dbc.CardBody(dbc.Table([html.Thead(html.Tr([html.Th("Empreendimento"), html.Th("Empresa"), html.Th("Vl. Contrato"), html.Th("Vl. Pago"), html.Th("Saldo Devedor"), html.Th("% Pago")])), html.Tbody(table_rows)], hover=True, responsive=True))], style={"border": "none", "borderRadius": "12px", "boxShadow": "0 4px 6px -1px rgba(0,0,0,0.1)", "marginBottom": "20px"}),

        # PARETO
        dbc.Card(dbc.CardBody(graph_pareto), style={"border": "none", "borderRadius": "12px", "boxShadow": "0 4px 6px -1px rgba(0,0,0,0.1)", "marginBottom": "20px"})
    ])

# --- CRUD E AÇÕES ---

@app.callback(Output("msg-obra", "children"), Input("btn-criar-obra", "n_clicks"), State("input-nova-obra", "value"), prevent_initial_call=True)
def criar_obra(n, nome):
    if not nome: return dbc.Alert("Erro", color="danger")
    with engine.connect() as conn: conn.execute(text("INSERT INTO projetos (nome) VALUES (:n)"), {"n": nome}); conn.commit()
    return dbc.Alert("Obra Criada!", color="success")

@app.callback(Output("confirm-delete-obra", "displayed"), Input("btn-ask-delete-obra", "n_clicks"), prevent_initial_call=True)
def show_delete_confirm(n): return True

@app.callback([Output("url", "pathname", allow_duplicate=True), Output("msg-obra", "children", allow_duplicate=True)], Input("confirm-delete-obra", "submit_n_clicks"), State("select-obra", "value"), prevent_initial_call=True)
def excluir_obra_completa(submit_n_clicks, obra_id):
    if not obra_id: return dash.no_update, dbc.Alert("Selecione!", color="warning")
    try:
        with engine.connect() as conn:
            for t in ["historico_fisico", "cronograma_etapas", "despesas", "permutas", "projetos"]:
                id_col = 'id' if t == 'projetos' else 'projeto_id'
                if t == 'historico_fisico': # Historico não tem projeto_id direto, apaga via cascade ou subquery, mas aqui garantimos limpeza
                    pass # O DB cascade cuida, ou limpamos via etapa
                else:
                    conn.execute(text(f"DELETE FROM {t} WHERE {id_col} = :id"), {"id": obra_id})
            conn.commit()
        return "/projetos", dbc.Alert("Excluído!", color="success")
    except Exception as e: return dash.no_update, dbc.Alert(f"Erro: {e}", color="danger")

# --- CALLBACK DE SALVAMENTO DE ETAPA COM HISTÓRICO ---
@app.callback(
    [Output("msg-etapa", "children"), Output("input-valor", "value"), Output("input-percent", "value"), Output("input-inicio", "value"), Output("input-fim", "value"), Output("select-etapa", "value"), Output("stored-etapa-id", "data"), Output("btn-excluir-etapa", "disabled"), Output("tabela-etapas-crud", "selected_rows"), Output("select-obra", "value")],
    [Input("btn-salvar-etapa", "n_clicks"), Input("btn-excluir-etapa", "n_clicks"), Input("btn-limpar-form", "n_clicks"), Input("tabela-etapas-crud", "selected_rows"), Input("grafico-gantt", "clickData")], 
    [State("select-obra", "value"), State("select-etapa", "value"), State("input-valor", "value"), State("input-percent", "value"), State("input-inicio", "value"), State("input-fim", "value"), State("stored-etapa-id", "data"), State("tabela-etapas-crud", "data")]
)
def manage_stage_crud(n_save, n_del, n_clean, selected_rows, clickData, obra_id, etapa, val, perc, ini, fim, current_id, table_data):
    ctx = callback_context
    trig = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ""
    
    if trig == "grafico-gantt" and clickData:
        try:
            cdata = clickData['points'][0]['customdata']
            return "", cdata[1], cdata[2], cdata[3], cdata[4], cdata[5], cdata[0], False, dash.no_update, cdata[6]
        except: pass
        
    if trig == "tabela-etapas-crud" and selected_rows:
        if table_data and selected_rows[0] < len(table_data):
            row = table_data[selected_rows[0]]
            return "", row['valor_estimado'], row['percentual'], row['data_inicio'], row['data_fim'], row['etapa'], row['id_etapa'], False, dash.no_update, row['projeto_id']
            
    if trig == "btn-limpar-form": return "", "", "", "", "", None, None, True, [], None
    
    if trig == "btn-excluir-etapa" and current_id:
        with engine.connect() as conn: conn.execute(text("DELETE FROM cronograma_etapas WHERE id = :id"), {"id": current_id}); conn.commit()
        return dbc.Alert("Excluído!", color="warning"), "", "", "", "", None, None, True, [], dash.no_update
        
    if trig == "btn-salvar-etapa":
        if not all([obra_id, etapa, ini, fim]): return dbc.Alert("Preencha!", color="warning"), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, current_id, (current_id is None), dash.no_update, dash.no_update
        
        val, perc = val or 0, perc or 0
        with engine.connect() as conn:
            if current_id: 
                conn.execute(text("UPDATE cronograma_etapas SET etapa=:e, data_inicio=:i, data_fim=:f, valor_estimado=:v, percentual=:p, projeto_id=:pid WHERE id=:id"), {"e": etapa, "i": ini, "f": fim, "v": val, "p": perc, "id": current_id, "pid": obra_id})
                # REGISTRA HISTÓRICO (UPDATE)
                conn.execute(text("INSERT INTO historico_fisico (etapa_id, data_registro, percentual_novo) VALUES (:eid, CURRENT_DATE, :p)"), {"eid": current_id, "p": perc})
            else: 
                # REGISTRA NOVO E HISTÓRICO
                res = conn.execute(text("INSERT INTO cronograma_etapas (projeto_id, etapa, data_inicio, data_fim, valor_estimado, percentual) VALUES (:pid, :e, :i, :f, :v, :p) RETURNING id"), {"pid": obra_id, "e": etapa, "i": ini, "f": fim, "v": val, "p": perc})
                new_id = res.fetchone()[0]
                conn.execute(text("INSERT INTO historico_fisico (etapa_id, data_registro, percentual_novo) VALUES (:eid, CURRENT_DATE, :p)"), {"eid": new_id, "p": perc})
            conn.commit()
        return dbc.Alert("Salvo e Registrado!", color="success"), "", "", "", "", None, None, True, [], dash.no_update
        
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, True, dash.no_update, dash.no_update

@app.callback([Output("grafico-gantt", "figure"), Output("tabela-etapas-crud", "data"), Output("select-obra", "options")], [Input("url", "pathname"), Input("msg-etapa", "children"), Input("msg-obra", "children"), Input("select-obra", "value")])
def update_view_projetos(path, msg_etapa, msg_obra, obra_id):
    df_proj = get_projetos()
    opts = [{'label': r['nome'], 'value': r['id']} for i, r in df_proj.iterrows()]
    tabela_data = []
    if obra_id:
        df_crono = get_cronograma()
        if not df_crono.empty:
            df_filtered = df_crono[df_crono['projeto_id'] == int(obra_id)].copy()
            df_filtered['data_inicio'] = pd.to_datetime(df_filtered['data_inicio']).dt.strftime('%Y-%m-%d')
            df_filtered['data_fim'] = pd.to_datetime(df_filtered['data_fim']).dt.strftime('%Y-%m-%d')
            tabela_data = df_filtered.to_dict('records')
    return gerar_figura_gantt(obra_id), tabela_data, opts

@app.callback([Output("modal-gantt-fullscreen", "is_open"), Output("grafico-gantt-modal", "figure")], [Input("btn-gantt-fullscreen", "n_clicks"), Input("btn-close-fullscreen", "n_clicks")], [State("modal-gantt-fullscreen", "is_open"), State("select-obra", "value")])
def toggle_fullscreen_gantt(n_open, n_close, is_open, obra_id):
    ctx = callback_context
    if not ctx.triggered: return is_open, dash.no_update
    btn = ctx.triggered[0]['prop_id'].split('.')[0]
    if btn == "btn-gantt-fullscreen": return True, gerar_figura_gantt(obra_id)
    return False, dash.no_update

@app.callback(Output("modal-permuta", "is_open"), [Input("btn-open-permuta", "n_clicks"), Input("btn-close-permuta", "n_clicks"), Input("btn-save-permuta", "n_clicks")], [State("modal-permuta", "is_open"), State("msg-permuta-save", "children")])
def toggle_permuta(n1, n2, n3, is_open, msg):
    ctx = callback_context
    if not ctx.triggered: return is_open
    if ctx.triggered[0]['prop_id'].split('.')[0] == "btn-save-permuta" and msg and "success" in str(msg): return False
    return not is_open

@app.callback(Output("msg-permuta-save", "children"), Input("btn-save-permuta", "n_clicks"), [State("modal-permuta-projeto", "value"), State("modal-permuta-desc", "value"), State("modal-permuta-valor", "value"), State("modal-permuta-data", "value")], prevent_initial_call=True)
def salvar_permuta(n, proj, desc, val, dt):
    if not all([proj, val, dt]): return dbc.Alert("Preencha!", color="warning")
    with engine.connect() as conn: conn.execute(text("INSERT INTO permutas (projeto_id, descricao, valor, data_permuta) VALUES (:p, :d, :v, :dt)"), {"p": proj, "d": desc or "", "v": val, "dt": dt}); conn.commit()
    return dbc.Alert("Sucesso!", color="success")

@app.callback(Output("modal-despesa", "is_open"), [Input("btn-open-modal", "n_clicks"), Input("btn-close-modal", "n_clicks"), Input("btn-save-despesa", "n_clicks")], [State("modal-despesa", "is_open"), State("msg-modal-save", "children")])
def toggle_despesa(n1, n2, n3, is_open, msg):
    ctx = callback_context
    if not ctx.triggered: return is_open
    if ctx.triggered[0]['prop_id'].split('.')[0] == "btn-save-despesa" and msg and "success" in str(msg): return False
    return not is_open

@app.callback(Output("msg-modal-save", "children"), Input("btn-save-despesa", "n_clicks"), [State("modal-projeto", "value"), State("modal-categoria", "value"), State("modal-desc", "value"), State("modal-valor", "value"), State("modal-data", "value")], prevent_initial_call=True)
def salvar_despesa(n, proj, cat, desc, val, dt):
    if not all([proj, cat, val, dt]): return dbc.Alert("Preencha!", color="warning")
    with engine.connect() as conn: conn.execute(text("INSERT INTO despesas (projeto_id, categoria, descricao, valor, data_pagamento) VALUES (:p, :c, :d, :v, :t)"), {"p": proj, "c": cat, "d": desc or "", "v": val, "dt": dt}); conn.commit()
    return dbc.Alert("Sucesso!", color="success")

@app.callback(Output("grafico-financeiro", "figure"), [Input("filtro-fin", "value"), Input("btn-save-despesa", "n_clicks")])
def update_graph(filtro, n):
    df = calcular_orcado_vs_realizado()
    if df.empty: return px.bar(title="Sem dados suficientes", template="plotly_white")
    if filtro and filtro != 'todos': df = df[df['projeto'] == filtro]
    df_tot = df.groupby('data_ref')[['valor_orcado', 'valor_realizado']].sum().reset_index().sort_values('data_ref')
    df_tot['acum_orcado'] = df_tot['valor_orcado'].cumsum()
    df_tot['acum_realizado'] = df_tot['valor_realizado'].cumsum()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_tot['data_ref'], y=df_tot['valor_realizado'], name='Desembolso', marker_color='rgba(16, 185, 129, 0.3)'))
    fig.add_trace(go.Scatter(x=df_tot['data_ref'], y=df_tot['acum_orcado'], name='Planejado', mode='lines+markers', line=dict(color='#3b82f6', width=3, dash='dot')))
    fig.add_trace(go.Scatter(x=df_tot['data_ref'], y=df_tot['acum_realizado'], name='Realizado', mode='lines+markers', line=dict(color='#10b981', width=4), fill='tozeroy'))
    fig.update_layout(title="Curva S & Fluxo de Caixa", template="plotly_white", hovermode="x unified", legend=dict(orientation="h", y=1.02), yaxis=dict(title="R$"))
    return fig

@app.callback(Output("grafico-pareto", "figure"), [Input("filtro-fin", "value"), Input("btn-save-despesa", "n_clicks"), Input("switch-pareto", "value")])
def update_pareto(filtro, n, modo_visao):
    if modo_visao == "orcado": df, col_v, col_c, tit, color = get_cronograma(), "valor_estimado", "etapa", "Valor Orçado", "#94a3b8"
    else: df, col_v, col_c, tit, color = get_despesas_realizadas(), "valor", "categoria", "Valor Pago", "#3b82f6"
    if df.empty: return px.bar(title="Sem dados", template="plotly_white")
    if filtro and filtro != 'todos': df = df[df['projeto'] == filtro]
    if df.empty: return px.bar(title="Sem dados para este filtro", template="plotly_white")
    df_cat = df.groupby(col_c)[col_v].sum().reset_index().sort_values(by=col_v, ascending=False)
    df_cat['perc_acumulado'] = (df_cat[col_v].cumsum() / df_cat[col_v].sum()) * 100
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_cat[col_c], y=df_cat[col_v], name=tit, marker_color=color))
    fig.add_trace(go.Scatter(x=df_cat[col_c], y=df_cat['perc_acumulado'], name='% Acumulada', yaxis='y2', mode='lines+markers', line=dict(color='#ef4444')))
    fig.update_layout(template="plotly_white", title=f"Curva ABC ({'Orçamento' if modo_visao == 'orcado' else 'Realizado'})", yaxis=dict(title="R$"), yaxis2=dict(title="%", overlaying='y', side='right', range=[0, 110], showgrid=False), legend=dict(orientation='h', y=1.1))
    return fig

@app.callback(Output("download-despesas", "data"), Input("btn-xls-despesas", "n_clicks"), prevent_initial_call=True)
def export_despesas(n): return dcc.send_data_frame(get_despesas_realizadas().to_excel, "relatorio_despesas.xlsx", index=False)

@app.callback(Output("download-permutas", "data"), Input("btn-xls-permutas", "n_clicks"), prevent_initial_call=True)
def export_permutas(n): return dcc.send_data_frame(get_permutas().to_excel, "relatorio_permutas.xlsx", index=False)

@app.callback(Output("grafico-projecao", "figure"), [Input("filtro-fin", "value")])
def update_projecao_chart(filtro):
    df_fut = calcular_projecao_futura()
    if df_fut.empty: return px.bar(title="Sem projeção futura", template="plotly_white")
    if filtro and filtro != 'todos': df_fut = df_fut[df_fut['Projeto'] == filtro]
    if df_fut.empty: return px.bar(title="Sem projeção para este filtro", template="plotly_white")
    fig = px.bar(df_fut, x='Data', y='Valor Projetado', color='Projeto', title="Fluxo de Caixa Projetado", template="plotly_white")
    fig.update_traces(marker_line_width=0)
    return fig

@app.callback([Output("msg-desp-crud", "children"), Output("input-desp-projeto", "value"), Output("input-desp-cat", "value"), Output("input-desp-desc", "value"), Output("input-desp-status", "value"), Output("input-desp-valor", "value"), Output("input-desp-data", "value"), Output("stored-despesa-id", "data"), Output("btn-del-desp-crud", "disabled"), Output("tabela-despesas-crud", "data"), Output("tabela-despesas-crud", "selected_rows")], [Input("btn-save-desp-crud", "n_clicks"), Input("btn-del-desp-crud", "n_clicks"), Input("btn-clean-desp-crud", "n_clicks"), Input("tabela-despesas-crud", "selected_rows"), Input("url", "pathname")], [State("input-desp-projeto", "value"), State("input-desp-cat", "value"), State("input-desp-desc", "value"), State("input-desp-status", "value"), State("input-desp-valor", "value"), State("input-desp-data", "value"), State("stored-despesa-id", "data"), State("tabela-despesas-crud", "data")])
def manage_despesas_crud(n_save, n_del, n_clean, selected, path, proj, cat, desc, status, val, dt, curr_id, table_data):
    ctx = callback_context
    trig = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else "url"
    reload_data = lambda: get_despesas_realizadas().to_dict('records')
    if trig == "url" or trig == "btn-clean-desp-crud": return "", "", "", "", "Pago", "", "", None, True, reload_data(), []
    if trig == "tabela-despesas-crud" and selected:
        row = table_data[selected[0]]
        return "", row['projeto_id'], row['categoria'], row['descricao'], row['status'], row['valor'], row['data_pagamento'], row['id'], False, dash.no_update, dash.no_update
    if trig == "btn-del-desp-crud" and curr_id:
        with engine.connect() as conn: conn.execute(text("DELETE FROM despesas WHERE id = :id"), {"id": curr_id}); conn.commit()
        return dbc.Alert("Excluído!", color="warning"), "", "", "", "Pago", "", "", None, True, reload_data(), []
    if trig == "btn-save-desp-crud":
        if not all([proj, cat, val, dt]): return dbc.Alert("Preencha!", color="warning"), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, curr_id, (curr_id is None), dash.no_update, dash.no_update
        with engine.connect() as conn:
            if curr_id: conn.execute(text("UPDATE despesas SET projeto_id=:p, categoria=:c, descricao=:d, valor=:v, data_pagamento=:dt, status=:s WHERE id=:id"), {"p": proj, "c": cat, "d": desc or "", "v": val, "dt": dt, "s": status, "id": curr_id})
            else: conn.execute(text("INSERT INTO despesas (projeto_id, categoria, descricao, valor, data_pagamento, status) VALUES (:p, :c, :d, :v, :dt, :s)"), {"p": proj, "c": cat, "d": desc or "", "v": val, "dt": dt, "s": status})
            conn.commit()
        return dbc.Alert("Salvo!", color="success"), "", "", "", "Pago", "", "", None, True, reload_data(), []
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, True, dash.no_update, dash.no_update

@app.callback([Output("msg-perm-crud", "children"), Output("input-perm-projeto", "value"), Output("input-perm-desc", "value"), Output("input-perm-valor", "value"), Output("input-perm-data", "value"), Output("stored-permuta-id", "data"), Output("btn-del-perm-crud", "disabled"), Output("tabela-permutas-crud", "data"), Output("tabela-permutas-crud", "selected_rows")], [Input("btn-save-perm-crud", "n_clicks"), Input("btn-del-perm-crud", "n_clicks"), Input("btn-clean-perm-crud", "n_clicks"), Input("tabela-permutas-crud", "selected_rows"), Input("url", "pathname")], [State("input-perm-projeto", "value"), State("input-perm-desc", "value"), State("input-perm-valor", "value"), State("input-perm-data", "value"), State("stored-permuta-id", "data"), State("tabela-permutas-crud", "data")])
def manage_permutas_crud(n_save, n_del, n_clean, selected, path, proj, desc, val, dt, curr_id, table_data):
    ctx = callback_context
    trig = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else "url"
    reload_data = lambda: get_permutas().to_dict('records')
    if trig == "url" or trig == "btn-clean-perm-crud": return "", "", "", "", "", None, True, reload_data(), []
    if trig == "tabela-permutas-crud" and selected:
        row = table_data[selected[0]]
        return "", row['projeto_id'], row['descricao'], row['valor'], row['data_permuta'], row['id'], False, dash.no_update, dash.no_update
    if trig == "btn-del-perm-crud" and curr_id:
        with engine.connect() as conn: conn.execute(text("DELETE FROM permutas WHERE id = :id"), {"id": curr_id}); conn.commit()
        return dbc.Alert("Excluído!", color="warning"), "", "", "", "", None, True, reload_data(), []
    if trig == "btn-save-perm-crud":
        if not all([proj, val, dt]): return dbc.Alert("Preencha!", color="warning"), dash.no_update, dash.no_update, dash.no_update, dash.no_update, curr_id, (curr_id is None), dash.no_update, dash.no_update
        with engine.connect() as conn:
            if curr_id: conn.execute(text("UPDATE permutas SET projeto_id=:p, descricao=:d, valor=:v, data_permuta=:dt WHERE id=:id"), {"p": proj, "d": desc or "", "v": val, "dt": dt, "id": curr_id})
            else: conn.execute(text("INSERT INTO permutas (projeto_id, descricao, valor, data_permuta) VALUES (:p, :d, :v, :dt)"), {"p": proj, "d": desc or "", "v": val, "dt": dt})
            conn.commit()
        return dbc.Alert("Salvo!", color="success"), "", "", "", "", None, True, reload_data(), []
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, True, dash.no_update, dash.no_update

# --- CALLBACK DE RISCO (CORRIGIDO COM PATTERN MATCHING) ---
@app.callback(
    [Output("modal-risk", "is_open"), Output("body-modal-risk", "children")],
    [Input({'type': 'btn-open-risk', 'index': ALL}, "n_clicks"), Input("btn-close-risk", "n_clicks")],
    [State("modal-risk", "is_open")]
)
def toggle_risk_modal(n_open_list, n_close, is_open):
    ctx = callback_context
    if not ctx.triggered: return is_open, dash.no_update
    
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trig_id == "btn-close-risk": return False, dash.no_update
    
    # Se clicou no botão de abrir (que pode ser dinâmico)
    if n_open_list and any(n_open_list):
        df = get_detalhes_atraso()
        if df.empty: return True, dbc.Alert("Nenhuma etapa em atraso.", color="success")
        return True, dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)
        
    return is_open, dash.no_update

if __name__ == "__main__":
    app.run(debug=True)