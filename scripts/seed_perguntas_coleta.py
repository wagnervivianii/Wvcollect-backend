from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.pergunta import Pergunta


PERGUNTAS = [
    {
        "codigo": "RESPONSAVEL_LOJA",
        "texto": "Qual o nome do responsável da loja?",
        "tipo_resposta": "TEXTO",
        "aplica_sku": False,
        "obrigatoria": False,
        "ordem": 1,
    },
    {
        "codigo": "MARCA_ALLEGRA",
        "texto": "A marca Allegra está exposta na loja?",
        "tipo_resposta": "SIM_NAO",
        "aplica_sku": False,
        "obrigatoria": False,
        "ordem": 2,
    },
    {
        "codigo": "MARCA_ANADOR",
        "texto": "A marca Anador está exposta na loja?",
        "tipo_resposta": "SIM_NAO",
        "aplica_sku": False,
        "obrigatoria": False,
        "ordem": 3,
    },
    {
        "codigo": "MARCA_BISOLVON",
        "texto": "A marca Bisolvon está exposta na loja?",
        "tipo_resposta": "SIM_NAO",
        "aplica_sku": False,
        "obrigatoria": False,
        "ordem": 4,
    },
    {
        "codigo": "MARCA_COLIRIO_MOURA_BRASIL",
        "texto": "A marca Colírio Moura Brasil está exposta na loja?",
        "tipo_resposta": "SIM_NAO",
        "aplica_sku": False,
        "obrigatoria": False,
        "ordem": 5,
    },
    {
        "codigo": "MARCA_DORFLEX",
        "texto": "A marca Dorflex está exposta na loja?",
        "tipo_resposta": "SIM_NAO",
        "aplica_sku": False,
        "obrigatoria": False,
        "ordem": 6,
    },
    {
        "codigo": "MARCA_DULCOLAX",
        "texto": "A marca Dulcolax está exposta na loja?",
        "tipo_resposta": "SIM_NAO",
        "aplica_sku": False,
        "obrigatoria": False,
        "ordem": 7,
    },
    {
        "codigo": "MARCA_ENTEROGERMINA",
        "texto": "A marca Enterogermina está exposta na loja?",
        "tipo_resposta": "SIM_NAO",
        "aplica_sku": False,
        "obrigatoria": False,
        "ordem": 8,
    },
    {
        "codigo": "MARCA_NOVALGINA",
        "texto": "A marca Novalgina está exposta na loja?",
        "tipo_resposta": "SIM_NAO",
        "aplica_sku": False,
        "obrigatoria": False,
        "ordem": 9,
    },
    {
        "codigo": "MARCA_OSCAL",
        "texto": "A marca OsCAL está exposta na loja?",
        "tipo_resposta": "SIM_NAO",
        "aplica_sku": False,
        "obrigatoria": False,
        "ordem": 10,
    },
    {
        "codigo": "MARCA_TARGIFOR",
        "texto": "A marca Targifor está exposta na loja?",
        "tipo_resposta": "SIM_NAO",
        "aplica_sku": False,
        "obrigatoria": False,
        "ordem": 11,
    },
    {
        "codigo": "PONTO_EXTRA_CONQUISTADO",
        "texto": "Algum ponto extra foi conquistado?",
        "tipo_resposta": "SIM_NAO",
        "aplica_sku": False,
        "obrigatoria": False,
        "ordem": 12,
    },
]


def main() -> None:
    db = SessionLocal()

    try:
        criadas = 0
        atualizadas = 0

        for dados in PERGUNTAS:
            pergunta = db.scalar(
                select(Pergunta).where(
                    Pergunta.codigo == dados["codigo"]
                )
            )

            if pergunta is None:
                pergunta = Pergunta(
                    **dados,
                    ativo=True,
                )

                db.add(pergunta)
                criadas += 1

            else:
                pergunta.texto = dados["texto"]
                pergunta.tipo_resposta = dados["tipo_resposta"]
                pergunta.aplica_sku = dados["aplica_sku"]
                pergunta.obrigatoria = dados["obrigatoria"]
                pergunta.ordem = dados["ordem"]
                pergunta.ativo = True

                atualizadas += 1

        db.commit()

        print(
            f"Perguntas carregadas com sucesso. "
            f"Criadas: {criadas}. "
            f"Atualizadas: {atualizadas}."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()