from __future__ import annotations

import os
import secrets
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import text

from app.db.session import engine


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

security = HTTPBasic()


def _admin_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """
    Autenticação independente para o painel web.

    Variáveis obrigatórias no .env de produção:
        WVCOLLECT_ADMIN_USER
        WVCOLLECT_ADMIN_PASSWORD
    """
    expected_user = os.getenv("WVCOLLECT_ADMIN_USER", "").strip()
    expected_password = os.getenv("WVCOLLECT_ADMIN_PASSWORD", "")

    if not expected_user or not expected_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin web não configurado.",
        )

    user_ok = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        expected_user.encode("utf-8"),
    )
    password_ok = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        expected_password.encode("utf-8"),
    )

    if not (user_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais administrativas inválidas.",
            headers={"WWW-Authenticate": "Basic"},
        )

    return expected_user


def _mask_cpf(cpf: str | None) -> str | None:
    if not cpf:
        return None

    digits = "".join(ch for ch in cpf if ch.isdigit())
    if len(digits) != 11:
        return "***"

    return f"{digits[:3]}.***.***-{digits[-2:]}"


def _row_dict(row: Any) -> dict[str, Any]:
    return dict(row._mapping)


@router.get("/ping")
def admin_ping(
    _: str = Depends(_admin_credentials),
):
    return {
        "status": "ok",
        "area": "admin",
    }


@router.get("/resumo")
def resumo_operacional(
    _: str = Depends(_admin_credentials),
):
    sql = text(
        """
        WITH pesquisas_ordenadas AS (
            SELECT
                r.id_roteiro,
                r.id_promotor,
                r.id_pdv,
                p.id_pesquisa,
                p.status,
                p.finalizada_em_dispositivo,
                p.envio_com_pendencias,
                ROW_NUMBER() OVER (
                    PARTITION BY r.id_roteiro
                    ORDER BY
                        p.numero_coleta DESC NULLS LAST,
                        p.criado_em DESC NULLS LAST
                ) AS rn
            FROM fto_roteiro r
            LEFT JOIN fto_pesquisa p
                ON p.id_roteiro = r.id_roteiro
            WHERE r.ativo = TRUE
        ),
        atual AS (
            SELECT *
            FROM pesquisas_ordenadas
            WHERE rn = 1
        )
        SELECT
            (SELECT COUNT(*) FROM dim_promotor WHERE ativo = TRUE)
                AS promotores_cadastrados,
            (SELECT COUNT(*) FROM dim_pdv WHERE ativo = TRUE)
                AS pdvs_cadastrados,
            COUNT(*) AS roteiros_ativos,
            COUNT(DISTINCT id_promotor) AS promotores_com_roteiro_ativo,
            COUNT(*) FILTER (
                WHERE id_pesquisa IS NULL
            ) AS pendentes,
            COUNT(*) FILTER (
                WHERE id_pesquisa IS NOT NULL
                  AND NOT (
                    finalizada_em_dispositivo IS NOT NULL
                    OR status IN ('FINALIZADA_LOCAL', 'SINCRONIZADA')
                  )
            ) AS em_andamento,
            COUNT(*) FILTER (
                WHERE
                    finalizada_em_dispositivo IS NOT NULL
                    OR status IN ('FINALIZADA_LOCAL', 'SINCRONIZADA')
            ) AS concluidas,
            COUNT(*) FILTER (
                WHERE envio_com_pendencias = TRUE
            ) AS concluidas_com_pendencias
        FROM atual
        """
    )

    with engine.connect() as connection:
        row = connection.execute(sql).one()

    data = _row_dict(row)

    ativos = int(data.get("roteiros_ativos") or 0)
    concluidas = int(data.get("concluidas") or 0)

    data["execucao_percentual"] = (
        round((concluidas / ativos) * 100, 2)
        if ativos
        else 0.0
    )

    return data


@router.get("/promotores")
def listar_promotores(
    _: str = Depends(_admin_credentials),
):
    sql = text(
        """
        WITH pesquisas_ordenadas AS (
            SELECT
                r.id_roteiro,
                r.id_promotor,
                p.id_pesquisa,
                p.status,
                p.finalizada_em_dispositivo,
                p.envio_com_pendencias,
                ROW_NUMBER() OVER (
                    PARTITION BY r.id_roteiro
                    ORDER BY
                        p.numero_coleta DESC NULLS LAST,
                        p.criado_em DESC NULLS LAST
                ) AS rn
            FROM fto_roteiro r
            LEFT JOIN fto_pesquisa p
                ON p.id_roteiro = r.id_roteiro
            WHERE r.ativo = TRUE
        ),
        atual AS (
            SELECT *
            FROM pesquisas_ordenadas
            WHERE rn = 1
        )
        SELECT
            pr.id_promotor,
            pr.nome,
            pr.cpf,
            pr.ativo,
            COUNT(a.id_roteiro) AS lojas_roteiro,
            COUNT(a.id_roteiro) FILTER (
                WHERE a.id_pesquisa IS NULL
            ) AS pendentes,
            COUNT(a.id_roteiro) FILTER (
                WHERE a.id_pesquisa IS NOT NULL
                  AND NOT (
                    a.finalizada_em_dispositivo IS NOT NULL
                    OR a.status IN ('FINALIZADA_LOCAL', 'SINCRONIZADA')
                  )
            ) AS em_andamento,
            COUNT(a.id_roteiro) FILTER (
                WHERE
                    a.finalizada_em_dispositivo IS NOT NULL
                    OR a.status IN ('FINALIZADA_LOCAL', 'SINCRONIZADA')
            ) AS concluidas,
            COUNT(a.id_roteiro) FILTER (
                WHERE a.envio_com_pendencias = TRUE
            ) AS concluidas_com_pendencias
        FROM dim_promotor pr
        LEFT JOIN atual a
            ON a.id_promotor = pr.id_promotor
        WHERE pr.ativo = TRUE
        GROUP BY
            pr.id_promotor,
            pr.nome,
            pr.cpf,
            pr.ativo
        ORDER BY
            CASE WHEN COUNT(a.id_roteiro) > 0 THEN 0 ELSE 1 END,
            pr.nome
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(sql).all()

    result: list[dict[str, Any]] = []

    for row in rows:
        item = _row_dict(row)
        item["cpf_mascarado"] = _mask_cpf(item.pop("cpf", None))

        roteiro = int(item.get("lojas_roteiro") or 0)
        concluidas = int(item.get("concluidas") or 0)

        item["execucao_percentual"] = (
            round((concluidas / roteiro) * 100, 2)
            if roteiro
            else 0.0
        )

        result.append(item)

    return {
        "total": len(result),
        "items": result,
    }


@router.get("/roteiros")
def listar_roteiros(
    promotor: str | None = Query(default=None, max_length=160),
    situacao: str | None = Query(default=None, max_length=30),
    _: str = Depends(_admin_credentials),
):
    sql = text(
        """
        WITH pesquisas_ordenadas AS (
            SELECT
                p.*,
                ROW_NUMBER() OVER (
                    PARTITION BY p.id_roteiro
                    ORDER BY
                        p.numero_coleta DESC,
                        p.criado_em DESC
                ) AS rn
            FROM fto_pesquisa p
        ),
        atual AS (
            SELECT *
            FROM pesquisas_ordenadas
            WHERE rn = 1
        ),
        base AS (
            SELECT
                r.id_roteiro,
                r.data_inicio,
                r.data_fim,
                pr.id_promotor,
                pr.nome AS promotor,
                pr.cpf,
                pdv.id_pdv,
                pdv.codigo_origem,
                pdv.cnpj,
                pdv.nome_pdv,
                pdv.endereco,
                pdv.bairro,
                pdv.cidade,
                pdv.uf,
                p.id_pesquisa,
                p.numero_coleta,
                p.status AS status_pesquisa,
                p.iniciada_em_dispositivo,
                p.finalizada_em_dispositivo,
                p.recebida_em_servidor,
                p.envio_com_pendencias,
                p.campos_pendentes,
                CASE
                    WHEN p.id_pesquisa IS NULL
                        THEN 'PENDENTE'
                    WHEN
                        p.finalizada_em_dispositivo IS NOT NULL
                        OR p.status IN ('FINALIZADA_LOCAL', 'SINCRONIZADA')
                        THEN 'CONCLUIDA'
                    ELSE 'EM_ANDAMENTO'
                END AS situacao
            FROM fto_roteiro r
            JOIN dim_promotor pr
                ON pr.id_promotor = r.id_promotor
            JOIN dim_pdv pdv
                ON pdv.id_pdv = r.id_pdv
            LEFT JOIN atual p
                ON p.id_roteiro = r.id_roteiro
            WHERE r.ativo = TRUE
        )
        SELECT *
        FROM base
        WHERE
            (
                CAST(:promotor AS TEXT) IS NULL
                OR LOWER(promotor) LIKE
                    '%' || LOWER(CAST(:promotor AS TEXT)) || '%'
            )
            AND (
                CAST(:situacao AS TEXT) IS NULL
                OR situacao = UPPER(CAST(:situacao AS TEXT))
            )
        ORDER BY
            CASE situacao
                WHEN 'EM_ANDAMENTO' THEN 0
                WHEN 'PENDENTE' THEN 1
                WHEN 'CONCLUIDA' THEN 2
                ELSE 3
            END,
            promotor,
            nome_pdv
        """
    )

    params = {
        "promotor": promotor.strip() if promotor else None,
        "situacao": situacao.strip() if situacao else None,
    }

    with engine.connect() as connection:
        rows = connection.execute(sql, params).all()

    items: list[dict[str, Any]] = []

    for row in rows:
        item = _row_dict(row)
        item["cpf_mascarado"] = _mask_cpf(item.pop("cpf", None))
        items.append(item)

    return {
        "total": len(items),
        "items": items,
    }


@router.get("/pesquisas/{id_pesquisa}")
def detalhe_pesquisa(
    id_pesquisa: uuid.UUID,
    _: str = Depends(_admin_credentials),
):
    pesquisa_sql = text(
        """
        SELECT
            p.id_pesquisa,
            p.id_roteiro,
            p.numero_coleta,
            p.id_pesquisa_origem,
            p.status,
            p.iniciada_em_dispositivo,
            p.finalizada_em_dispositivo,
            p.recebida_em_servidor,
            p.sincronizada_em,
            p.criada_offline,
            p.envio_com_pendencias,
            p.campos_pendentes,
            p.pendencias_confirmadas_em_dispositivo,
            p.latitude_inicio,
            p.longitude_inicio,
            p.precisao_inicio_metros,
            p.latitude_fim,
            p.longitude_fim,
            p.precisao_fim_metros,
            pr.id_promotor,
            pr.nome AS promotor,
            pr.cpf,
            pdv.id_pdv,
            pdv.codigo_origem,
            pdv.cnpj,
            pdv.nome_pdv,
            pdv.endereco,
            pdv.bairro,
            pdv.cidade,
            pdv.uf
        FROM fto_pesquisa p
        JOIN dim_promotor pr
            ON pr.id_promotor = p.id_promotor
        JOIN dim_pdv pdv
            ON pdv.id_pdv = p.id_pdv
        WHERE p.id_pesquisa = :id_pesquisa
        """
    )

    respostas_sql = text(
        """
        SELECT
            r.id_resposta,
            q.codigo,
            q.texto AS pergunta,
            q.tipo_resposta,
            q.ordem,
            r.valor,
            r.respondida_em_dispositivo,
            r.recebida_em_servidor
        FROM fto_resposta r
        JOIN dim_pergunta q
            ON q.id_pergunta = r.id_pergunta
        WHERE r.id_pesquisa = :id_pesquisa
        ORDER BY q.ordem, q.texto
        """
    )

    fotos_sql = text(
        """
        SELECT
            f.id_foto,
            f.tipo_evidencia,
            f.nome_arquivo_original,
            f.mime_type,
            f.tamanho_bytes,
            f.largura,
            f.altura,
            f.latitude,
            f.longitude,
            f.precisao_metros,
            f.capturada_em_dispositivo,
            f.recebida_em_servidor,
            f.status_upload
        FROM fto_foto f
        WHERE f.id_pesquisa = :id_pesquisa
        ORDER BY
            CASE f.tipo_evidencia
                WHEN 'ANTES' THEN 1
                WHEN 'DEPOIS' THEN 2
                WHEN 'PONTO_EXTRA' THEN 3
                WHEN 'GIRO_ESTOQUE' THEN 4
                ELSE 9
            END,
            f.capturada_em_dispositivo
        """
    )

    params = {"id_pesquisa": id_pesquisa}

    with engine.connect() as connection:
        pesquisa_row = connection.execute(
            pesquisa_sql,
            params,
        ).first()

        if pesquisa_row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pesquisa não encontrada.",
            )

        respostas_rows = connection.execute(
            respostas_sql,
            params,
        ).all()

        fotos_rows = connection.execute(
            fotos_sql,
            params,
        ).all()

    pesquisa = _row_dict(pesquisa_row)
    pesquisa["cpf_mascarado"] = _mask_cpf(
        pesquisa.pop("cpf", None)
    )

    respostas = [
        _row_dict(row)
        for row in respostas_rows
    ]

    fotos: list[dict[str, Any]] = []
    for row in fotos_rows:
        foto = _row_dict(row)
        foto["arquivo_endpoint"] = (
            f"/admin/fotos/{foto['id_foto']}/arquivo"
        )
        fotos.append(foto)

    return {
        "pesquisa": pesquisa,
        "respostas": respostas,
        "fotos": fotos,
    }


def _resolve_photo_path(storage_key: str) -> Path | None:
    project_root = Path.cwd().resolve()

    configured = os.getenv(
        "WVCOLLECT_STORAGE_DIR",
        "storage/fotos",
    ).strip()

    storage_root = Path(configured)
    if not storage_root.is_absolute():
        storage_root = project_root / storage_root
    storage_root = storage_root.resolve()

    raw = Path(storage_key)

    candidates: list[Path] = []

    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.extend(
            [
                project_root / raw,
                storage_root / raw,
                storage_root / raw.name,
            ]
        )

    allowed_roots = {
        storage_root,
        (project_root / "storage").resolve(),
    }

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue

        if not any(
            resolved == root or resolved.is_relative_to(root)
            for root in allowed_roots
        ):
            continue

        if resolved.is_file():
            return resolved

    return None


@router.get("/fotos/{id_foto}/arquivo")
def obter_arquivo_foto(
    id_foto: uuid.UUID,
    _: str = Depends(_admin_credentials),
):
    sql = text(
        """
        SELECT
            storage_key,
            mime_type,
            nome_arquivo_original
        FROM fto_foto
        WHERE id_foto = :id_foto
        """
    )

    with engine.connect() as connection:
        row = connection.execute(
            sql,
            {"id_foto": id_foto},
        ).first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foto não encontrada.",
        )

    data = _row_dict(row)

    photo_path = _resolve_photo_path(data["storage_key"])

    if photo_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo físico da foto não encontrado.",
        )

    media_type = data.get("mime_type") or "image/jpeg"
    filename = (
        data.get("nome_arquivo_original")
        or photo_path.name
    )

    return FileResponse(
        path=str(photo_path),
        media_type=media_type,
        filename=filename,
        content_disposition_type="inline",
    )

