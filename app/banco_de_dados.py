import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./raizes.db")
argumentos_conexao = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=argumentos_conexao, future=True)
SessaoLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def obter_sessao_banco():
    """Entrega uma sessão do banco e fecha a conexão ao terminar a requisição."""
    db = SessaoLocal()
    try:
        yield db
    finally:
        db.close()
