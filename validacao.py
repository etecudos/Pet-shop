"""
Mensagens de erro amigáveis (em português) para as validações dos schemas.

O Pydantic gera as mensagens de erro em inglês. Aqui interceptamos o
RequestValidationError do FastAPI e devolvemos, no JSON, uma mensagem clara
por campo, no formato:

    {"detail": [{"campo": "telefone", "mensagem": "O telefone deve conter 11 dígitos com o DDD."}]}
"""
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Nome "bonito" de cada campo, usado dentro das mensagens
ROTULOS = {
    "nome": "nome",
    "raca": "raça",
    "idade": "idade",
    "porte_id": "porte_id",
    "cpf": "CPF",
    "telefone": "telefone",
    "email": "e-mail",
    "cep": "CEP",
    "logradouro": "logradouro",
    "numero": "número",
    "complemento": "complemento",
    "cidade": "cidade",
    "uf_id": "uf_id",
    "pet_id": "pet_id",
    "funcionario_id": "funcionario_id",
    "cliente_id": "cliente_id",
    "servico": "serviço",
    "data_agendamento": "data do agendamento",
    "hora_agendamento": "hora do agendamento",
    "observacoes": "observações",
    "status": "status",
}

# Campos numéricos escritos como texto, com quantidade fixa de dígitos
MSG_DIGITOS = {
    "telefone": "O telefone deve conter 11 dígitos com o DDD.",
    "cpf": "O CPF deve conter 11 dígitos, apenas números.",
    "cep": "O CEP deve conter 8 dígitos, apenas números.",
}

MSG_EMAIL = "Insira um e-mail válido no formato nome@dominio.com."


def _rotulo(campo: str) -> str:
    return ROTULOS.get(campo, campo)


def _traduzir_erro(erro: dict) -> tuple[str, str]:
    """Recebe um erro do Pydantic e devolve (campo, mensagem amigável)."""
    loc = [str(parte) for parte in erro["loc"] if parte != "body"]
    campo = loc[-1] if loc else "corpo"
    rotulo = _rotulo(campo)
    tipo = erro["type"]
    ctx = erro.get("ctx") or {}
    valor = erro.get("input")

    # Campo ausente no JSON
    if tipo == "missing":
        return campo, f"O campo {rotulo} é obrigatório."

    # JSON inválido / corpo que não é um objeto
    if tipo in ("json_invalid", "model_attributes_type", "dict_type"):
        return campo, "O corpo da requisição deve ser um JSON válido."

    # E-mail
    if campo == "email":
        return campo, MSG_EMAIL

    # Telefone, CPF e CEP: qualquer falha de tamanho/formato cai na mesma mensagem
    if campo in MSG_DIGITOS and tipo in (
        "string_too_short", "string_too_long", "string_pattern_mismatch", "string_type",
    ):
        return campo, MSG_DIGITOS[campo]

    # Texto vazio ou só com espaços
    if tipo == "string_too_short" and isinstance(valor, str) and valor.strip() == "":
        return campo, f"O campo {rotulo} é obrigatório e não pode ficar em branco."

    if tipo == "string_too_short":
        return campo, f"O campo {rotulo} deve ter no mínimo {ctx.get('min_length')} caracteres."

    if tipo == "string_too_long":
        return campo, f"O campo {rotulo} deve ter no máximo {ctx.get('max_length')} caracteres."

    if tipo == "string_type":
        return campo, f"O campo {rotulo} deve ser um texto."

    # Números
    if tipo in ("greater_than", "greater_than_equal"):
        return campo, f"O campo {rotulo} deve ser um número maior que zero."

    if tipo in ("int_parsing", "int_type", "int_from_float"):
        return campo, f"O campo {rotulo} deve ser um número inteiro."

    # Datas e horas
    if tipo.startswith("date"):
        return campo, f"O campo {rotulo} deve ser uma data válida no formato AAAA-MM-DD."
    if tipo.startswith("time"):
        return campo, f"O campo {rotulo} deve ser uma hora válida no formato HH:MM."

    # Qualquer outro caso: devolve a mensagem original do Pydantic
    return campo, erro["msg"]


def registrar_handlers(app: FastAPI) -> None:
    """Registra o handler que troca as mensagens padrão pelas amigáveis."""

    @app.exception_handler(RequestValidationError)
    async def tratar_erro_de_validacao(request: Request, exc: RequestValidationError):
        mensagens = []
        campos_vistos = set()
        for erro in exc.errors():
            campo, mensagem = _traduzir_erro(erro)
            # Um campo pode falhar em mais de uma regra (ex.: tamanho e padrão).
            # Mostramos só uma mensagem por campo, para não repetir.
            if campo in campos_vistos:
                continue
            campos_vistos.add(campo)
            mensagens.append({"campo": campo, "mensagem": mensagem})

        return JSONResponse(
            status_code=422,
            content=jsonable_encoder({"detail": mensagens}),
        )
