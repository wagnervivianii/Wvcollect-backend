import uuid
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_promotor
from app.db.dependencies import get_db
from app.models.pergunta import Pergunta
from app.models.pesquisa import Pesquisa
from app.models.promotor import Promotor
from app.models.resposta import Resposta
from app.schemas.resposta import (
    RespostaSalvaResponse,
    SalvarRespostasRequest,
    SalvarRespostasResponse,
)


router = APIRouter(
    prefix="/pesquisas",
    tags=["Respostas"],
)


@router.post(
    "/{id_pesquisa}/respostas",
    response_model=SalvarRespostasResponse,
)
def salvar_respostas(
    id_pesquisa: uuid.UUID,
    payload: SalvarRespostasRequest,
    promotor: Promotor = Depends(
        get_current_promotor
    ),
    db: Session = Depends(get_db),
) -> SalvarRespostasResponse:

    # ----------------------------------
    # PESQUISA
    # ----------------------------------

    pesquisa = db.get(
        Pesquisa,
        id_pesquisa,
    )

    if (
        pesquisa is None
        or pesquisa.id_promotor
        != promotor.id_promotor
    ):
        raise HTTPException(
            status_code=404,
            detail={
                "code":
                    "PESQUISA_NAO_ENCONTRADA",
                "message":
                    "A coleta não foi encontrada.",
            },
        )

    if (
        pesquisa.finalizada_em_dispositivo
        is not None
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "code":
                    "PESQUISA_FINALIZADA",
                "message":
                    "Esta coleta já foi finalizada.",
            },
        )

    # Evita payload acidentalmente enorme.
    if len(payload.respostas) > 100:
        raise HTTPException(
            status_code=422,
            detail={
                "code":
                    "MUITAS_RESPOSTAS",
                "message":
                    "Quantidade de respostas inválida.",
            },
        )

    agora = datetime.now(
        timezone.utc
    )

    respostas_salvas: list[
        RespostaSalvaResponse
    ] = []

    try:
        for item in payload.respostas:

            # --------------------------
            # PERGUNTA
            # --------------------------

            pergunta = db.get(
                Pergunta,
                item.id_pergunta,
            )

            if (
                pergunta is None
                or not pergunta.ativo
            ):
                raise HTTPException(
                    status_code=422,
                    detail={
                        "code":
                            "PERGUNTA_INVALIDA",
                        "message":
                            "Uma das perguntas não está disponível.",
                    },
                )

            valor = item.valor.strip()

            if not valor:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "code":
                            "RESPOSTA_VAZIA",
                        "message":
                            "Uma das respostas está vazia.",
                    },
                )

            # --------------------------
            # IDEMPOTÊNCIA PELO UUID
            # --------------------------

            existente_por_id = db.get(
                Resposta,
                item.id_resposta,
            )

            if existente_por_id is not None:
                if (
                    existente_por_id.id_pesquisa
                    != id_pesquisa
                    or existente_por_id.id_pergunta
                    != item.id_pergunta
                    or existente_por_id.id_sku
                    != item.id_sku
                ):
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "code":
                                "RESPOSTA_ID_EM_USO",
                            "message":
                                "Não foi possível salvar uma das respostas.",
                        },
                    )

                existente_por_id.valor = valor

                existente_por_id.respondida_em_dispositivo = (
                    item.respondida_em_dispositivo
                )

                existente_por_id.recebida_em_servidor = (
                    agora
                )

                resposta = existente_por_id

            else:
                # ----------------------
                # IDEMPOTÊNCIA SEMÂNTICA
                # ----------------------
                #
                # Mesmo que por algum motivo
                # o aparelho gere outro UUID,
                # pesquisa + pergunta + SKU
                # continua sendo uma única
                # resposta.
                statement = select(
                    Resposta
                ).where(
                    Resposta.id_pesquisa
                    == id_pesquisa,

                    Resposta.id_pergunta
                    == item.id_pergunta,
                )

                if item.id_sku is None:
                    statement = (
                        statement.where(
                            Resposta.id_sku.is_(
                                None
                            )
                        )
                    )
                else:
                    statement = (
                        statement.where(
                            Resposta.id_sku
                            == item.id_sku
                        )
                    )

                existente_semantica = db.scalar(
                    statement
                )

                if (
                    existente_semantica
                    is not None
                ):
                    existente_semantica.valor = (
                        valor
                    )

                    existente_semantica.respondida_em_dispositivo = (
                        item.respondida_em_dispositivo
                    )

                    existente_semantica.recebida_em_servidor = (
                        agora
                    )

                    resposta = (
                        existente_semantica
                    )

                else:
                    resposta = Resposta(
                        id_resposta=(
                            item.id_resposta
                        ),

                        id_pesquisa=(
                            id_pesquisa
                        ),

                        id_pergunta=(
                            item.id_pergunta
                        ),

                        id_sku=(
                            item.id_sku
                        ),

                        valor=valor,

                        respondida_em_dispositivo=(
                            item.respondida_em_dispositivo
                        ),

                        recebida_em_servidor=(
                            agora
                        ),
                    )

                    db.add(resposta)

            db.flush()

            respostas_salvas.append(
                RespostaSalvaResponse(
                    id_resposta=(
                        resposta.id_resposta
                    ),
                    id_pergunta=(
                        resposta.id_pergunta
                    ),
                    id_sku=(
                        resposta.id_sku
                    ),
                    valor=(
                        resposta.valor
                    ),
                    respondida_em_dispositivo=(
                        resposta
                        .respondida_em_dispositivo
                    ),
                )
            )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise

    return SalvarRespostasResponse(
        id_pesquisa=id_pesquisa,
        total_recebidas=len(
            payload.respostas
        ),
        total_salvas=len(
            respostas_salvas
        ),
        respostas=respostas_salvas,
    )