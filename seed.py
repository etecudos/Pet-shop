from sqlalchemy.orm import Session

from models import PorteModel, UFModel

# Tabelas de domínio: valores fixos, criados automaticamente na inicialização
PORTES = ["PEQUENO", "MEDIO", "GRANDE"]

UFS = [
    ("AC", "Acre"), ("AL", "Alagoas"), ("AP", "Amapá"), ("AM", "Amazonas"),
    ("BA", "Bahia"), ("CE", "Ceará"), ("DF", "Distrito Federal"),
    ("ES", "Espírito Santo"), ("GO", "Goiás"), ("MA", "Maranhão"),
    ("MT", "Mato Grosso"), ("MS", "Mato Grosso do Sul"), ("MG", "Minas Gerais"),
    ("PA", "Pará"), ("PB", "Paraíba"), ("PR", "Paraná"), ("PE", "Pernambuco"),
    ("PI", "Piauí"), ("RJ", "Rio de Janeiro"), ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"), ("RO", "Rondônia"), ("RR", "Roraima"),
    ("SC", "Santa Catarina"), ("SP", "São Paulo"), ("SE", "Sergipe"),
    ("TO", "Tocantins"),
]


# Idempotente: só insere o que ainda não existe
def popular_tabelas_fixas(db: Session):
    portes_existentes = {p.nome for p in db.query(PorteModel).all()}
    for nome in PORTES:
        if nome not in portes_existentes:
            db.add(PorteModel(nome=nome))

    ufs_existentes = {u.sigla for u in db.query(UFModel).all()}
    for sigla, nome in UFS:
        if sigla not in ufs_existentes:
            db.add(UFModel(sigla=sigla, nome=nome))

    db.commit()
