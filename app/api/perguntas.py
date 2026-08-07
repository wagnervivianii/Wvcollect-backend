from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_promotor
from app.db.dependencies import get_db
from app.models.pergunta import Pergunta
from app.schemas.resposta import (
    ListaPerguntasResponse,
    PerguntaColetaResponse,
)


router = APIRouter(
    prefix="/perguntas",
    tags=["perguntas"],
)


@router.get(
    "/coleta",
    response_model=ListaPerguntasResponse,
)
def listar_perguntas_coleta(
    _promotor=Depends(get_current_promotor),
    db: Session = Depends(get_db),
) -> ListaPerguntasResponse:
    perguntas = db.scalars(
        select(Pergunta)
        .where(
            Pergunta.ativo.is_(True),
        )
        .order_by(
            Pergunta.ordem,
        )
    ).all()

    itens = [
        PerguntaColetaResponse(
            id_pergunta=pergunta.id_pergunta,
            codigo=pergunta.codigo,
            texto=pergunta.texto,
            tipo_resposta=pergunta.tipo_resposta,
            aplica_sku=pergunta.aplica_sku,
            obrigatoria=pergunta.obrigatoria,
            ordem=pergunta.ordem,
        )
        for pergunta in perguntas
    ]

    return ListaPerguntasResponse(
        total=len(itens),
        perguntas=itens,
    )