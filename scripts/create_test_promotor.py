from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.promotor import Promotor


CPF_TESTE = "99999999999"
SENHA_TESTE = "Teste@123"
NOME_TESTE = "Promotor Teste"


def main() -> None:
    with SessionLocal() as db:
        promotor = db.scalar(
            select(Promotor).where(
                Promotor.cpf == CPF_TESTE
            )
        )

        if promotor is None:
            promotor = Promotor(
                nome=NOME_TESTE,
                cpf=CPF_TESTE,
                senha_hash=hash_password(SENHA_TESTE),
                ativo=True,
            )

            db.add(promotor)
            db.commit()
            db.refresh(promotor)

            print("Promotor criado.")
        else:
            # Mantemos o teste reproduzível.
            promotor.nome = NOME_TESTE
            promotor.senha_hash = hash_password(SENHA_TESTE)
            promotor.ativo = True

            db.commit()
            db.refresh(promotor)

            print("Promotor de teste atualizado.")

        print("ID:", promotor.id_promotor)
        print("Nome:", promotor.nome)
        print("CPF:", promotor.cpf)
        print("Ativo:", promotor.ativo)


if __name__ == "__main__":
    main()