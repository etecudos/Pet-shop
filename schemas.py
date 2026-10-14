from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, EmailStr, Field



# ---------- Tabelas de domínio (UF e Porte) ----------

class UFSchema(BaseModel):
    id: int
    sigla: str
    nome: str

    model_config = ConfigDict(from_attributes=True)


class PorteSchema(BaseModel):
    id: int
    nome: str

    model_config = ConfigDict(from_attributes=True)


# ---------- Pet ----------
# (definido primeiro pois o Cliente referencia PetResumoSchema)
# Pet não tem mais vínculo com Cliente: é o Cliente que aponta para o Pet
# através do campo pet_id (ver seção Cliente logo abaixo).

class PetCreateSchema(BaseModel):
    # str_strip_whitespace remove espaços das pontas antes de validar,
    # então "   " vira "" e é barrado pelo min_length.
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=3, max_length=100, description="Nome do pet (3 a 100 caracteres)")
    raca: str = Field(min_length=3, max_length=50, description="Raça do pet (3 a 50 caracteres)")
    idade: int = Field(gt=0, description="Idade do pet, em anos (deve ser maior que zero)")
    porte_id: int = Field(gt=0, description="id de um porte existente (ver GET /portes)")


class PetUpdateSchema(PetCreateSchema):
    pass


# Versão resumida do Pet, usada dentro da resposta do Cliente e do Agendamento
# (inclui porte, como pedido no requisito 10)
class PetResumoSchema(BaseModel):
    id: int
    nome: str
    raca: str
    idade: int
    porte: PorteSchema

    model_config = ConfigDict(from_attributes=True)


class PetResponseSchema(BaseModel):
    id: int
    nome: str
    raca: str
    idade: int
    porte: PorteSchema

    model_config = ConfigDict(from_attributes=True)


# ---------- Cliente ----------
# Cliente = cadastro completo de uma pessoa (o dono do pet), sem senha:
# não existe login/autenticação aqui, só os dados de contato, endereço e o
# pet_id do pet já cadastrado que pertence a esse cliente.

# Schema de entrada de dados
class ClienteCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=3, max_length=100, description="Nome completo (3 a 100 caracteres)")
    cpf: str = Field(min_length=11, max_length=11, pattern=r"^\d{11}$", description="CPF: exatamente 11 dígitos, só números")
    telefone: str = Field(min_length=11, max_length=11, pattern=r"^\d{11}$", description="Telefone: DDD + número, exatamente 11 dígitos")
    email: EmailStr = Field(max_length=100, description="E-mail válido, no formato nome@dominio.com")
    cep: str = Field(min_length=8, max_length=8, pattern=r"^\d{8}$", description="CEP: exatamente 8 dígitos, só números")
    logradouro: str = Field(min_length=3, max_length=100, description="Rua/avenida (3 a 100 caracteres)")
    numero: int = Field(gt=0, description="Número do endereço, deve ser positivo")
    complemento: str | None = Field(default=None, max_length=100, description="Complemento (opcional, até 100 caracteres)")
    cidade: str = Field(min_length=2, max_length=100, description="Cidade (2 a 100 caracteres)")
    uf_id: int = Field(gt=0, description="id de uma UF existente (ver GET /ufs)")
    pet_id: int = Field(gt=0, description="id de um pet já cadastrado na tabela pets")


# Usado no PUT: os mesmos dados do Create
class ClienteUpdateSchema(ClienteCreateSchema):
    pass


# Schema de resposta
# data_criacao não entra aqui de propósito: continua sendo salva no banco
# (a coluna existe e é preenchida automaticamente), só não aparece na tela/API.
class ClienteResponseSchema(BaseModel):
    id: int
    nome: str
    cpf: str
    telefone: str
    email: str
    cep: str
    logradouro: str
    numero: int
    complemento: str | None = None
    cidade: str
    uf: UFSchema
    pet: PetResumoSchema  # pet completo (resumido), em vez do pet_id cru

    model_config = ConfigDict(from_attributes=True)


# Versão resumida do Cliente, usada dentro da resposta do Agendamento.
# Traz o pet dele aninhado (requisito: mostrar as informações do pet
# relacionado ao cliente na tela do agendamento).
class ClienteResumoComPetSchema(BaseModel):
    id: int
    nome: str
    telefone: str
    email: str
    pet: PetResumoSchema

    model_config = ConfigDict(from_attributes=True)


# ---------- Funcionario ----------
# Funcionario = colaborador do petshop (quem atende os agendamentos).
# Não tem nenhum vínculo com Pet nem com Cliente.

# Schema de entrada de dados (usado no POST / recebido do cliente)
class FuncionarioCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=3, max_length=100, description="Nome completo (3 a 100 caracteres)")
    cpf: str = Field(min_length=11, max_length=11, pattern=r"^\d{11}$", description="CPF: exatamente 11 dígitos, só números")
    telefone: str = Field(min_length=11, max_length=11, pattern=r"^\d{11}$", description="Telefone: DDD + número, exatamente 11 dígitos")
    email: EmailStr = Field(max_length=100, description="E-mail válido, no formato nome@dominio.com")
    cep: str = Field(min_length=8, max_length=8, pattern=r"^\d{8}$", description="CEP: exatamente 8 dígitos, só números")
    logradouro: str = Field(min_length=3, max_length=100, description="Rua/avenida (3 a 100 caracteres)")
    numero: int = Field(gt=0, description="Número do endereço, deve ser positivo")
    complemento: str | None = Field(default=None, max_length=100, description="Complemento (opcional, até 100 caracteres)")
    cidade: str = Field(min_length=2, max_length=100, description="Cidade (2 a 100 caracteres)")
    uf_id: int = Field(gt=0, description="id de uma UF existente (ver GET /ufs)")


# Usado no PUT: mesmos campos do Create
class FuncionarioUpdateSchema(FuncionarioCreateSchema):
    pass


# Schema de resposta (usado para retornar dados ao cliente, já com o id gerado)
class FuncionarioResponseSchema(BaseModel):
    id: int
    nome: str
    cpf: str
    telefone: str
    email: str
    cep: str
    logradouro: str
    numero: int
    complemento: str | None = None
    cidade: str
    uf: UFSchema

    # Permite que o Pydantic leia diretamente os objetos SQLAlchemy/ORM
    model_config = ConfigDict(from_attributes=True)


# Versão resumida do Funcionario, usada dentro da resposta do Agendamento
# (nome, email, telefone e endereço, como pedido)
class FuncionarioResumoSchema(BaseModel):
    id: int
    nome: str
    email: str
    telefone: str
    cep: str
    logradouro: str
    numero: int
    complemento: str | None = None
    cidade: str
    uf: UFSchema

    model_config = ConfigDict(from_attributes=True)


# ---------- Agendamento ----------

class AgendamentoCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    funcionario_id: int = Field(gt=0, description="id de um funcionário existente")
    cliente_id: int = Field(gt=0, description="id de um cliente existente")
    servico: str = Field(min_length=3, max_length=100, description="Ex: Banho, Tosa, Consulta veterinária (3 a 100 caracteres)")
    data_agendamento: date
    hora_agendamento: time
    observacoes: str | None = Field(default=None, max_length=255, description="Observações (opcional, até 255 caracteres)")
    # status não é exigido do cliente: todo agendamento novo nasce como "Agendado"


class AgendamentoUpdateSchema(AgendamentoCreateSchema):
    status: str = "Agendado"  # no update já pode fazer sentido mudar o status


# Resposta padrão: SEM o campo status (requisito 11)
class AgendamentoResponseSchema(BaseModel):
    id: int
    funcionario: FuncionarioResumoSchema
    cliente: ClienteResumoComPetSchema  # cliente + o pet dele, em vez do cliente_id cru
    servico: str
    data_agendamento: date
    hora_agendamento: time
    observacoes: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Resposta "completa": usada só quando o cliente pedir explicitamente (?completo=true)
class AgendamentoDetalhadoResponseSchema(AgendamentoResponseSchema):
    status: str
