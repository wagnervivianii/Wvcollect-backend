from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


@dataclass(frozen=True)
class StoredCartaFile:
    storage_key: str
    tamanho_bytes: int
    hash_sha256: str


class CartaLocalStorage:
    """
    Storage local dos arquivos pertencentes ao domínio Cartas.

    O PostgreSQL armazena somente a storage_key e os metadados.
    O conteúdo físico permanece no filesystem.
    """

    def __init__(
        self,
        root: str | Path | None = None,
    ) -> None:
        project_root = Path(__file__).resolve().parents[4]

        configured_root = root or os.getenv(
            "WVCOLLECT_CARTAS_STORAGE_DIR",
            "storage/cartas",
        )

        storage_root = Path(configured_root)

        if not storage_root.is_absolute():
            storage_root = project_root / storage_root

        self.root = storage_root.resolve()

    @staticmethod
    def _category_for_tipo(tipo: str) -> str:
        tipo_normalizado = tipo.strip().upper()

        if tipo_normalizado == "ESTATICO":
            return "estaticos"

        if tipo_normalizado == "VARIAVEL":
            return "variaveis"

        raise ValueError(
            f"Tipo de modelo não suportado: {tipo}"
        )

    def save_model_file(
        self,
        *,
        source: BinaryIO,
        tipo: str,
        id_modelo: str,
        id_versao: str,
        extensao: str,
    ) -> StoredCartaFile:
        category = self._category_for_tipo(tipo)

        extension = extensao.strip().lower()

        if not extension.startswith("."):
            extension = f".{extension}"

        target_dir = (
            self.root
            / "modelos"
            / category
            / str(id_modelo)
        )

        target_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = f"{id_versao}{extension}"
        target = target_dir / filename

        temporary = target.with_suffix(
            target.suffix + ".part"
        )

        digest = hashlib.sha256()
        tamanho = 0

        try:
            source.seek(0)

            with temporary.open("wb") as destination:
                while True:
                    chunk = source.read(1024 * 1024)

                    if not chunk:
                        break

                    destination.write(chunk)
                    digest.update(chunk)
                    tamanho += len(chunk)

            temporary.replace(target)

        except Exception:
            temporary.unlink(missing_ok=True)
            raise

        storage_key = target.relative_to(
            self.root
        ).as_posix()

        return StoredCartaFile(
            storage_key=storage_key,
            tamanho_bytes=tamanho,
            hash_sha256=digest.hexdigest(),
        )

    def resolve(self, storage_key: str) -> Path:
        candidate = (
            self.root / storage_key
        ).resolve()

        if not candidate.is_relative_to(self.root):
            raise ValueError(
                "Storage key fora da raiz permitida."
            )

        return candidate

    def delete(self, storage_key: str) -> None:
        target = self.resolve(storage_key)

        target.unlink(missing_ok=True)

        parent = target.parent

        while (
            parent != self.root
            and parent.is_relative_to(self.root)
        ):
            try:
                parent.rmdir()
            except OSError:
                break

            parent = parent.parent

    def clear_model_directory(
        self,
        *,
        tipo: str,
        id_modelo: str,
    ) -> None:
        category = self._category_for_tipo(tipo)

        target = (
            self.root
            / "modelos"
            / category
            / str(id_modelo)
        ).resolve()

        if not target.is_relative_to(self.root):
            raise ValueError(
                "Diretório fora da raiz permitida."
            )

        if target.exists():
            shutil.rmtree(target)
