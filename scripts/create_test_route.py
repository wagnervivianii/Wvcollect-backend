from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.pdv import PDV
from app.models.promotor import Promotor
from app.models.roteiro import Roteiro


CPF_TESTE = "99999999999"


PDVS_TESTE = [
    {
        "codigo_origem": "TESTE-001",
        "cnpj": "11111111000111",
        "nome_pdv": "Loja Teste Centro",
        "endereco": "Rua das Flores, 100",
        "bairro": "Centro",
        "cidade": "São Paulo",
        "uf": "SP",
    },
    {
        "codigo_origem": "TESTE-002",
        "cnpj": "22222222000122",
        "nome_pdv": "Loja Teste Shopping",
        "endereco": "Avenida Principal, 500",
        "bairro": "Jardins",
        "cidade": "São Paulo",
        "uf": "SP",
    },
]


def main() -> None:
    with SessionLocal() as db:
        promotor = db.scalar(
            select(Promotor).where(
                Promotor.cpf == CPF_TESTE
            )
        )

        if promotor is None:
            raise RuntimeError(
                "Promotor Teste não encontrado. "
                "Execute create_test_promotor.py primeiro."
            )

        print(
            f"Promotor: {promotor.nome} "
            f"({promotor.id_promotor})"
        )

        for dados_pdv in PDVS_TESTE:
            pdv = db.scalar(
                select(PDV).where(
                    PDV.codigo_origem
                    == dados_pdv["codigo_origem"]
                )
            )

            if pdv is None:
                pdv = PDV(
                    **dados_pdv,
                    ativo=True,
                )

                db.add(pdv)
                db.flush()

                print(
                    f"PDV criado: {pdv.nome_pdv}"
                )

            else:
                for campo, valor in dados_pdv.items():
                    setattr(
                        pdv,
                        campo,
                        valor,
                    )

                pdv.ativo = True

                print(
                    f"PDV atualizado: {pdv.nome_pdv}"
                )

            roteiro = db.scalar(
                select(Roteiro).where(
                    Roteiro.id_promotor
                    == promotor.id_promotor,
                    Roteiro.id_pdv
                    == pdv.id_pdv,
                )
            )

            if roteiro is None:
                roteiro = Roteiro(
                    id_promotor=promotor.id_promotor,
                    id_pdv=pdv.id_pdv,
                    ativo=True,
                )

                db.add(roteiro)

                print(
                    f"Roteiro criado: {pdv.nome_pdv}"
                )

            else:
                roteiro.ativo = True

                print(
                    f"Roteiro já existente: {pdv.nome_pdv}"
                )

        db.commit()

        print()
        print("Carga de teste concluída.")


if __name__ == "__main__":
    main()