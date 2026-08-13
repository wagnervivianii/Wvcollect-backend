from __future__ import annotations

import uuid
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from zipfile import BadZipFile, ZipFile

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.cartas.domain import (
    CartaGranularidade,
    CartaTipo,
    normalize_display_text,
    normalize_lookup_key,
)
from app.modules.cartas.repositories import (
    CartaModeloRepository,
)
from app.modules.cartas.storage import (
    CartaLocalStorage,
    StoredCartaFile,
)


PDF_MIME_TYPE = "application/pdf"

DOCX_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document"
)


class CartaModeloValidationError(ValueError):
    pass


class CartaModeloConflictError(RuntimeError):
    pass


@dataclass(frozen=True)
class CartaModeloCreationResult:
    id_modelo: uuid.UUID
    id_versao: uuid.UUID
    storage_key: str
    hash_sha256: str
    tamanho_bytes: int


class CartaModeloService:
    """
    Casos de uso relacionados aos modelos de cartas.

    Esta camada controla a transação que envolve:
    PostgreSQL + filesystem.
    """

    def __init__(
        self,
        db: Session,
        storage: CartaLocalStorage | None = None,
    ) -> None:
        self.db = db
        self.repository = CartaModeloRepository(db)
        self.storage = storage or CartaLocalStorage()

    def create_model(
        self,
        *,
        nome: str,
        tipo: str,
        granularidade: str,
        redes: list[str],
        nome_arquivo_original: str,
        arquivo: BinaryIO,
    ) -> CartaModeloCreationResult:
        nome_validado = self._validate_name(nome)

        tipo_validado = self._validate_tipo(tipo)

        granularidade_validada = (
            self._validate_granularidade(
                granularidade
            )
        )

        redes_validadas = self._prepare_networks(
            redes
        )

        (
            extensao,
            mime_type,
            nome_arquivo_seguro,
        ) = self._validate_file(
            tipo=tipo_validado,
            nome_arquivo_original=nome_arquivo_original,
            arquivo=arquivo,
        )

        stored: StoredCartaFile | None = None

        try:
            modelo = self.repository.create_model(
                nome=nome_validado,
                tipo=tipo_validado,
                granularidade=granularidade_validada,
            )

            for rede, rede_normalizada in redes_validadas:
                self.repository.add_network(
                    id_modelo=modelo.id_modelo,
                    rede=rede,
                    rede_normalizada=rede_normalizada,
                )

            id_versao = uuid.uuid4()

            stored = self.storage.save_model_file(
                source=arquivo,
                tipo=tipo_validado,
                id_modelo=str(modelo.id_modelo),
                id_versao=str(id_versao),
                extensao=extensao,
            )

            self.repository.add_version(
                id_modelo=modelo.id_modelo,
                id_versao=id_versao,
                numero_versao=1,
                nome_arquivo_original=(
                    nome_arquivo_seguro
                ),
                storage_key=stored.storage_key,
                mime_type=mime_type,
                tamanho_bytes=stored.tamanho_bytes,
                hash_sha256=stored.hash_sha256,
            )

            self.db.commit()

            return CartaModeloCreationResult(
                id_modelo=modelo.id_modelo,
                id_versao=id_versao,
                storage_key=stored.storage_key,
                hash_sha256=stored.hash_sha256,
                tamanho_bytes=stored.tamanho_bytes,
            )

        except IntegrityError as exc:
            self.db.rollback()

            if stored is not None:
                with suppress(Exception):
                    self.storage.delete(
                        stored.storage_key
                    )

            raise CartaModeloConflictError(
                "Conflito ao persistir o modelo de carta."
            ) from exc

        except Exception:
            self.db.rollback()

            if stored is not None:
                with suppress(Exception):
                    self.storage.delete(
                        stored.storage_key
                    )

            raise

    @staticmethod
    def _validate_name(nome: str) -> str:
        value = normalize_display_text(nome)

        if not value:
            raise CartaModeloValidationError(
                "O nome do modelo é obrigatório."
            )

        if len(value) > 180:
            raise CartaModeloValidationError(
                "O nome do modelo deve ter no máximo "
                "180 caracteres."
            )

        return value

    @staticmethod
    def _validate_tipo(tipo: str) -> str:
        value = tipo.strip().upper()

        try:
            return CartaTipo(value).value
        except ValueError as exc:
            raise CartaModeloValidationError(
                "Tipo deve ser ESTATICO ou VARIAVEL."
            ) from exc

    @staticmethod
    def _validate_granularidade(
        granularidade: str,
    ) -> str:
        value = granularidade.strip().upper()

        try:
            return CartaGranularidade(value).value
        except ValueError as exc:
            raise CartaModeloValidationError(
                "Granularidade deve ser "
                "PROMOTOR_REDE ou PDV."
            ) from exc

    @staticmethod
    def _prepare_networks(
        redes: list[str],
    ) -> list[tuple[str, str]]:
        result: list[tuple[str, str]] = []
        seen: set[str] = set()

        for raw in redes:
            display = normalize_display_text(raw)
            normalized = normalize_lookup_key(raw)

            if not display or not normalized:
                continue

            if len(display) > 160:
                raise CartaModeloValidationError(
                    "O nome da rede deve ter no máximo "
                    "160 caracteres."
                )

            if normalized in seen:
                continue

            seen.add(normalized)

            result.append(
                (
                    display,
                    normalized,
                )
            )

        if not result:
            raise CartaModeloValidationError(
                "Informe pelo menos uma rede."
            )

        return result

    @staticmethod
    def _validate_file(
        *,
        tipo: str,
        nome_arquivo_original: str,
        arquivo: BinaryIO,
    ) -> tuple[str, str, str]:
        filename = Path(
            nome_arquivo_original
        ).name.strip()

        if not filename:
            raise CartaModeloValidationError(
                "O nome do arquivo é obrigatório."
            )

        if len(filename) > 255:
            raise CartaModeloValidationError(
                "O nome do arquivo deve ter no máximo "
                "255 caracteres."
            )

        extension = Path(filename).suffix.lower()

        if tipo == CartaTipo.ESTATICO.value:
            if extension != ".pdf":
                raise CartaModeloValidationError(
                    "Modelos estáticos devem utilizar "
                    "arquivo PDF."
                )

            CartaModeloService._validate_pdf(
                arquivo
            )

            return (
                extension,
                PDF_MIME_TYPE,
                filename,
            )

        if extension != ".docx":
            raise CartaModeloValidationError(
                "Modelos variáveis devem utilizar "
                "arquivo DOCX."
            )

        CartaModeloService._validate_docx(
            arquivo
        )

        return (
            extension,
            DOCX_MIME_TYPE,
            filename,
        )

    @staticmethod
    def _validate_pdf(
        arquivo: BinaryIO,
    ) -> None:
        try:
            arquivo.seek(0)
            signature = arquivo.read(5)
        finally:
            arquivo.seek(0)

        if signature != b"%PDF-":
            raise CartaModeloValidationError(
                "O arquivo informado não é um PDF válido."
            )

    @staticmethod
    def _validate_docx(
        arquivo: BinaryIO,
    ) -> None:
        try:
            arquivo.seek(0)

            with ZipFile(arquivo) as docx:
                names = set(docx.namelist())

                required = {
                    "[Content_Types].xml",
                    "word/document.xml",
                }

                if not required.issubset(names):
                    raise CartaModeloValidationError(
                        "O arquivo informado não é um "
                        "DOCX válido."
                    )

        except BadZipFile as exc:
            raise CartaModeloValidationError(
                "O arquivo informado não é um DOCX válido."
            ) from exc

        finally:
            arquivo.seek(0)
