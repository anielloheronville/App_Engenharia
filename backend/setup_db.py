import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Date

# --- CONFIGURAÇÃO ---
DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASS = "Araguaia2025out" # <--- SUA SENHA AQUI
DB_NAME = "engmanager"

def create_database():
    """Conecta no banco padrão 'postgres' e cria o 'engmanager' se não existir"""
    try:
        # 1. Conecta ao banco padrão 'postgres'
        con = psycopg2.connect(dbname='postgres', user=DB_USER, host=DB_HOST, password=DB_PASS)
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) # Necessário para criar DB
        cur = con.cursor()

        # 2. Verifica se o banco já existe
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone()

        if not exists:
            print(f"🔨 Banco de dados '{DB_NAME}' não encontrado. Criando...")
            cur.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"✅ Banco de dados '{DB_NAME}' criado com sucesso!")
        else:
            print(f"ℹ️ O Banco de dados '{DB_NAME}' já existe.")

        cur.close()
        con.close()
    except Exception as e:
        print(f"❌ Erro ao criar banco: {e}")

# --- MODELOS DAS TABELAS (Schema) ---
Base = declarative_base()

class ObraDB(Base):
    __tablename__ = "obras"
    id = Column(Integer, primary_key=True, index=True)
    empreendimento = Column(String, index=True)
    fornecedor = Column(String)
    servico = Column(String)
    valor_total = Column(Float)
    valor_pago = Column(Float)
    status = Column(String)
    data_inicio = Column(String)
    data_fim = Column(String)

class FinanceiroDB(Base):
    __tablename__ = "financeiro"
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String)
    categoria = Column(String) # Ex: Material, Mão de Obra
    fornecedor = Column(String)
    valor = Column(Float)
    tipo = Column(String) # 'entrada' ou 'saida'
    status = Column(String) # 'Pago', 'Pendente', 'Atrasado'
    data_vencimento = Column(String)
    empreendimento_id = Column(Integer, nullable=True) # Para ligar à obra (opcional por enquanto)

def create_tables():
    """Conecta no banco novo 'engmanager' e cria as tabelas"""
    try:
        # URL de conexão com o banco NOVO
        db_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
        engine = create_engine(db_url)
        
        # Cria todas as tabelas definidas acima
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas 'obras' e 'financeiro' criadas/verificadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando configuração do Banco de Dados...")
    create_database()
    create_tables()
    print("🏁 Configuração concluída! Pode rodar o 'main.py' agora.")