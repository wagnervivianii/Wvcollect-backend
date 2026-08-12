from enum import Enum


class CartaTipo(str, Enum):
    """
    Define como o documento será obtido no momento do envio.

    ESTATICO:
        O arquivo armazenado é utilizado diretamente.
        Não existe geração de um novo documento.

    VARIAVEL:
        O modelo armazenado contém campos que serão
        preenchidos com dados temporários da planilha.
    """

    ESTATICO = "ESTATICO"
    VARIAVEL = "VARIAVEL"


class CartaGranularidade(str, Enum):
    """
    Define quantas cartas devem resultar dos registros
    encontrados na planilha.

    PROMOTOR_REDE:
        Um promotor atendendo vários PDVs da mesma rede
        recebe apenas uma carta.

    PDV:
        Cada combinação de promotor e PDV gera uma carta.
    """

    PROMOTOR_REDE = "PROMOTOR_REDE"
    PDV = "PDV"
