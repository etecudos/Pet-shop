from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import ClienteModel, PetModel, UFModel
from schemas import ClienteCreateSchema, ClienteResponseSchema, ClienteUpdateSchema

# Instância de APIRouter configurada com o prefixo e a tag da entidade
router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
)


# READ - Listar todos os clientes, com busca opcional por nome via query parameter
@router.get("/", response_model=List[ClienteResponseSchema], status_code=status.HTTP_200_OK)
def listar_clientes(nome: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(ClienteModel)
    if nome:
        query = query.filter(ClienteModel.nome.contains(nome))
    return query.all()


# READ - Buscar um cliente específico pelo id
@router.get("/{cliente_id}", response_model=ClienteResponseSchema, status_code=status.HTTP_200_OK)
def buscar_cliente_por_id(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado",
        )
    return cliente


# Função auxiliar: garante que o CPF informado não pertence a outro cliente
def _validar_cpf_unico(cpf: str, db: Session, cliente_id_atual: Optional[int] = None):
    query = db.query(ClienteModel).filter(ClienteModel.cpf == cpf)
    if cliente_id_atual is not None:
        query = query.filter(ClienteModel.id != cliente_id_atual)
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um cliente cadastrado com esse CPF",
        )


# Função auxiliar: garante que o e-mail informado não pertence a outro cliente
def _validar_email_unico(email: str, db: Session, cliente_id_atual: Optional[int] = None):
    query = db.query(ClienteModel).filter(ClienteModel.email == email)
    if cliente_id_atual is not None:
        query = query.filter(ClienteModel.id != cliente_id_atual)
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um cliente cadastrado com esse e-mail",
        )


# Função auxiliar: garante que o pet_id informado existe na tabela pets
def _validar_pet_existe(pet_id: int, db: Session):
    pet = db.query(PetModel).filter(PetModel.id == pet_id).first()
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pet_id informado não existe na tabela de pets",
        )


# Função auxiliar: garante que o uf_id informado existe na tabela ufs
def _validar_uf_existe(uf_id: int, db: Session):
    if not db.query(UFModel).filter(UFModel.id == uf_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="uf_id informado não existe na tabela de ufs",
        )


# CREATE - Cadastrar um novo cliente no banco
@router.post("/", response_model=ClienteResponseSchema, status_code=status.HTTP_201_CREATED)
def criar_cliente(dados_cliente: ClienteCreateSchema, db: Session = Depends(get_db)):
    _validar_email_unico(dados_cliente.email, db)
    _validar_cpf_unico(dados_cliente.cpf, db)
    _validar_pet_existe(dados_cliente.pet_id, db)
    _validar_uf_existe(dados_cliente.uf_id, db)

    novo_cliente = ClienteModel(**dados_cliente.model_dump())
    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)
    return novo_cliente


# UPDATE - Alterar todos os dados de um cliente existente
@router.put("/{cliente_id}", response_model=ClienteResponseSchema, status_code=status.HTTP_200_OK)
def atualizar_cliente(cliente_id: int, dados_cliente: ClienteUpdateSchema, db: Session = Depends(get_db)):
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado",
        )

    _validar_email_unico(dados_cliente.email, db, cliente_id_atual=cliente_id)
    _validar_cpf_unico(dados_cliente.cpf, db, cliente_id_atual=cliente_id)
    _validar_pet_existe(dados_cliente.pet_id, db)
    _validar_uf_existe(dados_cliente.uf_id, db)

    for campo, valor in dados_cliente.model_dump().items():
        setattr(cliente, campo, valor)

    db.commit()
    db.refresh(cliente)
    return cliente


# DELETE - Remover um cliente do banco
@router.delete("/{cliente_id}", status_code=status.HTTP_200_OK)
def deletar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado",
        )
    try:
        db.delete(cliente)
        db.commit()
    except IntegrityError:
        # Existe(m) Agendamento(s) apontando cliente_id para este cliente
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível remover: existe(m) agendamento(s) vinculado(s) a este cliente",
        )
    return {"mensagem": f"Cliente {cliente_id} removido com sucesso!"}
