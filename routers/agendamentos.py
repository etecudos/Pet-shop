from datetime import date, time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import AgendamentoModel, ClienteModel, FuncionarioModel
from schemas import (
    AgendamentoCreateSchema,
    AgendamentoDetalhadoResponseSchema,
    AgendamentoResponseSchema,
    AgendamentoUpdateSchema,
)

# Instância de APIRouter configurada com o prefixo e a tag da entidade
router = APIRouter(
    prefix="/agendamentos",
    tags=["Agendamentos"],
)


# Função auxiliar: garante que funcionario_id e cliente_id informados existem no banco
def _validar_funcionario_e_cliente(funcionario_id: int, cliente_id: int, db: Session):
    if not db.query(FuncionarioModel).filter(FuncionarioModel.id == funcionario_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="funcionario_id informado não existe",
        )
    if not db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cliente_id informado não existe",
        )


STATUS_CANCELADO = "Cancelado"
MSG_CONFLITO = "Este funcionário já possui um agendamento nessa data e horário"


# Função auxiliar: impede dois agendamentos do mesmo funcionário na mesma
# data/hora. Agendamentos "Cancelado" não contam (o horário volta a ficar livre).
# No PUT, passa-se agendamento_id_atual para não conflitar consigo mesmo.
def _validar_horario_livre(
    funcionario_id: int,
    data_agendamento: date,
    hora_agendamento: time,
    db: Session,
    agendamento_id_atual: Optional[int] = None,
):
    query = db.query(AgendamentoModel).filter(
        AgendamentoModel.funcionario_id == funcionario_id,
        AgendamentoModel.data_agendamento == data_agendamento,
        AgendamentoModel.hora_agendamento == hora_agendamento,
        AgendamentoModel.status != STATUS_CANCELADO,
    )
    if agendamento_id_atual is not None:
        query = query.filter(AgendamentoModel.id != agendamento_id_atual)
    if query.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MSG_CONFLITO)


# Escolhe o schema certo dependendo do parâmetro ?completo=true/false.
# response_model=None nos endpoints abaixo porque o schema muda em tempo de
# execução; a serialização final continua sendo feita pelo Pydantic.
def _serializar_agendamento(agendamento: AgendamentoModel, completo: bool):
    schema_cls = AgendamentoDetalhadoResponseSchema if completo else AgendamentoResponseSchema
    return schema_cls.model_validate(agendamento)


# READ - Listar todos os agendamentos, com busca opcional por status via query parameter.
# "status_filtro" é uma requisição específica (requisito 11), por isso continua
# funcionando mesmo com o status oculto na resposta normal.
@router.get(
    "/",
    response_model=None,  # o schema muda em runtime (ver _serializar_agendamento)
    status_code=status.HTTP_200_OK,
)
def listar_agendamentos(
    status_filtro: Optional[str] = None,
    completo: bool = Query(False, description="Se true, inclui o campo 'status' na resposta"),
    db: Session = Depends(get_db),
):
    query = db.query(AgendamentoModel)
    if status_filtro:
        query = query.filter(AgendamentoModel.status == status_filtro)
    agendamentos = query.all()
    return [_serializar_agendamento(a, completo) for a in agendamentos]


# READ - Buscar um agendamento específico pelo id
@router.get(
    "/{agendamento_id}",
    response_model=None,  # o schema muda em runtime (ver _serializar_agendamento)
    status_code=status.HTTP_200_OK,
)
def buscar_agendamento_por_id(
    agendamento_id: int,
    completo: bool = Query(False, description="Se true, inclui o campo 'status' na resposta"),
    db: Session = Depends(get_db),
):
    agendamento = db.query(AgendamentoModel).filter(AgendamentoModel.id == agendamento_id).first()
    if not agendamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agendamento não encontrado",
        )
    return _serializar_agendamento(agendamento, completo)


# CREATE - Cadastrar um novo agendamento no banco
@router.post(
    "/",
    response_model=None,  # o schema muda em runtime (ver _serializar_agendamento)
    status_code=status.HTTP_201_CREATED,
)
def criar_agendamento(
    dados_agendamento: AgendamentoCreateSchema,
    completo: bool = Query(False, description="Se true, inclui o campo 'status' na resposta"),
    db: Session = Depends(get_db),
):
    _validar_funcionario_e_cliente(dados_agendamento.funcionario_id, dados_agendamento.cliente_id, db)

    _validar_horario_livre(
        dados_agendamento.funcionario_id,
        dados_agendamento.data_agendamento,
        dados_agendamento.hora_agendamento,
        db,
    )

    # status não vem do cliente: todo agendamento novo nasce como "Agendado"
    novo_agendamento = AgendamentoModel(**dados_agendamento.model_dump(), status="Agendado")
    db.add(novo_agendamento)
    try:
        db.commit()
    except IntegrityError:
        # Duas requisições simultâneas passaram pela checagem: o índice único barra a segunda
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MSG_CONFLITO)
    db.refresh(novo_agendamento)
    return _serializar_agendamento(novo_agendamento, completo)


# UPDATE - Alterar todos os dados de um agendamento existente
@router.put(
    "/{agendamento_id}",
    response_model=None,  # o schema muda em runtime (ver _serializar_agendamento)
    status_code=status.HTTP_200_OK,
)
def atualizar_agendamento(
    agendamento_id: int,
    dados_agendamento: AgendamentoUpdateSchema,
    completo: bool = Query(False, description="Se true, inclui o campo 'status' na resposta"),
    db: Session = Depends(get_db),
):
    agendamento = db.query(AgendamentoModel).filter(AgendamentoModel.id == agendamento_id).first()
    if not agendamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agendamento não encontrado",
        )

    _validar_funcionario_e_cliente(dados_agendamento.funcionario_id, dados_agendamento.cliente_id, db)

    # Só checa conflito se o agendamento continuará ativo (não cancelado)
    if dados_agendamento.status != STATUS_CANCELADO:
        _validar_horario_livre(
            dados_agendamento.funcionario_id,
            dados_agendamento.data_agendamento,
            dados_agendamento.hora_agendamento,
            db,
            agendamento_id_atual=agendamento_id,
        )

    for campo, valor in dados_agendamento.model_dump().items():
        setattr(agendamento, campo, valor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MSG_CONFLITO)
    db.refresh(agendamento)
    return _serializar_agendamento(agendamento, completo)


# DELETE - Remover um agendamento do banco
@router.delete("/{agendamento_id}", status_code=status.HTTP_200_OK)
def deletar_agendamento(agendamento_id: int, db: Session = Depends(get_db)):
    agendamento = db.query(AgendamentoModel).filter(AgendamentoModel.id == agendamento_id).first()
    if not agendamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agendamento não encontrado",
        )
    db.delete(agendamento)
    db.commit()
    return {"mensagem": f"Agendamento {agendamento_id} removido com sucesso!"}
