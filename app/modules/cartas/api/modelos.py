from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.admin_auth import require_admin
from app.db.dependencies import get_db
from app.modules.cartas.schemas import (
    CartaModeloCreateResponse,
    CartaModeloItemResponse,
    CartaModeloListResponse,
    CartaModeloRedeResponse,
    CartaModeloVersaoResponse,
)
from app.modules.cartas.services import (
    CartaModeloConflictError,
    CartaModeloService,
    CartaModeloValidationError,
)


router = APIRouter(
    prefix="/modelos",
    tags=["Cartas - Modelos"],
)


@router.get(
    "",
    response_model=CartaModeloListResponse,
)
def listar_modelos(
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CartaModeloListResponse:
    service = CartaModeloService(db)

    modelos = service.list_active_models()

    items = []

    for modelo in modelos:
        versao = modelo.versao_ativa

        items.append(
            CartaModeloItemResponse(
                id_modelo=modelo.id_modelo,
                nome=modelo.nome,
                tipo=modelo.tipo,
                granularidade=modelo.granularidade,
                ativo=modelo.ativo,
                criado_em=modelo.criado_em,
                atualizado_em=modelo.atualizado_em,
                redes=[
                    CartaModeloRedeResponse(
                        rede=rede.rede,
                        rede_normalizada=(
                            rede.rede_normalizada
                        ),
                    )
                    for rede in modelo.redes
                ],
                versao_ativa=(
                    CartaModeloVersaoResponse(
                        id_versao=versao.id_versao,
                        numero_versao=(
                            versao.numero_versao
                        ),
                        nome_arquivo_original=(
                            versao.nome_arquivo_original
                        ),
                        mime_type=versao.mime_type,
                        criado_em=versao.criado_em,
                    )
                    if versao is not None
                    else None
                ),
            )
        )

    return CartaModeloListResponse(
        total=len(items),
        items=items,
    )


@router.post(
    "",
    response_model=CartaModeloCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_modelo(
    nome: str = Form(...),
    tipo: str = Form(...),
    granularidade: str = Form(...),
    redes: list[str] = Form(...),
    arquivo: UploadFile = File(...),
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CartaModeloCreateResponse:
    service = CartaModeloService(db)

    try:
        result = service.create_model(
            nome=nome,
            tipo=tipo,
            granularidade=granularidade,
            redes=redes,
            nome_arquivo_original=arquivo.filename or "",
            arquivo=arquivo.file,
        )

    except CartaModeloValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except CartaModeloConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return CartaModeloCreateResponse(
        id_modelo=result.id_modelo,
        id_versao=result.id_versao,
        storage_key=result.storage_key,
        hash_sha256=result.hash_sha256,
        tamanho_bytes=result.tamanho_bytes,
    )
