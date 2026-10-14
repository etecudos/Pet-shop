from fastapi import FastAPI

from database import Base, SessionLocal, engine
from routers import agendamentos, clientes, funcionarios, pets, portes, ufs
from seed import popular_tabelas_fixas
from validacao import registrar_handlers

# Cria as tabelas no banco (caso ainda não existam)
Base.metadata.create_all(bind=engine)

# Garante que as tabelas de domínio (ufs e portes) estejam populadas
with SessionLocal() as _db:
    popular_tabelas_fixas(_db)

app = FastAPI(
    title="PetShop API",
    description="API para cadastro e consulta de clientes, pets e funcionários",
)

# Mensagens de erro de validação em português (ver validacao.py)
registrar_handlers(app)

app.include_router(ufs.router)
app.include_router(portes.router)
app.include_router(funcionarios.router)
app.include_router(pets.router)
app.include_router(clientes.router)
app.include_router(agendamentos.router)


@app.get("/")
def home():
    return {"mensagem": "PetShop API rodando com sucesso"}
