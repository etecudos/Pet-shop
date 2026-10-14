from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import PorteModel
from schemas import PorteSchema

router = APIRouter(prefix="/portes", tags=["Portes"])


# READ - Listar todos os portes (tabela fixa, somente leitura)
@router.get("/", response_model=List[PorteSchema], status_code=status.HTTP_200_OK)
def listar_portes(db: Session = Depends(get_db)):
    return db.query(PorteModel).order_by(PorteModel.id).all()


# READ - Buscar um porte pelo id
@router.get("/{porte_id}", response_model=PorteSchema, status_code=status.HTTP_200_OK)
def buscar_porte_por_id(porte_id: int, db: Session = Depends(get_db)):
    porte = db.query(PorteModel).filter(PorteModel.id == porte_id).first()
    if not porte:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Porte não encontrado")
    return porte
