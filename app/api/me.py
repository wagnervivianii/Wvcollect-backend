from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_promotor
from app.db.dependencies import get_db
from app.models.pdv import PDV
from app.models.pesquisa import Pesquisa
from app.models.promotor import Promotor
from app.models.roteiro import Roteiro
from app.schemas.auth import PromotorResponse
from app.schemas.roteiro import (
    PDVRoteiroResponse,
    RoteiroResponse,
)


router = APIRouter(
    prefix="/me",
    tags=["Promotor"],
)


@router.get(
    "",
    response_model=PromotorResponse,
)
def get_me(
    promotor: Promotor = Depends(
        get_current_promotor
    ),
) -> PromotorResponse:
    return PromotorResponse(
        id_promotor=promotor.id_promotor,
        nome=promotor.nome,
    )


@router.get(
    "/roteiro",
    response_model=RoteiroResponse,
)
def get_meu_roteiro(
    promotor: Promotor = Depends(
        get_current_promotor
    ),
    db: Session = Depends(get_db),
) -> RoteiroResponse:

    # -------------------------------------------------
    # COLETAS CONCLUÍDAS
    # -------------------------------------------------
    #
    # Resume somente pesquisas realmente finalizadas.
    #
    # Mantemos:
    # - quantidade de coletas concluídas;
    # - data/hora da última coleta concluída.
    resumo_coletas = (
        select(
            Pesquisa.id_roteiro.label(
                "id_roteiro"
            ),
            func.count(
                Pesquisa.id_pesquisa
            ).label(
                "coletas_realizadas"
            ),
            func.max(
                Pesquisa.finalizada_em_dispositivo
            ).label(
                "ultima_coleta_em"
            ),
        )
        .where(
            Pesquisa.finalizada_em_dispositivo.is_not(
                None
            )
        )
        .group_by(
            Pesquisa.id_roteiro
        )
        .subquery()
    )

    # -------------------------------------------------
    # COLETA EM ANDAMENTO
    # -------------------------------------------------
    #
    # Uma pesquisa iniciada, mas ainda não finalizada,
    # precisa aparecer no roteiro como EM_ANDAMENTO.
    #
    # Usamos row_number para garantir que, mesmo se
    # houver alguma inconsistência histórica e mais
    # de uma pesquisa aberta para o mesmo roteiro,
    # somente a mais recente seja apresentada.
    pesquisas_abertas_ranked = (
        select(
            Pesquisa.id_roteiro.label(
                "id_roteiro"
            ),
            Pesquisa.id_pesquisa.label(
                "id_pesquisa"
            ),
            Pesquisa.numero_coleta.label(
                "numero_coleta"
            ),
            Pesquisa.iniciada_em_dispositivo.label(
                "iniciada_em_dispositivo"
            ),
            func.row_number()
            .over(
                partition_by=Pesquisa.id_roteiro,
                order_by=(
                    Pesquisa.iniciada_em_dispositivo.desc()
                ),
            )
            .label("rn"),
        )
        .where(
            Pesquisa.finalizada_em_dispositivo.is_(
                None
            ),
            Pesquisa.status
            == "EM_PREENCHIMENTO",
        )
        .subquery()
    )

    pesquisa_aberta = (
        select(
            pesquisas_abertas_ranked.c.id_roteiro,
            pesquisas_abertas_ranked.c.id_pesquisa,
            pesquisas_abertas_ranked.c.numero_coleta,
            pesquisas_abertas_ranked.c.iniciada_em_dispositivo,
        )
        .where(
            pesquisas_abertas_ranked.c.rn
            == 1
        )
        .subquery()
    )

    # -------------------------------------------------
    # ROTEIRO DO PROMOTOR
    # -------------------------------------------------

    statement = (
        select(
            Roteiro,
            PDV,
            func.coalesce(
                resumo_coletas.c.coletas_realizadas,
                0,
            ).label(
                "coletas_realizadas"
            ),
            resumo_coletas.c.ultima_coleta_em,
            pesquisa_aberta.c.id_pesquisa.label(
                "id_pesquisa_em_andamento"
            ),
            pesquisa_aberta.c.numero_coleta.label(
                "numero_coleta_em_andamento"
            ),
            pesquisa_aberta.c.iniciada_em_dispositivo.label(
                "iniciada_em_dispositivo"
            ),
        )
        .join(
            PDV,
            PDV.id_pdv
            == Roteiro.id_pdv,
        )
        .outerjoin(
            resumo_coletas,
            resumo_coletas.c.id_roteiro
            == Roteiro.id_roteiro,
        )
        .outerjoin(
            pesquisa_aberta,
            pesquisa_aberta.c.id_roteiro
            == Roteiro.id_roteiro,
        )
        .where(
            Roteiro.id_promotor
            == promotor.id_promotor,
            Roteiro.ativo.is_(True),
            PDV.ativo.is_(True),
        )
        .order_by(
            PDV.nome_pdv
        )
    )

    rows = db.execute(
        statement
    ).all()

    pdvs = []

    for (
        roteiro,
        pdv,
        coletas_realizadas,
        ultima_coleta_em,
        id_pesquisa_em_andamento,
        numero_coleta_em_andamento,
        iniciada_em_dispositivo,
    ) in rows:

        quantidade = int(
            coletas_realizadas or 0
        )

        # A pesquisa aberta sempre tem prioridade.
        #
        # Uma loja pode, por exemplo, ter:
        #
        # 1 coleta concluída
        # +
        # uma recoleta atualmente em andamento.
        if (
            id_pesquisa_em_andamento
            is not None
        ):
            status_coleta = (
                "EM_ANDAMENTO"
            )

        elif quantidade > 0:
            status_coleta = (
                "CONCLUIDA"
            )

        else:
            status_coleta = (
                "PENDENTE"
            )

        pdvs.append(
            PDVRoteiroResponse(
                id_roteiro=(
                    roteiro.id_roteiro
                ),
                id_pdv=pdv.id_pdv,
                codigo_origem=(
                    pdv.codigo_origem
                ),
                cnpj=pdv.cnpj,
                nome_pdv=pdv.nome_pdv,
                endereco=pdv.endereco,
                bairro=pdv.bairro,
                cidade=pdv.cidade,
                uf=pdv.uf,
                latitude=(
                    float(pdv.latitude)
                    if pdv.latitude
                    is not None
                    else None
                ),
                longitude=(
                    float(pdv.longitude)
                    if pdv.longitude
                    is not None
                    else None
                ),
                data_inicio=(
                    roteiro.data_inicio
                ),
                data_fim=(
                    roteiro.data_fim
                ),
                status_coleta=(
                    status_coleta
                ),
                coletas_realizadas=(
                    quantidade
                ),
                ultima_coleta_em=(
                    ultima_coleta_em
                ),
                id_pesquisa_em_andamento=(
                    id_pesquisa_em_andamento
                ),
                numero_coleta_em_andamento=(
                    numero_coleta_em_andamento
                ),
                iniciada_em_dispositivo=(
                    iniciada_em_dispositivo
                ),
            )
        )

    return RoteiroResponse(
        total=len(pdvs),
        pdvs=pdvs,
    )