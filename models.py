from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


# Tabela de domínio: UFs (estados). Os 27 registros são populados por seed.py
class UFModel(Base):
    __tablename__ = "ufs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sigla = Column(String(2), nullable=False, unique=True)  # ex: SP
    nome = Column(String, nullable=False, unique=True)  # ex: São Paulo


# Tabela de domínio: porte do pet (PEQUENO, MEDIO, GRANDE), populada por seed.py
class PorteModel(Base):
    __tablename__ = "portes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, nullable=False, unique=True)


class FuncionarioModel(Base):
    __tablename__ = "funcionarios"  # Nome da tabela no banco

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, nullable=False, index=True)
    cpf = Column(String(11), nullable=False, unique=True, index=True)  # texto: preserva zeros à esquerda
    telefone = Column(String(11), nullable=False)  # DDD + número (11 dígitos)
    email = Column(String, nullable=False)
    cep = Column(String(8), nullable=False)  # 8 dígitos, pode começar com zero
    logradouro = Column(String, nullable=False)
    numero = Column(Integer, nullable=False)
    complemento = Column(String, nullable=True)  # opcional: nem todo endereço tem
    cidade = Column(String, nullable=False)
    uf_id = Column(Integer, ForeignKey("ufs.id"), nullable=False)

    data_criacao = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    uf = relationship("UFModel")


class PetModel(Base):
    __tablename__ = "pets"  # Nome da tabela no banco

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, nullable=False, index=True)
    raca = Column(String, nullable=False)
    idade = Column(Integer, nullable=False)  # idade do pet, em anos
    porte_id = Column(Integer, ForeignKey("portes.id"), nullable=False)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    porte = relationship("PorteModel")


class ClienteModel(Base):
    __tablename__ = "clientes"  # Nome da tabela no banco

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, nullable=False, index=True)
    cpf = Column(String(11), nullable=False, unique=True, index=True)  # texto: preserva zeros à esquerda
    telefone = Column(String(11), nullable=False)  # DDD + número (11 dígitos)
    email = Column(String, nullable=False, unique=True, index=True)
    cep = Column(String(8), nullable=False)  # 8 dígitos, pode começar com zero
    logradouro = Column(String, nullable=False)
    numero = Column(Integer, nullable=False)
    complemento = Column(String, nullable=True)  # opcional: nem todo endereço tem
    cidade = Column(String, nullable=False)
    uf_id = Column(Integer, ForeignKey("ufs.id"), nullable=False)
    # nullable=False -> todo cliente precisa apontar para um Pet já cadastrado
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    uf = relationship("UFModel")
    pet = relationship("PetModel")


class AgendamentoModel(Base):
    __tablename__ = "agendamentos"  # Nome da tabela no banco

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    funcionario_id = Column(Integer, ForeignKey("funcionarios.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    servico = Column(String, nullable=False)  # ex: Banho, Tosa, Consulta veterinária
    data_agendamento = Column(Date, nullable=False)
    hora_agendamento = Column(Time, nullable=False)
    status = Column(String, nullable=False, default="Agendado")  # Agendado, Concluído, Cancelado
    observacoes = Column(String, nullable=True)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    funcionario = relationship("FuncionarioModel")
    cliente = relationship("ClienteModel")

    # Rede de segurança no banco: o mesmo funcionário não pode ter dois
    # agendamentos na mesma data/hora, a não ser que o anterior esteja Cancelado
    # (horário cancelado volta a ficar livre). Complementa a checagem feita
    # no router e protege contra duas requisições simultâneas.
    __table_args__ = (
        Index(
            "uq_agendamento_funcionario_data_hora",
            "funcionario_id",
            "data_agendamento",
            "hora_agendamento",
            unique=True,
            sqlite_where=(status != "Cancelado"),
        ),
    )
