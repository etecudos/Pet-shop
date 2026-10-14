from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

# Definir a conexão com o SQLite (o arquivo do banco é criado na raiz do projeto)
DATABASE_URL = "sqlite:///./pet.db"

# Criação do motor do SQLAlchemy, responsável pela comunicação com o banco.
# connect_args é necessário apenas para SQLite, que por padrão só permite
# uso na mesma thread que criou a conexão.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


# O SQLite vem com a checagem de chaves estrangeiras DESLIGADA por padrão.
# Sem isso, seria possível apagar um Pet mesmo com um Cliente apontando
# pet_id para ele, deixando uma referência quebrada no banco.
@event.listens_for(engine, "connect")
def _habilitar_foreign_keys(conexao_dbapi, connection_record):
    cursor = conexao_dbapi.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Fábrica que gera sessões de leitura e escrita no banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe genérica da qual todos os modelos (tabelas) herdam
Base = declarative_base()


# Dependência do FastAPI: abre uma sessão por requisição e garante o fechamento seguro
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
