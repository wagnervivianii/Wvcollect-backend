import hashlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_promotor
from app.db.dependencies import get_db
from app.models.foto import Foto
from app.models.pesquisa import Pesquisa
from app.models.promotor import Promotor


router = APIRouter(
    prefix="/pesquisas",
    tags=["Fotos"],
)


MAX_FOTOS_POR_TIPO = 10

MAX_TAMANHO_BYTES = (
    2 * 1024 * 1024
)

TIPOS_PERMITIDOS = {
    "ANTES",
    "DEPOIS",
    "PONTO_EXTRA",
    "GIRO_ESTOQUE",
}


STORAGE_ROOT = Path(
    os.getenv(
        "WVCOLLECT_STORAGE_DIR",
        "storage/fotos",
    )
).resolve()


def montar_resposta(
    foto: Foto,
) -> dict:
    return {
        "id_foto": str(
            foto.id_foto
        ),
        "id_pesquisa": str(
            foto.id_pesquisa
        ),
        "tipo_evidencia":
            foto.tipo_evidencia,
        "storage_key":
            foto.storage_key,
        "arquivo_url":
            foto.arquivo_url,
        "mime_type":
            foto.mime_type,
        "tamanho_bytes":
            foto.tamanho_bytes,
        "hash_sha256":
            foto.hash_sha256,
        "capturada_em_dispositivo":
            foto
            .capturada_em_dispositivo,
        "recebida_em_servidor":
            foto
            .recebida_em_servidor,
        "status_upload":
            foto.status_upload,
    }


@router.post(
    "/{id_pesquisa}/fotos",
    status_code=status.HTTP_201_CREATED,
)
async def enviar_foto(
    id_pesquisa: uuid.UUID,

    id_foto: uuid.UUID = Form(...),

    tipo_evidencia: str = Form(...),

    capturada_em_dispositivo:
        datetime = Form(...),

    latitude:
        float | None = Form(None),

    longitude:
        float | None = Form(None),

    precisao_metros:
        float | None = Form(None),

    arquivo: UploadFile = File(...),

    promotor: Promotor = Depends(
        get_current_promotor
    ),

    db: Session = Depends(
        get_db
    ),
) -> dict:

    # -------------------------------------
    # PESQUISA
    # -------------------------------------

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

    # -------------------------------------
    # TIPO DA FOTO
    # -------------------------------------

    tipo = (
        tipo_evidencia
        .strip()
        .upper()
    )

    if tipo not in TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=422,
            detail={
                "code":
                    "TIPO_FOTO_INVALIDO",

                "message":
                    "Tipo de foto inválido.",
            },
        )

    # -------------------------------------
    # IDEMPOTÊNCIA
    # -------------------------------------
    #
    # Se o mesmo UUID de foto for enviado
    # novamente por falha de rede/retry,
    # não criamos uma segunda foto.

    existente = db.get(
        Foto,
        id_foto,
    )

    if existente is not None:
        if (
            existente.id_pesquisa
            != id_pesquisa
        ):
            raise HTTPException(
                status_code=409,
                detail={
                    "code":
                        "FOTO_ID_EM_USO",

                    "message":
                        "Não foi possível enviar a foto.",
                },
            )

        return montar_resposta(
            existente
        )

    # -------------------------------------
    # LIMITE DE 10 POR TIPO
    # -------------------------------------

    quantidade = db.scalar(
        select(
            func.count(
                Foto.id_foto
            )
        ).where(
            Foto.id_pesquisa
            == id_pesquisa,

            Foto.tipo_evidencia
            == tipo,
        )
    )

    if (
        int(quantidade or 0)
        >= MAX_FOTOS_POR_TIPO
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "code":
                    "LIMITE_FOTOS_ATINGIDO",

                "message":
                    "O limite de 10 fotos para esta etapa foi atingido.",
            },
        )

    # -------------------------------------
    # ARQUIVO
    # -------------------------------------

    conteudo = await arquivo.read(
        MAX_TAMANHO_BYTES + 1
    )

    if (
        len(conteudo)
        > MAX_TAMANHO_BYTES
    ):
        raise HTTPException(
            status_code=413,
            detail={
                "code":
                    "FOTO_MUITO_GRANDE",

                "message":
                    "A foto ultrapassa o limite de 2 MB.",
            },
        )

    if not conteudo:
        raise HTTPException(
            status_code=422,
            detail={
                "code":
                    "FOTO_VAZIA",

                "message":
                    "A foto recebida está vazia.",
            },
        )

    mime_type = (
        arquivo.content_type
        or "image/jpeg"
    )

    if mime_type not in {
        "image/jpeg",
        "image/jpg",
    }:
        raise HTTPException(
            status_code=422,
            detail={
                "code":
                    "FORMATO_FOTO_INVALIDO",

                "message":
                    "Envie a foto no formato JPEG.",
            },
        )

    # -------------------------------------
    # HASH
    # -------------------------------------

    hash_sha256 = hashlib.sha256(
        conteudo
    ).hexdigest()

    # -------------------------------------
    # STORAGE
    # -------------------------------------

    pasta_pesquisa = (
        STORAGE_ROOT
        / str(id_pesquisa)
        / tipo.lower()
    )

    pasta_pesquisa.mkdir(
        parents=True,
        exist_ok=True,
    )

    nome_arquivo = (
        f"{id_foto}.jpg"
    )

    caminho = (
        pasta_pesquisa
        / nome_arquivo
    )

    storage_key = str(
        caminho.relative_to(
            STORAGE_ROOT
        )
    )

    # Escreve primeiro em temporário
    # e depois troca pelo arquivo final.
    temporario = caminho.with_suffix(
        ".tmp"
    )

    try:
        temporario.write_bytes(
            conteudo
        )

        temporario.replace(
            caminho
        )

    except OSError:
        try:
            temporario.unlink(
                missing_ok=True
            )
        except OSError:
            pass

        raise HTTPException(
            status_code=500,
            detail={
                "code":
                    "ERRO_ARMAZENAMENTO",

                "message":
                    "Não foi possível armazenar a foto.",
            },
        )

    # -------------------------------------
    # BANCO
    # -------------------------------------

    agora = datetime.now(
        timezone.utc
    )

    foto = Foto(
        id_foto=id_foto,

        id_pesquisa=id_pesquisa,

        id_sku=None,

        tipo_evidencia=tipo,

        nome_arquivo_original=(
            arquivo.filename
        ),

        storage_key=storage_key,

        arquivo_url=None,

        mime_type="image/jpeg",

        tamanho_bytes=len(
            conteudo
        ),

        largura=None,
        altura=None,

        hash_sha256=hash_sha256,

        latitude=latitude,

        longitude=longitude,

        precisao_metros=(
            precisao_metros
        ),

        capturada_em_dispositivo=(
            capturada_em_dispositivo
        ),

        recebida_em_servidor=(
            agora
        ),

        status_upload="ENVIADA",
    )

    db.add(foto)

    try:
        db.commit()
        db.refresh(foto)

    except Exception:
        db.rollback()

        try:
            caminho.unlink(
                missing_ok=True
            )
        except OSError:
            pass

        raise

    return montar_resposta(
        foto
    )