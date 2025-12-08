from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import pandas as pd 

# --- 1. CONFIGURAÇÃO DO BANCO (SQLite) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./engmanager.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODELOS (Tabelas do Banco) ---
class ObraDB(Base):
    __tablename__ = "obras"
    id = Column(Integer, primary_key=True, index=True)
    empreendimento = Column(String)
    fornecedor = Column(String)
    servico = Column(String)
    valor_total = Column(Float)
    valor_pago = Column(Float)
    status = Column(String)
    data_inicio = Column(String)
    data_fim = Column(String)
    prazo_execucao_meses = Column(Integer, default=1)
    orcamento_projetado = Column(Float, default=0.0)

class FinanceiroDB(Base):
    __tablename__ = "financeiro"
    id = Column(Integer, primary_key=True, index=True)
    obra_id = Column(Integer, ForeignKey("obras.id"), nullable=True)
    empreendimento = Column(String)
    tipo = Column(String) # 'entrada' ou 'saida'
    categoria = Column(String)
    descricao = Column(String)
    valor = Column(Float)
    data_vencimento = Column(String) # YYYY-MM-DD
    status = Column(String) # 'Pendente', 'Pago', 'Atrasado'

class OrcamentoDB(Base):
    __tablename__ = "orcamento_projetado"
    id = Column(Integer, primary_key=True, index=True)
    empreendimento = Column(String)
    mes_ano = Column(String) # YYYY-MM
    valor_orcado = Column(Float)
    
class AvancoDB(Base):
    __tablename__ = "avancos"
    id = Column(Integer, primary_key=True, index=True)
    empreendimento = Column(String)
    atividade = Column(String) # DRENAGEM, PAVIMENTAÇÃO, etc.
    mes_ano = Column(String) # YYYY-MM
    percentual_avanco = Column(Float) # % de 0.0 a 100.0


Base.metadata.create_all(bind=engine)

# --- 3. ESQUEMAS Pydantic ---
class ObraCreate(BaseModel):
    empreendimento: str
    fornecedor: str
    servico: str
    valor_total: float
    valor_pago: float = 0.0
    status: str
    data_inicio: str
    data_fim: str # Mantido como str, mas pode ser vazio
    prazo_execucao_meses: int
    orcamento_projetado: float = 0.0

class ObraUpdate(BaseModel): # Tornando todos os campos opcionais para o PUT
    empreendimento: Optional[str] = None
    fornecedor: Optional[str] = None
    servico: Optional[str] = None
    valor_total: Optional[float] = None
    valor_pago: Optional[float] = None
    status: Optional[str] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None 
    prazo_execucao_meses: Optional[int] = None
    orcamento_projetado: Optional[float] = None

class FinanceiroCreate(BaseModel):
    obra_id: Optional[int] = None
    empreendimento: str
    tipo: str
    categoria: str
    descricao: str
    valor: float
    data_vencimento: str
    status: str

class FinanceiroUpdate(FinanceiroCreate):
    pass
    
class OrcamentoCreate(BaseModel):
    empreendimento: str
    mes_ano: str
    valor_orcado: float

class AvancoCreate(BaseModel):
    empreendimento: str
    atividade: str
    mes_ano: str
    percentual_avanco: float

# NOVO SCHEMA SIMPLIFICADO
class ProgressoSimples(BaseModel):
    empreendimento: str
    valor_total: float
    valor_pago: float
    percentual_progresso: float


# --- FUNÇÃO DE UTILIDADE PARA DATAS ---
def get_meses_para_rateio(data_inicio_str, num_meses):
    """Gera uma lista de strings YYYY-MM a partir da data de início para N meses."""
    try:
        current_date = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
    except ValueError:
        return []

    meses = []
    for _ in range(num_meses):
        meses.append(current_date.strftime('%Y-%m'))
        current_date += relativedelta(months=1)
    
    return meses

# --- 4. CONFIGURAÇÃO DO FASTAPI E CORS ---
app = FastAPI(title="EngManager API", description="API para Gestão de Engenharia e Obras")

origins = [
    "http://localhost:5173",
    "https://anielloheronville.github.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependência do Banco de Dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 5. ROTAS DE CADASTRO (CRUD) ---

# --- CRUD OBRA ---
@app.post("/obras/", response_model=ObraCreate)
def create_obra(obra: ObraCreate, db: Session = Depends(get_db)):
    db_obra = ObraDB(**obra.dict())
    db.add(db_obra)
    db.commit()
    db.refresh(db_obra)
    return db_obra

@app.get("/obras/", response_model=List[ObraCreate])
def read_obras(db: Session = Depends(get_db)):
    return db.query(ObraDB).all()

@app.get("/obras/{obra_id}")
def read_obra(obra_id: int, db: Session = Depends(get_db)):
    db_obra = db.query(ObraDB).filter(ObraDB.id == obra_id).first()
    if db_obra is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    return db_obra

@app.put("/obras/{obra_id}", response_model=ObraCreate)
def update_obra(obra_id: int, obra: ObraUpdate, db: Session = Depends(get_db)):
    db_obra = db.query(ObraDB).filter(ObraDB.id == obra_id).first()
    if db_obra is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    
    # Melhoria de robustez: usa exclude_unset=True para ignorar campos não fornecidos
    for key, value in obra.dict(exclude_unset=True).items():
        setattr(db_obra, key, value)
        
    db.commit()
    db.refresh(db_obra)
    return db_obra

@app.delete("/obras/{obra_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_obra(obra_id: int, db: Session = Depends(get_db)):
    db_obra = db.query(ObraDB).filter(ObraDB.id == obra_id).first()
    if db_obra is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
        
    db.delete(db_obra)
    db.commit()
    return

# --- CRUD FINANCEIRO ---
@app.post("/financeiro/", response_model=FinanceiroCreate)
def create_lancamento(lancamento: FinanceiroCreate, db: Session = Depends(get_db)):
    db_lancamento = FinanceiroDB(**lancamento.dict())
    db.add(db_lancamento)
    db.commit()
    db.refresh(db_lancamento)
    return db_lancamento

@app.get("/financeiro/", response_model=List[FinanceiroCreate])
def read_lancamentos(db: Session = Depends(get_db)):
    return db.query(FinanceiroDB).all()

@app.get("/financeiro/obra/{obra_id}", response_model=List[FinanceiroCreate])
def read_lancamentos_by_obra(obra_id: int, db: Session = Depends(get_db)):
    lancamentos = db.query(FinanceiroDB).filter(FinanceiroDB.obra_id == obra_id).all()
    return lancamentos

@app.put("/financeiro/{lancamento_id}", response_model=FinanceiroCreate)
def update_lancamento(lancamento_id: int, lancamento: FinanceiroUpdate, db: Session = Depends(get_db)):
    db_lancamento = db.query(FinanceiroDB).filter(FinanceiroDB.id == lancamento_id).first()
    if db_lancamento is None:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
        
    for key, value in lancamento.dict(exclude_unset=True).items():
        setattr(db_lancamento, key, value)
        
    db.commit()
    db.refresh(db_lancamento)
    return db_lancamento
    
@app.delete("/financeiro/{lancamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lancamento(lancamento_id: int, db: Session = Depends(get_db)):
    db_lancamento = db.query(FinanceiroDB).filter(FinanceiroDB.id == lancamento_id).first()
    if db_lancamento is None:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
        
    db.delete(db_lancamento)
    db.commit()
    return

# --- CRUD ORÇAMENTO PROJETADO ---
@app.post("/orcamento/", response_model=OrcamentoCreate)
def create_orcamento(orcamento: OrcamentoCreate, db: Session = Depends(get_db)):
    db_orcamento = db.query(OrcamentoDB).filter(
        OrcamentoDB.empreendimento == orcamento.empreendimento,
        OrcamentoDB.mes_ano == orcamento.mes_ano
    ).first()
    
    if db_orcamento:
        db_orcamento.valor_orcado = orcamento.valor_orcado
    else:
        db_orcamento = OrcamentoDB(**orcamento.dict())
        db.add(db_orcamento)
        
    db.commit()
    db.refresh(db_orcamento)
    return db_orcamento

@app.post("/orcamento/projetar/")
def projetar_orcamento(
    valor_total: float, 
    data_inicio: str, 
    empreendimento: str,
    servico: str,
    num_meses_manual: int, 
    db: Session = Depends(get_db)
):
    
    db.query(OrcamentoDB).filter(
        OrcamentoDB.empreendimento == empreendimento,
    ).delete(synchronize_session=False)
    db.commit()

    meses = get_meses_para_rateio(data_inicio, num_meses_manual)
    num_meses_validos = len(meses)
    
    if num_meses_validos == 0:
        return {"message": "Erro: Período de execução inválido ou zero."}

    valor_mensal = valor_total / num_meses_validos

    for mes_ano in meses:
        novo_registro = OrcamentoDB(
            empreendimento=empreendimento,
            mes_ano=mes_ano,
            valor_orcado=valor_mensal
        )
        db.add(novo_registro)

    db.commit()
    return {"message": f"{num_meses_validos} registros de orçamento criados com sucesso."}


# --- ROTA: LANÇAMENTO DE AVANÇO ---
@app.post("/avanco/")
def create_avanco(avanco: AvancoCreate, db: Session = Depends(get_db)):
    if avanco.percentual_avanco < 0 or avanco.percentual_avanco > 100:
        raise HTTPException(status_code=400, detail="Percentual de avanço deve ser entre 0 e 100.")
        
    db_avanco = AvancoDB(**avanco.dict())
    db.add(db_avanco)
    db.commit()
    db.refresh(db_avanco)
    return db_avanco


# --- 6. ROTAS DE DASHBOARD E ANÁLISE ---

# ROTA SIMPLIFICADA (NOVA)
@app.get("/financeiro/progresso_simples", response_model=List[ProgressoSimples])
def get_progresso_simples(db: Session = Depends(get_db)):
    
    projects = db.query(ObraDB).all()

    results = []
    for p in projects:
        valor_total = p.valor_total or 0.0
        valor_pago = p.valor_pago or 0.0

        percentual = 0.0
        if valor_total > 0:
            percentual = (valor_pago / valor_total) * 100
        
        results.append({
            "empreendimento": p.empreendimento,
            "valor_total": valor_total,
            "valor_pago": valor_pago,
            "percentual_progresso": round(min(percentual, 100.0), 2) # Limita a 100%
        })
    
    return results

# Adicionar esta rota no seu main.py (se não existir)
@app.get("/kpis/")
def get_kpis(db: Session = Depends(get_db)):
    
    # Use func.coalesce para garantir que o resultado da soma seja 0.0 se for NULL
    total_contratado = db.query(func.coalesce(func.sum(ObraDB.valor_total), 0.0)).scalar()
    total_pago = db.query(func.coalesce(func.sum(ObraDB.valor_pago), 0.0)).scalar()
    
    carteira_total = total_contratado
    total_pago_real = total_pago
    saldo_devedor = carteira_total - total_pago_real

    saidas_totais_registradas = db.query(func.coalesce(func.sum(FinanceiroDB.valor), 0.0)).filter(FinanceiroDB.tipo == 'saida').scalar()
    entradas_totais_registradas = db.query(func.coalesce(func.sum(FinanceiroDB.valor), 0.0)).filter(FinanceiroDB.tipo == 'entrada').scalar()
    
    hoje = date.today().strftime('%Y-%m-%d')
    valor_atraso = db.query(func.coalesce(func.sum(FinanceiroDB.valor), 0.0)) \
                     .filter(FinanceiroDB.status == 'Pendente') \
                     .filter(FinanceiroDB.data_vencimento < hoje) \
                     .scalar()

    return {
        "carteiraTotal": float(carteira_total),
        "totalPago": float(total_pago_real),
        "saldoDevedor": float(saldo_devedor),
        "fluxoSaidas": float(saidas_totais_registradas),
        "fluxoEntradas": float(entradas_totais_registradas),
        "atrasoFinanceiro": float(valor_atraso)
    }

# Adicionar esta rota no seu main.py (se não existir)
@app.get("/desembolso/dados")
def get_desembolso_data(db: Session = Depends(get_db), projeto: Optional[str] = None):
    
    query_obras = db.query(ObraDB)
    if projeto:
        query_obras = query_obras.filter(ObraDB.empreendimento == projeto)
    
    obras = query_obras.all()

    if not obras:
        return []

    # Se a data estiver vazia ou for inválida, isso pode causar um crash.
    # Usamos try/except ou filtros para ignorar entradas inválidas.
    datas_inicio = [datetime.strptime(o.data_inicio, '%Y-%m-%d') for o in obras if o.data_inicio and len(o.data_inicio) == 10]
    datas_fim = [datetime.strptime(o.data_fim, '%Y-%m-%d') for o in obras if o.data_fim and len(o.data_fim) == 10]

    if not datas_inicio or not datas_fim:
        return []

    data_inicio_global = min(datas_inicio)
    data_fim_global = max(datas_fim)
    
    meses_ordenados = []
    current_date = data_inicio_global.replace(day=1)
    while current_date <= data_fim_global.replace(day=1):
        meses_ordenados.append(current_date.strftime('%Y-%m'))
        current_date += relativedelta(months=1)

    dados_grafico = {mes: {"Orçado Mensal": 0.0, "Desembolso Mensal": 0.0} for mes in meses_ordenados}

    query_orcamento = db.query(OrcamentoDB).filter(OrcamentoDB.mes_ano.in_(meses_ordenados))
    query_financeiro = db.query(FinanceiroDB.data_vencimento, FinanceiroDB.valor).filter(FinanceiroDB.tipo == 'saida')

    if projeto:
        query_orcamento = query_orcamento.filter(OrcamentoDB.empreendimento == projeto)
        query_financeiro = query_financeiro.filter(FinanceiroDB.empreendimento == projeto)

    projeccoes = query_orcamento.all()
    saidas_reais = query_financeiro.all()

    for proj in projeccoes:
        mes_ano = proj.mes_ano
        if mes_ano in dados_grafico:
            dados_grafico[mes_ano]["Orçado Mensal"] += proj.valor_orcado

    for data_str, valor in saidas_reais:
        try:
            mes_ano = pd.to_datetime(data_str).strftime('%Y-%m')
            if mes_ano in dados_grafico:
                dados_grafico[mes_ano]["Desembolso Mensal"] += valor
        except:
            continue

    mes_map = {'01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr', '05': 'Mai', '06': 'Jun',
               '07': 'Jul', '08': 'Ago', '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'}
               
    dados_finais = []
    orcado_acumulado = 0
    desembolso_acumulado = 0
    
    for mes_ano in meses_ordenados:
        orcado_acumulado += dados_grafico[mes_ano]["Orçado Mensal"]
        desembolso_acumulado += dados_grafico[mes_ano]["Desembolso Mensal"]
        
        ano, mes = mes_ano.split('-')
        
        dados_finais.append({
            "mesAno": f"{mes_map[mes]}/{ano[-2:]}",
            "Orçado Mensal": dados_grafico[mes_ano]["Orçado Mensal"],
            "Desembolso Mensal": dados_grafico[mes_ano]["Desembolso Mensal"],
            "Orçado Acumulado": orcado_acumulado,
            "Desembolso Acumulado": desembolso_acumulado,
        })
        
    return dados_finais

# ... (Rotas /avanco/consolidado, /desembolso/dados, /kpis/, etc., omitidas por serem a fonte do erro, 
# mas devem ser mantidas se você precisar delas no futuro. Para o teste atual,
# focaremos apenas na rota progresso_simples e kpis.)
# ...

# ROTA: EMPREENDIMENTOS
@app.get("/empreendimentos/")
def get_empreendimentos(db: Session = Depends(get_db)):
    empreendimentos = db.query(ObraDB.empreendimento).distinct().all()
    empreendimentos_fin = db.query(FinanceiroDB.empreendimento).distinct().all()
    empreendimentos_avanco = db.query(AvancoDB.empreendimento).distinct().all()
    
    todos_empreendimentos = set()
    for e in empreendimentos:
        todos_empreendimentos.add(e[0])
    for e in empreendimentos_fin:
        todos_empreendimentos.add(e[0])
    for e in empreendimentos_avanco:
        todos_empreendimentos.add(e[0])
        
    return sorted(list(todos_empreendimentos))