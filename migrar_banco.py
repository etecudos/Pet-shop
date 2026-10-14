"""
Migra um pet.db antigo (com colunas `uf` e `porte` em texto) para o schema novo
(tabelas `ufs` e `portes`, com `uf_id` e `porte_id`), preservando os dados.

Uso:  python migrar_banco.py
É seguro rodar mais de uma vez: se o banco já estiver no schema novo, não faz nada.
"""
import shutil
import sqlite3
import sys

from seed import PORTES, UFS

CAMINHO = "pet.db"

con = sqlite3.connect(CAMINHO)
cur = con.cursor()

tabelas = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
if not tabelas:
    print("Banco vazio: nada a migrar (as tabelas serão criadas ao iniciar a API).")
    sys.exit(0)
if "ufs" in tabelas:
    print("Banco já está no schema novo: nada a fazer.")
    sys.exit(0)

# backup de segurança antes de mexer em qualquer coisa
con.close()
shutil.copy(CAMINHO, CAMINHO + ".bak")
print(f"Backup salvo em {CAMINHO}.bak")
con = sqlite3.connect(CAMINHO)
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=OFF")
cur.execute("BEGIN")

# 1) tabelas de domínio
cur.execute("CREATE TABLE ufs (id INTEGER PRIMARY KEY AUTOINCREMENT, sigla VARCHAR(2) NOT NULL UNIQUE, nome VARCHAR NOT NULL UNIQUE)")
cur.execute("CREATE TABLE portes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome VARCHAR NOT NULL UNIQUE)")
cur.executemany("INSERT INTO ufs (sigla, nome) VALUES (?, ?)", UFS)
cur.executemany("INSERT INTO portes (nome) VALUES (?)", [(p,) for p in PORTES])

# 2) recria as tabelas com FKs e copia os dados
cur.execute("ALTER TABLE agendamentos RENAME TO agendamentos_old")
for t in ("clientes", "pets", "funcionarios"):
    cur.execute(f"ALTER TABLE {t} RENAME TO {t}_old")
    # índices antigos mantêm o nome após o rename; removê-los evita colisão
    for (ix,) in cur.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{t}_old' AND sql IS NOT NULL").fetchall():
        cur.execute(f"DROP INDEX {ix}")
for (ix,) in cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='agendamentos_old' AND sql IS NOT NULL").fetchall():
    cur.execute(f"DROP INDEX {ix}")

# usa o SQLAlchemy só para criar as tabelas novas no schema atual
from database import Base, engine  # noqa: E402
import models  # noqa: E402,F401

con.commit()
Base.metadata.create_all(bind=engine, tables=[
    models.FuncionarioModel.__table__, models.PetModel.__table__,
    models.ClienteModel.__table__, models.AgendamentoModel.__table__,
])

con = sqlite3.connect(CAMINHO)
cur = con.cursor()
cur.execute("PRAGMA foreign_keys=OFF")
cur.execute("BEGIN")
cur.execute("""INSERT INTO funcionarios (id,nome,cpf,telefone,email,cep,logradouro,numero,complemento,cidade,uf_id,data_criacao)
  SELECT f.id,f.nome,f.cpf,f.telefone,f.email,f.cep,f.logradouro,f.numero,f.complemento,f.cidade,u.id,f.data_criacao
  FROM funcionarios_old f JOIN ufs u ON u.sigla = UPPER(TRIM(f.uf))""")
cur.execute("""INSERT INTO pets (id,nome,raca,idade,porte_id,data_criacao)
  SELECT p.id,p.nome,p.raca,p.idade,o.id,p.data_criacao
  FROM pets_old p JOIN portes o ON o.nome = p.porte""")
cur.execute("""INSERT INTO clientes (id,nome,cpf,telefone,email,cep,logradouro,numero,complemento,cidade,uf_id,pet_id,data_criacao)
  SELECT c.id,c.nome,c.cpf,c.telefone,c.email,c.cep,c.logradouro,c.numero,c.complemento,c.cidade,u.id,c.pet_id,c.data_criacao
  FROM clientes_old c JOIN ufs u ON u.sigla = UPPER(TRIM(c.uf))""")
cur.execute("""INSERT INTO agendamentos (id,funcionario_id,cliente_id,servico,data_agendamento,hora_agendamento,status,observacoes,data_criacao)
  SELECT id,funcionario_id,cliente_id,servico,data_agendamento,hora_agendamento,status,observacoes,data_criacao FROM agendamentos_old""")

# confere que nenhuma linha foi perdida (ex.: UF/porte inválido no banco antigo)
for novo, antigo in (("funcionarios","funcionarios_old"),("pets","pets_old"),("clientes","clientes_old"),("agendamentos","agendamentos_old")):
    n, a = cur.execute(f"SELECT (SELECT COUNT(*) FROM {novo}), (SELECT COUNT(*) FROM {antigo})").fetchone()
    if n != a:
        con.rollback()
        con.close()
        engine.dispose()
        shutil.copy(CAMINHO + ".bak", CAMINHO)  # restaura o banco original
        sys.exit(f"ERRO: {novo} ficou com {n} linhas e o original tinha {a} (UF ou porte inválido?). Banco original restaurado.")

for t in ("agendamentos_old", "clientes_old", "pets_old", "funcionarios_old"):
    cur.execute(f"DROP TABLE {t}")
con.commit()
print("Migração concluída.")
