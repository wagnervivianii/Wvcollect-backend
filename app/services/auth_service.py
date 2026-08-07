import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.promotor import Promotor


def normalize_cpf(cpf: str) -> str:
    """
    Remove qualquer caractere que não seja número.

    Exemplo:
    123.456.789-00 -> 12345678900
    """
    return re.sub(r"\D", "", cpf)


def authenticate_promotor(
    db: Session,
    cpf: str,
    senha: str,
) -> Promotor | None:
    """
    Autentica um promotor por CPF e senha.

    Retorna o Promotor quando válido.
    Retorna None quando:
    - CPF não existe;
    - promotor está inativo;
    - ainda não possui senha;
    - senha está incorreta.
    """

    cpf_normalizado = normalize_cpf(cpf)

    if len(cpf_normalizado) != 11:
        return None

    statement = select(Promotor).where(
        Promotor.cpf == cpf_normalizado
    )

    promotor = db.scalar(statement)

    if promotor is None:
        return None

    if not promotor.ativo:
        return None

    if not promotor.senha_hash:
        return None

    if not verify_password(
        senha,
        promotor.senha_hash,
    ):
        return None

    return promotor