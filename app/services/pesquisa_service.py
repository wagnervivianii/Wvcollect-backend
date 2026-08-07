import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.pesquisa import Pesquisa
from app.models.roteiro import Roteiro
from app.schemas.pesquisa import (
    FinalizarPesquisaRequest,
    IniciarPesquisaRequest,
)


class RoteiroNaoEncontradoError(Exception):
    pass


class PesquisaNaoEncontradaError(Exception):
    pass


class PesquisaIdEmUsoError(Exception):
    pass


class HorarioFinalInvalidoError(Exception):
    pass


class PendenciasConfirmacaoNecessariaError(Exception):
    def __init__(
        self,
        campos_pendentes: list[str],
    ) -> None:
        self.campos_pendentes = campos_pendentes

        super().__init__(
            "Existem campos sem preenchimento."
        )


class ConfirmacaoPendenciasInvalidaError(Exception):
    pass


class ColetaEmAndamentoError(Exception):
    def __init__(
        self,
        id_pesquisa: uuid.UUID,
    ) -> None:
        self.id_pesquisa = id_pesquisa

        super().__init__(
            "Já existe uma coleta em andamento para esta loja."
        )


class RecoletaConfirmacaoNecessariaError(Exception):
    def __init__(
        self,
        coletas_realizadas: int,
        ultima_coleta_em: datetime | None,
    ) -> None:
        self.coletas_realizadas = coletas_realizadas
        self.ultima_coleta_em = ultima_coleta_em

        super().__init__(
            "Esta loja já possui coleta concluída."
        )


@dataclass
class InicioPesquisaResultado:
    pesquisa: Pesquisa
    coletas_anteriores: int


@dataclass
class FinalizacaoPesquisaResultado:
    pesquisa: Pesquisa
    duracao_segundos: int


def iniciar_pesquisa(
    db: Session,
    id_promotor: uuid.UUID,
    payload: IniciarPesquisaRequest,
) -> InicioPesquisaResultado:
    """
    Inicia uma nova pesquisa.

    Regras:
    - O roteiro deve pertencer ao promotor autenticado.
    - O UUID da pesquisa é gerado pelo celular.
    - Repetição da mesma requisição não duplica pesquisa.
    - Pesquisa anterior nunca é sobrescrita.
    - Recoleta exige confirmação.
    """

    pesquisa_existente = db.get(
        Pesquisa,
        payload.id_pesquisa,
    )

    if pesquisa_existente is not None:
        if (
            pesquisa_existente.id_promotor
            != id_promotor
            or pesquisa_existente.id_roteiro
            != payload.id_roteiro
        ):
            raise PesquisaIdEmUsoError(
                "O UUID da pesquisa já está sendo usado."
            )

        coletas_anteriores = db.scalar(
            select(
                func.count(
                    Pesquisa.id_pesquisa
                )
            ).where(
                Pesquisa.id_roteiro
                == pesquisa_existente.id_roteiro,

                Pesquisa.id_pesquisa
                != pesquisa_existente.id_pesquisa,

                Pesquisa.finalizada_em_dispositivo
                .is_not(None),
            )
        )

        return InicioPesquisaResultado(
            pesquisa=pesquisa_existente,
            coletas_anteriores=int(
                coletas_anteriores or 0
            ),
        )

    roteiro = db.scalar(
        select(Roteiro)
        .where(
            Roteiro.id_roteiro
            == payload.id_roteiro,

            Roteiro.id_promotor
            == id_promotor,

            Roteiro.ativo.is_(True),
        )
        .with_for_update()
    )

    if roteiro is None:
        raise RoteiroNaoEncontradoError(
            "Roteiro não encontrado."
        )

    pesquisa_em_andamento = db.scalar(
        select(Pesquisa)
        .where(
            Pesquisa.id_roteiro
            == roteiro.id_roteiro,

            Pesquisa.finalizada_em_dispositivo
            .is_(None),

            Pesquisa.status
            == "EM_PREENCHIMENTO",
        )
        .order_by(
            Pesquisa.iniciada_em_dispositivo.desc()
        )
        .limit(1)
    )

    if pesquisa_em_andamento is not None:
        raise ColetaEmAndamentoError(
            pesquisa_em_andamento.id_pesquisa
        )

    resumo = db.execute(
        select(
            func.count(
                Pesquisa.id_pesquisa
            ),
            func.max(
                Pesquisa.finalizada_em_dispositivo
            ),
        ).where(
            Pesquisa.id_roteiro
            == roteiro.id_roteiro,

            Pesquisa.finalizada_em_dispositivo
            .is_not(None),
        )
    ).one()

    coletas_anteriores = int(
        resumo[0] or 0
    )

    ultima_coleta_em = resumo[1]

    if (
        coletas_anteriores > 0
        and not payload.confirmar_recoleta
    ):
        raise RecoletaConfirmacaoNecessariaError(
            coletas_realizadas=coletas_anteriores,
            ultima_coleta_em=ultima_coleta_em,
        )

    maior_numero = db.scalar(
        select(
            func.max(
                Pesquisa.numero_coleta
            )
        ).where(
            Pesquisa.id_roteiro
            == roteiro.id_roteiro
        )
    )

    numero_coleta = (
        int(maior_numero or 0) + 1
    )

    id_pesquisa_origem = None

    if coletas_anteriores > 0:
        pesquisa_original = db.scalar(
            select(Pesquisa)
            .where(
                Pesquisa.id_roteiro
                == roteiro.id_roteiro,

                Pesquisa.numero_coleta == 1,
            )
            .order_by(
                Pesquisa.iniciada_em_dispositivo
            )
            .limit(1)
        )

        if pesquisa_original is not None:
            id_pesquisa_origem = (
                pesquisa_original.id_pesquisa
            )

    pesquisa = Pesquisa(
        id_pesquisa=payload.id_pesquisa,
        id_roteiro=roteiro.id_roteiro,
        id_promotor=id_promotor,
        id_pdv=roteiro.id_pdv,

        numero_coleta=numero_coleta,

        id_pesquisa_origem=(
            id_pesquisa_origem
        ),

        status="EM_PREENCHIMENTO",

        latitude_inicio=(
            payload.latitude_inicio
        ),

        longitude_inicio=(
            payload.longitude_inicio
        ),

        precisao_inicio_metros=(
            payload.precisao_inicio_metros
        ),

        iniciada_em_dispositivo=(
            payload.iniciada_em_dispositivo
        ),

        recebida_em_servidor=(
            datetime.now(timezone.utc)
        ),

        device_id=payload.device_id,
        app_version=payload.app_version,

        criada_offline=(
            payload.criada_offline
        ),
    )

    db.add(pesquisa)
    db.commit()
    db.refresh(pesquisa)

    return InicioPesquisaResultado(
        pesquisa=pesquisa,
        coletas_anteriores=(
            coletas_anteriores
        ),
    )


def finalizar_pesquisa(
    db: Session,
    id_promotor: uuid.UUID,
    id_pesquisa: uuid.UUID,
    payload: FinalizarPesquisaRequest,
) -> FinalizacaoPesquisaResultado:
    """
    Finaliza uma pesquisa existente.

    Regras:
    - O horário de início nunca é alterado.
    - O horário final vem do aparelho.
    - Se houver pendências, o promotor precisa
      confirmar conscientemente o envio.
    - A decisão e os campos faltantes ficam
      registrados para auditoria.
    - Retry da mesma finalização é idempotente.
    """

    pesquisa = db.scalar(
        select(Pesquisa)
        .where(
            Pesquisa.id_pesquisa
            == id_pesquisa,

            Pesquisa.id_promotor
            == id_promotor,
        )
        .with_for_update()
    )

    if pesquisa is None:
        raise PesquisaNaoEncontradaError(
            "Pesquisa não encontrada."
        )

    # ----------------------------------
    # FINALIZAÇÃO JÁ REGISTRADA
    # ----------------------------------
    #
    # Retry de sincronização não altera
    # horários nem auditoria já gravada.
    if (
        pesquisa.finalizada_em_dispositivo
        is not None
    ):
        duracao = (
            pesquisa.finalizada_em_dispositivo
            - pesquisa.iniciada_em_dispositivo
        )

        return FinalizacaoPesquisaResultado(
            pesquisa=pesquisa,
            duracao_segundos=max(
                0,
                int(
                    duracao.total_seconds()
                ),
            ),
        )

    # ----------------------------------
    # HORÁRIO
    # ----------------------------------

    if (
        payload.finalizada_em_dispositivo
        < pesquisa.iniciada_em_dispositivo
    ):
        raise HorarioFinalInvalidoError(
            "O horário final não pode ser anterior ao início."
        )

    # ----------------------------------
    # NORMALIZA PENDÊNCIAS
    # ----------------------------------
    #
    # Remove:
    # - textos vazios;
    # - espaços excedentes;
    # - duplicidades.
    #
    # Mantém a ordem em que o aplicativo
    # enviou os campos.
    campos_pendentes: list[str] = []

    campos_vistos: set[str] = set()

    for campo in payload.campos_pendentes:
        campo_limpo = campo.strip()

        if not campo_limpo:
            continue

        chave = campo_limpo.casefold()

        if chave in campos_vistos:
            continue

        campos_vistos.add(chave)

        campos_pendentes.append(
            campo_limpo
        )

    possui_pendencias = (
        len(campos_pendentes) > 0
    )

    # ----------------------------------
    # EXIGE CONFIRMAÇÃO
    # ----------------------------------

    if (
        possui_pendencias
        and not
        payload.confirmar_envio_com_pendencias
    ):
        raise PendenciasConfirmacaoNecessariaError(
            campos_pendentes=campos_pendentes
        )

    # Se afirmou que confirmou o envio
    # incompleto, precisamos também do
    # horário dessa confirmação no aparelho.
    if (
        possui_pendencias
        and payload.confirmar_envio_com_pendencias
        and payload
        .pendencias_confirmadas_em_dispositivo
        is None
    ):
        raise ConfirmacaoPendenciasInvalidaError(
            "O horário de confirmação das pendências não foi informado."
        )

    # Se não existem pendências, ignoramos
    # qualquer confirmação enviada por engano.
    if not possui_pendencias:
        envio_com_pendencias = False
        pendencias_confirmadas_em = None
        campos_para_gravar = None

    else:
        envio_com_pendencias = True

        pendencias_confirmadas_em = (
            payload
            .pendencias_confirmadas_em_dispositivo
        )

        campos_para_gravar = (
            campos_pendentes
        )

    # ----------------------------------
    # FINALIZAÇÃO
    # ----------------------------------

    pesquisa.finalizada_em_dispositivo = (
        payload.finalizada_em_dispositivo
    )

    pesquisa.latitude_fim = (
        payload.latitude_fim
    )

    pesquisa.longitude_fim = (
        payload.longitude_fim
    )

    pesquisa.precisao_fim_metros = (
        payload.precisao_fim_metros
    )

    # ----------------------------------
    # AUDITORIA DE PENDÊNCIAS
    # ----------------------------------

    pesquisa.envio_com_pendencias = (
        envio_com_pendencias
    )

    pesquisa.campos_pendentes = (
        campos_para_gravar
    )

    pesquisa.pendencias_confirmadas_em_dispositivo = (
        pendencias_confirmadas_em
    )

    # A coleta terminou no aparelho.
    pesquisa.status = "FINALIZADA_LOCAL"

    pesquisa.recebida_em_servidor = (
        datetime.now(timezone.utc)
    )

    db.commit()
    db.refresh(pesquisa)

    duracao = (
        pesquisa.finalizada_em_dispositivo
        - pesquisa.iniciada_em_dispositivo
    )

    return FinalizacaoPesquisaResultado(
        pesquisa=pesquisa,
        duracao_segundos=max(
            0,
            int(
                duracao.total_seconds()
            ),
        ),
    )