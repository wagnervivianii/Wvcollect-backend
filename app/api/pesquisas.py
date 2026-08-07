import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_promotor,
)
from app.db.dependencies import get_db
from app.models.promotor import Promotor
from app.schemas.pesquisa import (
    FinalizarPesquisaRequest,
    IniciarPesquisaRequest,
    PesquisaFinalizadaResponse,
    PesquisaIniciadaResponse,
)
from app.services.pesquisa_service import (
    ColetaEmAndamentoError,
    ConfirmacaoPendenciasInvalidaError,
    HorarioFinalInvalidoError,
    PendenciasConfirmacaoNecessariaError,
    PesquisaIdEmUsoError,
    PesquisaNaoEncontradaError,
    RecoletaConfirmacaoNecessariaError,
    RoteiroNaoEncontradoError,
    finalizar_pesquisa,
    iniciar_pesquisa,
)


router = APIRouter(
    prefix="/pesquisas",
    tags=["Pesquisas"],
)


@router.post(
    "/iniciar",
    response_model=PesquisaIniciadaResponse,
    status_code=status.HTTP_201_CREATED,
)
def iniciar(
    payload: IniciarPesquisaRequest,
    promotor: Promotor = Depends(
        get_current_promotor
    ),
    db: Session = Depends(get_db),
) -> PesquisaIniciadaResponse:
    try:
        resultado = iniciar_pesquisa(
            db=db,
            id_promotor=promotor.id_promotor,
            payload=payload,
        )

    except RoteiroNaoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ROTEIRO_NAO_ENCONTRADO",
                "message": (
                    "Esta loja não está disponível "
                    "no seu roteiro."
                ),
            },
        )

    except PesquisaIdEmUsoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PESQUISA_ID_EM_USO",
                "message": (
                    "Não foi possível iniciar a coleta. "
                    "Tente novamente."
                ),
            },
        )

    except ColetaEmAndamentoError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "COLETA_EM_ANDAMENTO",
                "message": (
                    "Já existe uma coleta em andamento "
                    "para esta loja."
                ),
                "id_pesquisa": str(
                    error.id_pesquisa
                ),
            },
        )

    except (
        RecoletaConfirmacaoNecessariaError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": (
                    "RECOLETA_CONFIRMACAO_NECESSARIA"
                ),
                "message": (
                    "Esta loja já possui coleta concluída. "
                    "Deseja coletar novamente?"
                ),
                "coletas_realizadas": (
                    error.coletas_realizadas
                ),
                "ultima_coleta_em": (
                    error.ultima_coleta_em.isoformat()
                    if error.ultima_coleta_em
                    else None
                ),
            },
        )

    pesquisa = resultado.pesquisa

    return PesquisaIniciadaResponse(
        id_pesquisa=pesquisa.id_pesquisa,
        id_roteiro=pesquisa.id_roteiro,
        id_pdv=pesquisa.id_pdv,
        numero_coleta=pesquisa.numero_coleta,
        id_pesquisa_origem=(
            pesquisa.id_pesquisa_origem
        ),
        status=pesquisa.status,
        iniciada_em_dispositivo=(
            pesquisa.iniciada_em_dispositivo
        ),
        recoleta=(
            pesquisa.numero_coleta > 1
        ),
        coletas_anteriores=(
            resultado.coletas_anteriores
        ),
    )


@router.post(
    "/{id_pesquisa}/finalizar",
    response_model=PesquisaFinalizadaResponse,
)
def finalizar(
    id_pesquisa: uuid.UUID,
    payload: FinalizarPesquisaRequest,
    promotor: Promotor = Depends(
        get_current_promotor
    ),
    db: Session = Depends(get_db),
) -> PesquisaFinalizadaResponse:
    try:
        resultado = finalizar_pesquisa(
            db=db,
            id_promotor=promotor.id_promotor,
            id_pesquisa=id_pesquisa,
            payload=payload,
        )

    except PesquisaNaoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PESQUISA_NAO_ENCONTRADA",
                "message": (
                    "A coleta não foi encontrada."
                ),
            },
        )

    except HorarioFinalInvalidoError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "HORARIO_FINAL_INVALIDO",
                "message": (
                    "Não foi possível finalizar a coleta. "
                    "Verifique a data e hora do aparelho."
                ),
            },
        )

    except (
        PendenciasConfirmacaoNecessariaError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": (
                    "PENDENCIAS_CONFIRMACAO_NECESSARIA"
                ),
                "message": (
                    "Existem campos sem preenchimento. "
                    "Confirme se deseja enviar mesmo assim."
                ),
                "campos_pendentes": (
                    error.campos_pendentes
                ),
            },
        )

    except ConfirmacaoPendenciasInvalidaError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": (
                    "CONFIRMACAO_PENDENCIAS_INVALIDA"
                ),
                "message": (
                    "Não foi possível confirmar o envio "
                    "com pendências."
                ),
            },
        )

    pesquisa = resultado.pesquisa

    return PesquisaFinalizadaResponse(
        id_pesquisa=pesquisa.id_pesquisa,
        id_roteiro=pesquisa.id_roteiro,
        id_pdv=pesquisa.id_pdv,
        numero_coleta=pesquisa.numero_coleta,
        status=pesquisa.status,
        iniciada_em_dispositivo=(
            pesquisa.iniciada_em_dispositivo
        ),
        finalizada_em_dispositivo=(
            pesquisa.finalizada_em_dispositivo
        ),
        duracao_segundos=(
            resultado.duracao_segundos
        ),
        recoleta=(
            pesquisa.numero_coleta > 1
        ),
        envio_com_pendencias=(
            pesquisa.envio_com_pendencias
        ),
        campos_pendentes=(
            pesquisa.campos_pendentes
            or []
        ),
        pendencias_confirmadas_em_dispositivo=(
            pesquisa
            .pendencias_confirmadas_em_dispositivo
        ),
    )