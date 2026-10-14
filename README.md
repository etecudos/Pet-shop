# PetShop API

## Integrantes

- Davi Oliveira
- Erik Henrique
- João Pedro Teixeira
- Lorenzzo Luighi
- Luan Ferreira

## Descrição

API para gerenciamento de um **Pet Shop**. O sistema controla os **clientes** (donos dos animais), os **funcionários** do petshop, os **pets** e os **agendamentos** de serviços, permitindo o CRUD completo de todas as entidades.

## Entidades

### `ufs` (tabela de domínio)

Os 27 estados brasileiros, populados automaticamente na inicialização (`seed.py`). Somente leitura na API.

| Campo | Tipo   | Descrição                  |
|-------|--------|------------------------------|
| id    | int    | Identificador único          |
| sigla | string | Sigla da UF (única), ex: SP  |
| nome  | string | Nome do estado (único)       |

### `portes` (tabela de domínio)

Portes possíveis de um pet (`PEQUENO`, `MEDIO`, `GRANDE`), populados automaticamente na inicialização. Somente leitura na API.

| Campo | Tipo   | Descrição                |
|-------|--------|----------------------------|
| id    | int    | Identificador único        |
| nome  | string | Nome do porte (único)      |

### `pets`

Referencia apenas a tabela `portes`.

| Campo | Tipo   | Descrição                    |
|-------|--------|--------------------------------|
| id    | int    | Identificador único            |
| nome  | string | Nome do pet                    |
| raca  | string | Raça do pet                    |
| idade | int    | Idade do pet, em anos (≥ 0)    |
| porte_id | int | Chave estrangeira — referência a `portes.id` |

### `clientes`

Cadastro completo de uma pessoa (o dono do pet), sem senha — não há login/autenticação, apenas dados de contato, endereço e o `pet_id` do pet que já deve estar cadastrado.

| Campo       | Tipo   | Descrição                                      |
|-------------|--------|---------------------------------------------------|
| id          | int    | Identificador único                                |
| nome        | string | Nome do cliente                                    |
| cpf         | string | CPF (11 dígitos, único)                            |
| telefone    | string | Telefone de contato                                |
| email       | string | E-mail de contato (único)                          |
| cep         | string | CEP (8 dígitos)                                    |
| logradouro  | string | Rua/avenida                                        |
| numero      | int    | Número do endereço                                 |
| complemento | string | Complemento (opcional)                             |
| cidade      | string | Cidade                                              |
| uf_id       | int    | Chave estrangeira — referência a `ufs.id`          |
| pet_id      | int    | Chave estrangeira — referência a um `pets.id` já existente |

> Repare que a chave estrangeira fica no **cliente**, não no pet: é o cliente que aponta para o pet, e não o contrário. Por isso um Pet precisa existir **antes** de cadastrar o Cliente.

### `funcionarios`

Colaboradores do petshop, responsáveis por atender os agendamentos. Entidade independente, sem vínculo com pets ou clientes.

| Campo       | Tipo   | Descrição                          |
|-------------|--------|--------------------------------------|
| id          | int    | Identificador único                  |
| nome        | string | Nome do funcionário                  |
| cpf         | string | CPF (11 dígitos, único)              |
| telefone    | string | Telefone de contato                  |
| email       | string | E-mail de contato                    |
| cep         | string | CEP (8 dígitos)                      |
| logradouro  | string | Rua/avenida                          |
| numero      | int    | Número do endereço                   |
| complemento | string | Complemento (opcional)               |
| cidade      | string | Cidade                               |
| uf_id       | int    | Chave estrangeira — referência a `ufs.id` |

### `agendamentos`

| Campo           | Tipo   | Descrição                                          |
|-----------------|--------|-------------------------------------------------------|
| id              | int    | Identificador único                                   |
| funcionario_id  | int    | Chave estrangeira — referência a `funcionarios.id`    |
| cliente_id      | int    | Chave estrangeira — referência a `clientes.id`        |
| servico         | string | Ex: Banho, Tosa, Consulta veterinária                 |
| data_agendamento| date   | Data do agendamento                                   |
| hora_agendamento| time   | Hora do agendamento                                   |
| status          | string | Agendado / Concluído / Cancelado (oculto na resposta padrão) |
| observacoes     | string | Observações (opcional)                                |

> **Regra de horário:** o mesmo funcionário não pode ter dois agendamentos na mesma data e hora — a API responde `409 Conflict`. Agendamentos com status `Cancelado` não contam, então o horário volta a ficar livre. A regra vale no POST e no PUT (e é reforçada por um índice único parcial no banco).

> O agendamento aponta para o **cliente**, não mais direto para o pet. Como o cliente já carrega o `pet_id` dele, a resposta do agendamento mostra o cliente com o pet aninhado dentro dele (`cliente.pet`), então dá pra ver as informações do pet relacionado ao cliente direto na tela.

## Ordem de criação (por causa das dependências)

0. **UFs e Portes** (já vêm populados automaticamente — consulte os ids em `GET /ufs` e `GET /portes`)
1. **Pet** (precisa de um `porte_id` existente)
2. **Funcionário** (precisa de um `uf_id` existente)
3. **Cliente** (precisa de um `pet_id` e um `uf_id` existentes)
4. **Agendamento** (precisa de um `funcionario_id` e um `cliente_id` já existentes)

O banco tem checagem de chaves estrangeiras habilitada (`PRAGMA foreign_keys=ON`), então não é possível excluir um Pet que ainda tenha um Cliente apontando para ele, nem excluir um Funcionário ou Cliente que ainda tenha Agendamentos vinculados — a API retorna erro 400 nesses casos.

## Contrato das Rotas HTTP

| Método | Rota                  | Descrição                                                    |
|--------|-----------------------|-------------------------------------------------------------|
| GET    | `/`                   | Mensagem de status da API                                    |
| GET    | `/ufs`                | Lista todas as UFs                                           |
| GET    | `/ufs/{id}`           | Retorna uma UF pelo id                                       |
| GET    | `/portes`             | Lista todos os portes                                        |
| GET    | `/portes/{id}`        | Retorna um porte pelo id                                     |
| GET    | `/pets`               | Lista todos os pets (aceita `?nome=` para busca)              |
| GET    | `/pets/{id}`          | Retorna um pet específico pelo id                             |
| POST   | `/pets`               | Cadastra um novo pet                                          |
| PUT    | `/pets/{id}`          | Atualiza um pet existente                                     |
| DELETE | `/pets/{id}`          | Remove um pet (falha se houver cliente vinculado)             |
| GET    | `/clientes`           | Lista todos os clientes (aceita `?nome=` para busca)          |
| GET    | `/clientes/{id}`      | Retorna um cliente específico pelo id                         |
| POST   | `/clientes`           | Cadastra um novo cliente (requer `pet_id` existente)          |
| PUT    | `/clientes/{id}`      | Atualiza um cliente existente                                 |
| DELETE | `/clientes/{id}`      | Remove um cliente (falha se houver agendamento vinculado)     |
| GET    | `/funcionarios`       | Lista todos os funcionários (aceita `?nome=` para busca)      |
| GET    | `/funcionarios/{id}`  | Retorna um funcionário específico pelo id                     |
| POST   | `/funcionarios`       | Cadastra um novo funcionário                                  |
| PUT    | `/funcionarios/{id}`  | Atualiza um funcionário existente                             |
| DELETE | `/funcionarios/{id}`  | Remove um funcionário                                         |
| GET    | `/agendamentos`       | Lista agendamentos (aceita `?status_filtro=` e `?completo=`)  |
| GET    | `/agendamentos/{id}`  | Retorna um agendamento específico pelo id                     |
| POST   | `/agendamentos`       | Cadastra um novo agendamento (409 se o funcionário já estiver ocupado no horário) |
| PUT    | `/agendamentos/{id}`  | Atualiza um agendamento existente (mesma regra de conflito)   |
| DELETE | `/agendamentos/{id}`  | Remove um agendamento                                         |


## Arquitetura

Arquitetura em camadas, com persistência real em SQLite via SQLAlchemy:

```
Pet-shop/
├── main.py                    # instância do FastAPI, inclui os routers e a rota raiz
├── database.py                # conexão SQLAlchemy/SQLite (engine, SessionLocal, Base, get_db)
├── models.py                  # modelos SQLAlchemy (UF, Porte, Pet, Cliente, Funcionario, Agendamento)
├── seed.py                    # popula as tabelas de domínio (ufs e portes) na inicialização
├── migrar_banco.py            # migra um pet.db antigo (uf/porte em texto) para o schema com ids
├── schemas.py                 # schemas Pydantic de entrada/saída (com validações via Field)
├── validacao.py               # mensagens de erro de validação em português
├── pet.db                      # banco SQLite local (já no schema novo)
├── routers/
│   ├── ufs.py                  # GET /ufs e /ufs/{id}
│   ├── portes.py               # GET /portes e /portes/{id}
├── .gitignore
└── README.md
```

## Como executar

```bash
pip install -r requirements.txt
fastapi dev main.py
```

Depois acesse `http://127.0.0.1:8000/docs` para testar os endpoints pelo Swagger.

O arquivo `pet.db` já vem neste projeto, migrado para o schema atual. Se preferir começar do zero, basta apagá-lo: ele é recriado (e as UFs/portes repopulados) automaticamente na próxima execução.

## Validações dos dados de entrada

Os schemas de entrada (`schemas.py`) usam `Field` do Pydantic. Quando uma regra falha, a API responde `422` com uma mensagem em português por campo (ver `validacao.py`), no formato:

```json
{"detail": [{"campo": "telefone", "mensagem": "O telefone deve conter 11 dígitos com o DDD."}]}
```

| Campo | Regra |
|-------|-------|
| `nome` (cliente, funcionário, pet) | obrigatório, sem espaços vazios, 3 a 100 caracteres |
| `raca` | obrigatório, 3 a 50 caracteres |
| `logradouro`, `servico` | obrigatório, 3 a 100 caracteres |
| `cidade` | obrigatório, 2 a 100 caracteres |
| `complemento` | opcional, até 100 caracteres |
| `observacoes` | opcional, até 255 caracteres |
| `cpf` | exatamente 11 dígitos (somente números) |
| `telefone` | exatamente 11 dígitos com DDD (somente números) |
| `cep` | exatamente 8 dígitos (somente números) |
| `email` | e-mail válido (`EmailStr`), até 100 caracteres |
| `idade`, `numero` e todos os `*_id` | número inteiro maior que zero |

> `cpf`, `telefone` e `cep` são guardados como **texto** (e não inteiro) para preservar zeros à esquerda, como em CEP `01310100`. Se você tem um `pet.db` criado antes dessa mudança, apague-o: ele é recriado automaticamente ao iniciar a API.

### Já tenho um `pet.db` do schema antigo

O `create_all` não altera tabelas existentes, então rode uma vez, antes de subir a API:

```bash
python migrar_banco.py
```

Ele faz backup em `pet.db.bak`, converte `uf`/`porte` (texto) para `uf_id`/`porte_id` e preserva todos os dados.
