from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.cartas.models import (
    CartaModelo,
    CartaModeloRede,
    CartaModeloVersao,
)


class CartaModeloRepository:
    """
    Persistência dos modelos de cartas.

    O repository executa operações de banco,
    mas não controla a transação.

    commit e rollback pertencem à camada de serviço.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_model(
        self,
        *,
        nome: str,
        tipo: str,
        granularidade: str,
    ) -> CartaModelo:
        modelo = CartaModelo(
            nome=nome,
            tipo=tipo,
            granularidade=granularidade,
            ativo=True,
        )

        self.db.add(modelo)
        self.db.flush()

        return modelo

    def add_network(
        self,
        *,
        id_modelo: uuid.UUID,
        rede: str,
        rede_normalizada: str,
    ) -> CartaModeloRede:
        associacao = CartaModeloRede(
            id_modelo=id_modelo,
            rede=rede,
            rede_normalizada=rede_normalizada,
        )

        self.db.add(associacao)
        self.db.flush()

        return associacao

    def add_version(
        self,
        *,
        id_modelo: uuid.UUID,
        id_versao: uuid.UUID,
        numero_versao: int,
        nome_arquivo_original: str,
        storage_key: str,
        mime_type: str | None,
        tamanho_bytes: int | None,
        hash_sha256: str | None,
    ) -> CartaModeloVersao:
        versao = CartaModeloVersao(
            id_versao=id_versao,
            id_modelo=id_modelo,
            numero_versao=numero_versao,
            nome_arquivo_original=nome_arquivo_original,
            storage_key=storage_key,
            mime_type=mime_type,
            tamanho_bytes=tamanho_bytes,
            hash_sha256=hash_sha256,
            ativo=True,
        )

        self.db.add(versao)
        self.db.flush()

        return versao

    def get_model(
        self,
        id_modelo: uuid.UUID,
    ) -> CartaModelo | None:
        statement = select(CartaModelo).where(
            CartaModelo.id_modelo == id_modelo
        )

        return self.db.scalar(statement)

    def list_active_models(
        self,
    ) -> list[CartaModelo]:
        statement = (
            select(CartaModelo)
            .where(CartaModelo.ativo.is_(True))
            .order_by(CartaModelo.nome)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_active_version(
        self,
        id_modelo: uuid.UUID,
    ) -> CartaModeloVersao | None:
        statement = select(CartaModeloVersao).where(
            CartaModeloVersao.id_modelo == id_modelo,
            CartaModeloVersao.ativo.is_(True),
        )

        return self.db.scalar(statement)

    def find_active_models_by_network(
        self,
        rede_normalizada: str,
    ) -> list[CartaModelo]:
        statement = (
            select(CartaModelo)
            .join(
                CartaModeloRede,
                CartaModeloRede.id_modelo
                == CartaModelo.id_modelo,
            )
            .where(
                CartaModelo.ativo.is_(True),
                CartaModeloRede.rede_normalizada
                == rede_normalizada,
            )
            .order_by(CartaModelo.nome)
        )

        return list(
            self.db.scalars(statement).all()
        )
