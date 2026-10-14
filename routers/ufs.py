from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import UFModel
from schemas import UFSchema

router = APIRouter(prefix="/ufs", tags=["UFs"])


# READ - Listar todas as UFs (tabela fixa, somente leitura)
@router.get("/", response_model=List[UFSchema], status_code=status.HTTP_200_OK)
def listar_ufs(db: Session = Depends(get_db)):
    return db.query(UFModel).order_by(UFModel.sigla).all()


# READ - Buscar uma UF pelo id
@router.get("/{uf_id}", response_model=UFSchema, status_code=status.HTTP_200_OK)
def buscar_uf_por_id(uf_id: int, db: Session = Depends(get_db)):
    uf = db.query(UFModel).filter(UFModel.id == uf_id).first()
    if not uf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UF não encontrada")
    return uf
